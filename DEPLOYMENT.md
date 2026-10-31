# EU AI Act Classifier Deployment

The classifier has three surfaces:

- the Python CLI and local API bridge, which are the source of truth for legal-rule evaluation;
- the static browser playground in `docs/playground/`, which runs the same package client-side;
- the optional `web/` cockpit, which is a Next.js fixture demo that runs locally.

Hosted surface: the browser playground at https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/, served by GitHub Pages from `docs/` on `main` through the CI deployment below. It needs no server: the page loads Pyodide and Pydantic from the Pyodide CDN and installs the classifier wheel committed next to it. Profiles never leave the browser.

Publishing: the `deploy` job in `.github/workflows/ci.yml` uploads `docs/` and deploys it to GitHub Pages. It runs on a push to `main`, after the `test` and `web` jobs pass for that commit. Pull request runs skip it, and a failed check publishes nothing. The repository's Pages source must be GitHub Actions: with a branch as the source, GitHub also publishes `docs/` on every push to `main`, before CI finishes.

The cockpit is not hosted. Its API routes spawn the Python classifier, which a static or serverless host cannot execute, so the earlier Vercel build never returned a result. Run the cockpit locally.

## Playground

Rebuild after any change under `src/`, `examples/` or the `SystemProfile` fields:

```bash
uv run python scripts/build_playground.py
uv run pytest tests/test_playground.py
node --test tests/playground/*.test.mjs
```

The script regenerates `samples.json` and `fields.json` and replaces the wheel. `tests/test_playground.py` fails while any of them is stale. The `deploy` job publishes the result once CI passes on the next push to `main`.

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

`npm run dev` and `npm run start` listen on `127.0.0.1` only; open the cockpit at `http://127.0.0.1:3000` or `http://localhost:3000`. The POST routes accept a request only when its body is `application/json` (415 otherwise) and when it comes from the cockpit's own origin: `Host` and `Origin` must name `localhost` or `127.0.0.1` at the port the server listens on, and `Sec-Fetch-Site`, when sent, must be `same-origin` or `none` (403 otherwise). A web page on another site, or one that rebinds its DNS name to `127.0.0.1`, cannot write to the review workspace.

## Hosting the Cockpit

Do not deploy the cockpit to a host that cannot run the Python bridge. If you host it on one that can, keep it fixture-only. Before deploying:

1. Run `uv run pytest`.
2. Run `cd web && npm run build`.
3. Confirm the demo does not persist client, matter, candidate, account, or privileged data.
4. Confirm no external model API key is required.
5. Keep generated artifacts labelled as draft review material.

## Environment

See `web/.env.example`.

No secret is required for the default fixture cockpit. Do not add API keys or confidential data to hosting environment variables for a public demo.
