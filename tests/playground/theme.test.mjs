import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import { THEMES, THEME_KEY, THEME_LABELS, applyTheme, nextTheme, readTheme, showTheme, shownTheme, wireThemeToggle } from "../../docs/playground/theme.mjs";

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
  ["ink", "bg"], ["ink", "paper"], ["ink", "surface-subtle"], ["ink", "surface-sunken"], ["ink", "selected"], ["ink", "hover"], ["ink", "error-bg-soft"],
  ["ink-soft", "paper"], ["ink-soft", "surface-sunken"],
  ["code", "surface-subtle"],
  ["muted", "bg"], ["muted", "paper"], ["muted", "surface-subtle"], ["muted", "surface-sunken"], ["muted", "chip"], ["muted", "grey-tint"], ["muted", "hover"],
  ["muted", "red-tint"], ["muted", "amber-tint"], ["muted", "blue-tint"], ["muted", "green-tint"],
  ["heading-muted", "bg"],
  // Placeholders: the search field and the JSON field, and the guided date field.
  ["placeholder", "surface-subtle"], ["placeholder", "paper"],
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

// Every way CSS writes a colour without a token: hex, a colour function, one of the 148
// named colours, or a system colour. transparent and currentColor are the same in both
// sets and stay allowed. Only declaration values are read, after var(), url() and strings
// are taken out, so a selector such as .red or a token such as --red is not a finding.
const NAMED_COLOURS = `
  aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue
  blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk
  crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki
  darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen
  darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue
  dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite
  gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki
  lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
  lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen
  lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen
  magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen
  mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream
  mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid
  palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum
  powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown
  seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen
  steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen
`.trim().split(/\s+/);
const SYSTEM_COLOURS = `
  accentcolor accentcolortext activetext buttonborder buttonface buttontext canvas canvastext
  field fieldtext graytext highlight highlighttext linktext mark marktext selecteditem
  selecteditemtext visitedtext
`.trim().split(/\s+/);
const COLOUR = new RegExp(
  `#[0-9a-f]{3,8}\\b|\\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark|device-cmyk)\\(|(?<![\\w-])(?:${[...NAMED_COLOURS, ...SYSTEM_COLOURS].join("|")})(?![\\w-])`,
  "gi",
);
export function strayColours(rules) {
  const found = [];
  for (const [, property, value] of rules.matchAll(/([a-z-]+)\s*:\s*([^;{}]+)(?=[;}])/g)) {
    const bare = value.replace(/var\(--[a-z-]+\)|url\([^)]*\)|"[^"]*"|'[^']*'/g, " ");
    for (const match of bare.match(COLOUR) ?? []) found.push(`${property}: ${match}`);
  }
  return found;
}

