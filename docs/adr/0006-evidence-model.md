# 0006 Evidence model

Status: Proposed

## Context

`ObligationGraphItem.evidence_artifact` is a string. Governance teams track evidence per obligation with a state, an owner and freshness. Peers model this with control states and time-to-live, or let an LLM judge evidence adequacy.

## Decision

Keep the binding report unchanged. Store evidence state in the cockpit's local workspace keyed by `obligation_id`: `not_started`, `in_progress`, `evidence_attached`, `reviewed` or `stale`, plus an owner and a reviewed-on date. An item becomes `stale` when the report it belongs to changes or its reviewed-on date is older than the source manifest's retrieval date. Lanes (applies now, upcoming, contested) derive from `application_date` and `application_date_note`. No model judges evidence.

## Consequences

- The overlay never changes the classification.
- Exports of the tracker carry `DRAFT_NOTICE`.
