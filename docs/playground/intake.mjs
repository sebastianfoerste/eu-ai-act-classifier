// Interpreter for the guided-intake definition in intake.json, which
// scripts/build_playground.py generates from src/eu_ai_act_classifier/intake.py.
// It mirrors that module's interpreter and holds no legal logic of its own:
// questions, order, skip conditions and "I don't know" handling all come from
// the definition. tests/playground/intake.test.mjs holds it to Python's output.

export const UNKNOWN = "unknown";

export function readField(profile, field) {
  let value = profile;
  for (const part of field.split(".")) value = value && typeof value === "object" ? value[part] : undefined;
  return value === undefined ? null : value;
}

function writeField(profile, field, value) {
  const parts = field.split(".");
  const last = parts.pop();
  let target = profile;
  for (const part of parts) target = target[part] ??= {};
  target[last] = value;
}

export function holds(condition, profile) {
  if (!condition) return true;
  if ("all" in condition) return condition.all.every(c => holds(c, profile));
  if ("any" in condition) return condition.any.some(c => holds(c, profile));
  if ("not" in condition) return !holds(condition.not, profile);
  const value = readField(profile, condition.field);
  if ("is" in condition) return value === condition.is;
  if ("in" in condition) return condition.in.includes(value);
  if ("has" in condition) return Array.isArray(value) && value.includes(condition.has);
  if ("empty" in condition) return (!value || value.length === 0) === condition.empty;
  throw new Error("Unknown intake condition");
}

const baseProfile = definition => structuredClone(definition.defaults);

// Apply answers in question order. A question is asked only if its condition
// holds on the profile built from the answers before it.
export function answersToProfile(definition, answers) {
  const profile = baseProfile(definition);
  const asked = [], blocked = [], missing = [];
  for (const question of definition.questions) {
    if (!holds(question.show_if, profile)) continue;
    asked.push(question.id);
    const answer = answers[question.id];
    if (answer === UNKNOWN) {
      const policy = question.unknown;
      if (!policy || policy === "block") blocked.push(question.id);
      else writeField(profile, question.field, policy.value);
      continue;
    }
    if (!isAnswered(question, answer)) {
      missing.push(question.id);
      continue;
    }
    switch (question.kind) {
      case "details":
        for (const entry of question.fields) {
          const text = (answer?.[entry.field] ?? "").trim();
          writeField(profile, entry.field, entry.type === "date" ? text || null : text);
        }
        break;
      case "boolean": writeField(profile, question.field, answer === "yes"); break;
      case "single": writeField(profile, question.field, answer === "none" ? null : answer); break;
      case "multi": writeField(profile, question.field, [...answer]); break;
      case "flags":
        for (const option of question.options) writeField(profile, option.field, answer.includes(option.field));
        break;
      case "number": writeField(profile, question.field, answer === "" || answer === null ? null : Number(answer)); break;
      default: throw new Error("Unknown question kind");
    }
  }
  return { profile, asked, blocked, missing };
}

export function isAnswered(question, answer) {
  switch (question.kind) {
    case "details":
      return question.fields.every(entry => !entry.required || String(answer?.[entry.field] ?? "").trim());
    case "boolean": return answer === "yes" || answer === "no";
    case "single": return answer === "none" || question.options.some(option => option.value === answer);
    case "multi":
      return Array.isArray(answer) && (!question.required || answer.length > 0)
        && answer.every(value => question.options.some(option => option.value === value));
    case "flags": return Array.isArray(answer);
    case "number": return answer === "" || answer === null || (answer !== undefined && Number.isFinite(Number(answer)));
    default: return false;
  }
}

