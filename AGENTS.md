# Agent Guide: EU AI Act Classifier

Welcome, AI Agent!

## Git and Branching Rules
- **NO Direct-to-Main/Master Merges**: You must **NEVER** autonomously merge feature branches (e.g., `feature/*`, `release/*`) directly into default branches (`main`, `master`, or `develop`).
- **NO Autonomously Pushing to Default Branches**: You must **NEVER** autonomously push commits directly to remote default branches (`origin/main`, `origin/master`, or `origin/develop`).
- **Always Ask / PR Flow**: All merges and pushes to default branches must either:
  - Be explicitly approved by the user in the current chat session.
  - Be submitted as a Pull Request (PR) for user review.
- **Pre-flight & Parity Gating**: Before proposing any merge or push, you must run all local validation checks (e.g., schema parity checks, test suites, database migration validations) on the feature branch first to ensure stability.
