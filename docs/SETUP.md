# Setup: EU AI Act Classifier

## Prerequisites

1. Python 3.13 or newer.
2. `uv`.
3. Node.js and npm only when running the optional web cockpit.

## Python Package

Create the environment and install development dependencies:

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
