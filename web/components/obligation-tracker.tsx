"use client";

import { Download, FileText } from "lucide-react";
import { Fragment, useEffect, useId, useRef, useState } from "react";
import {
  EVIDENCE_STATES,
  SETTABLE_STATES,
  draftFor,
  evidenceKey,
  evidenceTone,
  focusAfterSave,
  rowNames,
  shownLanes,
  type EvidenceDraft,
  type EvidenceRowFeedback,
  type EvidenceView,
  type EvidenceViewItem,
  type SettableEvidenceState,
} from "../lib/evidence";
import { labelFor } from "../lib/labels";
import type { ClassificationReport } from "../lib/types";

const COLUMNS = [
  "Article",
  "Actor",
  "Evidence artifact",
  "Due",
  "Status",
  "Evidence state",
  "Owner",
  "Reviewed on",
  "Save",
];

export function StatusPill({ label, tone }: { label: string; tone: string }) {
  return <span className={`statusPill ${tone}`}>{label}</span>;
}

export type ObligationTrackerProps = {
  report: ClassificationReport | null;
  view: EvidenceView | null;
  disabled: boolean;
  /** The tracker-wide status (a load failure, the blank intake), shown above the lanes. */
  message: string;
  /** Each row's last save outcome, by evidenceKey; shown in that row. */
  feedback: Record<string, EvidenceRowFeedback>;
  /** Resolves to the row's outcome, or null when a newer classification took over. */
  onSave: (item: EvidenceViewItem, draft: EvidenceDraft) => Promise<EvidenceRowFeedback | null>;
  onExport: () => void;
};

/**
 * The obligation tracker (ADR 0006): one table per lane, each row with its evidence
 * state, owner and reviewed-on date. Lanes, staleness and its reasons come from the
 * bridge. Without a tracker view (loading, the blank intake, or a bridge failure) the
 * report's obligation graph still shows, read-only. A save's outcome shows in its row.
 */
