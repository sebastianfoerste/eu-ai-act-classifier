// What the cockpit prints for a draft artifact (ADR 0003, part 1): the draft notice
// first in the page flow, then the artifact, under a document title that starts with
// "DRAFT". The browser's print dialog turns this into a PDF; nothing here adds a
// dependency or a running header (`@page` margin boxes print only in Chromium).

export const DRAFT_TITLE_PREFIX = "DRAFT";

// The notice the engine puts in every artifact (DRAFT_NOTICE in
// src/eu_ai_act_classifier/artifacts.py). Used only when the dossier does not carry
// its own copy, so a printed page never goes out without one.
export const FALLBACK_DRAFT_NOTICE =
  "Draft only. This work product is not legal advice, not a conformity assessment " +
  "and not a final regulatory filing. It requires human legal review before use.";

export type PrintDocument = {
  title: string;
  notice: string;
  content: string;
};

export function printDocument(
  notice: string | null | undefined,
  artifactLabel: string,
  system: string,
  content: string,
): PrintDocument {
  const text = notice?.trim() ? notice.trim() : FALLBACK_DRAFT_NOTICE;
  return {
    title: printTitle(artifactLabel, system),
    notice: text,
    content,
  };
}

export function printTitle(artifactLabel: string, system: string): string {
  const parts = [artifactLabel.trim(), system.trim()].filter(Boolean);
  return parts.length ? `${DRAFT_TITLE_PREFIX}: ${parts.join(" - ")}` : DRAFT_TITLE_PREFIX;
}
