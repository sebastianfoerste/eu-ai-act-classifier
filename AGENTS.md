# Agent Guide: EU AI Act Classifier

Welcome, AI Agent!

## Git and Branching Rules
Do not merge feature branches into `main`, `master` or `develop`, and do not push to those remote branches, unless the user approved it in the current session or the change goes up as a pull request for review. These branches deploy; an unreviewed merge cannot be recalled.

Before proposing a merge or push, run the local validation checks on the feature branch: schema parity, the test suite, and database migration validation.
