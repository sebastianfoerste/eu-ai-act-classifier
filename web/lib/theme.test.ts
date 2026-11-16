import { readFileSync } from "node:fs";
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

// The three token blocks: light, dark by system setting, dark by stored choice.
function tokenBlocks() {
  return [...css.matchAll(/(:root[^{]*)\{\s*color-scheme: (light|dark);([^}]*)\}/g)].map(
    ([, selector, scheme, body]) => ({
      selector: selector.trim(),
      scheme,
      tokens: Object.fromEntries(
        [...body.matchAll(/--([a-z-]+): ([^;]+);/g)].map(([, name, value]) => [name, value]),
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
  ["muted-on-tint", "surface-muted"],
  ["blue", "background"],
  ["blue", "surface"],
  ["blue", "info-bg"],
  ["on-primary", "blue"],
  ["green", "success-bg"],
  ["amber", "warning-bg"],
  ["red", "danger-bg"],
  ["violet", "surface"],
  ["violet", "surface-muted"],
  ["info-text", "info-bg-soft"],
  ["info-muted", "info-bg-soft"],
  ["code-text", "code-bg"],
];
// Below 4.5:1 in the light set, which is why --muted-on-tint exists and no rule puts
// --muted on --surface-muted. The dark set needs no such exception.
const LIGHT_BELOW: Array<[string, string]> = [["muted", "surface-muted"]];
// The line around a button, select or input, in the dark set: 3:1.
const DARK_LINES: Array<[string, string]> = [
  ["control-border", "surface"],
  ["control-border", "surface-muted"],
  ["control-border", "background"],
  ["control-border", "danger-bg"],
  ["input-border", "surface"],
  ["input-border", "surface-muted"],
];
// The focus ring, in both sets: 3:1.
const FOCUS: Array<[string, string]> = [
  ["blue", "background"],
  ["blue", "surface"],
  ["blue", "surface-muted"],
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
    const bare = value.replace(/var\(--[a-z-]+\)|url\([^)]*\)|"[^"]*"|'[^']*'/g, " ");
    for (const match of bare.match(COLOUR) ?? []) found.push(`${property}: ${match}`);
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
    expect(css.match(/color-scheme: dark;/g)).toHaveLength(2);
    expect(darkBySystem.tokens).toEqual(darkByChoice.tokens);
    expect(Object.keys(darkBySystem.tokens)).toEqual(Object.keys(light.tokens));
    expect(Object.keys(light.tokens).length).toBeGreaterThan(25);
  });

  it("writes no colour outside the token sets", () => {
    const rules = css.slice(css.indexOf("* {"));
    expect(strayColours(rules)).toEqual([]);
    // Hex anywhere in the rules, also outside a declaration.
    expect(rules.match(/#[0-9a-fA-F]{3,8}\b/g)).toBeNull();
    for (const [, name] of rules.matchAll(/var\(--([a-z-]+)\)/g)) {
      expect(Object.keys(light.tokens)).toContain(name);
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

  it("dark: no pair is excepted, light keeps its known one", () => {
    for (const [text, surface] of LIGHT_BELOW) {
      expect(contrast(light.tokens[text], light.tokens[surface])).toBeLessThan(4.5);
      expect(contrast(darkBySystem.tokens[text], darkBySystem.tokens[surface])).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("puts no muted text on the tinted surface in one rule", () => {
    for (const [rule] of css.matchAll(/[^{}]+\{[^{}]*\}/g)) {
      const tinted = rule.includes("background: var(--surface-muted);");
      expect(tinted && rule.includes("color: var(--muted);"), rule.split("{")[0].trim()).toBe(false);
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
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => void data.set(key, value),
    removeItem: (key: string) => void data.delete(key),
    data,
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
