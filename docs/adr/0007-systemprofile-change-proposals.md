# 0007 SystemProfile change proposals

Status: Proposed, needs owner decision

## Context

The guided intake never maps "I don't know" to false. Where a screen is a non-nullable boolean, it must block the run until counsel answers. Peers that let a run continue with unknown facts mark the result as open or conditional.

## Proposal

Make selected screens nullable, with the engine adding a review question when they are null: the Art. 5 practice screens as a separate "not yet screened" flag, `annex_i_safety_component`, `is_gpai_model`, and the Art. 50 screens. Decide whether a null `significant_change_after_application_date` should raise a review question.

## Consequences if accepted

- More guided runs reach a `requires_review` result instead of blocking.
- Schemas, the field guide, `web/lib/types.ts`, `web/lib/samples.ts` and the intake definition change; existing examples and goldens keep their outcomes because their values are set.
