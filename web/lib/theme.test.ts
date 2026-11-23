import { readFileSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  THEMES,
  THEME_INIT_SCRIPT,
  THEME_KEY,
  THEME_LABELS,
  type Theme,
  applyTheme,
  cycleTheme,
  nextTheme,
  readTheme,
  restoreTheme,
  shownTheme,
  themeAnnouncement,
  watchTheme,
} from "./theme";

const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
// The stylesheet without comments, so a note that names a token or a colour is not read
// as a declaration.
const bare = css.replace(/\/\*[\s\S]*?\*\//g, "");
// Every innermost rule: the rules inside @media come out without their wrapper.
const rules = [...bare.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map(([, selector, body]) => ({
  selector: selector.trim().replace(/\s+/g, " "),
  body,
}));
// A rule that styles a button, select, input or text field.
const CONTROL =
  /(?:^|[\s,>])(?:button|input|select|textarea)\b|\.(?:iconButton|primaryButton|secondaryButton|inventoryItem|textInput)\b|\.triState button/;

// The three token blocks: light, dark by system setting, dark by stored choice.
function tokenBlocks() {
  return [...bare.matchAll(/(:root[^{]*)\{\s*color-scheme: (light|dark);([^}]*)\}/g)].map(
    ([, selector, scheme, body]) => ({
      selector: selector.trim(),
      scheme,
      tokens: Object.fromEntries(
        [...body.matchAll(/--([\w-]+): ([^;]+);/g)].map(([, name, value]) => [name, value]),
      ),
    }),
  );
}
const [light, darkBySystem, darkByChoice] = tokenBlocks();

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5]
    .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (high + 0.05) / (low + 0.05);
}

// Text on the surface it is drawn on: WCAG 2.2 AA, 4.5:1.
const TEXT: Array<[string, string]> = [
  ["text", "background"],
  ["text", "surface"],
  ["text", "surface-muted"],
  ["muted", "background"],
  ["muted", "surface"],
  ["muted", "surface-muted"],
  ["muted-on-tint", "surface-muted"],
  ["blue", "background"],
  ["blue", "surface"],
  ["blue", "info-bg"],
  ["on-primary", "blue"],
  ["green", "success-bg"],
  ["amber", "warning-bg"],
  // .rowMessage.error in a table cell.
  ["red", "surface"],
  ["red", "danger-bg"],
  ["violet", "surface"],
  ["violet", "surface-muted"],
  ["info-text", "info-bg-soft"],
  ["info-muted", "info-bg-soft"],
  ["code-text", "code-bg"],
];
// The line around a button, select or input, in the dark set: 3:1.
const DARK_LINES: Array<[string, string]> = [
  ["control-border", "surface"],
  ["control-border", "surface-muted"],
  ["control-border", "background"],
  ["control-border", "danger-bg"],
  ["input-border", "surface"],
  ["input-border", "surface-muted"],
];
// The same lines in the light set stay below 3:1, at the ratios recorded here. This is a
// recorded design decision of the owner and open for change. WCAG 2.2 SC 1.4.11 may
// require 3:1 for the line of a text field, where the line alone shows the control.
// Changing a light line token fails this test on purpose, so the change is made here too.
const LIGHT_LINES_BELOW: Array<[string, string, string]> = [
  ["control-border", "surface", "1.37"],
  ["control-border", "surface-muted", "1.23"],
  ["control-border", "background", "1.28"],
  ["control-border", "danger-bg", "1.24"],
  ["input-border", "surface", "2.48"],
  ["input-border", "surface-muted", "2.22"],
];
// The focus ring, in both sets: 3:1.
const FOCUS: Array<[string, string]> = [
  ["blue", "background"],
  ["blue", "surface"],
  ["blue", "surface-muted"],
  // The Retry metadata button inside .errorBanner.
  ["blue", "danger-bg"],
];

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
function strayColours(rules: string): string[] {
  const found: string[] = [];
  for (const [, property, value] of rules.matchAll(/([a-z-]+)\s*:\s*([^;{}]+)(?=[;}])/g)) {
    const plain = value.replace(/var\(--[\w-]+\)|url\([^)]*\)|"[^"]*"|'[^']*'/g, " ");
    for (const match of plain.match(COLOUR) ?? []) found.push(`${property}: ${match}`);
  }
  return found;
}

