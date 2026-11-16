import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import { THEMES, THEME_KEY, THEME_LABELS, applyTheme, nextTheme, readTheme } from "../../docs/playground/theme.mjs";

const read = name => readFileSync(new URL(`../../docs/playground/${name}`, import.meta.url), "utf8");
const css = read("styles.css");

// The three token blocks: light, dark by system setting, dark by stored choice.
function tokenBlocks() {
  const blocks = [...css.matchAll(/(:root[^{]*)\{ color-scheme: (light|dark);\n([^}]*)\}/g)];
  return blocks.map(([, selector, scheme, body]) => ({
    selector: selector.trim(),
    scheme,
    tokens: Object.fromEntries([...body.matchAll(/--([a-z-]+): (#[0-9a-f]{3,8});/g)].map(([, name, value]) => [name, value])),
  }));
}
const [light, darkBySystem, darkByChoice] = tokenBlocks();

function luminance(hex) {
  const value = hex.length === 4 ? [...hex.slice(1)].map(c => c + c).join("") : hex.slice(1, 7);
  const [r, g, b] = [0, 2, 4].map(i => parseInt(value.slice(i, i + 2), 16) / 255)
    .map(c => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
export function contrast(a, b) {
  const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (high + 0.05) / (low + 0.05);
}

// Text on the surface it is drawn on: WCAG 2.2 AA, 4.5:1.
const TEXT = [
  ["ink", "bg"], ["ink", "paper"], ["ink", "surface-subtle"], ["ink", "surface-sunken"], ["ink", "selected"], ["ink", "hover"],
  ["ink-soft", "paper"], ["ink-soft", "surface-sunken"],
  ["code", "surface-subtle"],
  ["muted", "bg"], ["muted", "paper"], ["muted", "surface-subtle"], ["muted", "surface-sunken"], ["muted", "chip"], ["muted", "grey-tint"],
  ["muted", "red-tint"], ["muted", "amber-tint"], ["muted", "blue-tint"], ["muted", "green-tint"],
  ["heading-muted", "bg"], ["placeholder", "surface-subtle"],
  ["accent", "bg"], ["accent", "paper"], ["accent", "surface-subtle"], ["accent", "surface-sunken"], ["accent", "accent-tint"],
  ["on-accent", "accent"], ["on-accent", "accent-strong"], ["on-ink", "ink"],
  ["red", "paper"], ["red", "red-tint"], ["red", "error-bg-soft"],
  ["amber", "paper"], ["amber", "amber-tint"],
  ["blue", "paper"], ["blue", "blue-tint"],
  ["green", "bg"], ["green", "paper"], ["green", "green-tint"],
  ["error-ink", "error-bg"], ["notice-ink", "notice-bg"],
];
// The focus ring on every surface, and in the dark set the line that marks a button, a
// select or a text input: 3:1. The light set keeps the control lines it had before
// dark mode; they are below 3:1 and listed here so that a change shows up.
const FOCUS = [["focus", "bg"], ["focus", "paper"], ["focus", "surface-subtle"], ["focus", "surface-sunken"]];
const CONTROLS = [["control-line", "paper"], ["control-line", "bg"], ["control-line-hover", "paper"], ["input-line", "paper"]];

test("the stylesheet has a light token set and two identical dark ones", () => {
  assert.equal(light.selector, ":root");
  assert.equal(light.scheme, "light");
  assert.equal(darkBySystem.selector, ':root:not([data-theme="light"])');
  assert.equal(darkByChoice.selector, ':root[data-theme="dark"]');
  assert.equal(darkBySystem.scheme, "dark");
  assert.equal(darkByChoice.scheme, "dark");
  // Both dark blocks are for screens only: a page printed from a dark screen uses the light set.
  assert.match(css, /@media screen and \(prefers-color-scheme: dark\) \{ :root:not\(\[data-theme="light"\]\) \{/);
  assert.match(css, /@media screen \{ :root\[data-theme="dark"\] \{/);
  assert.equal(css.match(/color-scheme: dark;/g).length, 2);
  assert.deepEqual(darkBySystem.tokens, darkByChoice.tokens);
  assert.deepEqual(Object.keys(darkBySystem.tokens), Object.keys(light.tokens));
  assert.ok(Object.keys(light.tokens).length > 40);
});

test("no colour is written outside the token sets", () => {
  const rules = css.slice(css.indexOf("* { box-sizing"));
  // The keyword as a value only: "white-space" is a property name.
  assert.deepEqual(rules.match(/#[0-9a-fA-F]{3,8}\b|(?<![\w-])(?:white|black)(?![\w-])|rgba?\(|hsla?\(/g), null);
  assert.equal(rules.includes("var(--paper)-"), false);
  for (const [, name] of rules.matchAll(/var\(--([a-z-]+)\)/g)) assert.ok(name in light.tokens, name);
});

for (const [scheme, tokens] of [["light", light.tokens], ["dark", darkBySystem.tokens]]) {
  test(`${scheme}: text reaches 4.5:1 on its surface`, () => {
    for (const [text, surface] of TEXT) {
      const ratio = contrast(tokens[text], tokens[surface]);
      assert.ok(ratio >= 4.5, `--${text} on --${surface}: ${ratio.toFixed(2)}:1`);
    }
  });
  test(`${scheme}: the focus ring reaches 3:1 on every surface`, () => {
    for (const [ring, surface] of FOCUS) {
      const ratio = contrast(tokens[ring], tokens[surface]);
      assert.ok(ratio >= 3, `--${ring} on --${surface}: ${ratio.toFixed(2)}:1`);
    }
  });
}

test("dark: the line around a button, select or text input reaches 3:1", () => {
  for (const [line, surface] of CONTROLS) {
    const ratio = contrast(darkBySystem.tokens[line], darkBySystem.tokens[surface]);
    assert.ok(ratio >= 3, `--${line} on --${surface}: ${ratio.toFixed(2)}:1`);
  }
});

test("the contrast function gives the WCAG reference values", () => {
  assert.equal(contrast("#000000", "#ffffff").toFixed(2), "21.00");
  assert.equal(contrast("#fff", "#ffffff").toFixed(2), "1.00");
  assert.equal(contrast("#767676", "#ffffff").toFixed(2), "4.54");
});

function memoryStorage(initial = {}) {
  const data = new Map(Object.entries(initial));
  return { getItem: key => data.get(key) ?? null, setItem: (key, value) => data.set(key, String(value)), removeItem: key => data.delete(key), data };
}
const blocked = { getItem() { throw new Error("blocked"); }, setItem() { throw new Error("blocked"); }, removeItem() { throw new Error("blocked"); } };

test("the choice cycles System, Light, Dark and back", () => {
  assert.deepEqual(THEMES, ["system", "light", "dark"]);
  assert.deepEqual(THEMES.map(nextTheme), ["light", "dark", "system"]);
  assert.equal(nextTheme("sepia"), "system");
  assert.deepEqual(Object.keys(THEME_LABELS), THEMES);
});

test("only a stored light or dark overrides the system setting", () => {
  assert.equal(readTheme(memoryStorage()), "system");
  assert.equal(readTheme(memoryStorage({ [THEME_KEY]: "dark" })), "dark");
  assert.equal(readTheme(memoryStorage({ [THEME_KEY]: "light" })), "light");
  assert.equal(readTheme(memoryStorage({ [THEME_KEY]: "sepia" })), "system");
  assert.equal(readTheme(null), "system");
  assert.equal(readTheme(blocked), "system");
});

test("applying a choice sets the attribute and stores only that word", () => {
  const root = { dataset: {} };
  const storage = memoryStorage();
  applyTheme(root, storage, "dark");
  assert.deepEqual(root.dataset, { theme: "dark" });
  assert.deepEqual([...storage.data], [[THEME_KEY, "dark"]]);
  applyTheme(root, storage, "light");
  assert.deepEqual(root.dataset, { theme: "light" });
  applyTheme(root, storage, "system");
  assert.deepEqual(root.dataset, {});
  assert.equal(storage.data.size, 0);
  applyTheme(root, blocked, "dark");
  assert.deepEqual(root.dataset, { theme: "dark" });
  applyTheme(root, null, "system");
  assert.deepEqual(root.dataset, {});
});

function runEarlyScript(localStorage) {
  const document = { documentElement: { dataset: {} } };
  vm.runInNewContext(read("theme.js"), { window: { localStorage }, document });
  return document.documentElement.dataset;
}

test("theme.js applies a stored choice before the page script, with the same key", () => {
  assert.ok(read("theme.js").includes(`"${THEME_KEY}"`));
  assert.deepEqual(runEarlyScript(memoryStorage({ [THEME_KEY]: "dark" })), { theme: "dark" });
  assert.deepEqual(runEarlyScript(memoryStorage({ [THEME_KEY]: "light" })), { theme: "light" });
  assert.deepEqual(runEarlyScript(memoryStorage({ [THEME_KEY]: "sepia" })), {});
  assert.deepEqual(runEarlyScript(memoryStorage()), {});
  assert.deepEqual(runEarlyScript(blocked), {});
  // A classic script in the head, before any module: it must run before the first paint.
  const html = read("index.html");
  assert.match(html, /<script src="theme\.js"><\/script>\n<\/head>/);
  assert.match(html, /<button type="button" id="theme-toggle"[^>]*>Theme: System<\/button>/);
});
