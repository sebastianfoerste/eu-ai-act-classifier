# Demo Asset Plan

## Screenshots Needed

1. CLI output for `examples/credit_scoring.json --strict`.
2. Source manifest output showing binding, provisional and advisory status separation.
3. Cockpit risk map with open legal questions visible.
4. Artifact preview showing draft-only review status.

## Synthetic Input

Use `examples/credit_scoring.json`, `examples/cv_screening.json` and one GPAI example from the existing synthetic fixtures.

## Output To Show

Show classification tier, disposition, obligation graph, source manifest, open legal questions and draft artifact list.

## Material To Exclude

Do not show real AI-system inventories, candidate data, employee data, procurement details, customer deployments or confidential model documentation.

## 60 Second Demo

1. Run `uv run eu-ai-act-classify examples/credit_scoring.json --strict`.
2. Run the same profile with `--sources`.
3. Generate a draft artifact pack into `/tmp`.
4. Open the cockpit and show the same result.
5. Point to binding, provisional and advisory source separation.

## Buyer Or Recruiter Takeaway

The app demonstrates typed regulatory triage, source status discipline, artifact generation and explicit human review boundaries.

## Hosting Readiness

CLI and local cockpit demo ready. Hosted demo should use only synthetic profiles and should not imply current legal-source verification without a source-refresh routine.