// Deprecated system colours such as WindowText, and vendor keywords such as
// -webkit-link. These words are also common property names or values elsewhere
// (`transition: background`), so they are searched only in properties that draw a
// colour, anywhere in the value.
const DEPRECATED_COLOUR =
  /(?<![\w-])(?:activeborder|activecaption|appworkspace|background|buttonhighlight|buttonshadow|captiontext|inactive\w+|infobackground|infotext|menu|menutext|scrollbar|threed\w+|window|windowframe|windowtext)(?![\w-])|(?<![\w-])-(?:webkit|moz)-[a-z-]+/gi;
const COLOUR_PROPERTY =
  /^(?:color|background(?:-[a-z-]+)?|border(?:-[a-z-]+)?|outline(?:-color)?|box-shadow|text-shadow|fill|stroke|caret-color|accent-color|column-rule(?:-color)?|text-decoration(?:-color)?|text-emphasis(?:-color)?|scrollbar-color|stop-color|flood-color|lighting-color|-webkit-[a-z-]+)$/;
function deprecatedColours(rules: string): string[] {
  const found: string[] = [];
  for (const [, property, value] of rules.matchAll(/([a-z-]+)\s*:\s*([^;{}]+)(?=[;}])/g)) {
    if (!COLOUR_PROPERTY.test(property)) continue;
    const plain = value.replace(/var\(--[\w-]+\)|url\([^)]*\)|"[^"]*"|'[^']*'/g, " ");
    for (const match of plain.match(DEPRECATED_COLOUR) ?? []) found.push(`${property}: ${match}`);
  }
  return found;
}

