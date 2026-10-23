import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  MAX_BYTES, TIERS, annexCitation, formatProfile, groupByRole, matchesQuery,
  parseProfile, practiceCitation, reportIsCurrent,
} from "../../docs/playground/model.mjs";

const samples = JSON.parse(readFileSync(new URL("../../docs/playground/samples.json", import.meta.url)));
const parse = data => parseProfile(JSON.stringify(data));

test("accepts every bundled example and requires only a name", () => {
  for (const profile of Object.values(samples.profiles)) assert.deepEqual(parse(profile), profile);
  assert.deepEqual(parse({ name: "x" }), { name: "x" });
});

test("rejects malformed JSON, non-objects and a missing or blank name", () => {
  assert.throws(() => parseProfile("{"), /valid JSON/);
  for (const data of [null, [], 3, "profile"]) assert.throws(() => parse(data), /JSON object/);
  for (const name of [undefined, "", "   ", 7, null, ["x"]]) assert.throws(() => parse({ name }), /"name"/);
});

test("applies the size limit to UTF-8 bytes rather than character count", () => {
  assert.throws(() => parseProfile(" ".repeat(MAX_BYTES + 1)), /up to 1 MB/);
  assert.throws(() => parse({ name: "x", description: "€".repeat(MAX_BYTES / 2) }), /up to 1 MB/);
});

test("formatting keeps numbers, key order and duplicate keys exactly as written", () => {
  const text = '{"name":"Atlas","training_flops":5e+25,"roles":["gpai_provider"],"name":"Atlas-70B","derogation":{}}';
  const formatted = formatProfile(text);
  assert.match(formatted, /"training_flops": 5e\+25/);
  assert.equal(formatted.indexOf('"name": "Atlas"') < formatted.indexOf('"name": "Atlas-70B"'), true);
  assert.match(formatted, /"derogation": \{\}/);
  assert.deepEqual(JSON.parse(formatted), JSON.parse(text));
  assert.equal(formatProfile(formatted), formatted);
});

test("a result is exportable only for the exact text and advisory setting it was run on", () => {
  const run = { text: "a", advisory: false };
  assert.equal(reportIsCurrent(null, run, run), false);
  assert.equal(reportIsCurrent({}, null, run), false);
  assert.equal(reportIsCurrent({}, run, { text: "a", advisory: false }), true);
  assert.equal(reportIsCurrent({}, run, { text: "b", advisory: false }), false);
  assert.equal(reportIsCurrent({}, run, { text: "a", advisory: true }), false);
});

test("groups obligations by role in report order", () => {
  const obligations = [
    { applies_to: "provider", article: "Art. 9 AIA" },
    { applies_to: "deployer", article: "Art. 26 AIA" },
    { applies_to: "provider", article: "Art. 10 AIA" },
  ];
  const groups = groupByRole(obligations);
  assert.deepEqual(groups.map(g => g.label), ["Provider", "Deployer"]);
  assert.deepEqual(groups[0].items.map(o => o.article), ["Art. 9 AIA", "Art. 10 AIA"]);
});

test("search ignores case and surrounding space and skips empty values", () => {
  assert.equal(matchesQuery(["Art. 9 AIA", "Risk management system"], " art. 9 "), true);
  assert.equal(matchesQuery(["Art. 9 AIA", null, undefined], "RISK"), false);
  assert.equal(matchesQuery(["anything"], "   "), true);
  assert.equal(matchesQuery(["Art. 9 AIA"], "<script>"), false);
});

test("cites screen values the way the engine cites them", () => {
  assert.equal(practiceCitation("5.1.c"), "Art. 5(1)(c)");
  assert.equal(practiceCitation("5.1.ba"), "Art. 5(1)(ba)");
  assert.equal(practiceCitation("5.1.bb"), "Art. 5(1)(bb)");
  assert.equal(annexCitation("III.5.b"), "Annex III(5)(b)");
  assert.equal(annexCitation("III.2"), "Annex III(2)");
  assert.equal(annexCitation("III.unsure"), "Annex III, point unsettled");
  assert.equal(annexCitation("bogus"), "bogus");
});

test("labels every risk tier the engine can return", () => {
  const models = readFileSync(new URL("../../src/eu_ai_act_classifier/models.py", import.meta.url), "utf8");
  const tierBlock = models.slice(models.indexOf("class RiskTier"), models.indexOf("TIER_ORDER: dict"));
  const values = [...tierBlock.matchAll(/= "([a-z_]+)"/g)].map(m => m[1]);
  assert.deepEqual(values.sort(), Object.keys(TIERS).sort());
});
