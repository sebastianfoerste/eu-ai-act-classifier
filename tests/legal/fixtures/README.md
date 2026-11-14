# Legal fixtures

Each file encodes one provision as cases written from the snapshotted source
text in [`sources/`](../../../sources/README.md). The cases come from pull
request #34, where they were written from the snapshots before the rule code,
and were adapted to the models on `main` when the rules were ported: the
GPAI model is dated by `gpai_model_placing_on_market_date`, a declared
`5.1.ba` or `5.1.bb` stands for the elements, and the interim screen question
replaces a separate "not screened" finding. Together the files cover the date
triads: assessment on 1, 2 and 3 December 2026 and 1, 2 and 3 August 2027,
placement on 1, 2 and 3 August 2025 and 2026, and unknown dates.

A case states the facts in plain language, the `SystemProfile` that expresses
them, and the result the source text requires. The ported and the new cases
were written before the port's first test run, and no expectation was changed
after one.

## File format

- `rule`: the provision under test, with pinpoint.
- `sources`: `source_id` from `sources/manifest.json` and the pinpoint read.
- `interpretations`: reading choices the text does not settle, keyed to the
  owner's answers C1 to C10 (docs/methodology.md). They are the reviewer's to
  confirm. A case that names one must find "interpretation" in a finding or
  open question of its report.
- `base_profile`: merged into every case's `profile` (nested objects merge key
  by key; `null` overrides).
- `cases[].matrix`: one of `applies`, `element_fails`, `unknown_input`,
  `boundary_before`, `boundary_on`, `boundary_after`, `conflict`,
  `invalid_input`, `irrelevant_input`.

## Expectation keys

| Key | Meaning |
| --- | --- |
| `risk_tier`, `disposition` | Exact value in the report |
| `findings` | Map of `rule_id` to severity; each must be present |
| `findings_absent` | `rule_id`s that must not appear |
| `finding_citations` | Map of `rule_id` to a substring of its citation |
| `open_question_contains` | Each substring must occur in some open question |
| `no_open_questions` | The report has no open question |
| `obligations_include`, `obligations_exclude` | Articles in obligations or documentation |
| `transparency_articles` | Exact list of transparency obligation articles |
| `graph` | Obligation-graph items matched by `article`; listed keys must be equal |
| `graph_absent_prefix` | No obligation-graph item id starts with these prefixes |
| `timeline_includes` | Timeline rows by `applies_from` and a substring of `provision` |
| `validation_error_loc` | The profile is rejected with an error at this location |
