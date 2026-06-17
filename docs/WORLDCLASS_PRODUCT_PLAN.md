# Worldclass Product Plan

## App Summary
EU AI Act Classifier is a deterministic Python classifier, CLI, MCP tool and local cockpit for first-pass EU AI Act risk routing.

## Ideal Target User
AI governance teams, legal engineers, product counsel and compliance reviewers who need source-visible triage before legal review.

## Main Competitor Set
Harvey, Legora, Thomson Reuters CoCounsel, Lexis+ AI, generic ChatGPT workflows and internal GRC spreadsheets.

## Product Positioning
Rules-first AI Act intake that keeps binding law, provisional timelines and nonbinding guidance separate.

## One Sentence Value Proposition
Classify AI-system facts into a reviewable EU AI Act route with citations, open questions and draft-only compliance artifacts.

## Three Sentence Homepage Pitch
Turn AI-system intake facts into a cited review packet. The classifier separates binding sources from advisory guidance and shows where facts still need legal judgment. Use the CLI for auditability and the local cockpit for reviewer-friendly exploration.

## Best Possible Demo Flow
Run `uv run pytest`, classify `examples/credit_scoring.json`, emit `--sources`, generate `--artifact all`, then open the cockpit and show the same result with reviewer notes and source provenance.

## UX Weaknesses
The cockpit is useful but dense. The strongest flow is still CLI-first, and the web UI needs clearer state transitions, artifact empty states and error recovery.

## Technical Weaknesses
The web bridge shells into Python and should eventually expose a more robust local service contract. The source set must be kept current by a documented update routine.

## Security Weaknesses
No persistence is a strength for demos. Future persistence needs explicit data classification, retention controls and local-only defaults.

## Documentation Weaknesses
The README now covers the core path, but screenshots, a generated sample artifact pack and a source-update runbook would increase trust.

## Immediate Fixes
Keep the cockpit loading and error states visible. Add tests for source manifest and artifact bridge behavior. Show the draft-only review boundary in every generated artifact surface.

## Seven Day Improvement Plan
Add a screenshot set, create a sample artifact bundle under docs or examples, add a source-update checklist and add a compact architecture diagram.

## Thirty Day Improvement Plan
Add a source freshness command, version source manifests, add golden output snapshots for artifacts and expose a typed local API server for the cockpit.

## Ninety Day Improvement Plan
Add organization-specific intake templates, policy-profile overlays, offline source bundles and a hosted public demo using only synthetic profiles.

## Killer Feature Proposal
One-click EU AI Act review dossier: classification report, obligation graph, source manifest, open questions and draft artifacts in one signed local bundle.

## Commercialization Angle
Open-source core with paid implementation workshops, governance intake customization and internal reviewer workflow integration for regulated companies.

## GitHub README Improvement Plan
Keep CLI commands first, show generated artifact examples, add screenshots and state source currency clearly.

## Portfolio Storytelling Angle
This is Sebastian Förste as a German-qualified lawyer translating EU AI Act obligations into typed, testable, review-gated software.
