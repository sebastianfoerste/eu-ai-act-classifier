# 0006 Evidence model

Status: Accepted

## Context

`ObligationGraphItem.evidence_artifact` is a string. Governance teams track evidence per obligation with a state, an owner and freshness. Peers model this with control states and time-to-live, or let an LLM judge evidence adequacy.

## Decision

Keep the binding report unchanged. Store evidence state in the cockpit's local workspace (`runtime-data/collaboration-workspace.json`): `not_started`, `in_progress`, `evidence_attached`, `reviewed` or `stale`, plus an owner and a reviewed-on date. No model judges evidence.

D1. Key. A record is keyed by the cockpit system, the obligation and the actor: `(system_id, obligation_id, obligation_actor)`. `system_id` is the id of a cockpit sample (`web/lib/samples.ts`, such as `credit-provider`), since the cockpit's Inventory panel is where a reviewer picks the system whose report the cockpit shows. The three parts are stored as separate fields and never parsed out of a display string. Patterns: `system_id` `^[a-z0-9][a-z0-9-]{0,63}$`, `obligation_id` `^[a-z0-9][a-z0-9._-]{0,79}$`, the actor a `Role`. The blank intake (`new`) has no stable identity, so it keeps no evidence: the cockpit disables the tracker and the bridge rejects it.

D2. Where things are computed. Python computes the report and item digests, the lanes, the retrieval dates and the stale reasons (`src/eu_ai_act_classifier/evidence_tracker.py`). The bridge classifies the profile the cockpit sent, the same cleaned profile it sent for the dossier. The browser only displays and posts: it reads no clock, never supplies a digest, and the bridge checks that the item exists in the report.

D3. Report digest. `report_digest` is the SHA-256 of `json.dumps(view, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`, where `view` is the report dumped as JSON without `advisory_notes`, `classifier_version` and `system`, and without `scope.assessment_date` and each graph item's `applies_on_assessment_date`. The advisory notes are non-binding and follow the overlay toggle; a version bump that changes no content changes nothing that matters; the system name is a display name and the key already names the system; the assessment-date fields are lane inputs. Where the assessment date changes substance (Art. 5(1)(ba) AIA from 2026-12-02), other fields change and so does the digest. Any change of the digest marks every saved item of that system stale ("the report it belongs to changes"). An item digest, the same canonical dump of one item without `applies_on_assessment_date`, is stored too and shows which rows changed themselves; it also catches a positional id such as `transparency.1` that now names another duty.

D4. Retrieval date. The `retrieved_on` of the report's `source_manifest` entry whose url is the item's `source_url`; failing that the `ai-act-2024-1689` entry, then the first entry. An empty manifest gives no date and no date reason. Not the latest date in the manifest, and not `sources/manifest.json`, which is not in the report.

D5. Stale rule. `stale` is derived and never stored; posting it answers HTTP 400. A missing record or a stored `not_started` is never stale. Any other record is stale for each of these reasons, listed in this order:

- `report_changed`: the stored report digest differs from the current one;
- `item_changed`: the stored item digest differs from the current one;
- `reviewed_before_source_retrieval`: the reviewed-on date is before the retrieval date. The same date is not stale.

Saving the row again stores the current digests. The date reason clears only with a reviewed-on date on or after the retrieval date. A save that stays stale is accepted, and the tracker says why. A `reviewed` record needs a reviewed-on date, which may not be after the bridge's current date.

D6. Lanes, in this order of precedence:

1. `applies_on_assessment_date` is true: applies now, even with a note, since the engine found it applies on every reading.
2. An `application_date_note`, or no `application_date`: contested or open.
3. `applies_on_assessment_date` is false: upcoming.
4. An assessment date is given and the application date is on or before it: applies now. A defensive fallback; the engine's output does not reach it today.
5. Otherwise upcoming.

D7. Assessment date. The cockpit's intake gains a control for the existing `SystemProfile.assessment_date`, empty by default, so nothing changes until it is set. Without it the engine leaves `applies_on_assessment_date` null and the tracker says that dated items without a note are listed as upcoming. The engine is unchanged.

D8. Persistence and migration. `CollaborationWorkspace` gains `evidence`, a list of records, under the same schema id `review.collaboration.v1`, and the inventory digest is untouched, so a file saved before the tracker loads with no evidence and is not archived. Duplicate keys make a file invalid. When a stored file goes stale for the inventory it is archived as before, and its evidence is carried into the new workspace, since the key does not depend on the examples; the `recovered` event then has `evidenceCarried`. An unreadable file carries nothing. An import whose file has an `evidence` key replaces the evidence; a file without one keeps it. A build from before the tracker ignores `evidence` and drops it on its next save, so export the workspace before going back to one.

D9. Export. The tracker downloads the bridge's view as JSON with `draftNotice` (`DRAFT_NOTICE`) as its first key. The collaboration snapshot carries `draftNotice`, and the self-assessment page's "Export local workspace" writes it first; an import ignores it. JSON only.

D10. Labels. The wording of states, lanes and stale reasons lives in the label catalog (`labels.py`, namespaces `evidence_state`, `evidence_lane` and `evidence_stale_reason`), which `scripts/build_playground.py` writes to `web/lib/labels.json`.

D11. Not in scope: locks on evidence rows (each row has a revision, and a stale one answers 409), a per-row history beyond the activity log, and a printed tracker. Two bridge processes saving different rows at the same moment can lose one write, since the whole file is written last, as for review cells. The cockpit disables the tracker while a save runs, which removes this within one tab; across tabs it remains.

## Consequences

- The overlay never changes the classification.
- Exports of the tracker carry `DRAFT_NOTICE`.
- Each classification in the cockpit runs a second bridge process for the tracker, in parallel with the dossier request.
