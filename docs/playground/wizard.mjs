// Guided intake: one question per page, then a check-answers page. Renders the
// definition in intake.json through the pure helpers in intake.mjs.
import { UNKNOWN, answerError, answersToProfile, askedQuestions, compactProfile, describeAnswer, readField } from "./intake.mjs";

const CHECK = "check";

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function button(text, className, onClick) {
  const element = node("button", className, text);
  element.type = "button";
  element.addEventListener("click", onClick);
  return element;
}

export function createWizard({ root, definition, canClassify, onClassify, onEditJson, onChange }) {
  let answers = {};
  let page = null;
  let error = "";
  const byId = Object.fromEntries(definition.questions.map(q => [q.id, q]));

  const pages = () => askedQuestions(definition, answers);
  const firstPage = () => pages()[0]?.id ?? CHECK;

  function go(next, { focus = true } = {}) {
    page = next;
    error = "";
    render();
    if (focus) root.querySelector("[data-focus]")?.focus();
  }

  function setAnswer(id, value) {
    answers = { ...answers, [id]: value };
    error = "";
    onChange();
  }

  function current() { return page === CHECK ? null : byId[page]; }

  function next() {
    const question = current();
    // Optional text pages count as answered once the user continues past them.
    if (answers[question.id] === undefined && question.kind === "details") setAnswer(question.id, {});
    if (answers[question.id] === undefined && question.kind === "number") setAnswer(question.id, "");
    const message = answerError(question, answers[question.id]);
    if (message) {
      error = message;
      render();
      root.querySelector(".error-summary")?.focus();
      return;
    }
    const list = pages();
    const index = list.findIndex(q => q.id === question.id);
    // Questions after this one may have appeared or gone; continue with the
    // first unanswered one, else go to the check-answers page.
    const following = list.slice(index + 1);
    const open = following.find(q => answers[q.id] === undefined);
    go(open ? open.id : CHECK);
  }

  function back() {
    const list = pages();
    if (page === CHECK) return go(list.at(-1)?.id ?? CHECK);
    const index = list.findIndex(q => q.id === page);
    if (index > 0) go(list[index - 1].id);
  }

  // Checkbox groups re-render to keep "None" and "I don't know" exclusive;
  // keep keyboard focus on the box the user just toggled.
  function rerender(name, value) {
    render();
    root.querySelector(`input[name="${name}"][value="${CSS.escape(value)}"]`)?.focus();
  }

  function choice(type, name, value, label, checked, onSelect, extraClass = "") {
    const wrap = node("label", `choice ${extraClass}`.trim());
    const input = node("input");
    input.type = type;
    input.name = name;
    input.value = value;
    input.checked = checked;
    input.addEventListener("change", () => onSelect(input.checked));
    wrap.append(input, node("span", "", label));
    return wrap;
  }

  function renderQuestion(question) {
    const answer = answers[question.id];
    const list = pages();
    const position = list.findIndex(q => q.id === question.id) + 1;
    const form = node("form", "question");
    form.noValidate = true;
    form.addEventListener("submit", event => { event.preventDefault(); next(); });

    const top = node("div", "question-top");
    top.append(node("span", "progress", `Question ${position} of ${list.length}`));
    if (position > 1) top.append(button("Back", "text-button back-link", back));
    form.append(top);

    if (error) {
      const summary = node("div", "error-summary");
      summary.setAttribute("role", "alert");
      summary.tabIndex = -1;
      summary.append(node("h4", "", "There is a problem"), node("p", "", error));
      form.append(summary);
    }

    const fieldset = node("fieldset");
    const legend = node("legend");
    const heading = node("h3", "question-title", question.title);
    heading.tabIndex = -1;
    heading.dataset.focus = "";
    legend.append(heading);
    fieldset.append(legend);
    if (question.article) fieldset.append(node("p", "question-article", question.article));
    if (question.hint) fieldset.append(node("p", "question-hint", question.hint));

    const name = `q-${question.id}`;
    const unknownLabel = definition.answers.unknown;
    if (question.kind === "details") {
      for (const entry of question.fields) {
        const id = `${name}-${entry.field}`;
        const label = node("label", "text-label", entry.required ? entry.label : `${entry.label} (optional)`);
        label.htmlFor = id;
        const input = node("input", "text-input");
        input.id = id;
        input.type = "text";
        if (entry.type === "date") { input.inputMode = "numeric"; input.placeholder = "YYYY-MM-DD"; }
        input.autocomplete = "off";
        input.value = answer?.[entry.field] ?? "";
        input.addEventListener("input", () => setAnswer(question.id, { ...(answers[question.id] ?? {}), [entry.field]: input.value }));
        fieldset.append(label, input);
      }
    } else if (question.kind === "number") {
      const id = `${name}-input`;
      const label = node("label", "text-label", "FLOP (optional)");
      label.htmlFor = id;
      const input = node("input", "text-input");
      input.id = id;
      input.type = "text";
      input.inputMode = "decimal";
      input.autocomplete = "off";
      input.value = answer ?? "";
      input.addEventListener("input", () => setAnswer(question.id, input.value.trim()));
      fieldset.append(label, input);
    } else if (question.kind === "boolean" || question.kind === "single") {
      const options = question.kind === "boolean"
        ? [["yes", definition.answers.yes], ["no", definition.answers.no]]
        : [...question.options.map(o => [o.value, o.label]), ["none", question.none_label]];
      const group = node("div", "choices");
      for (const [value, label] of options) group.append(choice("radio", name, value, label, answer === value, () => setAnswer(question.id, value)));
      if (question.unknown) {
        group.append(node("p", "choice-divider", "or"));
        group.append(choice("radio", name, UNKNOWN, unknownLabel, answer === UNKNOWN, () => setAnswer(question.id, UNKNOWN)));
      }
      fieldset.append(group);
    } else {
      const selected = Array.isArray(answer) ? answer : [];
      const options = question.kind === "flags"
        ? question.options.map(o => [o.field, o.label])
        : question.options.map(o => [o.value, o.label]);
      const group = node("div", "choices");
      for (const [value, label] of options) {
        group.append(choice("checkbox", name, value, label, selected.includes(value), checked => {
          const base = Array.isArray(answers[question.id]) ? answers[question.id] : [];
          setAnswer(question.id, checked ? [...base.filter(v => v !== value), value] : base.filter(v => v !== value));
          rerender(name, value);
        }));
      }
      if (question.none_label) {
        group.append(node("p", "choice-divider", "or"));
        group.append(choice("checkbox", name, "none", question.none_label, Array.isArray(answer) && !answer.length, checked => {
          setAnswer(question.id, checked ? [] : undefined);
          rerender(name, "none");
        }));
      }
      if (question.unknown) {
        if (!question.none_label) group.append(node("p", "choice-divider", "or"));
        group.append(choice("checkbox", name, UNKNOWN, unknownLabel, answer === UNKNOWN, checked => {
          setAnswer(question.id, checked ? UNKNOWN : undefined);
          rerender(name, UNKNOWN);
        }));
      }
      fieldset.append(group);
    }
    if (question.unknown === "block") fieldset.append(node("p", "question-hint unknown-note", `${unknownLabel} pauses the run: counsel characterises this fact before classification.`));
    else if (question.unknown) fieldset.append(node("p", "question-hint unknown-note", `${unknownLabel} is recorded and the result is routed to review.`));

    form.append(fieldset);
    const actions = node("div", "question-actions");
    const submit = node("button", "primary", "Continue");
    submit.type = "submit";
    actions.append(submit);
    form.append(actions);
    return form;
  }

  function renderCheck() {
    const wrap = node("div", "check-answers");
    const top = node("div", "question-top");
    top.append(node("span", "progress", "Check your answers"));
    if (pages().length) top.append(button("Back", "text-button back-link", back));
    wrap.append(top);
    const heading = node("h3", "question-title", "Check your answers before classifying");
    heading.tabIndex = -1;
    heading.dataset.focus = "";
    wrap.append(heading);

    const { profile, asked, blocked, missing } = answersToProfile(definition, answers);
    if (blocked.length || missing.length) {
      const notice = node("div", blocked.length ? "notice block-notice" : "error-summary");
      notice.setAttribute("role", "status");
      if (blocked.length) {
        notice.append(node("strong", "", "Counsel must answer before classification"));
        notice.append(node("p", "", `${blocked.length} answer${blocked.length > 1 ? "s are" : " is"} "${definition.answers.unknown}" on a fact the engine cannot assume. No result is produced until a qualified reviewer characterises ${blocked.length > 1 ? "them" : "it"}.`));
      }
      if (missing.length) notice.append(node("p", "", `${missing.length} question${missing.length > 1 ? "s are" : " is"} not answered yet.`));
      wrap.append(notice);
    }

    const list = node("dl", "answer-list");
    for (const id of asked) {
      const question = byId[id];
      const row = node("div", "answer-row");
      if (blocked.includes(id)) row.classList.add("is-blocked");
      if (missing.includes(id)) row.classList.add("is-missing");
      const term = node("dt");
      term.append(node("span", "", question.title));
      if (question.article) term.append(node("small", "", question.article));
      const value = node("dd", "", missing.includes(id) ? "Not answered" : describeAnswer(definition, question, answers[id]));
      const change = node("dd", "change");
      const link = button("Change", "text-button", () => go(id));
      link.append(node("span", "sr-only", ` ${question.title}`));
      change.append(link);
      row.append(term, value, change);
      list.append(row);
    }
    wrap.append(list);

    const skipped = definition.questions.filter(q => !asked.includes(q.id));
    if (skipped.length) {
      const details = node("details", "defaults");
      details.append(node("summary", "", `Not asked: ${skipped.length} question${skipped.length > 1 ? "s" : ""} keep the default value`));
      details.append(node("p", "question-hint", "Earlier answers settle these. Python tests try every answer to them over a grid of earlier answers and find no change in the result."));
      const defaults = node("ul");
      for (const question of skipped) {
        const fields = question.kind === "flags" ? question.options.map(o => o.field) : question.kind === "details" ? question.fields.map(f => f.field) : [question.field];
        defaults.append(node("li", "", `${question.title} ${fields.map(f => `${f} = ${JSON.stringify(readField(profile, f))}`).join(", ")}`));
      }
      details.append(defaults);
      wrap.append(details);
    }

    const actions = node("div", "question-actions");
    const ready = !blocked.length && !missing.length;
    const classify = node("button", "primary", "Classify");
    classify.type = "button";
    classify.disabled = !ready || !canClassify();
    classify.addEventListener("click", () => onClassify(compactProfile(definition, profile)));
    actions.append(classify);
    const json = button("Edit as JSON", "text-button", () => onEditJson(compactProfile(definition, profile)));
    json.disabled = !ready;
    actions.append(json);
    wrap.append(actions);
    if (ready && !canClassify()) wrap.append(node("p", "question-hint", "The rule engine is still loading. Classify becomes available when it is ready."));
    return wrap;
  }

  function render() {
    if (page === null) page = firstPage();
    if (page !== CHECK && !pages().some(q => q.id === page)) page = CHECK;
    root.replaceChildren(page === CHECK ? renderCheck() : renderQuestion(current()));
  }

  return {
    render,
    // Re-render the check-answers page when the engine becomes ready; other
    // pages are left alone so focus and typing are not disturbed.
    refresh() { if (page === CHECK) render(); },
    reset() { answers = {}; go(firstPage(), { focus: false }); onChange(); },
    review(newAnswers) { answers = structuredClone(newAnswers); go(CHECK, { focus: false }); onChange(); },
    get answers() { return answers; },
  };
}