// A field-level problem with an answer, as a sentence, or "" when it is fine.
export function answerError(question, answer) {
  if (answer === UNKNOWN) return "";
  if (question.kind === "details") {
    for (const entry of question.fields) {
      const text = String(answer?.[entry.field] ?? "").trim();
      if (entry.required && !text) return `Enter the ${entry.label.toLowerCase()}.`;
      if (entry.type === "date" && text && !isIsoDate(text)) return `${entry.label}: enter a date as YYYY-MM-DD, for example 2026-03-01.`;
    }
    return "";
  }
  if (question.kind === "number" && answer !== "" && answer !== null && answer !== undefined && !Number.isFinite(Number(answer))) {
    return "Enter a number, for example 2e25, or leave it blank.";
  }
  if (question.kind === "multi" && question.required && Array.isArray(answer) && !answer.length) return "Select at least one option.";
  return isAnswered(question, answer) ? "" : "Select an answer.";
}

export function isIsoDate(text) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) return false;
  const date = new Date(`${text}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === text;
}

// The answers that reproduce a profile, so an example or the JSON editor's
// profile can be opened in the guided intake.
export function profileToAnswers(definition, profile) {
  const full = baseProfile(definition);
  for (const [key, value] of Object.entries(profile)) {
    if (key === "derogation") Object.assign(full.derogation, value);
    else if (key !== "$schema") full[key] = value;
  }
  const answers = {};
  for (const question of definition.questions) {
    if (question.kind === "details") {
      answers[question.id] = Object.fromEntries(question.fields.map(entry => [entry.field, readField(full, entry.field) || ""]));
    } else if (question.kind === "flags") {
      answers[question.id] = question.options.filter(option => readField(full, option.field)).map(option => option.field);
    } else {
      const value = readField(full, question.field);
      if (question.kind === "boolean") answers[question.id] = value === null ? UNKNOWN : value ? "yes" : "no";
      else if (question.kind === "single") answers[question.id] = value === null ? "none" : value;
      else if (question.kind === "multi") answers[question.id] = [...value];
      else if (question.kind === "number") answers[question.id] = value === null ? "" : value;
    }
  }
  return answers;
}

// The questions asked for these answers, in order: the wizard's page list.
export function askedQuestions(definition, answers) {
  const { asked } = answersToProfile(definition, answers);
  return definition.questions.filter(question => asked.includes(question.id));
}

// Human-readable answer for the check-answers page.
export function describeAnswer(definition, question, answer) {
  if (answer === UNKNOWN) {
    const policy = question.unknown;
    if (!policy || policy === "block") return `${definition.answers.unknown}: counsel must answer before classification`;
    return `${definition.answers.unknown}: recorded as ${policy.value === null ? "not confirmed (null)" : policy.value}, routed to review`;
  }
  if (answer === undefined) return "Not answered";
  switch (question.kind) {
    case "details":
      return question.fields.map(entry => `${entry.label}: ${String(answer?.[entry.field] ?? "").trim() || "Not provided"}`).join("\n");
    case "boolean": return definition.answers[answer] ?? "Not answered";
    case "single":
      return answer === "none" ? question.none_label : question.options.find(option => option.value === answer)?.label ?? answer;
    case "multi":
      return answer.length ? answer.map(value => question.options.find(option => option.value === value)?.label ?? value).join("\n") : question.none_label ?? "None";
    case "flags":
      return answer.length ? answer.map(field => question.options.find(option => option.field === field)?.label ?? field).join("\n") : question.none_label ?? "None";
    case "number": return answer === "" || answer === null ? "Not provided" : String(answer);
    default: return String(answer);
  }
}

// Serialise the profile the way the JSON editor shows it: only fields that
// differ from the defaults, plus the name.
export function compactProfile(definition, profile) {
  const out = { name: profile.name };
  for (const [key, value] of Object.entries(profile)) {
    if (key === "name") continue;
    const fallback = definition.defaults[key];
    if (key === "derogation") {
      const changed = Object.fromEntries(Object.entries(value).filter(([flag, set]) => set !== fallback[flag]));
      if (Object.keys(changed).length) out.derogation = changed;
    } else if (JSON.stringify(value) !== JSON.stringify(fallback)) out[key] = value;
  }
  return out;
}
