# Codex Worldclass Implementation Prompt

You are Codex working in the repository: /Users/sebastian/Developer/eu-ai-act-classifier

The app is a deterministic EU AI Act classifier with a Python CLI, MCP surface, local JSON bridge and optional Next.js cockpit.

Current problems: the CLI is strong, but the product story needs better sample packs, source-update proof, cockpit screenshots, and tighter bridge reliability. The target state is a reviewer-credible AI governance tool that shows source status, open questions and draft-only artifacts without suggesting autonomous legal conclusions.

Inspect first:
- `README.md`
- `pyproject.toml`
- `src/eu_ai_act_classifier/`
- `tests/`
- `examples/`
- `web/app/`, `web/components/`, `web/lib/`
- `docs/WORLDCLASS_PRODUCT_PLAN.md`

Implement focused improvements:
- Add or refresh a sample review dossier using synthetic examples only.
- Add tests for any new bridge, source or artifact behavior.
- Improve cockpit copy only where it clarifies review state, loading, errors or source provenance.
- Add documentation for source-update and artifact-review workflow.

Do not change:
- Core legal classification logic unless tests prove a defect.
- Source dates or legal status labels without verifying current primary sources.
- Any review-gated safety wording.
- Any external sending, hosting, persistence or telemetry behavior.

Run checks:
- `uv run pytest`
- `cd web && npm run build`

Update documentation:
- `README.md`
- `docs/TESTING.md` if commands change
- any sample-output docs you add

Final report:
- Summarize exact files changed.
- State tests and build results.
- State remaining legal/source currency risks.
- Do not invent legal claims, client names, credentials, benchmarks or regulatory conclusions.
