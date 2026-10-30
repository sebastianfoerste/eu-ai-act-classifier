# 0001 Guided intake source of truth

Status: Accepted

## Context

The playground took JSON only, and the cockpit's toggles and `/self-assessment` text fields were not mapped to one question set. Open-source peers that keep separate question trees per surface show how they drift: in one, the CLI and the web wizard ask different questions in a different order, and the web wizard drops answers it cannot map (see the [landscape](../research/2026-10-competitive-landscape.md#key-findings)). `docs/DESIGN.md` keeps legal logic in Python.

## Decision

`src/eu_ai_act_classifier/intake.py` defines every guided question: the profile fields it sets, its order, a declarative condition for when it is asked, and its "I don't know" policy. `scripts/build_playground.py` writes it to `docs/playground/intake.json`. The browser module `intake.mjs` only interprets that data; it holds no question text or rule of its own.

"I don't know" is one of three policies, declared per question: write `null` where the field is nullable and the engine routes it to review; write `III.unsure` for the Annex III point; or block the run until counsel characterises the fact. It is never `false`. A value policy may not write the model default, which the compact profile would drop, with one exception: a conditional question whose null default the fail-closed test shows yields `requires_review` wherever the question is asked. `significant_change_after_application_date` is that exception (owner decision, 28 October 2026). It is asked only for a high-risk system, with no prohibited practice, placed on the market or put into service before its Chapter III date, where a null raises the Art. 111(2) AIA open question, so "I don't know" writes null and a profile that leaves it null opens with "I don't know" selected. Elsewhere the engine reports a given answer as not used, and the guided mode refuses to open a profile that gives one there rather than drop it. Any other model-default null opens as unanswered rather than as "I don't know". The three profile fields added for Regulation (EU) 2026/1744 in #30 (`annex_i_section`, `gpai_model_placing_on_market_date`, `deployer_public_authority`) follow the same rule: "I don't know" blocks where a missing value would not reach review, and a blank model date means "not given".

The article shown under a question must be a pinpoint the engine already cites; a test enforces this, so the intake cannot add a citation outside the claim ledger.

A condition may skip a question only where `tests/test_intake.py` tries every answer to it over grids of states the intake can reach and finds no change in the classification report. A grid state is built the way the intake builds a profile: a question it skips keeps its default. The one allowed difference is the engine's own statement that a value given there is not used (a section without the Art. 6(1) route, a model date without a general-purpose AI model). Advisory notes must match as well, except for a profile outside the AI Act's scope, where they may still reflect a screen the intake skips. The grids fix some secondary fields at one value, so this is a check, not a proof; mutating a skip condition makes it fail.

## Consequences

- New intake surfaces (the cockpit, the MCP server) can read the same file.
- A rule change that makes a skipped question relevant fails the skip-rule test, so the definition cannot silently go stale.
- Many screens are non-nullable, so "I don't know" blocks often; see [0007](0007-systemprofile-change-proposals.md).
- `tests/playground/intake-fixtures.json` holds the browser interpreter to Python's output.
