# API Contracts

The Python classifier is the source of truth. The local API bridge and optional
web cockpit only expose deterministic projections for review.

## Local Commands

```bash
eu-ai-act-local-api schema
eu-ai-act-local-api inventory
echo '{"profile":{"name":"CreditSightScore"}}' | eu-ai-act-local-api classify
echo '{"profile":{"name":"CreditSightScore"}}' | eu-ai-act-local-api dossier
```

## Errors

`eu-ai-act-local-api` exits 2 with one JSON line, `{"error": "..."}`, on stderr
when it rejects the input. For a payload that fails validation the message is
the number of errors, each field path and each reason, without the rejected
value. Any other failure exits 1 with `{"error": "the classifier bridge
failed"}` and no traceback.

The cockpit routes answer 400 with local_api's message for rejected input, 409
for a stale revision or a lock held by another reviewer, and 400 with `request
body is not valid JSON` for a body that does not parse. Any other failure
answers 500 with `classifier bridge timed out` or `classifier bridge failed`.
No response carries stderr, a traceback or the request body.

## Inventory

`eu-ai-act-local-api inventory` and `GET /api/inventory` return
`eu-ai-act-classifier.system-inventory.v1`.

Important nested contracts:

1. `eu-ai-act-classifier.system-review-table.v1`
2. `eu-ai-act-classifier.review-control-profile.v1`
3. `eu-ai-act-classifier.system-review-table-scale.v1`
4. `eu-ai-act-classifier.system-prompt-brief.v1`
5. Review-gate metadata for draft artifacts and blocked external action state.

`externalActionAllowed` is always `false`. Regulator, customer, deployment and
public-facing outputs remain draft-only until qualified human review is
recorded.

## Review Boundary

The system review table may restate classifier output, source status and draft
artifact references. It must not add article-level conclusions beyond the
existing deterministic classifier result.

Review rows expose `cellStatus` for the factor-level review state. Pinpoint
citations expose source id, citation label, URL, verification flag, legal status
class, source class, quote snippet and optional offsets when the source
manifest supports them.
