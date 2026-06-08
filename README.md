# EU AI Act Classifier

A deterministic EU AI Act triage engine for AI-system intake, risk classification,
source provenance, obligation tracking and draft legal work products.

The classifier applies Regulation (EU) 2024/1689 as the binding Level 1 source.
It also records provisional AI Omnibus dates and optional Commission guidance
overlays as separate, nonbinding context. Legal outputs remain draft-only and
review-gated.

## What It Does

The engine runs six gates over a typed `SystemProfile`.

1. Scope and intake: AI-system status, intended-purpose source, EU nexus,
   excluded-use flags, placement dates, significant changes and public-authority
   use.
2. Prohibited practices: Art. 5 AIA.
3. High-risk classification: Art. 6, Annex I and Annex III.
4. General-purpose AI models: Arts. 51, 53, 55 and 56 AIA.
5. Transparency: Art. 50 AIA.
6. Resolution: risk tier, disposition, obligation graph, timeline and open
   legal questions.

Existing alpha profiles remain compatible. Missing new scope fields default to
an in-scope AI system so the original 14 synthetic examples keep their expected
results.

## Source Statuses

Reports and draft artifacts use a versioned source manifest.

Binding Level 1 text:
Regulation (EU) 2024/1689 and the Art. 113 application timeline.

Provisional political agreement:
The AI Omnibus political agreement, including 2 December 2027 for Annex III
high-risk systems and 2 August 2028 for product-embedded high-risk systems.
These dates are labelled provisional until formal adoption and Official Journal
publication.

Nonbinding guidance:
Commission prohibited-practices guidance, AI-system-definition guidance, draft
high-risk guidance, AI Act Service Desk materials, the GPAI Code of Practice,
GPAI provider guidance and future transparency guidance.

Guidance overlays are advisory notes. They do not override the binding
classification logic.

## Outputs

`ClassificationReport` contains:

1. Risk tier and disposition.
2. Scope assessment and transitional notes.
3. Findings with citation status.
4. Backward-compatible obligation, documentation and transparency fields.
5. Structured `obligation_graph` items with trigger, actor, evidence artifact,
   application date, review status and source metadata.
6. Binding and provisional timelines rendered separately.
7. Source manifest with URL, retrieval date, legal status, citation label and
   implementation note.
8. Optional advisory overlay notes.
9. Open legal questions and unverified citations.

## Quick Start

```bash
uv venv
uv pip install -e ".[dev]"

eu-ai-act-classify examples/cv_screening.json
eu-ai-act-classify examples/foundation_model_systemic.json --json
cat examples/credit_scoring.json | eu-ai-act-classify -
eu-ai-act-classify examples/employment_derogation.json --strict
```

Use `--advisory` to include nonbinding guidance notes.

Use `--sources` to emit the source manifest as JSON.

Generate draft work products only when an output directory is supplied:

```bash
eu-ai-act-classify examples/credit_scoring.json \
  --artifact all \
  --artifacts-dir ./draft-artifacts
```

Available artifact names:

1. `art-6-4-assessment`
2. `fria`
3. `annex-iv-checklist`
4. `post-market-monitoring-plan`
5. `serious-incident-register`
6. `gpai-model-documentation`
7. `training-content-summary`

Artifacts are drafts. They are not legal advice, not conformity assessments and
not final regulatory filings.

## MCP And Local API

The MCP server remains available:

```bash
uv pip install -e ".[mcp]"
python -m eu_ai_act_classifier.mcp_server
```

The local JSON bridge is used by the optional web cockpit:

```bash
eu-ai-act-local-api schema
echo '{"profile":{"name":"x"}}' | eu-ai-act-local-api classify
```

The bridge exposes schema, classify, sources and artifacts commands. It keeps
the Python classifier as the legal source of truth.

## Optional Web Cockpit

The `web/` folder contains a local Next.js App Router cockpit with:

1. System inventory.
2. Guided questionnaire.
3. Risk map.
4. Open legal questions.
5. Reviewer notes.
6. Source provenance.
7. Obligation tracker.
8. Export pack preview.

Run it locally:

```bash
cd web
npm install
npm run dev
```

The web app uses in-memory state for v1. It does not persist client, matter,
candidate, account or privileged data.

Route surface:

1. `GET /api/health`
2. `GET /api/schema`
3. `POST /api/classify`
4. `GET /api/sources`
5. `POST /api/artifacts`

## Eval Set

`examples/` holds 14 synthetic systems spanning prohibited, high-risk, limited
risk, minimal risk, GPAI and review-required cases. The expected results are
asserted in `tests/test_examples.py`.

`examples/guidance/` holds Commission-derived guidance examples and stored beta
Compliance Checker comparisons. They are nonbinding review evidence and are
tested separately from the binding classifier logic.

See [examples/README.md](examples/README.md) and
[docs/launch-readiness.md](docs/launch-readiness.md).

## Stack

Python 3.13+, Pydantic v2, pytest, ruff and uv for the classifier.

Next.js App Router, React and lucide-react for the optional local cockpit.

The core classifier has one runtime dependency. MCP and the web cockpit remain
optional surfaces.

## Safety

This is a screening tool for supervised legal review. It does not produce legal
advice, a conformity assessment or a binding regulatory conclusion.

Determinations marked `requires_review` turn on facts the engine cannot settle.
Generated work products require human legal review before use.

## License

MIT. See [LICENSE](LICENSE).
