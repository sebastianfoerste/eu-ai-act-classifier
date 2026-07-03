# Testing: EU AI Act Classifier

## Python Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Focused Source And Artifact Checks

```bash
uv run pytest tests/test_required_dispositions.py tests/test_obligations_and_artifacts.py tests/test_local_api.py
```

## CLI Smoke

```bash
uv run eu-ai-act-classify examples/credit_scoring.json --strict
uv run eu-ai-act-classify examples/credit_scoring.json --sources
```

## Artifact Smoke

```bash
uv run eu-ai-act-classify examples/credit_scoring.json --artifact all --artifacts-dir /tmp/eu-ai-act-draft-pack
```

## Optional Web Check

```bash
cd web
npm run build
```

## Quality Expectations

1. Binding text, provisional context and nonbinding guidance stay visibly separated.
2. `requires_review`, `open_questions` and `unverified_citations` remain visible.
3. Draft artifacts keep legal-review wording.
4. Tests use synthetic profiles only.
