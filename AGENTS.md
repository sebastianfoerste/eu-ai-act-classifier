# Agent Guide: EU AI Act Classifier

Welcome, AI Agent!

## Git and Branching Rules
Do not merge feature branches into `main`, `master` or `develop`, and do not push to those remote branches, unless the user approved it in the current session or the change goes up as a pull request for review. These branches deploy; an unreviewed merge cannot be recalled.

## Checks Before Proposing a Merge or Push
Run on the feature branch what CI runs (`.github/workflows/ci.yml`):

```bash
uv sync --locked --extra dev --extra mcp
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=eu_ai_act_classifier --cov-report=term --cov-fail-under=94
for file in docs/playground/*.mjs; do node --check "$file"; done
node --test tests/playground/*.test.mjs
(cd web && npm ci && npm test && npm run build)
wc -w README.md   # at most 350 words; tests/test_docs.py enforces it
# The other CI jobs: the suite on Python 3.14 as well, the declared dependency floors,
# and the built wheel run from a clean environment.
uv run --isolated --python 3.14 --extra dev --extra mcp pytest
uv run --isolated --resolution lowest-direct --extra dev --extra mcp pytest   # must leave uv.lock unchanged
uv build && uv venv /tmp/smoke && uv pip install --python /tmp/smoke/bin/python dist/*.whl \
  && /tmp/smoke/bin/eu-ai-act-classify examples/spam_filter.json \
  && ! /tmp/smoke/bin/eu-ai-act-classify examples/social_scoring.json --strict   # exits 1
```

The coverage floor (`--cov-fail-under`) is the integer part of the measured total; raise it when coverage grows, never lower it to get green.

`uv run pytest` includes two parity checks on generated files. When one fails, regenerate the files; do not edit the test.

- Schema parity, `tests/test_schemas.py`: `uv run python scripts/build_schemas.py`.
- Playground parity, `tests/test_playground.py`: `uv run python scripts/build_playground.py`. Any change under `src/` needs it, because it rebuilds the committed playground wheel.
