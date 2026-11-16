import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  THEMES,
  THEME_INIT_SCRIPT,
  THEME_KEY,
  THEME_LABELS,
  type Theme,
  applyTheme,
  nextTheme,
  readTheme,
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
    expect(rules.match(/#[0-9a-fA-F]{3,8}\b|(?<![\w-])(?:white|black)(?![\w-])|rgba?\(|hsla?\(/g)).toBeNull();
    for (const [, name] of rules.matchAll(/var\(--([a-z-]+)\)/g)) {
      expect(Object.keys(light.tokens)).toContain(name);
    }
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