test("no colour is written outside the token sets", () => {
  const rules = css.slice(css.indexOf("* { box-sizing"));
  assert.deepEqual(strayColours(rules), []);
  // Hex anywhere in the rules, also outside a declaration.
  assert.deepEqual(rules.match(/#[0-9a-fA-F]{3,8}\b/g), null);
  assert.equal(rules.includes("var(--paper)-"), false);
  for (const [, name] of rules.matchAll(/var\(--([a-z-]+)\)/g)) assert.ok(name in light.tokens, name);
});

test("the guard finds each way of writing a colour and passes tokens", () => {
  const stray = value => strayColours(`a { color: ${value}; }`).length;
  for (const value of ["#fff", "#0a1b2c80", "white", "Black", "red", "rebeccapurple", "rgb(0 0 0)", "rgba(0,0,0,.5)",
    "hsl(0 0% 0%)", "hwb(0 0% 0%)", "lab(50% 0 0)", "lch(50% 0 0)", "oklab(50% 0 0)", "oklch(50% 0 0)",
    "color(srgb 0 0 0)", "color-mix(in srgb, var(--ink), var(--paper))", "light-dark(var(--ink), var(--paper))", "CanvasText"]) {
    assert.equal(stray(value), 1, value);
  }
  for (const value of ["var(--red)", "var(--blue-tint)", "transparent", "currentColor", "inherit"]) assert.equal(stray(value), 0, value);
  assert.deepEqual(strayColours(".red, a:hover { white-space: nowrap; border: 1px solid var(--line); content: \"red\"; }"), []);
  assert.deepEqual(strayColours("a { box-shadow: 0 1px 2px grey }"), ["box-shadow: grey"]);
});

test("every placeholder uses the placeholder token at full opacity", () => {
  const rules = [...css.matchAll(/([^{}]*::placeholder[^{}]*)\{([^}]*)\}/g)];
  assert.equal(rules.length, 1);
  const [, selector, body] = rules[0];
  assert.deepEqual(selector.split("*/").pop().trim().split(/,\s*/), ["#search::placeholder", "textarea::placeholder", ".text-input::placeholder"]);
  assert.equal(body.trim(), "color: var(--placeholder); opacity: 1;");
  // The surfaces behind them, which the TEXT list pairs with the token.
  assert.match(css, /\n#search \{[^}]*background: var\(--surface-subtle\);/);
  assert.match(css, /\ntextarea \{[^}]*background: var\(--surface-subtle\);/);
  assert.match(css, /\n\.text-input \{[^}]*background: var\(--paper\);/);
  // Every placeholder in the page sits in one of the three fields.
  assert.equal(read("index.html").match(/placeholder=/g).length, 2);
  assert.match(read("wizard.mjs"), /node\("input", "text-input"\);[^}]*input\.placeholder = "YYYY-MM-DD"/);
  assert.equal([...read("wizard.mjs").matchAll(/\.placeholder\b/g)].length, 1);
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
});

function fakeTarget() {
  const listeners = {};
  return {
    addEventListener: (type, listener) => { (listeners[type] ??= []).push(listener); },
    dispatch: (type, event = {}) => { for (const listener of listeners[type] ?? []) listener(event); },
    count: type => (listeners[type] ?? []).length,
  };
}

function wired(storage, dataset = {}) {
  const root = { dataset };
  const button = fakeTarget();
  const events = fakeTarget();
  const status = { textContent: "" };
  wireThemeToggle({ root, button, status, storage: () => storage, events });
  return { root, button, events, status };
}

test("the shown choice is the attribute on the root element", () => {
  assert.equal(shownTheme({ dataset: {} }), "system");
  assert.equal(shownTheme({ dataset: { theme: "dark" } }), "dark");
  assert.equal(shownTheme({ dataset: { theme: "sepia" } }), "system");
  const root = { dataset: {} };
  showTheme(root, "light");
  assert.deepEqual(root.dataset, { theme: "light" });
  showTheme(root, "system");
  assert.deepEqual(root.dataset, {});
});

test("a click on the Theme button cycles, stores and announces the choice", () => {
  const storage = memoryStorage();
  const { root, button, events, status } = wired(storage);
  assert.equal(button.count("click"), 1);
  assert.equal(events.count("storage"), 1);
  // Wiring changes nothing: theme.js has applied a stored choice already.
  assert.deepEqual(root.dataset, {});
  assert.equal(status.textContent, "");
  button.dispatch("click");
  assert.deepEqual(root.dataset, { theme: "light" });
  assert.equal(storage.data.get(THEME_KEY), "light");
  assert.equal(status.textContent, "Theme set to Light");
  button.dispatch("click");
  assert.deepEqual(root.dataset, { theme: "dark" });
  assert.equal(status.textContent, "Theme set to Dark");
  button.dispatch("click");
  assert.deepEqual(root.dataset, {});
  assert.equal(storage.data.size, 0);
  assert.equal(status.textContent, "Theme set to System");
});

test("the button starts from a stored choice that theme.js applied", () => {
  const storage = memoryStorage({ [THEME_KEY]: "dark" });
  const { root, button, status } = wired(storage, runEarlyScript(storage));
  button.dispatch("click");
  assert.deepEqual(root.dataset, {});
  assert.equal(status.textContent, "Theme set to System");
});

test("with blocked storage the button still cycles through all three", () => {
  for (const storage of [blocked, null]) {
    const { root, button, status } = wired(storage);
    button.dispatch("click");
    button.dispatch("click");
    assert.deepEqual(root.dataset, { theme: "dark" });
    assert.equal(status.textContent, "Theme set to Dark");
    button.dispatch("click");
    assert.deepEqual(root.dataset, {});
  }
});

test("a choice made in another tab is shown, not announced, and the next click starts from it", () => {
  const storage = memoryStorage();
  const { root, button, events, status } = wired(storage);
  button.dispatch("click");
  assert.equal(status.textContent, "Theme set to Light");
  storage.setItem(THEME_KEY, "dark");
  events.dispatch("storage", { key: THEME_KEY });
  assert.deepEqual(root.dataset, { theme: "dark" });
  assert.equal(status.textContent, "");
  button.dispatch("click");
  assert.deepEqual(root.dataset, {});
  // Another key changes nothing; a cleared storage (key null) returns to the system setting.
  storage.setItem(THEME_KEY, "light");
  events.dispatch("storage", { key: "eu-ai-act-classifier.draft" });
  assert.deepEqual(root.dataset, {});
  events.dispatch("storage", { key: THEME_KEY });
  assert.deepEqual(root.dataset, { theme: "light" });
  storage.removeItem(THEME_KEY);
  events.dispatch("storage", { key: null });
  assert.deepEqual(root.dataset, {});
});

test("the page wires the button, a hidden status element and all three names", () => {
  const html = read("index.html");
  assert.match(html, /<button type="button" id="theme-toggle"[^>]*>Theme: <span class="theme-name" data-theme-name="system">System<\/span><span class="theme-name" data-theme-name="light">Light<\/span><span class="theme-name" data-theme-name="dark">Dark<\/span><\/button><span id="theme-status" class="sr-only" role="status"><\/span>/);
  for (const theme of THEMES) assert.ok(html.includes(`data-theme-name="${theme}">${THEME_LABELS[theme]}</span>`));
  // The stylesheet shows exactly the name that matches data-theme, so the label is right
  // before any script runs.
  assert.ok(css.includes(".theme-name { display: none; }"));
  assert.ok(css.includes(`:root:not([data-theme="light"]):not([data-theme="dark"]) .theme-name[data-theme-name="system"],
:root[data-theme="light"] .theme-name[data-theme-name="light"],
:root[data-theme="dark"] .theme-name[data-theme-name="dark"] { display: inline; }`));
  const app = read("app.mjs");
  assert.match(app, /wireThemeToggle\(\{\s*root: document\.documentElement,\s*button: \$\("theme-toggle"\),\s*status: \$\("theme-status"\),/);
  assert.match(app, /events: window,/);
});
