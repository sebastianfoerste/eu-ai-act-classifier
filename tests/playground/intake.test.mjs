import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { UNKNOWN, answerError, answersToProfile, askedQuestions, compactProfile, describeAnswer, isIsoDate, profileToAnswers } from "../../docs/playground/intake.mjs";

const read = path => JSON.parse(readFileSync(new URL(path, import.meta.url), "utf8"));
const definition = read("../../docs/playground/intake.json");
const samples = read("../../docs/playground/samples.json");
const { cases } = read("./intake-fixtures.json");

test("asks, skips and blocks exactly as the Python interpreter does", () => {
  for (const [key, expected] of Object.entries(cases)) {
    const { profile, asked, blocked, missing } = answersToProfile(definition, expected.answers);
    assert.deepEqual(missing, [], key);
    assert.deepEqual(asked, expected.asked, key);
    assert.deepEqual(blocked, expected.blocked, key);
    assert.deepEqual(profile, expected.profile, key);
  }
});

test("round-trips every bundled example", () => {
  for (const [key, example] of Object.entries(samples.profiles)) {
    const answers = profileToAnswers(definition, example);
    assert.deepEqual(answers, cases[key].answers, key);
    const { profile, blocked } = answersToProfile(definition, answers);
    assert.deepEqual(blocked, [], key);
    const compact = compactProfile(definition, profile);
    assert.deepEqual(profileToAnswers(definition, compact), answers, key);
    for (const [field, value] of Object.entries(example)) {
      if (field === "derogation") for (const [flag, set] of Object.entries(value)) assert.equal(profile.derogation[flag], set, key);
      else assert.deepEqual(profile[field], value, `${key}.${field}`);
    }
  }
});

test("never turns I don't know into false or drops the field", () => {
  const base = profileToAnswers(definition, samples.profiles.credit_scoring);
  for (const question of definition.questions) {
    if (!question.unknown) continue;
    const answers = { ...base, [question.id]: UNKNOWN };
    const { profile, asked, blocked } = answersToProfile(definition, answers);
    if (!asked.includes(question.id)) continue;
    if (question.unknown === "block") {
      assert.ok(blocked.includes(question.id), question.id);
    } else {
      assert.notEqual(question.unknown.value, false, question.id);
      const field = question.field.split(".");
      assert.ok(field[0] in profile, question.id);
    }
  }
});

test("missing answers are reported, not defaulted", () => {
  const { missing, blocked } = answersToProfile(definition, {});
  assert.ok(missing.includes("system"));
  assert.ok(missing.includes("roles"));
  assert.deepEqual(blocked, []);
});

test("an earlier answer changes which questions follow", () => {
  const answers = profileToAnswers(definition, samples.profiles.credit_scoring);
  const ids = () => askedQuestions(definition, answers).map(q => q.id);
  assert.ok(ids().includes("prohibited_practices"));
  answers.is_ai_system = "no";
  assert.ok(!ids().includes("prohibited_practices"));
  assert.ok(!ids().includes("annex_iii_area"));
});

test("validates dates, numbers and required fields with plain messages", () => {
  const system = definition.questions.find(q => q.id === "system");
  const dates = definition.questions.find(q => q.id === "dates");
  const flops = definition.questions.find(q => q.id === "training_flops");
  assert.match(answerError(system, { name: " " }), /system name/);
  assert.match(answerError(dates, { placing_on_market_date: "01.03.2026" }), /YYYY-MM-DD/);
  assert.equal(answerError(dates, { placing_on_market_date: "2026-03-01" }), "");
  assert.equal(isIsoDate("2026-02-30"), false);
  assert.match(answerError(flops, "lots"), /number/);
  assert.equal(answerError(flops, "2e25"), "");
});

test("check-answers text says what an unknown answer does", () => {
  const roles = definition.questions.find(q => q.id === "roles");
  const annex = definition.questions.find(q => q.id === "annex_iii_area");
  assert.match(describeAnswer(definition, roles, UNKNOWN), /counsel must answer/);
  assert.match(describeAnswer(definition, annex, UNKNOWN), /III\.unsure.*review/);
  assert.match(describeAnswer(definition, annex, "III.5.b"), /^Annex III\(5\)\(b\): Creditworthiness/);
});
