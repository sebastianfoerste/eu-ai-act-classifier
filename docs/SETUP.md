# Setup: EU AI Act Classifier

## Prerequisites

1. Python 3.13 or newer.
2. `uv`.
3. Node.js and npm only when running the optional web cockpit.

## Quick Start

The package is on PyPI as [`eu-ai-act-classifier`](https://pypi.org/project/eu-ai-act-classifier/) (Python 3.13+). With [uv](https://docs.astral.sh/uv/), `uvx` fetches it from PyPI and runs it without installing it. Save a profile and classify it:

```bash
cat > profile.json <<'JSON'
{
  "name": "CitizenScore",
  "description": "Scores individuals on social behaviour to gate access to services.",
  "roles": ["provider"],
  "purpose": "Social scoring",
  "sector": "GovTech",
  "prohibited_practices": ["5.1.c"]
}
JSON
uvx --from eu-ai-act-classifier eu-ai-act-classify profile.json
```

Or install it with pip:

```bash
pip install eu-ai-act-classifier
eu-ai-act-classify profile.json
```

To try changes on `main` that are not on PyPI yet, point uvx at the repository instead: `uvx --from git+https://github.com/sebastianfoerste/eu-ai-act-classifier eu-ai-act-classify profile.json`. To develop, work from a clone:

```bash
git clone https://github.com/sebastianfoerste/eu-ai-act-classifier
cd eu-ai-act-classifier
uv sync --extra dev
uv run eu-ai-act-classify examples/credit_scoring.json
```

Runs end to end, offline and deterministically. [Example output](sample-output.md#example-output) shows the output, and [Local verification](surfaces.md#local-verification) has more commands, starting with the test suite.

JSON Schemas for the input profile and the report are in [schemas/](../schemas/) (also `eu-ai-act-classify --schema profile` or `--schema report`). Add `"$schema": "https://raw.githubusercontent.com/sebastianfoerste/eu-ai-act-classifier/main/schemas/system-profile.v1.schema.json"` to a profile for editor autocomplete; the classifier ignores that key. The flag and the key need 0.2.2 or later: 0.2.1 rejects both.

## Python Package

The package is on [PyPI](https://pypi.org/project/eu-ai-act-classifier/). To use the CLI without a clone:

```bash
pip install eu-ai-act-classifier
eu-ai-act-classify --help
```

For development, create the environment in a clone and install development dependencies:

```bash
uv venv
uv pip install -e ".[dev]"
```

Run the CLI against a synthetic profile:

```bash
uv run eu-ai-act-classify examples/credit_scoring.json --strict
```

Generate draft artifacts into a local directory:

```bash
uv run eu-ai-act-classify examples/credit_scoring.json --artifact all --artifacts-dir ./draft-artifacts
```

## Optional Web Cockpit

```bash
cd web
npm install
npm run dev
```

The cockpit calls the local Python bridge. It does not persist client, matter, candidate, account or privileged data.

## Data Boundary

Use synthetic AI-system profiles only unless Sebastian explicitly approves another local dataset. Treat draft artifacts as review materials, not final legal advice, conformity assessments or regulatory filings.
