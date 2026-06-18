# EU AI Act Classifier

AI governance teams need a fast way to triage AI-system facts under Regulation
(EU) 2024/1689 without turning a demo into a legal-advice machine. The hard
part is not producing a confident label. The hard part is showing which facts
trigger the legal route, which source supports the route and where human review
is still required.

EU AI Act Classifier is a deterministic Python classifier, CLI, MCP tool and
optional local cockpit. It applies the binding Level 1 text, keeps provisional
dates separate, adds nonbinding guidance only as an advisory overlay and emits
draft-only reports for supervised legal review.

Quick evaluator command:

```bash
uv run eu-ai-act-classify examples/credit_scoring.json
```

Sample output:

```text
EU AI Act classification: CreditSightScore
Risk tier: HIGH-RISK (Art. 6 AIA)
Disposition: DETERMINED
Scope status: in_scope
Roles: provider
```

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

## Reviewer Demo Path

Use the CLI first. It is the authoritative product surface and does not require
web dependencies:

```bash
uv run pytest
uv run eu-ai-act-classify examples/credit_scoring.json --strict
uv run eu-ai-act-classify examples/credit_scoring.json --sources
uv run eu-ai-act-classify examples/credit_scoring.json \
  --artifact all \
  --artifacts-dir /tmp/eu-ai-act-draft-pack
```

Then inspect `/tmp/eu-ai-act-draft-pack`. The generated files are draft review
artifacts, not legal opinions, conformity assessments or filing documents.

Run the optional cockpit only after the Python checks pass:

```bash
cd web
npm install
npm run build
npm run dev
```

The cockpit is a local reviewer interface over the Python bridge. It does not
change the classifier result and it does not persist client or matter data.

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

## Risk-Tier Map

| Tier | Trigger | Citation | Obligation | Review status |
| --- | --- | --- | --- | --- |
| Prohibited | Art. 5 practice, such as social scoring | Art. 5 AIA | Do not place, put into service or use | Blocker, legal review required |
| High risk | Annex I product route or Annex III area | Art. 6, Annex I, Annex III AIA | Provider, deployer and value-chain obligations | Determined or requires review |
| GPAI | General-purpose AI model facts | Arts. 51, 53, 55 and 56 AIA | GPAI provider documentation and systemic-risk duties | Determined or requires review |
| Limited risk | Transparency-only system | Art. 50 AIA | User-facing transparency duties | Determined |
| Minimal risk | No higher-tier trigger | No specific higher-tier trigger | No classifier-derived AIA duty | Determined, keep governance record |
| Requires review | Ambiguous facts or unverified legal route | Depends on open question | Route to qualified reviewer | Human review required |

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

The cockpit now shows loading, bridge-error and empty-artifact states explicitly.
If the local JSON bridge fails, retry metadata or run the CLI commands above to
separate a UI issue from a classifier issue.

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

## Optional Cockpit Snapshot

The web cockpit is an optional reviewer surface. The Python classifier remains
the legal source of truth.

```text
Inventory -> Guided intake -> Python classify bridge -> Risk map
          -> Open questions -> Source provenance -> Obligation tracker
          -> Draft export preview

Current sample:
System: CreditSightScore
Tier: high_risk
Disposition: determined
Primary citation: Annex III(5)(b) AIA
Review note: draft only, lawyer review before reliance
```

## Known Legal Limits

- Guidance changes. Commission, AI Office and national materials can change and
  remain nonbinding unless adopted through the relevant legal route.
- National implementation. Market-surveillance practice, penalties and
  notified-body practice may vary by Member State.
- Fact dependency. The engine applies rules to characterised facts; it does not
  decide disputed intended purpose, operator role or factual deployment scope.
- Lawyer review. `requires_review`, draft artifacts and advisory overlays must
  be reviewed before reliance.

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

See [Deterministic Classification Versus Legal Advice](docs/deterministic-classification-vs-legal-advice.md).

## Reviewer Checklist

Use this checklist when evaluating the repository as a portfolio project or employer demo:

- [ ] Run `uv run pytest` - 74 tests pass with no external dependencies.
- [ ] Run `uv run eu-ai-act-classify examples/credit_scoring.json --strict` - CLI produces risk tier, disposition and obligation graph.
- [ ] Run `uv run eu-ai-act-classify examples/credit_scoring.json --sources` - source manifest shows binding, provisional and advisory separation.
- [ ] Run `uv run eu-ai-act-classify examples/credit_scoring.json --artifact all --artifacts-dir /tmp/eu-ai-act-draft-pack` - draft artifact pack written to `/tmp`.
- [ ] Review `tests/test_local_api.py` - confirms `review_status: draft_only_human_review_required` on all artifact outputs.
- [ ] Review `docs/deterministic-classification-vs-legal-advice.md` - confirms classification logic and legal limits.
- [ ] Review `docs/sample-output.md` - confirms report language is review-gated.
- [ ] Review [docs/sample-review-dossier.md](docs/sample-review-dossier.md) - confirms synthetic review dossier with CLI outputs.
- [ ] Review `PRIVACY.md` - confirm synthetic-only demo boundary.
- [ ] Review `docs/DEMO_ASSET_PLAN.md` for demo guidance and hosting readiness assessment.
- [ ] Confirm all 14 synthetic example profiles still produce their expected classification tier.


## License

MIT. See [LICENSE](LICENSE).
