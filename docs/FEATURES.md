# Features: EU AI Act Classifier

## Deterministic Classification

Classifies a typed `SystemProfile` through scope, prohibited-practices, high-risk, general-purpose AI, transparency and resolution gates.

Implementation:

1. `src/eu_ai_act_classifier/engine.py`
2. `src/eu_ai_act_classifier/models.py`
3. `tests/test_engine.py`

## Source Status Model

Separates binding Level 1 text, provisional political-agreement context and nonbinding guidance. Guidance overlays are advisory and do not change the deterministic classification path.

Implementation:

1. `src/eu_ai_act_classifier/citations.py`
2. `src/eu_ai_act_classifier/verify_sources.py`
3. `docs/source-status-model.md`
4. `tests/test_required_dispositions.py`

## Obligation Graph

Turns classification findings into reviewer-facing obligations with article, actor role, trigger, evidence artifact, source status, application date and review status.

Implementation:

1. `src/eu_ai_act_classifier/obligation_graph.py`
2. `tests/test_obligations_and_artifacts.py`

## Draft Review Artifacts

Generates draft-only artifacts for supervised review, including an Art. 6(4) assessment, FRIA, Annex IV checklist, post-market monitoring plan, serious-incident register, GPAI model documentation and training-content summary.

Implementation:

1. `src/eu_ai_act_classifier/artifacts.py`
2. `docs/sample-review-dossier.md`
3. `tests/test_obligations_and_artifacts.py`

## Optional Local Cockpit

Provides a local Next.js reviewer surface over the Python bridge. It keeps the Python classifier as the source of truth and uses in-memory state for v1.

Implementation:

1. `web/app`
2. `src/eu_ai_act_classifier/local_api.py`
