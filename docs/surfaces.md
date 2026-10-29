# Surfaces and detail

Longer reference material moved out of the README. The CLI remains the authoritative product surface and the Python classifier is the legal source of truth for every other surface.

## Surfaces

| Surface | Use it for | Details |
|---|---|---|
| Browser playground | Zero-install trial, nothing leaves the page | [playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) |
| CLI (`eu-ai-act-classify`) | Authoritative surface; `--json`, `--strict`, `--sources`, draft artifacts | [Local verification](#local-verification) |
| MCP server | Let an agent call the classifier | [docs/mcp-configuration-guide.md](mcp-configuration-guide.md) |
| Local API and web cockpit | Local inventory, review and export workflow | [MCP and local API](#mcp-and-local-api), [Optional web cockpit](#optional-web-cockpit) |

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

Reports and draft artifacts use a versioned source manifest. The current binding layer includes Regulation (EU) 2024/1689 as consolidated on 27 July 2026 and Regulation (EU) 2026/1744. The rules encode the amending regulation only in part; the [claim ledger](REGULATORY_CLAIM_LEDGER.md) lists the amendments that are encoded and the limits of that encoding. Any future provisional material and nonbinding guidance remain separately labelled. Guidance overlays are advisory notes and do not override the binding classification logic.

## Browser playground

The [playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) runs the classifier client-side with Pyodide. It opens on guided questions: one question per page with the article under it, an "I don't know" answer where the fact may be open, and a check-answers page that also lists every value left at its default. "I don't know" never becomes "no": it records an unconfirmed value that routes the result to review, marks the Annex III point as unsettled, or pauses the run until counsel answers. The JSON editor stays available as a second mode: pick a synthetic example or paste a `SystemProfile`, classify it, then export the JSON or text report. A field guide lists every input field and its allowed values.

The questions, their order and when each is asked come from `src/eu_ai_act_classifier/intake.py`; the browser only interprets the generated `intake.json`. `tests/test_intake.py` checks that every example round-trips through the questions, that every "I don't know" either pauses the run or yields `requires_review`, and, over grids of states the intake can reach, that no answer to a skipped question changes the classification, apart from the engine's own note that a value given there is not used. Nonbinding advisory notes are outside that check for a profile outside the AI Act's scope. The Art. 111(2) significant-change question is asked only for a high-risk system with a date before its Chapter III date, the one case where the answer changes the result; there "I don't know" leaves the value open and the engine raises an Art. 111(2) open question. Elsewhere the engine reports a given answer as not used. The pinpoint shown under a question is always one the engine already cites; the intake adds no citation of its own.

"Create share link" puts the profile, compressed, in the address after the `#`. Browsers do not send that part to a server. Opening such a link loads the profile for checking and never classifies it on its own. The link is encoded, not encrypted, and browser history sync and chat services keep it, so share synthetic or public facts only. Profiles that would need more than 8,000 characters are refused; save the JSON instead.

The page installs a wheel of this package, so it applies the same rules as the CLI. `tests/test_playground.py` fails if the wheel, the bundled examples or the field guide drift from the source. Rebuild after a rule change:

```bash
uv run python scripts/build_playground.py
```

[![Browser playground: CreditSightScore classified high-risk under Art. 6 AIA, with the cited provider obligations from Article 9 onwards](playground.png)](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/)

## MCP and local API

The MCP server ships in the [PyPI package](https://pypi.org/project/eu-ai-act-classifier/) behind the `[mcp]` extra. Install it and start the server:

```bash
pip install "eu-ai-act-classifier[mcp]" "mcp<2"
eu-ai-act-classifier-mcp
```

Or let uv fetch and run it: `uvx --python 3.13 --from "eu-ai-act-classifier[mcp]" --with "mcp<2" eu-ai-act-classifier-mcp`. Client configuration (Claude Desktop, Cursor) and the reason for the `mcp<2` constraint are in [mcp-configuration-guide.md](mcp-configuration-guide.md).

Keep `mcp<2`: the server is built on the 1.x `mcp` SDK, and `mcp` 2.x renamed the API the server imports. The `[mcp]` extra pins `mcp<2` from 0.2.1; the 0.2.0 extra does not.

The local JSON bridge is used by the optional web cockpit. Run it from the repository root, because `inventory` and `workspace` read the synthetic profiles in `examples/`:

```bash
eu-ai-act-local-api schema
eu-ai-act-local-api inventory
echo '{"profile":{"name":"x"}}' | eu-ai-act-local-api classify
echo '{"profile":{"name":"x"}}' | eu-ai-act-local-api dossier
```

The bridge exposes schema, inventory, classify, sources, workspace, artifacts and dossier commands. It keeps the Python classifier as the legal source of truth.

`eu-ai-act-local-api workspace` and `/workspace` expose the same deterministic portfolio workspace: an AI-system inventory, guided assessment workflows and a fleet command center. All deployment and external-use decisions remain review-gated.

The inventory payload includes a system review table with classifier-backed rows, source status, open facts, obligations, draft artifacts and review state. External action is blocked and all deployment, regulator, customer and public-facing use remains review-gated.

## Optional web cockpit

![Full-page screenshot of the web cockpit in its single-column layout with the CreditSightScore sample: the sample inventory, a guided intake, the review panel (requires_review, high risk, one Art. 111(2) open question), reviewer notes, the AI systems inventory and system review tables, the obligation tracker with 17 graph items, source provenance and a draft export pack](cockpit.png)

*Full-page capture of the local web cockpit (`web/`, production build, 1180 px wide) with its CreditSightScore sample loaded, reduced to 256 colours; the steps are in [TESTING.md](TESTING.md#generated-files). The cockpit's sample gives a placing-on-market date of 2026-10-01 and `examples/credit_scoring.json` gives none, so only the cockpit raises the Art. 111(2) question.*

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
