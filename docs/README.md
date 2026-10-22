# Documentation index

Every guide in `docs/` and the main project files. The [README](../README.md) covers what the classifier is, install, the quick start and the MCP server; the [overview](overview.md) has the longer introduction.

## Start here

- [docs/overview.md](overview.md): who it's for, the playground, human-authored legal judgment, honest limits and the EU regulation as code suite
- [docs/SETUP.md](SETUP.md): the full quick start, JSON Schemas, development setup and the optional web cockpit
- [docs/sample-output.md](sample-output.md): CLI output for prohibited and high-risk examples, what a draft artifact contains, and GPAI JSON
- [docs/launch-readiness.md](launch-readiness.md): a quick route for evaluators

## Legal method and sources

- [docs/methodology.md](methodology.md): how Regulation (EU) 2024/1689 is encoded, including gate order and source versions; the legal audit surface
- [docs/REGULATORY_CLAIM_LEDGER.md](REGULATORY_CLAIM_LEDGER.md): the record of legal claims, including the amended high-risk application dates, each with its primary source, access date and review note
- [docs/source-status-model.md](source-status-model.md): binding text, provisional context and nonbinding guidance
- [docs/deterministic-classification-vs-legal-advice.md](deterministic-classification-vs-legal-advice.md): what the classifier does and does not do
- [docs/reviewer-notes.md](reviewer-notes.md): review triggers and the practical review rule
- [docs/coverage.md](coverage.md): Annex III coverage, generated from the code
- [docs/sample-review-dossier.md](sample-review-dossier.md): a sample review dossier from synthetic profiles

## Product and engineering

- [docs/FEATURES.md](FEATURES.md): what it checks, and the implementation and tests behind each feature
- [docs/surfaces.md](surfaces.md): every surface in detail, from the CLI to the web cockpit
- [docs/DESIGN.md](DESIGN.md): goal, data flow, module boundaries and key decisions
- [docs/mcp-configuration-guide.md](mcp-configuration-guide.md): MCP client configuration for Claude Desktop, Cursor and VS Code
- [docs/API.md](API.md): local API bridge contracts
- [docs/COLLABORATION_PROGRAMME.md](COLLABORATION_PROGRAMME.md): the review-workspace programme
- [docs/TESTING.md](TESTING.md): checks and smoke tests
- [docs/integrations/README.md](integrations/README.md): integration records
- [schemas/](../schemas/): JSON Schemas for the input profile and the report
- [examples/README.md](../examples/README.md): the synthetic eval set

## Research and decisions

- [docs/research/2026-10-competitive-landscape.md](research/2026-10-competitive-landscape.md): competitive research method, products, findings and sources
- [docs/research/feature-matrix.csv](research/feature-matrix.csv): capability matrix with an evidence tag per product
- [docs/research/design-teardown.md](research/design-teardown.md): interface patterns and a comparison per surface
- [docs/research/adaptation-plan.md](research/adaptation-plan.md): baseline, scored candidates, specs and open owner decisions
- [docs/adr/](adr/README.md): architecture decision records
- [CHANGELOG.md](../CHANGELOG.md): unreleased changes

## Docs and links

- [Playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) (hosted demo)
- [CASE_STUDY.md](../CASE_STUDY.md): problem, controls and limitations
- [docs/surfaces.md](surfaces.md): CLI verification, source statuses, MCP and local API, cockpit, collaboration workspace, eval set, stack
- [docs/methodology.md](methodology.md), [docs/DESIGN.md](DESIGN.md), [docs/launch-readiness.md](launch-readiness.md)
- [DEPLOYMENT.md](../DEPLOYMENT.md), [CONTRIBUTING.md](../CONTRIBUTING.md), [SECURITY.md](../SECURITY.md), [PRIVACY.md](../PRIVACY.md)
