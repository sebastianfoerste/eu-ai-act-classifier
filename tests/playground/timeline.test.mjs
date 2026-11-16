import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { assessmentLabel, shownDates, timelineModel } from "../../docs/playground/timeline.mjs";

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

test("marks the contested or conditional dates and nothing else", () => {
  let contested = 0;
  for (const [key, report] of Object.entries(reports)) {
    const model = timelineModel(report);
    const items = [...model.columns.flatMap(c => c.items), ...model.open];
    const byId = new Map(report.obligation_graph.map(g => [`${g.obligation_id}|${g.actor}`, g]));
    for (const item of items) {
      const source = byId.get(`${item.id}|${item.actor}`);
      assert.equal(item.contested, Boolean(source.application_date_note), `${key}: ${item.id}`);
      assert.equal(item.appliesOnAssessmentDate, source.applies_on_assessment_date ?? null, `${key}: ${item.id}`);
      if (item.contested) contested += 1;
    }
    for (const item of model.open) assert.equal(item.contested, true, `${key}: an open date without its note`);
  }
  assert.ok(contested > 0, "no bundled example has a contested date, so the marker is untested");
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

test("computes no date in the browser", () => {
  for (const file of ["timeline.mjs", "app.mjs"]) {
    const source = readFileSync(new URL(`../../docs/playground/${file}`, import.meta.url), "utf8");
    assert.doesNotMatch(source, /\bnew Date\b|\bDate\.(now|parse|UTC)\b|\bIntl\.DateTimeFormat\b/, file);
  }
});
