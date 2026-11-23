# Privacy Notes

## Data Processed

The classifier may process AI-system names, intended purpose, actor roles, deployment context, public-authority use, GPAI facts, risk triggers, source metadata and draft artifact content.

## Demo Boundary

The examples are synthetic system profiles. Use them for public demos. Do not paste client AI inventories, candidate-screening details, procurement records or confidential product roadmaps into the CLI or cockpit for screenshots.

## Local Cockpit

The cockpit runs the classifier through a local Python bridge. Classification, artifact and dossier requests keep no state. The collaboration workspace behind `/self-assessment` and the cockpit's Obligation Tracker is saved, with reviewer names, overrides and comments, and evidence states, owners and reviewed-on dates, to `runtime-data/collaboration-workspace.json` under the repository root. Next to it the bridge keeps an empty lock file, `runtime-data/collaboration-workspace.json.lock`, from the first time the workspace is opened, also when nothing has been saved; it holds no data and can be deleted with the folder. The workspace records who did what and when (activity entries, comments and cell locks carry the name and a time stamp). The file is git-ignored and stays on the machine until you delete it. When the bridge cannot use a stored file, it keeps it in `runtime-data/` under a name with `unreadable` or `stale` and the time; delete those copies too. Use synthetic data there too.

## Browser Storage

The playground and the cockpit store one value in the browser's local storage: the colour scheme chosen with the Theme button (`light` or `dark`). Choosing System removes it. No profile, answer or result is stored.

## Artifacts

Generated artifacts are draft review materials. They are not legal advice, conformity assessments, filing documents or regulatory approvals.

## Source Currency

The source manifest separates binding, provisional and advisory sources. Legal status and dates should be rechecked against primary sources before any real matter use.
