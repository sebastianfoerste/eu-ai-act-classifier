# 0003 Export route

Status: Accepted for parts 1 and 3 (built on 16 November 2026); part 2 (DOCX) proposed

## Context

The seven draft artifacts and the dossier are Markdown and JSON, each with `DRAFT_NOTICE`. The cockpit's "Word package" lists only JSON, Markdown and draft artifacts. No inspected peer keeps a draft status on exported documents. Running page headers in print CSS (`@page` margin boxes) work only in Chromium.

## Decision

1. PDF through a print stylesheet on the artifact preview, with `DRAFT_NOTICE` as the first block in the page flow and "DRAFT" in the document title. No dependency.
2. DOCX through `python-docx` (MIT) in an optional `[docx]` extra, never in the core install, with the notice as the first paragraph and in the core properties title.
3. Until DOCX exists, rename the cockpit's "Word package" to "Draft package".

## Implementation

- Part 1: the cockpit's Export Pack has a print button. `web/lib/print.ts` builds what is printed: the dossier's `draft_notice` (or, if it is missing, a copy of `DRAFT_NOTICE` that a test keeps equal to the engine's) as the first block, then the selected artifact, under a document title that starts with "DRAFT". The title is set on `beforeprint` and restored on `afterprint`, so it also applies when printing starts from the browser menu. The `@media print` rules in `web/app/globals.css` hide everything else in the page flow; there are no `@page` margin boxes.
- Part 3: the tile reads "Draft package". The inventory field keeps its name, `wordExportPackage`, because renaming it would change the inventory JSON that integrations read.
- Checked in Chromium (print media and a PDF of the page): only the notice and the artifact print, the notice first. Firefox and WebKit were not available where this was built and remain to be checked.

## Consequences

- The core stays Pydantic-only.
- A browser-side DOCX library (npm `docx`, about 131 KB gzip minified) is not needed.
