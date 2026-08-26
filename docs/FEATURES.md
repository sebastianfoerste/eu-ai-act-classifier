# Features: EU AI Act Classifier

## Deterministic Classification

Classifies a typed `SystemProfile` through scope, prohibited-practices, high-risk, general-purpose AI, transparency and resolution gates.

Implementation:

1. `src/eu_ai_act_classifier/engine.py`
2. `src/eu_ai_act_classifier/models.py`
3. `tests/test_engine.py`

## Source Status Model

Separates binding Level 1 text, any future provisional political-agreement context and nonbinding guidance. Regulation (EU) 2026/1744 is recorded as an adopted and published Level 1 amendment. Guidance overlays are advisory and do not change the deterministic classification path.

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

## AI Systems Inventory And Review Table

Aggregates example profiles into reviewer-facing inventory rows. Each row carries role, risk tier, disposition, source-manifest status, open facts, obligations, draft artifacts, review status and next action, with the Python classifier as the source of truth.

The same payload now includes `eu-ai-act-classifier.system-review-table.v1`, a factor-level review table over scope, risk classification, operator role and draft artifact pack. Rows expose classifier-backed values, source status, obligation graph refs, draft artifacts, reviewer notes, cell status, citation source class, review state and next action. The table remains draft-only and does not turn classifier output into a legal conclusion without reviewer sign-off.

The review table also records draft artifact status and blocked external action state so reviewer notes remain tied to classifier-backed rows.

Implementation:

1. `src/eu_ai_act_classifier/inventory.py`
2. `src/eu_ai_act_classifier/local_api.py`
3. `web/components/cockpit.tsx`
4. `web/lib/types.ts`
5. `tests/test_system_inventory.py`

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
