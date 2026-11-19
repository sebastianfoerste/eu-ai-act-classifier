// The guided wizard hands a typed number to the interpreter as typed, so the one grammar
// in intake.mjs decides what the browser accepts. A small DOM stand-in is enough here:
// the wizard creates elements, listens for events and replaces its root's children.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { UNKNOWN, answersToProfile, profileToAnswers } from "../../docs/playground/intake.mjs";
import { createWizard } from "../../docs/playground/wizard.mjs";

class FakeElement {
  constructor(tag) {
    this.tagName = tag;
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this.attributes = {};
    this.className = "";
    this.value = "";
    this.classList = { add: name => { this.className = `${this.className} ${name}`.trim(); } };
  }
  addEventListener(type, listener) { (this.listeners[type] ??= []).push(listener); }
  dispatch(type) { for (const listener of this.listeners[type] ?? []) listener({ preventDefault() {} }); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  setAttribute(name, value) { this.attributes[name] = value; }
  focus() {}
  querySelector() { return null; }
  *walk() { yield this; for (const child of this.children) yield* child.walk(); }
  find(matches) { for (const element of this.walk()) if (matches(element)) return element; return null; }
  get text() { return [...this.walk()].map(element => element.textContent ?? "").join(" "); }
}
globalThis.document = { createElement: tag => new FakeElement(tag) };
globalThis.CSS = { escape: value => value };

const definition = JSON.parse(readFileSync(new URL("../../docs/playground/intake.json", import.meta.url), "utf8"));
const question = definition.questions.find(q => q.kind === "number");

// Open the training-compute page of a general-purpose AI model from the check-answers
// page, type the text and press Continue.
function typeNumber(typed) {
  const root = new FakeElement("div");
  const wizard = createWizard({ root, definition, canClassify: () => true, onClassify() {}, onEditJson() {}, onChange() {} });
  wizard.review(profileToAnswers(definition, { name: "x", roles: ["gpai_provider"], is_gpai_model: true }));
  const row = root.find(element => element.className.startsWith("answer-row") && element.text.includes(question.title));
  row.find(element => element.tagName === "button").dispatch("click");
  const input = root.find(element => element.tagName === "input" && element.className === "text-input");
  input.value = typed;
  input.dispatch("input");
  root.find(element => element.tagName === "form").dispatch("submit");
  const alert = root.find(element => element.className === "error-summary" && element.attributes.role === "alert");
  const { profile, missing } = answersToProfile(definition, wizard.answers);
  return {
    error: alert ? alert.text : "",
    stored: wizard.answers[question.id],
    missing: missing.includes(question.id),
    flops: profile[question.field],
  };
}

test("a number padded with whitespace other than ASCII is refused, as in the Python intake", () => {
  // String.prototype.trim() would remove each of these before the grammar sees the text.
  for (const typed of ["\u00a05", "5\u00a0", "\ufeff5", "5\u2028", "\u30005", "2e25\u202f"]) {
    const result = typeNumber(typed);
    assert.match(result.error, /Enter a number/, JSON.stringify(typed));
    assert.equal(result.stored, typed);
    assert.equal(result.missing, true, JSON.stringify(typed));
    assert.equal(result.flops, null, JSON.stringify(typed));
  }
});

test("ASCII whitespace around a number is ignored, and whitespace alone is not a blank answer", () => {
  for (const [typed, flops] of [["2e25", 2e25], [" 5 ", 5], ["\t10", 10]]) {
    const result = typeNumber(typed);
    assert.equal(result.error, "", JSON.stringify(typed));
    assert.equal(result.missing, false, JSON.stringify(typed));
    assert.equal(result.flops, flops, JSON.stringify(typed));
  }
  const blank = typeNumber("");
  assert.deepEqual([blank.error, blank.missing, blank.flops], ["", false, null]);
  for (const typed of ["   ", "\u00a0"]) {
    const result = typeNumber(typed);
    assert.match(result.error, /Enter a number/, JSON.stringify(typed));
    assert.equal(result.missing, true, JSON.stringify(typed));
  }
});

// --- D5: the Annex III question in two steps ---------------------------------------

const annex = definition.questions.find(q => q.id === "annex_iii_area");
const radios = root => [...root.walk()].filter(e => e.tagName === "input" && e.type === "radio");

function openAnnex() {
  const root = new FakeElement("div");
  const wizard = createWizard({ root, definition, canClassify: () => true, onClassify() {}, onEditJson() {}, onChange() {} });
  wizard.review(profileToAnswers(definition, { name: "x", roles: ["provider"] }));
  const row = root.find(element => element.className.startsWith("answer-row") && element.text.includes(annex.title));
  row.find(element => element.tagName === "button").dispatch("click");
  return { root, wizard };
}

function pick(root, value) {
  const input = radios(root).find(r => r.value === value);
  assert.ok(input, `no option ${value}`);
  input.checked = true;
  input.dispatch("change");
}
const submit = root => root.find(element => element.tagName === "form").dispatch("submit");
const title = root => root.find(element => element.tagName === "h3").textContent;

test("Annex III: the area page lists the eight areas, None and I don't know", () => {
  const { root } = openAnnex();
  assert.equal(title(root), annex.title);
  assert.deepEqual(radios(root).map(r => r.value), [...annex.groups.map(g => g.value), "none", UNKNOWN]);
});

const progress = root => root.find(element => element.className === "progress").textContent;
const errorShown = root => Boolean(root.find(element => element.className === "error-summary"));
const back = root => root.find(element => element.tagName === "button" && element.textContent === "Back").dispatch("click");
const checked = root => radios(root).filter(r => r.checked).map(r => r.value);

// Back until the Annex III question shows; returns its page title.
function backToAnnex(root) {
  for (let i = 0; i < 20 && ![annex.title, annex.group_title].includes(title(root)); i++) back(root);
  return title(root);
}

function openWith(profile) {
  const root = new FakeElement("div");
  const wizard = createWizard({ root, definition, canClassify: () => true, onClassify() {}, onEditJson() {}, onChange() {} });
  wizard.review(profileToAnswers(definition, { name: "x", roles: ["provider"], ...profile }));
  const row = root.find(element => element.className.startsWith("answer-row") && element.text.includes(annex.title));
  row.find(element => element.tagName === "button").dispatch("click");
  return { root, wizard };
}

test("Annex III: the point page lists only the chosen area's points and stores the point", () => {
  const { root, wizard } = openAnnex();
  pick(root, "5");
  submit(root);
  assert.equal(title(root), annex.group_title);
  assert.deepEqual(radios(root).map(r => r.value), ["III.5.a", "III.5.b", "III.5.c", "III.5.d", "none", UNKNOWN]);
  pick(root, "III.5.b");
  submit(root);
  assert.equal(wizard.answers.annex_iii_area, "III.5.b");
  assert.equal(answersToProfile(definition, wizard.answers).profile.annex_iii_area, "III.5.b");
  assert.notEqual(title(root), annex.group_title);
});

test("Annex III: an area with one point still shows the point with its own wording", () => {
  // Point 2 covers safety components only; the area heading alone is wider.
  const { root, wizard } = openAnnex();
  pick(root, "2");
  submit(root);
  assert.equal(title(root), annex.group_title);
  assert.deepEqual(radios(root).map(r => r.value), ["III.2", "none", UNKNOWN]);
  assert.match(root.text, /Safety component/);
  pick(root, "III.2");
  submit(root);
  assert.equal(wizard.answers.annex_iii_area, "III.2");
});

test("Annex III: I don't know on either page writes the unsettled point and moves on", () => {
  for (const onPointPage of [false, true]) {
    const { root, wizard } = openAnnex();
    if (onPointPage) { pick(root, "6"); submit(root); }
    pick(root, UNKNOWN);
    submit(root);
    assert.equal(errorShown(root), false);
    assert.notEqual(title(root), annex.title);
    assert.notEqual(title(root), annex.group_title);
    assert.equal(wizard.answers.annex_iii_area, UNKNOWN);
    assert.equal(answersToProfile(definition, wizard.answers).profile.annex_iii_area, "III.unsure");
  }
});

test("Annex III: None of these on the point page records no Annex III use", () => {
  const { root, wizard } = openAnnex();
  pick(root, "4");
  submit(root);
  pick(root, "none");
  submit(root);
  assert.equal(errorShown(root), false);
  assert.equal(wizard.answers.annex_iii_area, "none");
  assert.equal(answersToProfile(definition, wizard.answers).profile.annex_iii_area, null);
});

test("Annex III: no area chosen and no point chosen are both refused", () => {
  const first = openAnnex();
  first.wizard.review({ ...first.wizard.answers, annex_iii_area: undefined });
  const row = first.root.find(element => element.className.startsWith("answer-row") && element.text.includes(annex.title));
  row.find(element => element.tagName === "button").dispatch("click");
  submit(first.root);
  assert.match(first.root.text, /Choose an area/);
  const second = openAnnex();
  pick(second.root, "1");
  submit(second.root);
  submit(second.root);
  assert.match(second.root.text, /Choose the point/);
});

test("Annex III: Back on the point page returns to the area page with the area chosen", () => {
  const { root } = openAnnex();
  pick(root, "7");
  submit(root);
  back(root);
  assert.equal(title(root), annex.title);
  assert.deepEqual(checked(root), ["7"]);
});

test("Annex III: Back from the next question returns to the point page", () => {
  const { root } = openWith({ annex_iii_area: "III.5.b" });
  submit(root);
  submit(root);
  assert.notEqual(title(root), annex.group_title);
  assert.equal(backToAnnex(root), annex.group_title);
  assert.deepEqual(checked(root), ["III.5.b"]);
});

test("Annex III: browsing the area radios changes no answer", () => {
  const { root, wizard } = openWith({ annex_iii_area: "III.4.a" });
  assert.deepEqual(checked(root), ["4"]);
  for (const value of ["5", "2", "none", UNKNOWN, "4"]) pick(root, value);
  assert.equal(wizard.answers.annex_iii_area, "III.4.a");
  submit(root);
  assert.deepEqual(checked(root), ["III.4.a"]);
  // Leaving the page without Continue keeps the answer too.
  pick(root, "III.4.b");
  back(root);
  pick(root, "8");
  back(root);
  assert.equal(wizard.answers.annex_iii_area, "III.4.b");
});

test("Annex III: a saved point or an unsettled point reopens on the right choices", () => {
  const saved = openWith({ annex_iii_area: "III.5.b" });
  assert.deepEqual(checked(saved.root), ["5"]);
  submit(saved.root);
  assert.deepEqual(checked(saved.root), ["III.5.b"]);
  const unsure = openWith({ annex_iii_area: "III.unsure" });
  assert.deepEqual(checked(unsure.root), [UNKNOWN]);
});

test("Annex III: I don't know which point keeps the area for Back and Change", () => {
  const { root, wizard } = openWith({ annex_iii_area: "III.3.d" });
  submit(root);
  pick(root, UNKNOWN);
  submit(root);
  assert.equal(wizard.answers.annex_iii_area, UNKNOWN);
  // Back from the next question returns to the point page the answer was given on.
  assert.equal(backToAnnex(root), annex.group_title);
  assert.deepEqual(checked(root), [UNKNOWN]);
  back(root);
  assert.equal(title(root), annex.title);
  assert.deepEqual(checked(root), ["3"]);
  submit(root);
  assert.deepEqual(checked(root), [UNKNOWN]);
});

test("Annex III: None of these on a point page is where Back from the next question returns", () => {
  const { root, wizard } = openWith({ annex_iii_area: "III.4.a" });
  submit(root);
  pick(root, "none");
  submit(root);
  assert.equal(wizard.answers.annex_iii_area, "none");
  assert.equal(backToAnnex(root), annex.group_title);
  assert.deepEqual(checked(root), ["none"]);
});

test("Annex III: peeking at another area's points and going Back keeps the saved point", () => {
  const { root, wizard } = openWith({ annex_iii_area: "III.5.b" });
  pick(root, "4");
  submit(root);
  assert.equal(title(root), annex.group_title);
  assert.deepEqual(checked(root), []);
  back(root);
  assert.equal(wizard.answers.annex_iii_area, "III.5.b");
  // The area just looked at stays selected, unsubmitted; going back to area 5 shows the
  // saved point, and leaving the page keeps it.
  assert.deepEqual(checked(root), ["4"]);
  pick(root, "5");
  submit(root);
  assert.deepEqual(checked(root), ["III.5.b"]);
  submit(root);
  assert.equal(wizard.answers.annex_iii_area, "III.5.b");
});

test("Annex III: loading new answers drops the area chosen before", () => {
  const { root, wizard } = openAnnex();
  pick(root, "7");
  submit(root);
  wizard.review(profileToAnswers(definition, { name: "x", roles: ["provider"], annex_iii_area: "III.1.a" }));
  const row = root.find(element => element.className.startsWith("answer-row") && element.text.includes(annex.title));
  row.find(element => element.tagName === "button").dispatch("click");
  assert.deepEqual(checked(root), ["1"]);
});

test("Annex III: the progress line names the page without promising a second one", () => {
  const { root } = openAnnex();
  assert.match(progress(root), /^Question \d+ of \d+: the area$/);
  pick(root, "5");
  submit(root);
  assert.match(progress(root), /^Question \d+ of \d+: the use$/);
});
