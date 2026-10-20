# 0001 Guided intake source of truth

Status: Accepted

## Context

The playground took JSON only, and the cockpit's toggles and `/self-assessment` text fields were not mapped to one question set. Open-source peers that keep separate question trees per surface show how they drift: in one, the CLI and the web wizard ask different questions in a different order, and the web wizard drops answers it cannot map (see the [landscape](../research/2026-10-competitive-landscape.md#key-findings)). `docs/DESIGN.md` keeps legal logic in Python.

## Decision

`src/eu_ai_act_classifier/intake.py` defines every guided question: the profile fields it sets, its order, a declarative condition for when it is asked, and its "I don't know" policy. `scripts/build_playground.py` writes it to `docs/playground/intake.json`. The browser module `intake.mjs` only interprets that data; it holds no question text or rule of its own.

"I don't know" is one of three policies, declared per question: write `null` where the field is nullable and the engine routes it to review; write `III.unsure` for the Annex III point; or block the run until counsel characterises the fact. It is never `false` and never an omitted field.

A condition may skip a question only where `tests/test_intake.py` shows, over a grid of earlier answers, that no answer to it changes the report.

## Consequences

- New intake surfaces (the cockpit, the MCP server) can read the same file.
- A rule change that makes a skipped question relevant fails the skip-rule test, so the definition cannot silently go stale.
- Many screens are non-nullable, so "I don't know" blocks often; see [0007](0007-systemprofile-change-proposals.md).
- `tests/playground/intake-fixtures.json` holds the browser interpreter to Python's output.
