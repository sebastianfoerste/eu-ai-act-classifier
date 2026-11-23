import { readFileSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";

// A region that scrolls on its own must be reachable by keyboard and must say what it
// holds: a role, a name and tabIndex={0}, with a visible focus ring from the stylesheet.
// Checked in the source, since the web tests run without a DOM.

const ROOTS = ["../components/", "../app/"];
// The printed draft's <pre> sits in the .printOnly section of this file. It is shown in
// print only, wraps and does not scroll, so it is the one <pre> left out.
const PRINT_ONLY_FILE = "components/printable-artifact.tsx";
const SCROLL_CLASS = /\b(?:tableWrap|scrollX)\b/;

type Region = { file: string; tag: string; source: string };
type Source = { file: string; source: string };

// An id attribute itself, not data-testid or another attribute that ends in id.
function idCount(source: string, value: string): number {
  const escaped = value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return source.match(new RegExp(`(?<![\\w-])id=${escaped}`, "g"))?.length ?? 0;
}

function sources(): Source[] {
  const found: Source[] = [];
  for (const root of ROOTS) {
    const files = readdirSync(new URL(root, import.meta.url), { recursive: true, encoding: "utf8" });
    for (const file of files.filter((name) => name.endsWith(".tsx") && !name.includes(".test.")).sort()) {
      found.push({ file: `${root.slice(3)}${file}`, source: readFileSync(new URL(root + file, import.meta.url), "utf8") });
    }
  }
  return found;
}

// Where the print-only section starts and ends in its file.
function printOnlyRange(source: string): [number, number] {
  const start = source.indexOf('className="printOnly"');
  return [start, start < 0 ? -1 : source.indexOf("</section>", start)];
}

// The opening tag that starts at `start`, with braces counted so that `>` inside a JSX
// expression does not end it.
function openingTag(source: string, start: number): string {
  let depth = 0;
  for (let i = start; i < source.length; i += 1) {
    const char = source[i];
    if (char === "{") depth += 1;
    else if (char === "}") depth -= 1;
    else if (char === ">" && depth === 0) return source.slice(start, i + 1);
  }
  return source.slice(start);
}

function scrollRegions(): Region[] {
  const regions: Region[] = [];
  for (const { file, source } of sources()) {
    const [printStart, printEnd] = file === PRINT_ONLY_FILE ? printOnlyRange(source) : [-1, -1];
    for (const match of source.matchAll(/<(\w+)\b/g)) {
      const tag = openingTag(source, match.index);
      const scrolls = /\sclassName="[^"]*\b(?:tableWrap|scrollX)\b[^"]*"/.test(tag);
      const printOnly = match.index > printStart && match.index < printEnd;
      const isPre = match[1] === "pre" && !printOnly;
      if (scrolls || isPre) regions.push({ file, tag: tag.replace(/\s+/g, " "), source });
    }
  }
  return regions;
}

const regions = scrollRegions();

describe("scroll regions", () => {
  it("finds every scrolling table wrapper and code block", () => {
    const count = (file: string, pattern: RegExp) =>
      regions.filter((region) => region.file === file && pattern.test(region.tag)).length;
    expect(regions).toHaveLength(11);
    expect(count("components/cockpit.tsx", /tableWrap/)).toBe(6);
    expect(count("components/cockpit.tsx", /^<pre\b/)).toBe(2);
    expect(count("components/obligation-tracker.tsx", /tableWrap/)).toBe(2);
    expect(count("app/workspace/page.tsx", /scrollX/)).toBe(1);
    // Every mention of a scroll class is a region found above, so a class written another
    // way (className={"tableWrap"}, a template string) cannot slip past the scan.
    for (const { file, source } of sources()) {
      const mentions = source.match(new RegExp(SCROLL_CLASS.source, "g"))?.length ?? 0;
      expect(mentions, file).toBe(count(file, SCROLL_CLASS));
    }
    // The print-only file holds exactly one <pre>, the one inside .printOnly.
    const printable = sources().find(({ file }) => file === PRINT_ONLY_FILE)?.source ?? "";
    const [printStart, printEnd] = printOnlyRange(printable);
    const pres = [...printable.matchAll(/<pre\b/g)].map((match) => match.index);
    expect(pres).toHaveLength(1);
    expect(pres[0] > printStart && pres[0] < printEnd).toBe(true);
  });

  it("gives each one a role, a name that resolves in its file, and tabIndex={0}", () => {
    const names: string[] = [];
    for (const { file, tag, source } of regions) {
      const where = `${file}: ${tag}`;
      expect(tag, where).toMatch(/\srole="(?:group|region)"/);
      expect(tag, where).toMatch(/\stabIndex=\{0\}/);
      const label = tag.match(/\saria-label="([^"]+)"/)?.[1];
      const labelledBy = tag.match(/\saria-labelledby="([^"]+)"/)?.[1];
      const labelledByExpression = tag.match(/\saria-labelledby=\{(\w+)\}/)?.[1];
      expect([label, labelledBy, labelledByExpression].filter(Boolean), where).toHaveLength(1);
      if (label) names.push(`${file}#${label}`);
      if (labelledBy) {
        for (const id of labelledBy.split(/\s+/)) {
          expect(idCount(source, `"${id}"`), `${where}: id="${id}"`).toBe(1);
        }
        names.push(`${file}#${labelledBy}`);
      }
      if (labelledByExpression) {
        expect(idCount(source, `{${labelledByExpression}}`), `${where}: id={${labelledByExpression}}`).toBeGreaterThan(0);
      }
    }
    // Two regions in one file with the same fixed name could not be told apart.
    expect(new Set(names).size).toBe(names.length);
  });

  it("keeps the focus ring for table wrappers and code blocks", () => {
    const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8").replace(
      /\/\*[\s\S]*?\*\//g,
      "",
    );
    const rules = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map(([, selector, body]) => ({
      selectors: selector.split(",").map((part) => part.trim()),
      body,
    }));
    const ring = rules.find(
      ({ selectors }) => selectors.includes(".tableWrap:focus-visible") && selectors.includes("pre:focus-visible"),
    );
    const outlines = (body: string) => [...body.matchAll(/(?<![\w-])(outline(?:-[a-z-]+)?)\s*:\s*([^;}]+)/g)];
    expect(ring?.body ?? "").toMatch(/outline: 3px solid var\(--blue\);/);
    expect(outlines(ring?.body ?? "").map(([, property]) => property)).toEqual(["outline", "outline-offset"]);
    // No other rule may touch the outline of a table wrapper or a code block, also not in a
    // selector list and not through outline-style, outline-color or outline-width.
    const TARGET = /(?:\.tableWrap|(?<![\w.#-])pre)(?::focus(?:-visible)?)?$/;
    for (const rule of rules.filter((candidate) => candidate !== ring)) {
      if (!rule.selectors.some((selector) => TARGET.test(selector))) continue;
      expect(outlines(rule.body).map(([declaration]) => declaration), rule.selectors.join(", ")).toEqual([]);
    }
  });
});