export function ObligationTracker({ report, view, disabled, message, feedback, onSave, onExport }: ObligationTrackerProps) {
  const items = view ? view.lanes.flatMap((lane) => lane.items) : [];
  const names = rowNames(items, (actor) => labelFor("roles", actor));
  const graphItems = view ? items.length : (report?.obligation_graph.length ?? 0);
  return (
    <section className="panel trackerPanel evidenceTrackerPanel" aria-labelledby="tracker-heading">
      <div className="panelHeader">
        <div>
          <h2 id="tracker-heading">Obligation Tracker</h2>
          <p>
            {graphItems} graph items
            {view
              ? `: ${EVIDENCE_STATES.map((state) => `${labelFor("evidence_state", state)} ${view.counts[state] ?? 0}`).join(", ")}`
              : ""}
          </p>
        </div>
        <div className="toolbar">
          <button
            className="iconButton"
            type="button"
            title="Download obligation evidence tracker"
            aria-label="Download obligation evidence tracker"
            disabled={!view || disabled}
            onClick={onExport}
          >
            <Download size={18} aria-hidden />
          </button>
          <FileText size={18} aria-hidden />
        </div>
      </div>
      <p className="meta" role="status" aria-live="polite">
        {message}
      </p>
      {view ? (
        <>
          <p className="meta">
            {view.assessmentDate ? `Assessment date ${view.assessmentDate}.` : "No assessment date set."} Lanes are
            placed against the assessment date; while none is set, dated items wait under &ldquo;
            {labelFor("evidence_lane", "no_assessment_date")}&rdquo;.
          </p>
          {shownLanes(view).map((lane) => {
            const laneId = `tracker-lane-${lane.lane}`;
            return (
              <section className="laneSection" key={lane.lane} aria-labelledby={laneId}>
                <h3 id={laneId}>
                  {labelFor("evidence_lane", lane.lane)} ({lane.items.length})
                </h3>
                <div className="tableWrap" role="group" tabIndex={0} aria-labelledby={laneId}>
                  <table>
                    <thead>
                      <tr>
                        {COLUMNS.map((column) => (
                          <th key={column} scope="col">
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {lane.items.length ? (
                        lane.items.map((item) => (
                          <EvidenceRow
                            key={evidenceKey(item)}
                            item={item}
                            name={names.get(evidenceKey(item)) ?? item.article}
                            disabled={disabled}
                            feedback={feedback[evidenceKey(item)] ?? null}
                            onSave={onSave}
                          />
                        ))
                      ) : (
                        <tr>
                          <td colSpan={COLUMNS.length}>No items in this lane.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            );
          })}
          {view.orphanedRecords.length ? (
            <details className="orphanedEvidence">
              <summary>Saved evidence for items not in this report ({view.orphanedRecords.length})</summary>
              <ul className="plainList">
                {view.orphanedRecords.map((record) => (
                  <li key={`${record.obligationId}|${record.obligationActor}`}>
                    {record.obligationId}, {labelFor("roles", record.obligationActor)}:{" "}
                    {labelFor("evidence_state", record.state)}
                    {record.owner ? `, owner ${record.owner}` : ""}
                    {record.reviewedOn ? `, reviewed on ${record.reviewedOn}` : ""}, revision {record.revision}
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </>
      ) : (
        <GraphTable report={report} />
      )}
    </section>
  );
}

/**
 * One tracker row. It is keyed by evidenceKey alone, so a save keeps the row mounted
 * and its Save button focusable; the draft resets when the saved revision changes.
 */
function EvidenceRow({
  item,
  name,
  disabled,
  feedback,
  onSave,
}: {
  item: EvidenceViewItem;
  name: string;
  disabled: boolean;
  feedback: EvidenceRowFeedback | null;
  onSave: ObligationTrackerProps["onSave"];
}) {
  const [draft, setDraft] = useState<EvidenceDraft>(() => draftFor(item));
  const [settled, setSettled] = useState<EvidenceRowFeedback | null>(null);
  const messageId = useId();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const messageRef = useRef<HTMLParagraphElement>(null);
  const reviewedOnInvalid = feedback?.kind === "error" && feedback.invalidField === "reviewedOn";

  useEffect(() => {
    setDraft(draftFor(item));
    // Only a new saved revision replaces what the reviewer typed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item.revision]);

  // Runs after the outcome has rendered, so the message is there to take focus.
  useEffect(() => {
    if (settled) {
      focusAfterSave(settled, { button: buttonRef.current, message: messageRef.current });
      setSettled(null);
    }
  }, [settled]);

  async function save() {
    // aria-disabled, not disabled: a disabled button would drop focus to <body>.
    if (disabled) {
      return;
    }
    const outcome = await onSave(item, draft);
    if (outcome) {
      setSettled(outcome);
    }
  }

  return (
    <tr>
      <th scope="row">{item.article}</th>
      <td>{labelFor("roles", item.actor)}</td>
      <td>{item.evidenceArtifact}</td>
      <td>
        {item.applicationDate ?? "Open: see note"}
        {item.applicationDateNote ? <small>{item.applicationDateNote}</small> : null}
      </td>
      <td>{labelFor("review_status", item.reviewStatus)}</td>
      <td className="evidenceControls">
        <StatusPill label={labelFor("evidence_state", item.state)} tone={evidenceTone(item.state)} />
        {item.staleReasons.map((reason) => (
          <small key={reason}>{labelFor("evidence_stale_reason", reason)}</small>
        ))}
        <select
          aria-label={`Evidence state, ${name}`}
          value={draft.state}
          disabled={disabled}
          onChange={(event) => setDraft({ ...draft, state: event.target.value as SettableEvidenceState })}
        >
          {SETTABLE_STATES.map((state) => (
            <option key={state} value={state}>
              {labelFor("evidence_state", state)}
            </option>
          ))}
        </select>
      </td>
      <td className="evidenceControls">
        <input
          aria-label={`Owner, ${name}`}
          maxLength={120}
          value={draft.owner}
          disabled={disabled}
          onChange={(event) => setDraft({ ...draft, owner: event.target.value })}
        />
      </td>
      <td className="evidenceControls">
        <input
          aria-label={`Reviewed on, ${name}`}
          type="date"
          value={draft.reviewedOn}
          aria-invalid={reviewedOnInvalid || undefined}
          aria-describedby={reviewedOnInvalid ? messageId : undefined}
          disabled={disabled}
          onChange={(event) => setDraft({ ...draft, reviewedOn: event.target.value })}
        />
      </td>
      <td>
        <button
          ref={buttonRef}
          className="secondaryButton"
          type="button"
          aria-label={`Save evidence, ${name}`}
          aria-describedby={messageId}
          aria-disabled={disabled || undefined}
          onClick={() => void save()}
        >
          Save
        </button>
        <p
          ref={messageRef}
          id={messageId}
          className={feedback?.kind === "error" ? "rowMessage error" : "rowMessage"}
          role={feedback?.kind === "error" ? "alert" : "status"}
          tabIndex={-1}
        >
          {feedback?.text}
        </p>
      </td>
    </tr>
  );
}

/** The report's obligation graph, read-only, for when no tracker view is loaded. */
function GraphTable({ report }: { report: ClassificationReport | null }) {
  return (
    <div className="tableWrap" role="group" aria-labelledby="tracker-heading" tabIndex={0}>
      <table>
        <thead>
          <tr>
            <th>Article</th>
            <th>Actor</th>
            <th>Evidence</th>
            <th>Due</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {report?.obligation_graph.length ? (
            report.obligation_graph.map((item) => (
              <Fragment key={`${item.obligation_id}|${item.actor}`}>
                <tr>
                  <td>{item.article}</td>
                  <td>{labelFor("roles", item.actor)}</td>
                  <td>{item.evidence_artifact}</td>
                  <td>{item.application_date ?? "Open: see note"}</td>
                  <td>{labelFor("review_status", item.review_status)}</td>
                </tr>
                {item.application_date_note ? (
                  <tr>
                    <td colSpan={5}>
                      <small>{item.application_date_note}</small>
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            ))
          ) : (
            <tr>
              <td colSpan={5}>No obligation graph available.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
