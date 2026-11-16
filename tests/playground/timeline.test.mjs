import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync } from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { assessmentLabel, renderTimeline, shownDates, timelineModel } from "../../docs/playground/timeline.mjs";

// A small DOM stand-in, as in wizard.test.mjs: renderTimeline only creates elements,
// sets text, classes and attributes, and appends children.
class FakeElement {
  constructor(tag) { this.tagName = tag; this.children = []; this.attributes = {}; this.className = ""; }
  append(...nodes) { this.children.push(...nodes); }
  setAttribute(name, value) { this.attributes[name] = value; }
  *walk() { yield this; for (const child of this.children) yield* child.walk(); }
  all(className) { return [...this.walk()].filter(e => e.className.split(" ").includes(className)); }
}
const fakeDocument = { createElement: tag => new FakeElement(tag) };

const ROOT = fileURLToPath(new URL("../..", import.meta.url));

// The engine's reports for every bundled example, as the playground receives them.
function bundledReports() {
  const script = [
    "import json, pathlib",
    "from eu_ai_act_classifier import SystemProfile, classify",
    "samples = json.loads(pathlib.Path('docs/playground/samples.json').read_text(encoding='utf-8'))",
    "print(json.dumps({key: classify(SystemProfile.model_validate(profile)).model_dump(mode='json')",
    "                  for key, profile in samples['profiles'].items()}))",
  ].join("\n");
  const out = execFileSync("uv", ["run", "--no-sync", "python", "-c", script], { cwd: ROOT, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  return JSON.parse(out);
}

const reports = bundledReports();

test("covers every bundled example", () => {
  const samples = JSON.parse(readFileSync(new URL("../../docs/playground/samples.json", import.meta.url), "utf8"));
  assert.deepEqual(Object.keys(reports).sort(), Object.keys(samples.profiles).sort());
});

test("shows exactly the dates the report carries, in date order", () => {
  for (const [key, report] of Object.entries(reports)) {
    const model = timelineModel(report);
    const carried = new Set([
      ...report.timeline.map(t => t.applies_from),
      ...report.obligation_graph.map(g => g.application_date).filter(d => d != null),
    ]);
    const shown = shownDates(model);
    assert.deepEqual(new Set(shown), carried, key);
    assert.equal(shown.length, carried.size, `${key}: a date shown twice`);
    assert.deepEqual(shown, [...shown].sort(), `${key}: dates out of order`);
  }
});

test("places every milestone and graph item once, under its own date", () => {
  for (const [key, report] of Object.entries(reports)) {
    const model = timelineModel(report);
    const milestones = model.columns.flatMap(c => c.milestones.map(m => [c.date, m.provision]));
    assert.deepEqual(milestones.sort(), report.timeline.map(t => [t.applies_from, t.provision]).sort(), key);
    const placed = [
      ...model.columns.flatMap(c => c.items.map(i => [i.id, i.actor, c.date])),
      ...model.open.map(i => [i.id, i.actor, null]),
    ];
    const expected = report.obligation_graph.map(g => [g.obligation_id, g.actor, g.application_date ?? null]);
    assert.deepEqual(placed.sort(), expected.sort(), key);
  }
});

test("marks the items whose date carries a note and passes the assessment answer through", () => {
  let noted = 0;
  for (const [key, report] of Object.entries(reports)) {
    const model = timelineModel(report);
    const items = [...model.columns.flatMap(c => c.items), ...model.open];
    const byId = new Map(report.obligation_graph.map(g => [`${g.obligation_id}|${g.actor}`, g]));
    for (const item of items) {
      const source = byId.get(`${item.id}|${item.actor}`);
      assert.equal(item.hasDateNote, Boolean(source.application_date_note), `${key}: ${item.id}`);
      assert.equal(item.appliesOnAssessmentDate, source.applies_on_assessment_date ?? null, `${key}: ${item.id}`);
      if (item.hasDateNote) noted += 1;
    }
    for (const item of model.open) assert.equal(item.hasDateNote, true, `${key}: an open date without its note`);
  }
  assert.ok(noted > 0, "no bundled example has a date note, so the marker is untested");
});

test("renders exactly the model: dates, milestones, items, markers and answers", () => {
  for (const [key, report] of Object.entries(reports)) {
    const model = timelineModel(report);
    const view = renderTimeline(fakeDocument, report, { provider: "Provider", deployer: "Deployer" });
    assert.equal(view.attributes.role, "region", key);
    const headers = view.all("timeline-when").map(e => e.textContent);
    assert.deepEqual(headers, [...shownDates(model), ...(model.open.length ? ["Date open"] : [])], key);
    assert.deepEqual(view.all("timeline-milestone").map(e => e.textContent), model.columns.flatMap(c => c.milestones.map(m => m.provision)), key);
    const items = [...model.columns.flatMap(c => c.items), ...model.open];
    assert.equal(view.all("timeline-item").length, items.length, key);
    assert.equal(view.all("timeline-note").length, items.filter(i => i.hasDateNote).length, key);
    assert.equal(view.all("timeline-status").length, items.filter(i => i.appliesOnAssessmentDate !== null).length, key);
    // The marker says only that a note exists; it never calls the date contested.
    for (const note of view.all("timeline-note")) assert.equal(note.textContent, "see the date note");
  }
});

test("renders an open date, both assessment answers and no marker without a note", () => {
  const report = {
    timeline: [{ applies_from: "2026-08-02", provision: "General application", note: "" }],
    obligation_graph: [
      { obligation_id: "a", article: "Art. 9 AIA", actor: "provider", application_date: "2026-08-02", application_date_note: null, applies_on_assessment_date: true },
      { obligation_id: "b", article: "Art. 26 AIA", actor: "deployer", application_date: "2026-08-02", application_date_note: "a contested reading", applies_on_assessment_date: false },
      { obligation_id: "c", article: "Art. 53 AIA", actor: "gpai_provider", application_date: null, application_date_note: "turns on the placing date", applies_on_assessment_date: null },
    ],
  };
  const view = renderTimeline(fakeDocument, report, { provider: "Provider", deployer: "Deployer" });
  assert.deepEqual(view.all("timeline-when").map(e => e.textContent), ["2026-08-02", "Date open"]);
  assert.deepEqual(view.all("timeline-status").map(e => e.textContent), ["applies on the assessment date", "not yet applicable on the assessment date"]);
  const [first, second, third] = view.all("timeline-item");
  assert.equal(first.all("timeline-note").length, 0);
  assert.equal(second.all("timeline-note").length, 1);
  assert.equal(third.all("timeline-note").length, 1);
  assert.equal(second.all("timeline-actor")[0].textContent, "Deployer");
  assert.equal(third.all("timeline-actor")[0].textContent, "gpai_provider");
  assert.equal(renderTimeline(fakeDocument, { timeline: [], obligation_graph: [] }), null);
});

test("keeps a value that is not an ISO date after the ISO dates, in report order", () => {
  const model = timelineModel({
    timeline: [
      { applies_from: "on notification", provision: "B", note: "" },
      { applies_from: "2027-12-02", provision: "C", note: "" },
      { applies_from: "2025-02-02", provision: "A", note: "" },
    ],
    obligation_graph: [{ obligation_id: "x", article: "Art. 4 AIA", actor: "provider", application_date: null, application_date_note: "turns on a fact", review_status: "review_required" }],
  });
  assert.deepEqual(shownDates(model), ["2025-02-02", "2027-12-02", "on notification"]);
  assert.equal(model.open.length, 1);
  assert.deepEqual(timelineModel({}), { columns: [], open: [] });
});

test("words the engine's assessment-date answer and adds none of its own", () => {
  assert.equal(assessmentLabel(true), "applies on the assessment date");
  assert.equal(assessmentLabel(false), "not yet applicable on the assessment date");
  assert.equal(assessmentLabel(null), null);
  assert.equal(assessmentLabel(undefined), null);
});

test("constructs or formats no date in the results view", () => {
  // Every playground module except intake.mjs, whose isIsoDate checks a date the user
  // typed into the guided intake; nothing in the results view may build, parse or
  // format a date or read the clock.
  const pattern = /\bDate\s*[.(]|\bnew\s+Date\b|\bTemporal\b|DateTimeFormat|toLocale(?:Date|Time)String|performance\.now/;
  const files = readdirSync(new URL("../../docs/playground/", import.meta.url)).filter(f => f.endsWith(".mjs") && f !== "intake.mjs");
  assert.ok(files.includes("timeline.mjs") && files.includes("app.mjs"));
  for (const file of files) {
    const source = readFileSync(new URL(`../../docs/playground/${file}`, import.meta.url), "utf8");
    assert.doesNotMatch(source, pattern, file);
  }
});
