# 0003 Export route

Status: Accepted for parts 1 and 3 (built on 16 November 2026); part 2 (DOCX) proposed

## Context

The seven draft artifacts and the dossier are Markdown and JSON, each with `DRAFT_NOTICE`. The cockpit's "Word package" lists only JSON, Markdown and draft artifacts. No inspected peer keeps a draft status on exported documents. Running page headers in print CSS (`@page` margin boxes) work only in Chromium.

## Decision

1. PDF through a print stylesheet on the artifact preview, with `DRAFT_NOTICE` as the first block in the page flow and "DRAFT" in the document title. No dependency. (As built, a separate printable section carries the artifact and repeats the notice at the top of every page; see Implementation.)
2. DOCX through `python-docx` (MIT) in an optional `[docx]` extra, never in the core install, with the notice as the first paragraph and in the core properties title.
3. Until DOCX exists, rename the cockpit's "Word package" to "Draft package".

## Implementation

- Part 1: the cockpit's Export Pack has a print button. `web/lib/print.ts` builds what is printed: the dossier's `draft_notice` (or, if it is missing, a copy of `DRAFT_NOTICE` that a test keeps equal to the engine's) and the selected artifact, under a document title that starts with "DRAFT". The title is set on `beforeprint` and restored on `afterprint`, so it also applies when printing starts from the browser menu. `web/components/printable-artifact.tsx` puts the notice in the header group of a layout table, which browsers repeat at the top of every printed page, and the artifact in its body; no `@page` margin boxes are used. The `@media print` rules in `web/app/globals.css` hide the rest of the cockpit only while a printable section exists; nothing is printable while a classification runs, so the previous system's artifact cannot be printed then.
- Part 3: the tile reads "Draft package". The inventory field keeps its name, `wordExportPackage`, because renaming it would change the inventory JSON that integrations read.
- Tests: `web/components/printable-artifact.test.tsx` renders the printable section once per artifact name, with synthetic content, and checks that the notice comes before the artifact and sits in the repeating header; it checks the print rules, and it pins in `cockpit.tsx` that the printable section is a direct child of `.shell` (which the print rules need) and that nothing is printable while a classification runs; `web/lib/print.test.ts` checks the notice value, its fallback and the title; `tests/test_review_dossier.py` checks that every artifact of every bundled example contains `DRAFT_NOTICE`.
- Checked by hand in Chromium only: print media and saved PDFs of all seven real artifacts on A4 (the notice opens every page; the full artifact prints, with its source manifest), a held-back classification (no printable section, print button disabled) and a blank intake (the page prints as it is). Firefox and WebKit, which S8's acceptance names, were not available where this was built and remain to be checked.

## Consequences

- The core stays Pydantic-only.
- A browser-side DOCX library (npm `docx`, about 131 KB gzip minified) is not needed.
