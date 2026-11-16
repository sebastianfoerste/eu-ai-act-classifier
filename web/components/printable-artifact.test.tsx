import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { FALLBACK_DRAFT_NOTICE, printDocument } from "../lib/print";
import { PrintableArtifact } from "./printable-artifact";

const ARTIFACTS = [
  "art-6-4-assessment",
  "fria",
  "annex-iv-checklist",
  "post-market-monitoring-plan",
  "serious-incident-register",
  "gpai-model-documentation",
  "training-content-summary",
];

function textOf(markup: string, tag: string): string[] {
  return [...markup.matchAll(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, "g"))].map((m) => m[1]);
}

describe("PrintableArtifact", () => {
  it.each(ARTIFACTS)("prints the notice before the %s artifact, in the repeating header", (name) => {
    const doc = printDocument(FALLBACK_DRAFT_NOTICE, name, "CreditSightScore", `# ${name}\n\nbody of ${name}`);
    const markup = renderToStaticMarkup(<PrintableArtifact doc={doc} />);
    const notice = markup.indexOf(`<p class="printNotice">${FALLBACK_DRAFT_NOTICE}</p>`);
    const artifact = markup.indexOf(`<pre># ${name}`);
    expect(notice).toBeGreaterThan(-1);
    expect(artifact).toBeGreaterThan(notice);
    // The notice sits in the table header group, which print repeats on every page.
    expect(textOf(markup, "thead")[0]).toContain(FALLBACK_DRAFT_NOTICE);
    expect(textOf(markup, "tbody")[0]).not.toContain("printNotice");
    expect(markup.startsWith('<section class="printOnly"')).toBe(true);
  });

  it("prints the fallback notice when the dossier carries none", () => {
    const markup = renderToStaticMarkup(<PrintableArtifact doc={printDocument(undefined, "FRIA", "x", "body")} />);
    expect(markup).toContain(FALLBACK_DRAFT_NOTICE);
  });
});

describe("print stylesheet", () => {
  const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
  const print = css.slice(css.indexOf("@media print"));

  it("hides the app only where a printable section exists, and shows that section", () => {
    expect(print).toMatch(/\.shell:has\(> \.printOnly\) > :not\(\.printOnly\)\s*\{\s*display: none !important;/);
    expect(print).toMatch(/\.printOnly\s*\{[^}]*display: block;/);
    expect(css).toMatch(/^\.printOnly\s*\{\s*display: none;\s*\}/m);
  });

  it("repeats the table header group on every printed page", () => {
    expect(print).toMatch(/\.printSheet thead\s*\{\s*display: table-header-group;/);
  });
});
