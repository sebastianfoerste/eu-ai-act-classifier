# Testing: EU AI Act Classifier

## Python Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=eu_ai_act_classifier --cov-report=term --cov-fail-under=96
```

CI also runs the suite on Python 3.14, at the lowest declared dependency versions
(`uv run --isolated --resolution lowest-direct --extra dev --extra mcp pytest`) and
from the built wheel installed into a clean environment (`uv build`, then the CLI on
`examples/spam_filter.json` and, expecting exit 1, `examples/social_scoring.json --strict`).

## Focused Source And Artifact Checks

```bash
uv run pytest tests/test_required_dispositions.py tests/test_obligations_and_artifacts.py tests/test_local_api.py
uv run pytest tests/legal   # fixtures written from the snapshots in sources/
```

The legal fixtures in `tests/legal/fixtures/` state each case's facts, the
`SystemProfile` that expresses them and the result the cited source text
requires (format in `tests/legal/fixtures/README.md`). A failure there means the
engine and the source-derived expectation disagree: check the fixture against
the snapshot before changing either.

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
npm test
npm run build
```

## Obligation Tracker

The tracker's rules are tested where they are computed, in Python:

- `tests/test_evidence_tracker.py`: the report and item digests (pinned
  algorithm, what they ignore and what changes them, the Art. 5(1)(ba) date
  prose that moves the digest only where the outcome changes), the lane
  precedence over every example, seven assessment dates and none (the
  `no_assessment_date` lane), the retrieval date per item, the
  stale reasons matrix, the view's shape and order, and record validation.
- `tests/test_collaboration_workspace.py`: saving with revisions and conflicts,
  two concurrent saves of one row under the file lock, rejected input leaving
  the file unchanged, the reviewed-on date checked against the bridge's local
  date, the stale reasons after a profile change, an assessment date that
  stales nothing, a read-only `evidence_view` on an unreadable or stale file, a
  pre-tracker file, evidence carried through a stale-workspace recovery, and
  import with and without an `evidence` key.
- `tests/test_local_api.py`: the round trip, the 409 and a rejected `stale`
  through the bridge's exit codes.

On the web side, `web/lib/evidence.test.ts` covers the payloads, row names and
export, and checks that `evidence.ts` and `obligation-tracker.tsx` contain no
date logic; `web/components/obligation-tracker.test.tsx` renders the tracker
(lanes, columns, accessible names, the stale row, the disabled state, orphaned
records, the fallback table) and checks the cockpit wiring in its source; the
collaboration route test covers the evidence actions' 200, 400, 403, 409 and
415 answers.

A change to `labels.py` or anything else under `src/` needs
`uv run python scripts/build_playground.py`, which rewrites
`web/lib/labels.json` and the playground wheel.

Accessibility runs with axe-core from a scratch directory outside the
repository (Playwright with `@axe-core/playwright`, or the browser extension),
so no dependency is added: at 1280 and 375 px, each in light and dark, with the
`wcag2a` and `wcag2aa` tags, on the tracker with a stale row, a saved row, the
blank intake, an error message and the orphaned records open. Expect no
violations. By hand: every control has a unique name, the lane headings appear
in the heading outline, the state pills carry text, Tab reaches each scroll
region and row control with a visible focus, the page does not scroll sideways
at 375 px, and the date and state controls work from the keyboard.

## Generated Files

```bash
uv run python scripts/build_schemas.py      # schemas/*.json
uv run python scripts/build_playground.py   # playground samples, field guide and wheel
uv run python scripts/build_coverage.py     # docs/coverage.md
uv run eu-ai-act-classify examples/credit_scoring.json --json > examples/classification-packet.json
uv run eu-ai-act-classify examples/credit_scoring.json > examples/classification-packet.md
uv run python scripts/render_demo.py        # docs/demo.png, needs headless Chrome
uv run python tests/test_golden_json.py     # tests/goldens/, one report per example
```

`docs/cockpit.png` is a full-page capture of the production build, taken
headlessly at 1180 px wide. That is the single-column layout: in the wider
layouts the obligation tracker's table scrolls sideways, so a capture cuts off
its Status column and notes.

```bash
cd web && npm ci && CLASSIFIER_REPO_ROOT=.. npx next build
CLASSIFIER_REPO_ROOT=.. timeout 600 npx next start -H 127.0.0.1 -p 3917 &
SERVER=$!
timeout 120 google-chrome --headless=new --no-sandbox --force-device-scale-factor=1 \
  --virtual-time-budget=20000 --window-size=1180,18000 --screenshot=../docs/cockpit.png http://127.0.0.1:3917/
kill "$SERVER"
```

The scroll bars stay visible, so the roles, Art. 5 and source lists show that
they scroll rather than looking cut off. Crop the empty space below the page to
a 24 px margin, then reduce the image to 256 colours (for example with Pillow:
`quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)`,
saved with `optimize=True`), which keeps it near 1 MB instead of 3 MB.

## Quality Expectations

1. Binding text, provisional context and nonbinding guidance stay visibly separated.
2. `requires_review`, `open_questions` and `unverified_citations` remain visible.
3. Draft artifacts keep legal-review wording.
4. Tests use synthetic profiles only.
