# 0003 Export route

Status: Proposed

## Context

The seven draft artifacts and the dossier are Markdown and JSON, each with `DRAFT_NOTICE`. The cockpit's "Word package" lists only JSON, Markdown and draft artifacts. No inspected peer keeps a draft status on exported documents. Running page headers in print CSS (`@page` margin boxes) work only in Chromium.

## Decision

1. PDF through a print stylesheet on the artifact preview, with `DRAFT_NOTICE` as the first block in the page flow and "DRAFT" in the document title. No dependency.
2. DOCX through `python-docx` (MIT) in an optional `[docx]` extra, never in the core install, with the notice as the first paragraph and in the core properties title.
3. Until DOCX exists, rename the cockpit's "Word package" to "Draft package".

## Consequences

- The core stays Pydantic-only.
- A browser-side DOCX library (npm `docx`, about 131 KB gzip minified) is not needed.
