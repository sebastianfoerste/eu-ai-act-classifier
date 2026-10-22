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

## Generated Files

```bash
uv run python scripts/build_schemas.py      # schemas/*.json
uv run python scripts/build_playground.py   # playground samples, field guide and wheel
uv run python scripts/build_coverage.py     # docs/coverage.md
uv run eu-ai-act-classify examples/credit_scoring.json --json > examples/classification-packet.json
uv run eu-ai-act-classify examples/credit_scoring.json > examples/classification-packet.md
uv run python scripts/render_demo.py        # docs/demo.png, needs headless Chrome
```

`docs/cockpit.png` is a full-page capture of the production build, taken
headlessly at 1180 px wide. That is the single-column layout: in the wider
layouts the obligation tracker's table scrolls sideways, so a capture cuts off
its Status column and notes.

```bash
cd web && npm ci && CLASSIFIER_REPO_ROOT=.. npx next build
CLASSIFIER_REPO_ROOT=.. timeout 600 npx next start -p 3917 &
SERVER=$!
timeout 120 google-chrome --headless=new --no-sandbox --force-device-scale-factor=1 \
  --virtual-time-budget=20000 --window-size=1180,16000 --screenshot=../docs/cockpit.png http://127.0.0.1:3917/
kill "$SERVER"
```

The scroll bars stay visible, so the roles, Art. 5 and source lists show that
they scroll rather than looking cut off. Crop the empty space below the page to
a 24 px margin, then reduce the image to 256 colours (for example with Pillow:
`quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)`,
saved with `optimize=True`), which keeps it near 0.65 MB instead of 1.9 MB.

## Quality Expectations

1. Binding text, provisional context and nonbinding guidance stay visibly separated.
2. `requires_review`, `open_questions` and `unverified_citations` remain visible.
3. Draft artifacts keep legal-review wording.
4. Tests use synthetic profiles only.
