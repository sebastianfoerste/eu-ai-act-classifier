# Features: EU AI Act Classifier

## Deterministic Classification

Classifies a typed `SystemProfile` through scope, prohibited-practices, high-risk, general-purpose AI, transparency and resolution gates.

Implementation:

1. `src/eu_ai_act_classifier/engine.py`
2. `src/eu_ai_act_classifier/models.py`
3. `tests/test_engine.py`

## What It Checks

| Gate | Decides | Example from the eval set |
|---|---|---|
| Scope and intake | AI-system status, EU nexus, and the Art. 111 transitions: placing-on-market and putting-into-service dates compared with the Chapter III date (Art. 111(2), with the Art. 111(1) carve-out named), the model date (Art. 111(3)) and Art. 50(2) for systems already on the market (Art. 111(4)) | `examples/ambiguous_use_case.json` |
| Prohibited practices (Art. 5) | Flags prohibited use cases, including Art. 5(1)(ba) and (bb) from 2 December 2026 | `examples/social_scoring.json`, `examples/emotion_hiring.json`, `examples/intimate_imagery_generator.json` |
| High-risk (Art. 6, Annex I, Annex III) | Risk tier and provider/deployer obligations. An Annex I, Section B product with no Annex III area gets the Art. 2(2) provisions instead of the Chapter III duties; with an Annex III area it keeps the Annex III duties. Every Section B product keeps Art. 5 and Art. 50, which Art. 2(2) does not list. Each kept position is the conservative reading, flagged "Literal reading, confirm with counsel": the Annex III duties on the Art. 6(1) finding and the Art. 2(2) item, Art. 5 on its finding, Art. 50 on the `TRANSPARENCY.50` finding and each Art. 50 item. Each flag is also an open question, so the result goes to review | `examples/credit_scoring.json`, `examples/cv_screening.json` |
| GPAI | Systemic-risk status and compute scale | `examples/gpai_systemic_by_flops.json` |
| Transparency | Limited-risk cases | `examples/deepfake_generator.json`, `examples/support_chatbot.json` |

Which example lands in which tier is asserted in `tests/test_examples.py`. See [examples/README.md](../examples/README.md).

Which Annex III points the classifier covers, with the citation each emits and the examples and tests behind it: [docs/coverage.md](coverage.md), generated from the code.

## Source Status Model

Separates binding Level 1 text, any future provisional political-agreement context and nonbinding guidance. Regulation (EU) 2026/1744 is recorded as an adopted and published Level 1 amendment. Guidance overlays are advisory and do not change the deterministic classification path.

Implementation:

1. `src/eu_ai_act_classifier/citations.py`
2. `src/eu_ai_act_classifier/verify_sources.py`
3. `docs/source-status-model.md`
4. `tests/test_required_dispositions.py`

## Obligation Graph

Turns classification findings into reviewer-facing obligations with article, actor role, trigger, evidence artifact, source status, application date, review status and, where the date rests on a contestable reading or a transitional rule, an application date note.

Beyond the Chapter III duties, the graph covers Art. 49(3) registration of use by public-authority deployers (inferred for review where the deployer's status is unset and the system is intended to be used by public authorities or its Annex III point is 5(a), 6 or 7), the Art. 49(5) pointer for point 2, the Art. 111(2) transition for high-risk systems already on the market (one item per operator role, with the 2 August 2030 deadline for the providers and deployers of systems intended to be used by public authorities), the Art. 2(2) limit for Annex I, Section B products, and the Art. 111(3) and (4) transitions dated by separate model and system dates. Contested items carry "Literal reading, confirm with counsel" and are `review_required`.

A high-risk system placed on the market or put into service before its Chapter III date gets a flagged Art. 111(2) note on every high-risk item and an open question, so its disposition is `requires_review` and `--strict` exits 1 until `significant_change_after_application_date` is answered. A GPAI profile dated only by `placing_on_market_date` also goes to review until the model's own date is given.

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

## Guided Intake

Collects characterised facts one question per page in the browser playground, with the article under each question and a check-answers page that lists every defaulted value. Questions, order and skip conditions are defined once in Python. "I don't know" never becomes "no": it records an unconfirmed value that routes the result to review, marks the Annex III point as unsettled, or pauses the run until counsel answers.

Implementation:

1. `src/eu_ai_act_classifier/intake.py`
2. `docs/playground/intake.mjs` and `docs/playground/wizard.mjs`
3. `tests/test_intake.py` and `tests/playground/intake.test.mjs`

## Display Labels

One label catalog for Annex III points, Art. 5 practices, roles, statuses and draft artifacts, generated for the playground field guide and the cockpit. Annex III and Art. 5 labels reuse the pinpoints and titles in `catalog.py`.

Implementation:

1. `src/eu_ai_act_classifier/labels.py`
2. `web/lib/labels.ts`
3. `tests/test_labels.py`

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
3. `web/app/globals.css`: plain CSS for every cockpit page, including the portfolio (`/workspace`) and self-assessment pages