describe("colour tokens", () => {
  it("has a light set and two identical dark sets", () => {
    expect(light.selector).toBe(":root");
    expect(light.scheme).toBe("light");
    expect(darkBySystem.selector).toBe(':root:not([data-theme="light"])');
    expect(darkByChoice.selector).toBe(':root[data-theme="dark"]');
    expect(css).toMatch(
      /@media screen and \(prefers-color-scheme: dark\) \{\s*:root:not\(\[data-theme="light"\]\) \{/,
    );
    expect(css).toMatch(/@media screen \{\s*:root\[data-theme="dark"\] \{/);
    expect(bare.match(/color-scheme: dark;/g)).toHaveLength(2);
    // The light block and the two dark blocks, and no rule that switches the scheme.
    expect(bare.match(/(?<![\w-])color-scheme:/g)).toHaveLength(3);
    expect(darkBySystem.tokens).toEqual(darkByChoice.tokens);
    expect(Object.keys(darkBySystem.tokens)).toEqual(Object.keys(light.tokens));
    expect(Object.keys(light.tokens).length).toBeGreaterThan(25);
  });

  it("declares tokens in the three blocks only, and nothing else before the rules", () => {
    const declared = bare.match(/(?<![\w(-])--[\w-]+\s*:/g) ?? [];
    expect(declared).toHaveLength(3 * Object.keys(light.tokens).length);
    // Three blocks and the two @media screen wrappers of the dark blocks.
    const head = bare.slice(0, bare.indexOf("* {"));
    expect(head.match(/\{/g)).toHaveLength(5);
    // Nor a rule without braces, such as an @import whose stylesheet no check here reads.
    const rest = head.replace(/:root[^{]*\{[^{}]*\}/g, "").replace(/@media screen[^{]*\{\s*\}/g, "");
    expect(rest.trim()).toBe("");
    for (const [, name] of bare.matchAll(/var\(\s*--([\w-]+)/g)) {
      expect(Object.keys(light.tokens), name).toContain(name);
    }
  });

  it("writes no colour outside the token sets", () => {
    const body = bare.slice(bare.indexOf("* {"));
    expect(strayColours(body)).toEqual([]);
    expect(deprecatedColours(bare)).toEqual([]);
    // Hex anywhere in the rules, also outside a declaration.
    expect(body.match(/#[0-9a-fA-F]{3,8}\b/g)).toBeNull();
  });

  it("finds deprecated and vendor colour keywords only where they draw a colour", () => {
    for (const declaration of [
      "color: WindowText", "color: WindowText !important", "background: InfoBackground",
      "border: WindowText 1px solid", "border: 1px solid -webkit-link", "color: -webkit-link",
      "outline: -webkit-focus-ring-color auto 1px", "border-top-color: ThreeDShadow",
      "scrollbar-color: WindowText", "background-image: linear-gradient(Window, red)",
    ]) {
      expect(deprecatedColours(`a { ${declaration}; }`), declaration).toHaveLength(1);
    }
    for (const declaration of [
      "transition: background 0.2s", "background: var(--surface)", "font-family: -apple-system",
      "-webkit-appearance: none", "border: 1px solid var(--control-border)",
      "background-repeat: no-repeat", "background-image: url(menu.svg)",
    ]) {
      expect(deprecatedColours(`a { ${declaration}; }`), declaration).toEqual([]);
    }
  });

  // An inline style would bypass the stylesheet and every check in this file.
  it("has no inline style in the components and pages", () => {
    for (const dir of ["../components/", "../app/"]) {
      const files = readdirSync(new URL(dir, import.meta.url), { recursive: true, encoding: "utf8" });
      const sources = files.filter((file) => file.endsWith(".tsx") && !file.includes(".test."));
      expect(sources.length, dir).toBeGreaterThan(2);
      for (const file of sources) {
        expect(readFileSync(new URL(dir + file, import.meta.url), "utf8"), file).not.toMatch(/\bstyle=/);
      }
    }
  });

  it("finds each way of writing a colour and passes tokens", () => {
    const stray = (value: string) => strayColours(`a { color: ${value}; }`).length;
    for (const value of [
      "#fff", "#0a1b2c80", "white", "Black", "red", "rebeccapurple", "rgb(0 0 0)", "rgba(0,0,0,.5)",
      "hsl(0 0% 0%)", "hwb(0 0% 0%)", "lab(50% 0 0)", "lch(50% 0 0)", "oklab(50% 0 0)", "oklch(50% 0 0)",
      "color(srgb 0 0 0)", "color-mix(in srgb, var(--text), var(--surface))",
      "light-dark(var(--text), var(--surface))", "CanvasText",
    ]) {
      expect(stray(value), value).toBe(1);
    }
    for (const value of ["var(--red)", "var(--blue)", "transparent", "currentColor", "inherit"]) {
      expect(stray(value), value).toBe(0);
    }
    expect(strayColours('.red, a:hover { white-space: nowrap; border: 1px solid var(--border); content: "red"; }')).toEqual([]);
    expect(strayColours("a { box-shadow: 0 1px 2px grey }")).toEqual(["box-shadow: grey"]);
  });

  it.each([
    ["light", light.tokens],
    ["dark", darkBySystem.tokens],
  ] as const)("%s: text reaches 4.5:1 on its surface", (_scheme, tokens) => {
    for (const [text, surface] of TEXT) {
      expect(contrast(tokens[text], tokens[surface]), `--${text} on --${surface}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  // Both dark blocks are for screens only, so print resolves every token in the light
  // set. The printed draft is black on the white surface.
  it("prints with the light set: black on white", () => {
    const print = css.slice(css.indexOf("@media print {"));
    expect(print).toContain("background: var(--surface);");
    expect(print).toContain("color: var(--print-ink);");
    expect(print).toContain("border: 2px solid var(--print-ink);");
    expect(print).not.toContain("color-scheme");
    expect(contrast(light.tokens["print-ink"], light.tokens.surface).toFixed(2)).toBe("21.00");
  });

  // --muted reaches 4.5:1 on --surface-muted with little margin, so text on a tinted
  // container uses the stronger --muted-on-tint. Limit: this reads selectors, not markup.
  // It catches a rule that names a tinted container, not one that reaches a tinted
  // element through the markup alone (for example `.orphanedEvidence li`).
  it("puts no muted text inside a tinted container", () => {
    const TINT = /background(?:-color)?: var\(--surface-muted\);/;
    const tintedSelectors = rules
      .filter((rule) => TINT.test(rule.body))
      .flatMap((rule) => rule.selector.split(","))
      .map((selector) => selector.trim());
    // A tint on an element alone (th, thead, li) names no container this test can follow,
    // and the global muted rules for small, .meta and th would land on it.
    expect(tintedSelectors.filter((selector) => !/\.[A-Za-z]/.test(selector))).toEqual([]);
    const tinted = [
      ...new Set(
        tintedSelectors
          .map((selector) => selector.match(/\.[A-Za-z]+(?:\.[A-Za-z]+)?/)?.[0])
          .filter((name): name is string => Boolean(name)),
      ),
    ].sort();
    expect(tinted).toEqual([
      ".blockHeader", ".dataTable", ".notesList", ".plainList", ".promptBrief", ".questionList",
      ".riskMap", ".secondaryButton", ".statusPill.neutral", ".triState",
    ]);
    for (const rule of rules.filter((r) => /(?:^|\s)color: var\(--muted\);/.test(r.body))) {
      expect(TINT.test(rule.body), rule.selector).toBe(false);
      for (const selector of rule.selector.split(",").map((part) => part.trim())) {
        // .triState > span is the question label above the buttons, on --surface.
        if (selector === ".triState > span") continue;
        for (const name of tinted) {
          expect(selector.includes(name), `${selector} sets --muted inside ${name}`).toBe(false);
        }
      }
    }
    // The global muted rules (small, .panel p, .meta, th) are overridden where they land on the tint.
    for (const override of [".promptBrief small", ".promptBrief p", ".plainList .meta", ".questionList .meta", ".dataTable th"]) {
      const rule = rules.find((r) => r.selector.split(",").some((s) => s.trim() === override));
      expect(rule?.body ?? "", override).toMatch(/color: var\(--(?:muted-on-tint|violet)\);/);
    }
  });

  it("dark: control lines reach 3:1", () => {
    for (const [line, surface] of DARK_LINES) {
      expect(
        contrast(darkBySystem.tokens[line], darkBySystem.tokens[surface]),
        `--${line} on --${surface}`,
      ).toBeGreaterThanOrEqual(3);
    }
  });

  it("light: control lines stay at the recorded ratios below 3:1", () => {
    expect(LIGHT_LINES_BELOW.map(([line, surface]) => [line, surface])).toEqual(DARK_LINES);
    for (const [line, surface, ratio] of LIGHT_LINES_BELOW) {
      const measured = contrast(light.tokens[line], light.tokens[surface]);
      expect(measured, `--${line} on --${surface}`).toBeLessThan(3);
      expect(measured.toFixed(2), `--${line} on --${surface}`).toBe(ratio);
    }
  });

  // A token on the line, so it follows the scheme; the three tokens a control line may use.
  it("draws every control line with a control token", () => {
    const controls = rules.filter((rule) => CONTROL.test(rule.selector));
    const lines = controls.filter((rule) => /(?:^|\s)border:/.test(rule.body));
    expect(lines.map((rule) => rule.selector)).toEqual([
      ".iconButton, .primaryButton, .secondaryButton",
      ".inventoryItem",
      "input, select, textarea",
      ".triState button",
      ".textInput",
    ]);
    for (const rule of lines) {
      expect(rule.body, rule.selector).toMatch(/border: 1px solid var\(--(?:control-border|input-border)\);/);
    }
    // Every other line on a control, also a side or logical side shorthand or a colour
    // longhand, and also the last declaration without a semicolon, may only name a line
    // token or the accent, or draw no line at all.
    const LINE = /^border(?:-(?:top|right|bottom|left|block|inline)(?:-(?:start|end))?)?(?:-color)?$/;
    for (const rule of controls) {
      for (const [, property, value] of rule.body.matchAll(/([a-z-]+)\s*:\s*([^;}]+)(?:;|$)/g)) {
        if (!LINE.test(property)) continue;
        const where = `${rule.selector} { ${property}: ${value.trim()} }`;
        if (/^(?:0|none)$/.test(value.trim())) continue;
        const tokens = [...value.matchAll(/var\(\s*--([\w-]+)/g)].map(([, name]) => name);
        expect(tokens.length, where).toBeGreaterThan(0);
        for (const name of tokens) expect(["control-border", "input-border", "blue"], where).toContain(name);
      }
    }
  });

  // Without its own colour a control takes the browser's ButtonText or FieldText, which
  // this file cannot check against the token background.
  it("gives every control with a background a token text colour", () => {
    const filled = rules.filter((rule) => CONTROL.test(rule.selector) && /background(?:-color)?:/.test(rule.body));
    expect(filled.length).toBeGreaterThan(5);
    for (const rule of filled) {
      expect(rule.body, rule.selector).toMatch(/(?:^|\s)color: var\(--[\w-]+\);/);
    }
  });

  it.each([
    ["light", light.tokens],
    ["dark", darkBySystem.tokens],
  ] as const)("%s: the focus ring reaches 3:1", (_scheme, tokens) => {
    for (const [ring, surface] of FOCUS) {
      expect(contrast(tokens[ring], tokens[surface]), `--${ring} on --${surface}`).toBeGreaterThanOrEqual(3);
    }
  });

  it("measures contrast as WCAG does", () => {
    expect(contrast("#000000", "#ffffff").toFixed(2)).toBe("21.00");
    expect(contrast("#767676", "#ffffff").toFixed(2)).toBe("4.54");
  });
});

function memoryStorage(initial: Record<string, string> = {}) {
  const data = new Map(Object.entries(initial));
  const calls: string[] = [];
  return {
    getItem: (key: string) => (calls.push("getItem"), data.get(key) ?? null),
    setItem: (key: string, value: string) => (calls.push("setItem"), void data.set(key, value)),
    removeItem: (key: string) => (calls.push("removeItem"), void data.delete(key)),
    data,
    calls,
  };
}

const blocked = {
  getItem(): string | null {
    throw new Error("blocked");
  },
  setItem(): void {
    throw new Error("blocked");
  },
  removeItem(): void {
    throw new Error("blocked");
  },
};

describe("theme choice", () => {
  it("cycles System, Light, Dark and back", () => {
    expect(THEMES.map(nextTheme)).toEqual(["light", "dark", "system"]);
    expect(Object.keys(THEME_LABELS)).toEqual([...THEMES]);
  });

  it("reads only a stored light or dark as an override", () => {
    expect(readTheme(memoryStorage())).toBe("system");
    expect(readTheme(memoryStorage({ [THEME_KEY]: "dark" }))).toBe("dark");
    expect(readTheme(memoryStorage({ [THEME_KEY]: "light" }))).toBe("light");
    expect(readTheme(memoryStorage({ [THEME_KEY]: "sepia" }))).toBe("system");
    expect(readTheme(null)).toBe("system");
    expect(readTheme(blocked)).toBe("system");
  });

  it("sets the attribute and stores only that word", () => {
    const root = { dataset: {} as Record<string, string | undefined> };
    const storage = memoryStorage();
    applyTheme(root, storage, "dark");
    expect(root.dataset).toEqual({ theme: "dark" });
    expect([...storage.data]).toEqual([[THEME_KEY, "dark"]]);
    applyTheme(root, storage, "system");
    expect(root.dataset).toEqual({});
    expect(storage.data.size).toBe(0);
    applyTheme(root, blocked, "light");
    expect(root.dataset).toEqual({ theme: "light" });
  });

  it("cycles from the choice the page shows, with storage and without", () => {
    expect(shownTheme({ dataset: {} })).toBe("system");
    expect(shownTheme({ dataset: { theme: "dark" } })).toBe("dark");
    expect(shownTheme({ dataset: { theme: "sepia" } })).toBe("system");
    for (const storage of [memoryStorage(), blocked, null]) {
      const root = { dataset: {} as Record<string, string | undefined> };
      expect(cycleTheme(root, storage)).toBe("light");
      expect(cycleTheme(root, storage)).toBe("dark");
      expect(root.dataset).toEqual({ theme: "dark" });
      expect(cycleTheme(root, storage)).toBe("system");
      expect(root.dataset).toEqual({});
    }
    expect(THEMES.map(themeAnnouncement)).toEqual([
      "Theme set to System",
      "Theme set to Light",
      "Theme set to Dark",
    ]);
  });

  it("restores a stored light or dark and leaves the page alone otherwise", () => {
    const root = { dataset: {} as Record<string, string | undefined> };
    restoreTheme(root, memoryStorage({ [THEME_KEY]: "dark" }));
    expect(root.dataset).toEqual({ theme: "dark" });
    // Blocked or empty storage reads as "system": a choice made on this visit stays.
    for (const storage of [blocked, null, memoryStorage(), memoryStorage({ [THEME_KEY]: "sepia" })]) {
      restoreTheme(root, storage);
      expect(root.dataset).toEqual({ theme: "dark" });
    }
    restoreTheme(root, memoryStorage({ [THEME_KEY]: "light" }));
    expect(root.dataset).toEqual({ theme: "light" });
  });

  // A page load must not change what is stored, also not a value it does not understand.
  it.each<Record<string, string>>([{}, { [THEME_KEY]: "dark" }, { [THEME_KEY]: "light" }, { [THEME_KEY]: "sepia" }])(
    "restores by reading only, and keeps the store as it was: %j",
    (initial) => {
      const storage = memoryStorage(initial);
      restoreTheme({ dataset: {} }, storage);
      expect(storage.calls).toEqual(["getItem"]);
      expect(Object.fromEntries(storage.data)).toEqual(initial);
    },
  );

  it("shows a choice made in another tab until it stops listening", () => {
    const listeners = new Set<(event: { key: string | null }) => void>();
    const events = {
      addEventListener: (_type: "storage", listener: (event: { key: string | null }) => void) =>
        void listeners.add(listener),
      removeEventListener: (_type: "storage", listener: (event: { key: string | null }) => void) =>
        void listeners.delete(listener),
    };
    const fire = (key: string | null) => listeners.forEach((listener) => listener({ key }));
    const root = { dataset: {} as Record<string, string | undefined> };
    const storage = memoryStorage();
    let changes = 0;
    const stop = watchTheme(events, root, () => storage, () => void changes++);
    expect(listeners.size).toBe(1);

    storage.setItem(THEME_KEY, "dark");
    fire("another.key");
    expect(root.dataset).toEqual({});
    expect(changes).toBe(0);
    fire(THEME_KEY);
    expect(root.dataset).toEqual({ theme: "dark" });
    expect(changes).toBe(1);
    // The next click starts from the other tab's choice.
    expect(cycleTheme(root, storage)).toBe("system");
    // Key null: the storage was cleared.
    root.dataset.theme = "light";
    fire(null);
    expect(root.dataset).toEqual({});

    stop();
    expect(listeners.size).toBe(0);
  });

  it("applies a stored choice in the inline script of the layout", () => {
    const run = (stored: Record<string, string> | "blocked") => {
      const document = { documentElement: { dataset: {} as Record<string, string> } };
      const window = { localStorage: stored === "blocked" ? blocked : memoryStorage(stored) };
      new Function("window", "document", THEME_INIT_SCRIPT)(window, document);
      return document.documentElement.dataset;
    };
    const stored = (theme: Theme | "sepia") => ({ [THEME_KEY]: theme });
    expect(run(stored("dark"))).toEqual({ theme: "dark" });
    expect(run(stored("light"))).toEqual({ theme: "light" });
    expect(run(stored("sepia"))).toEqual({});
    expect(run({})).toEqual({});
    expect(run("blocked")).toEqual({});
    const layout = readFileSync(new URL("../app/layout.tsx", import.meta.url), "utf8");
    expect(layout).toContain("dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }}");
    expect(layout).toContain('<html lang="en" suppressHydrationWarning>');
  });
});
