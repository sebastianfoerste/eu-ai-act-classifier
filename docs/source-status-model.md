# Source Status Model

The classifier records source status as part of the product contract. A reviewer must be able to see whether an output is driven by binding text, provisional context, or nonbinding guidance.

## Status Categories

1. `binding_level_1`: Regulation (EU) 2024/1689 as encoded in the deterministic classification and obligation logic.
2. `provisional_political_agreement`: context tracked separately from binding classification logic until formal adoption and publication.
3. `nonbinding_guidance`: advisory material that may inform reviewer context without changing the classification result.

## Implementation Surfaces

1. `src/eu_ai_act_classifier/citations.py` defines source metadata.
2. `src/eu_ai_act_classifier/verify_sources.py` checks the source boundary.
3. `src/eu_ai_act_classifier/report.py` renders source material into reports.
4. `src/eu_ai_act_classifier/artifacts.py` carries source status into draft work products.

## Review Rules

1. Classification logic must stay tied to binding legal text and characterised facts.
2. Provisional dates and guidance overlays must be labelled.
3. Open legal questions and unverified citations must remain visible in reviewer outputs.
4. Draft artifacts must not claim to be legal advice, conformity assessments or filing documents.

## Validation

```bash
uv run pytest tests/test_required_dispositions.py tests/test_obligations_and_artifacts.py tests/test_local_api.py
```
