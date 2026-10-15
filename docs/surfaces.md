# Surfaces and detail

Longer reference material moved out of the README. The CLI remains the authoritative product surface and the Python classifier is the legal source of truth for every other surface.

## Local verification

Use the CLI first. It does not require web dependencies:

```bash
uv run pytest
uv run eu-ai-act-classify examples/credit_scoring.json --strict
uv run eu-ai-act-classify examples/credit_scoring.json --sources
uv run eu-ai-act-classify examples/credit_scoring.json --artifact all --artifacts-dir /tmp/eu-ai-act-draft-pack
```

Then inspect `/tmp/eu-ai-act-draft-pack`. The generated files are draft review artifacts, not legal opinions, conformity assessments or filing documents.

## Source statuses

Reports and draft artifacts use a versioned source manifest. The current binding layer includes Regulation (EU) 2024/1689 as consolidated on 27 July 2026 and Regulation (EU) 2026/1744. The rules encode the amending regulation only in part; the [claim ledger](REGULATORY_CLAIM_LEDGER.md) lists what is and is not encoded. Any future provisional material and nonbinding guidance remain separately labelled. Guidance overlays are advisory notes and do not override the binding classification logic.

## Browser playground

The [playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) runs the classifier client-side with Pyodide. Pick a synthetic example or paste a `SystemProfile`, classify it, then export the JSON or text report. A field guide lists every input field and its allowed values.

The page installs a wheel of this package, so it applies the same rules as the CLI. `tests/test_playground.py` fails if the wheel, the bundled examples or the field guide drift from the source. Rebuild after a rule change:

```bash
uv run python scripts/build_playground.py
```

## MCP and local API

The MCP server ships in the [PyPI package](https://pypi.org/project/eu-ai-act-classifier/) behind the `[mcp]` extra. Install it and start the server:

```bash
pip install "eu-ai-act-classifier[mcp]" "mcp<2"
eu-ai-act-classifier-mcp
```

Or let uv fetch and run it: `uvx --from "eu-ai-act-classifier[mcp]" --with "mcp<2" eu-ai-act-classifier-mcp`. Client configuration (Claude Desktop, Cursor) and the reason for the `mcp<2` constraint are in [mcp-configuration-guide.md](mcp-configuration-guide.md).

The local JSON bridge is used by the optional web cockpit. Run it from the repository root, because `inventory` and `workspace` read the synthetic profiles in `examples/`:

```bash
eu-ai-act-local-api schema
eu-ai-act-local-api inventory
echo '{"profile":{"name":"x"}}' | eu-ai-act-local-api classify
echo '{"profile":{"name":"x"}}' | eu-ai-act-local-api dossier
```

The bridge exposes schema, inventory, classify, sources, workspace, artifacts and dossier commands. It keeps the Python classifier as the legal source of truth.

`eu-ai-act-local-api workspace` and `/workspace` expose the same deterministic portfolio workspace: an AI-system register, guided assessment workflows and a fleet command center. All deployment and external-use decisions remain review-gated.

The inventory payload includes a system review table with classifier-backed rows, source status, open facts, obligations, draft artifacts and review state. External action is blocked and all deployment, regulator, customer and public-facing use remains review-gated.

## Optional web cockpit

![Screenshot of the local web cockpit with the CreditSightScore sample: system inventory, guided intake, review panel showing determined with 0 open questions, reviewer notes, an obligation tracker with 16 graph items from Art. 16 AIA, source provenance and a draft export pack](cockpit.png)

*Screenshot of the local web cockpit (`web/`) with the CreditSightScore sample loaded.*

The `web/` folder contains a local Next.js App Router cockpit with system inventory, guided questionnaire, risk map, open legal questions, reviewer notes, source provenance, obligation tracker and export pack preview.

The cockpit runs locally. Its API routes spawn the Python classifier from the repository root, so it is not hosted:

```bash
cd web
npm install
npm run dev
```

The web app uses in-memory state for v1. It does not persist client, matter, candidate, account or privileged data.

Deployment notes for the playground and the cockpit are in [DEPLOYMENT.md](../DEPLOYMENT.md).

## Collaborative assessment workspace

The local `collaboration` bridge command and `/self-assessment` route add stable inventory review cells, optimistic locks, versioned classification and policy workflows, and a synthetic self-assessment portal. Mutable state exports as `review.collaboration.v1`; deterministic classifier results remain separate from reviewer overrides and blocked classifications remain deployment-blocking.

## Eval set

`examples/` holds synthetic systems spanning prohibited, high-risk, limited risk, minimal risk, GPAI and review-required cases. The expected results are asserted in `tests/test_examples.py`. See [examples/README.md](../examples/README.md).

## Stack

Python 3.13+, Pydantic v2, pytest, ruff and uv for the classifier. Pyodide and plain JavaScript for the browser playground. Next.js App Router and React for the optional local cockpit.
