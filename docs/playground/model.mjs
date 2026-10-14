// Pure input and report helpers shared with the browser regression tests.
export const MAX_BYTES = 1024 * 1024;

// Labels mirror _TIER_LABEL in src/eu_ai_act_classifier/report.py.
export const TIERS = {
  prohibited: { label: "Prohibited", basis: "Art. 5 AIA", tone: "red" },
  high_risk: { label: "High-risk", basis: "Art. 6 AIA", tone: "amber" },
  limited_risk: { label: "Limited risk", basis: "Transparency only, Art. 50 AIA", tone: "blue" },
  minimal_risk: { label: "Minimal risk", basis: "No tier-specific obligations", tone: "green" },
  outside_scope: { label: "Outside AI Act scope", basis: "Scope and intake screens", tone: "grey" },
};

export const DISPOSITIONS = {
  determined: "Determined",
  requires_review: "Requires review",
};

export const ROLE_LABELS = {
  provider: "Provider",
  deployer: "Deployer",
  importer: "Importer",
  distributor: "Distributor",
  authorized_representative: "Authorised representative",
  gpai_provider: "GPAI model provider",
};

// "5.1.c" -> "Art. 5(1)(c)" and "III.5.b" -> "Annex III(5)(b)", as the engine cites them.
export function practiceCitation(value) {
  const match = /^(\d+)\.(\d+)\.([a-z])$/.exec(value);
  return match ? `Art. ${match[1]}(${match[2]})(${match[3]})` : String(value);
}

export function annexCitation(value) {
  if (value === "III.unsure") return "Annex III, point unsettled";
  const match = /^III\.(\d+)(?:\.([a-z]))?$/.exec(value);
  return match ? `Annex III(${match[1]})${match[2] ? `(${match[2]})` : ""}` : String(value);
}

export function parseProfile(text) {
  if (new TextEncoder().encode(text).length > MAX_BYTES) {
    throw new Error("This playground accepts profiles up to 1 MB. Use the CLI for larger files.");
  }
  let profile;
  try { profile = JSON.parse(text); }
  catch { throw new Error("The profile is not valid JSON. Check quotation marks, commas and brackets."); }
  if (!profile || typeof profile !== "object" || Array.isArray(profile)) {
    throw new Error("The profile must be a JSON object. Load an example to see the structure.");
  }
  if (typeof profile.name !== "string" || !profile.name.trim()) {
    throw new Error('Add a "name" for the system. It is the only required field.');
  }
  return profile;
}

export function reportIsCurrent(report, checked, current) {
  return Boolean(report) && Boolean(checked) && checked.text === current.text && checked.advisory === current.advisory;
}

export function groupByRole(obligations) {
  const groups = new Map();
  for (const obligation of obligations) {
    if (!groups.has(obligation.applies_to)) groups.set(obligation.applies_to, []);
    groups.get(obligation.applies_to).push(obligation);
  }
  return [...groups].map(([role, items]) => ({ role, label: ROLE_LABELS[role] ?? role, items }));
}

export function matchesQuery(values, search = "") {
  const query = search.trim().toLowerCase();
  return !query || values.filter(value => value !== undefined && value !== null)
    .join(" ").toLowerCase().includes(query);
}

// The formatter walks the profile's own characters. Round-tripping through
// JSON.parse/JSON.stringify would rewrite numbers such as 5e+25 and drop
// duplicate keys, none of which Python's json does. Callers validate first.
const WHITESPACE = " \t\n\r";

function skipWhitespace(text, i) {
  while (i < text.length && WHITESPACE.includes(text[i])) i += 1;
  return i;
}

function stringEnd(text, i) {
  for (i += 1; text[i] !== '"'; i += 1) if (text[i] === "\\") i += 1;
  return i + 1;
}

export function formatProfile(text) {
  parseProfile(text);
  let out = "", depth = 0;
  const newline = () => "\n" + "  ".repeat(depth);
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === '"') {
      const end = stringEnd(text, i);
      out += text.slice(i, end);
      i = end - 1;
    } else if (char === "{" || char === "[") {
      const next = skipWhitespace(text, i + 1);
      if (text[next] === (char === "{" ? "}" : "]")) { out += char + text[next]; i = next; }
      else { depth += 1; out += char + newline(); }
    } else if (char === "}" || char === "]") { depth -= 1; out += newline() + char; }
    else if (char === ",") out += "," + newline();
    else if (char === ":") out += ": ";
    else if (!WHITESPACE.includes(char)) out += char;
  }
  return out;
}

// An obligation-graph item's date line. A null date turns on a fact the profile
// does not give; applies_on_assessment_date is null without an assessment date.
export function applicationLabel(item) {
  if (!item.application_date) return "application date unknown (see open questions)";
  const on = item.applies_on_assessment_date;
  const status = on === true ? ", applies on the assessment date" : on === false ? ", not yet on the assessment date" : "";
  return `applies from ${item.application_date}${status}`;
}

export function describeDefault(field) {
  return field.default === null || field.default === undefined ? "null" : JSON.stringify(field.default);
}
