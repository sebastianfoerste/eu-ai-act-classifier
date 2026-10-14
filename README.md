# eu-ai-act-classifier

[![CI](https://github.com/sebastianfoerste/eu-ai-act-classifier/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-ai-act-classifier/actions/workflows/ci.yml)

Deterministic EU AI Act first-pass classifier: works out which risk tier an AI system falls into and lists the obligations that follow, each with its article, application date and review status. Runs as a CLI, as MCP-style tools or in the browser; a lawyer confirms the result. Not legal advice; data is synthetic.

**[Try it in your browser](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/)**: no install, and nothing you paste leaves the page. The playground runs the same engine as the CLI.

[![Browser playground: CreditSightScore classified high-risk under Art. 6 AIA, with the cited provider obligations from Article 9 onwards](docs/playground.png)](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/)

> **If you don't code:** open the [playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) and pick one of the 18 synthetic examples, or scroll to [What the demo produces](#what-the-demo-produces). The point isn't the code; it's whether the legal work is structured, cited, reviewable, and testable.

See [CASE_STUDY.md](CASE_STUDY.md) for the problem, controls, and limitations. Launch readiness is tracked in [docs/launch-readiness.md](docs/launch-readiness.md).

## Run it

```bash
git clone https://github.com/sebastianfoerste/eu-ai-act-classifier
cd eu-ai-act-classifier
uv sync
uv run python -m src.eu_ai_act_classifier.cli examples/credit_scoring.json
```

Runs end to end, offline and deterministically.

## Browser playground

The [playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) runs the classifier client-side with Pyodide. Pick a synthetic example or paste a `SystemProfile`, classify it, then export the JSON or text report. A field guide lists every input field and its allowed values.

The page installs a wheel of this package, so it applies the same rules as the CLI. `tests/test_playground.py` fails if the wheel, the bundled examples or the field guide drift from the source. Rebuild after a rule change:

```bash
uv run python scripts/build_playground.py
```

## What the demo produces

The classifier runs a gates-based review over a system profile and outputs a report detailing the risk tier, binding timeline, regulatory sources, applicable obligations and review status. You can read the committed sample output in [`examples/classification-packet.md`](examples/classification-packet.md) and [`examples/classification-packet.json`](examples/classification-packet.json).

```markdown
EU AI Act classification: CreditSightScore
Risk tier: HIGH-RISK (Art. 6 AIA)
Disposition: DETERMINED
Scope status: in_scope
Roles: provider

Obligations:
  - Art. 9 AIA: Risk management system.
  - Art. 10 AIA: Data and data governance.
  - Art. 11 AIA: Technical documentation.
```

In the sample run, every tier and obligation is cited to an Article and carries an explicit review status.

![CLI sample output: CreditSightScore classified high-risk with Articles 9, 10 and 11 obligations](docs/demo.png)

## What it checks / does

| Gates / Steps | Focus | Verification Method |
|---|---|---|
| Scope and Intake | Alignment | Checks AI-system status, EU nexus, and transitional dates |
| Prohibited Practices | Art. 5 verification | Flags prohibited use cases |
| High-Risk & GPAI | Art. 6 / Annex III / GPAI | Classifies obligations based on deployment areas and compute scale |

## Local Verification

Use the CLI first. It is the authoritative product surface and does not require web dependencies:

```bash
uv run pytest
uv run eu-ai-act-classify examples/credit_scoring.json --strict
uv run eu-ai-act-classify examples/credit_scoring.json --sources
uv run eu-ai-act-classify examples/credit_scoring.json --artifact all --artifacts-dir /tmp/eu-ai-act-draft-pack
```

Then inspect `/tmp/eu-ai-act-draft-pack`. The generated files are draft review artifacts, not legal opinions, conformity assessments or filing documents.

## Source Statuses

Reports and draft artifacts use a versioned source manifest. The current binding layer includes Regulation (EU) 2024/1689 as consolidated on 27 July 2026 and Regulation (EU) 2026/1744. Any future provisional material and nonbinding guidance remain separately labelled. Guidance overlays are advisory notes and do not override the binding classification logic.

## MCP And Local API

For Claude Code or Claude Desktop, use [eu-reg-mcp](https://github.com/sebastianfoerste/eu-reg-mcp). It serves this classifier as an MCP tool next to its MiCAR tools, and `uvx` runs it without a clone:

```bash
uvx --from 'eu-reg-mcp[lint,classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp' eu-reg-mcp
```

To register it with Claude Code, put `claude mcp add eu-reg --` in front of that command. The Claude Desktop configuration is in the [MCP configuration guide](docs/mcp-configuration-guide.md).

This repository's own two-tool MCP server remains available as a secondary, local option. Its `[mcp]` extra pins `mcp>=1.2,<2`, because the server is built on `mcp.server.fastmcp`, which mcp 2.0 removed. Without a compatible `mcp`, the server exits with a message that names the pin and the eu-reg-mcp command.

```bash
uv run --extra mcp python -m eu_ai_act_classifier.mcp_server
```

The local JSON bridge is used by the optional web cockpit:

```bash
eu-ai-act-local-api schema
eu-ai-act-local-api inventory
echo '{"profile":{"name":"x"}}' | eu-ai-act-local-api classify
echo '{"profile":{"name":"x"}}' | eu-ai-act-local-api dossier
```

The bridge exposes schema, inventory, classify, sources, workspace, artifacts and dossier commands. It keeps the Python classifier as the legal source of truth.

`eu-ai-act-local-api workspace` and `/workspace` expose the same deterministic portfolio workspace: an AI-system vault, guided assessment workflows and a fleet command center. All deployment and external-use decisions remain review-gated.

The inventory payload includes a system review table with classifier-backed rows,
source status, open facts, obligations, draft artifacts and review state.
External action is blocked and all deployment, regulator, customer and
public-facing use remains review-gated.

## Optional Web Cockpit

![Web cockpit: a guided intake for CreditSightScore classified high-risk, with the system inventory, risk map, reviewer notes, source provenance, the Article 9-15 obligation tracker and a draft export pack](docs/cockpit.png)

The `web/` folder contains a local Next.js App Router cockpit with system inventory, guided questionnaire, risk map, open legal questions, reviewer notes, source provenance, obligation tracker and export pack preview.

The cockpit runs locally: `cd web && npm install && npm run dev`. Its API routes spawn the Python classifier from the repository root, so it is not hosted. The [browser playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) is the hosted surface, and the CLI remains the authoritative legal-rule surface.

Run it locally:

```bash
cd web
npm install
npm run dev
```

The web app uses in-memory state for v1. It does not persist client, matter, candidate, account or privileged data.

Deployment notes for the playground and the cockpit are in [DEPLOYMENT.md](DEPLOYMENT.md).

## Eval Set

`examples/` holds synthetic systems spanning prohibited, high-risk, limited risk, minimal risk, GPAI and review-required cases. The expected results are asserted in `tests/test_examples.py`.

## Known Legal Limits

- Guidance changes.
- National implementation and supervisory practice may vary by Member State.
- The engine applies rules to characterised facts and does not decide disputed intended purpose, operator role or factual deployment scope.
- `requires_review`, draft artifacts and advisory overlays must be reviewed before reliance.

## Stack

Python 3.13+, Pydantic v2, pytest, ruff and uv for the classifier. Pyodide and plain JavaScript for the browser playground. Next.js App Router and React for the optional local cockpit.

## Collaborative assessment workspace

The local `collaboration` bridge command and `/self-assessment` route add stable inventory review cells, optimistic locks, versioned classification and policy workflows, and a synthetic self-assessment portal. Mutable state exports as `review.collaboration.v1`; deterministic classifier results remain separate from reviewer overrides and blocked classifications remain deployment-blocking.

## Safety

This is a screening tool for supervised legal review. It does not produce legal advice, a conformity assessment or a binding regulatory conclusion. Generated work products require human legal review before use.

## Human-authored legal judgment

AI tools assisted the implementation, but the parts that carry the value are human-authored: the Annex/Article mappings, the obligation set, and the prohibited-practice and review-status logic. The point of this repository is not code volume; it is showing how legal judgment can be made structured, testable, and reviewable.

## Related

Part of a portfolio of deterministic, review-gated EU-regulation tools:

- [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter): MiCAR whitepaper linter with pinpoint citations, a browser playground and a CI action.
- [dpa-and-data-transfer-review](https://github.com/sebastianfoerste/dpa-and-data-transfer-review): GDPR Art. 28 and Chapter V transfer checks with a visible review state.

Curated index of EU financial-regulation primary sources and tools: [awesome-eu-fintech-regulation](https://github.com/sebastianfoerste/awesome-eu-fintech-regulation).
