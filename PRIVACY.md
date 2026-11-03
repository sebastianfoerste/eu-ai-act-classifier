# Privacy Notes

## Data Processed

The classifier may process AI-system names, intended purpose, actor roles, deployment context, public-authority use, GPAI facts, risk triggers, source metadata and draft artifact content.

## Demo Boundary

The examples are synthetic system profiles. Use them for public demos. Do not paste client AI inventories, candidate-screening details, procurement records or confidential product roadmaps into the CLI or cockpit for screenshots.

## Local Cockpit

The cockpit runs the classifier through a local Python bridge. Classification, artifact and dossier requests keep no state. The collaboration workspace behind `/self-assessment` is saved, with reviewer names, overrides and comments, to `runtime-data/collaboration-workspace.json` under the repository root. The file is git-ignored and stays on the machine until you delete it. When the bridge cannot use a stored file, it keeps it in `runtime-data/` under a name with `unreadable` or `stale` and the time; delete those copies too. Use synthetic data there too.

## Artifacts

Generated artifacts are draft review materials. They are not legal advice, conformity assessments, filing documents or regulatory approvals.

## Source Currency

The source manifest separates binding, provisional and advisory sources. Legal status and dates should be rechecked against primary sources before any real matter use.
