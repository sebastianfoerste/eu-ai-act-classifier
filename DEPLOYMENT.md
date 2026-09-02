# EU AI Act Classifier Deployment

The classifier has two surfaces:

- the Python CLI and local API bridge, which are the source of truth for legal-rule evaluation;
- the optional `web/` cockpit, which is a Next.js fixture demo.

Hosted deployment: none working as of 2026-09-02. The earlier Vercel build at https://web-opal-chi-38.vercel.app cannot execute the Python classifier its API routes spawn and never returns a result; the repository homepage field has been cleared. Run the cockpit locally.

## Local Web Run

From the repository root:

```bash
uv sync
cd web
npm install
cp .env.example .env.local
npm run dev
```

The web app shells out to the Python bridge through `uv`. Keep `CLASSIFIER_REPO_ROOT` pointed at the repository root if the web app runs from another working directory.

## Vercel Notes

The hosted cockpit should stay fixture-only. Before deploying:

1. Run `uv run pytest`.
2. Run `cd web && npm run build`.
3. Confirm the demo does not persist client, matter, candidate, account, or privileged data.
4. Confirm no external model API key is required.
5. Keep generated artifacts labelled as draft review material.

## Environment

See `web/.env.example`.

No secret is required for the default fixture cockpit. Do not add API keys or confidential data to Vercel environment variables for the public demo.
