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
for a stale revision (of a review cell or an obligation tracker row) or a lock
held by another reviewer, and 400 with `request
body is not valid JSON` for a body that does not parse. Any other failure
answers 500 with `classifier bridge timed out` or `classifier bridge failed`.
No response carries stderr, a traceback or the request body.

## Obligation tracker

The cockpit's Obligation Tracker posts two actions to `POST /api/collaboration`
(`eu-ai-act-local-api collaboration`). Both carry `systemId`, the id of a cockpit
sample such as `credit-provider` (not `new`), and `profile`, the profile the
cockpit classified. The bridge classifies that profile without the advisory
overlay and answers with the tracker view, not the workspace snapshot.

- `{"action": "evidence_view", "systemId": ..., "profile": {...}}` returns the
  view and is read-only: it saves nothing and never sets a stored file aside.
  An unreadable or stale workspace file reads as no saved evidence. The
  cockpit posts it on each classification.
- `{"action": "evidence", "systemId": ..., "profile": {...}, "obligationId":
  ..., "obligationActor": "provider", "state": "in_progress", "owner": "Owner
  A", "reviewedOn": null, "expectedRevision": 0, "actor": "Local reviewer"}`
  saves one item's record and returns the view. `state` is `not_started`,
  `in_progress`, `evidence_attached` or `reviewed`; `reviewed` needs
  `reviewedOn` (YYYY-MM-DD). In every state a `reviewedOn` may not be after
  the bridge's local calendar date. `owner` holds at most
  120 characters. `expectedRevision` is the row's `revision` (0 before the
  first save).

The view, `cockpit.obligation-evidence.v1`, starts with `draftNotice`, then
`schema`, `systemId`, `system`, `classifierVersion`, `assessmentDate`,
`reportDigest`, `counts` per state, `lanes` (`applies_now`, `upcoming`,
`no_assessment_date`, `contested_or_open`, in that order, each with its items
in the engine's order)
and `orphanedRecords` (saved records whose item is no longer in the report).
Each item carries the graph item's article, actor, evidence artifact, dates and
review status, `sourceRetrievedOn`, `state`, `storedState`, `staleReasons`,
`owner`, `reviewedOn`, `revision`, `updatedBy` and `updatedAt`.

`stale` is derived, never stored: a saved record other than `not_started` is
stale when the report digest or the item digest differs from the saved one, or
when `reviewedOn` is before the retrieval date of the item's source in the
report's source manifest. [ADR 0006](adr/0006-evidence-model.md) defines the
digests and the lane precedence. Posting `stale`, an unknown item, a bad id or
a bad date answers 400; a stale `expectedRevision` answers 409 (`409 Conflict:
stale evidence revision`). The bridge holds a file lock from the load through
the save, so of two saves of one row from the same revision, across processes
too, one is saved and the other answers 409.

Lanes are placed against the assessment date, not against today:
`applies_now` applies on the assessment date, `upcoming` applies after it,
`no_assessment_date` holds dated items while no assessment date is set, and
`contested_or_open` holds items with a date note or no date. With a date the
engine says, where every reading agrees, whether an item applies on it; items
whose date is contested stay in Contested or open.

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
