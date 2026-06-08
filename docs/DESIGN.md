# Design

## Goal

Turn EU AI Act intake into a deterministic, cited and review-gated function that
can be called from a CLI, MCP tool, local API route or optional web cockpit.

## Data Flow

```text
SystemProfile
  -> scope
  -> prohibited practices
  -> high-risk classification
  -> GPAI
  -> transparency
  -> engine resolution
  -> ClassificationReport
```

`ClassificationReport` is the stable output. It keeps the older lists for
compatibility and adds source manifest, scope assessment, obligation graph,
advisory notes and draft artifact support.

## Module Boundaries

`models.py` defines typed inputs, outputs and enums.

`citations.py` defines the source registry, binding application dates and
provisional political-agreement dates.

`catalog.py` maps legal duties and Annex III references to structured
obligations.

`rules/` contains pure gate modules.

`engine.py` aggregates gates, resolves tier, attaches obligations and builds the
report.

`obligation_graph.py` expands legal duties into review workflow items.

`artifacts.py` renders draft work products from the report.

`advisory.py` adds optional nonbinding guidance notes.

`guidance_eval.py` evaluates the Commission-derived guidance corpus.

`local_api.py` is the JSON bridge for the optional web cockpit.

`web/` contains the local Next.js App Router cockpit and route handlers.

## Product Surfaces

The CLI is the fastest deterministic interface and remains the regression
anchor.

The MCP server lets agents call the classifier without changing legal logic.

The local API bridge exposes schema, classify, sources and artifacts commands.

The Next.js cockpit gives reviewers an intake workspace with inventory,
questionnaire, risk map, open questions, notes, provenance, obligation tracker
and export preview.

## Key Decisions

The Python classifier remains the source of legal truth.

Guidance overlays are advisory only. They remain separate from Level 1 logic.

AI Omnibus dates are displayed separately from binding Art. 113 dates.

Draft work products always include a review notice and source manifest.

The web cockpit uses local in-memory state for v1.

## Testing

The base eval set has 14 synthetic examples. The guidance corpus adds
Commission-derived examples and stored beta Compliance Checker comparisons as
nonbinding review evidence.

Unit tests cover the scope gate, FRIA edge cases, obligation graph, artifact
generation, advisory overlay, local API bridge, docs integrity and compatibility
with the original examples.
