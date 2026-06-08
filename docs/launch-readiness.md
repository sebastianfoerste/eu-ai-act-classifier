# Launch Readiness

This note helps a reviewer evaluate the EU AI Act Classifier quickly.

## What This Repo Proves

The classifier turns Regulation (EU) 2024/1689 into a deterministic triage
product. A typed `SystemProfile` produces a cited `ClassificationReport` with
scope status, risk tier, source provenance, obligations, draft artifacts and
open legal questions.

The proof is legal engineering discipline: characterised facts in, source-backed
outputs out, and review gates where the engine cannot settle the fact pattern.

## Local Launch Path

```bash
uv venv
uv pip install -e ".[dev]"
eu-ai-act-classify examples/cv_screening.json
eu-ai-act-classify examples/foundation_model_systemic.json --json
eu-ai-act-classify examples/employment_derogation.json --strict
eu-ai-act-classify examples/credit_scoring.json --artifact all --artifacts-dir ./draft-artifacts
```

Optional cockpit:

```bash
cd web
npm install
npm run dev
```

## Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
cd web && npm run build
cd web && npm audit --json
```

## Sample Data Rule

Use synthetic AI-system profiles only. Do not add client product designs,
privileged risk assessments, internal launch materials or personal data to the
example set.

## Source Review

Inspect `src/eu_ai_act_classifier/citations.py` first. It separates binding
Level 1 text, provisional political agreement and nonbinding guidance.

Inspect `docs/methodology.md` next. It explains the scope gate, FRIA logic,
obligation graph and artifact posture.

## Good Evaluator Route

Review these surfaces:

1. `README.md`
2. `docs/methodology.md`
3. `src/eu_ai_act_classifier/engine.py`
4. `src/eu_ai_act_classifier/obligation_graph.py`
5. `src/eu_ai_act_classifier/artifacts.py`
6. `examples/`
7. `examples/guidance/`
8. `tests/`
9. `web/`

The key signal is that uncertainty remains visible through `requires_review`,
`open_questions`, `unverified_citations` and draft-only artifact notices.

## Safety Posture

This is a screening tool for supervised legal review. It does not produce legal
advice, a conformity assessment or a binding regulatory conclusion.
