// The guided wizard hands a typed number to the interpreter as typed, so the one grammar
// in intake.mjs decides what the browser accepts. A small DOM stand-in is enough here:
// the wizard creates elements, listens for events and replaces its root's children.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { answersToProfile, profileToAnswers } from "../../docs/playground/intake.mjs";
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
