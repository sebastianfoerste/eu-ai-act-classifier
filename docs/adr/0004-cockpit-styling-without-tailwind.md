# 0004 Cockpit styling without Tailwind

Status: Accepted

## Context

`/workspace` and `/self-assessment` used Tailwind utility classes, but Tailwind is not a dependency, so both pages rendered unstyled. The cockpit home uses plain classes in `web/app/globals.css`.

## Decision

Move both pages to a small set of plain classes in `globals.css` on the existing cockpit tokens. Do not add Tailwind.

Text on tinted surfaces uses a new `--muted-on-tint` token, because `--muted` on `--surface-muted` measured 4.48:1, below WCAG AA. Update of 23 November 2026: `--muted` changed from `#64717f` to `#63707e` and now measures 4.54:1 on `--surface-muted`; `--muted-on-tint` stays for the text on tinted surfaces.

## Consequences

- No new dependency, no build configuration change.
- One stylesheet for the cockpit; a later dark mode redefines the tokens once.
