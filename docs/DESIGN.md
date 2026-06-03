# Design

## Goal

Turn the recurring question — *is this AI system high-risk under the EU AI Act,
and what does it owe?* — into a deterministic, cited, review-gated function that
a general counsel can run, drop into a pipeline, or expose to an agent.

## Data flow

```
SystemProfile (typed facts)
      │
      ▼
  prohibited → high_risk → gpai → transparency   (four gates, each pure)
      │
      ▼
   engine: resolve tier (max vote), attach obligations by tier + role
      │
      ▼
ClassificationReport ──► JSON (pipelines)  ──► render_report (humans)  ──► review gate
```

## Module boundaries

| Module | Responsibility | Depends on |
| --- | --- | --- |
| `models.py` | Typed input/output (Pydantic) and enums | pydantic |
| `citations.py` | Regulation reference, application dates, the `Citation` flag | — |
| `catalog.py` | The substantive mapping: areas, practices, obligation sets | models, citations |
| `rules/*.py` | One gate each; pure `evaluate(profile) -> GateOutput` | models, catalog |
| `engine.py` | Aggregate gate votes, attach obligations, assemble report | rules, catalog, citations |
| `report.py` | Human-readable rendering of a report | models |
| `cli.py` | File/stdin → report; `--json`, `--strict` | engine, report |
| `mcp_server.py` | Agent-callable tool surface (optional `mcp` extra) | engine, report |

Each unit answers: what does it do, how is it used, what does it depend on. The
substance (which use case maps to which Annex III point) is isolated in
`catalog.py` so a lawyer can audit it without reading the engine.

## Key decisions

- **Lawyer characterises, engine subsumes.** The `SystemProfile` carries
  characterised facts; the engine never infers them. Keeps output deterministic.
- **Gates vote; the engine resolves.** Tiers are not mutually exclusive in the
  law (a high-risk system can also owe Art. 50 transparency, and be built on a
  GPAI model). Gates emit votes and additive obligations; the engine takes the
  highest tier and stacks the rest.
- **The engine refuses to bluff.** Any determination resting on a fact the engine
  cannot settle returns `requires_review` with a named open question, rather than
  a confident-but-wrong tier.
- **Citations are first-class and falsifiable.** Every finding and obligation
  carries its article; unconfirmed pinpoints are flagged, not hidden.

## Testing

`tests/test_examples.py` runs the 14 example profiles as an eval set against
documented expectations — a rule change that moves any of them fails the build.
Per-gate unit tests cover the edges: prohibited dominance, the Art. 6(3)
derogation and its profiling carve-out, the GPAI systemic threshold and the
unknown-compute review path, transparency stacking on high-risk.

## Roadmap

- Add Level 2 delegated/implementing-act triggers (e.g. Art. 6(3) acts) as adopted.
- Expand Annex I sectoral product-safety mappings for the Art. 6(1) route.
- Optional Level 3 overlay (Commission guidelines) as a separate, clearly-labelled
  advisory layer — never merged into the Level 1 determination.
