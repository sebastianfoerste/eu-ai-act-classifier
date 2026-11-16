import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { DRAFT_TITLE_PREFIX, FALLBACK_DRAFT_NOTICE, printDocument, printTitle } from "./print";

describe("printDocument", () => {
  it("puts the dossier's draft notice first and keeps the artifact unchanged", () => {
    const doc = printDocument("Draft only. Review first.", "FRIA", "CreditSightScore", "# FRIA\n\nbody");
    expect(doc.notice).toBe("Draft only. Review first.");
    expect(doc.content).toBe("# FRIA\n\nbody");
    expect(doc.title.startsWith(`${DRAFT_TITLE_PREFIX}: `)).toBe(true);
  });

  it.each([null, undefined, "", "   "])("never prints without a notice (%j)", (notice) => {
    expect(printDocument(notice, "FRIA", "x", "body").notice).toBe(FALLBACK_DRAFT_NOTICE);
  });

  it("keeps the fallback notice equal to the engine's DRAFT_NOTICE", () => {
    const source = readFileSync(
      new URL("../../src/eu_ai_act_classifier/artifacts.py", import.meta.url),
      "utf8",
    );
    const match = source.match(/DRAFT_NOTICE = \(\n((?:\s+"[^"]*"\n)+)\)/);
    expect(match).not.toBeNull();
    const engineNotice = [...match![1].matchAll(/"([^"]*)"/g)].map((part) => part[1]).join("");
    expect(FALLBACK_DRAFT_NOTICE).toBe(engineNotice);
  });
});

describe("printTitle", () => {
  it("starts with DRAFT whatever it is given", () => {
    expect(printTitle("FRIA", "CreditSightScore")).toBe("DRAFT: FRIA - CreditSightScore");
    expect(printTitle("", "CreditSightScore")).toBe("DRAFT: CreditSightScore");
    expect(printTitle(" ", " ")).toBe("DRAFT");
  });
});
