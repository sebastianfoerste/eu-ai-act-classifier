# Changelog

## Unreleased

### Added

- Guided intake in the browser playground: one question per page, an "I don't know" answer that routes to review or pauses the run for counsel, and a check-answers page listing every defaulted value. Questions, order and skip conditions come from `src/eu_ai_act_classifier/intake.py`; the JSON editor remains as a second mode.
- `labels.py`: one display-label catalog for the playground field guide and the cockpit, using the pinpoints and titles in `catalog.py`.
- Competitive research, a feature matrix, a design teardown and an adaptation plan in `docs/research/`, and architecture decision records in `docs/adr/`.

### Changed

- The cockpit shows catalog labels (for example "Annex III(5)(b): Creditworthiness evaluation and credit scoring") instead of mechanically formatted values.
- The cockpit portfolio (`/workspace`) and self-assessment pages use plain CSS classes instead of Tailwind classes, which were not installed; self-assessment inputs have labels.

### Unchanged

- Classification rules, citations, application dates, examples and goldens. No new legal claim was added: the article shown under each guided question is one the engine already cites, and `tests/test_intake.py` enforces that.
