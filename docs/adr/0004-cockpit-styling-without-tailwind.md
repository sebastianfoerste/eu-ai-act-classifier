# 0004 Cockpit styling without Tailwind

Status: Accepted

## Context

`/workspace` and `/self-assessment` used Tailwind utility classes, but Tailwind is not a dependency, so both pages rendered unstyled. The cockpit home uses plain classes in `web/app/globals.css`.

## Decision

Move both pages to a small set of plain classes in `globals.css` on the existing cockpit tokens. Do not add Tailwind.

Text on tinted surfaces uses a new `--muted-on-tint` token, because `--muted` on `--surface-muted` measured 4.47:1, below WCAG AA.

## Consequences

- No new dependency, no build configuration change.
- One stylesheet for the cockpit; a later dark mode redefines the tokens once.
