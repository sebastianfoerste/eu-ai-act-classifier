# Review-workspace programme

The self-assessment workspace stores versioned local JSON under the ignored `runtime-data` directory. `/api/collaboration` supports snapshot, lock, comment, comment resolution, reviewer override, import and guided self-assessment actions. The browser surface supports local import and export.

The deterministic classifier result is immutable in each review cell. Reviewer overrides are separate fields. Workflow runs record the exact definition snapshot, classifier version, source versions, artifacts, decisions and audit events. Draft packets remain synthetic, local and human-review gated.

Run `uv run --isolated --extra dev ruff check .`, `uv run --isolated --extra dev ruff format --check .`, `uv run --isolated --extra dev pytest -q`, and `cd web && npm test && npm run build`.
