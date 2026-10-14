# Legal fixtures

Each file encodes one provision as cases written from the snapshotted source
text in [`sources/`](../../../sources/README.md), before the rule code was
changed. A case states the facts in plain language, the `SystemProfile` that
expresses them, and the result the source text requires.

## File format

- `rule`: the provision under test, with pinpoint.
- `sources`: `source_id` from `sources/manifest.json` and the pinpoint read.
- `interpretations`: reading choices the text does not settle. They are the
  reviewer's to confirm and are labelled `interpretation` in the engine output.
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
