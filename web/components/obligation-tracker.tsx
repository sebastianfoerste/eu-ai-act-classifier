"use client";

import { Download, FileText } from "lucide-react";
import { Fragment, useState } from "react";
import {
  EVIDENCE_STATES,
  SETTABLE_STATES,
  draftFor,
  evidenceKey,
  evidenceTone,
  rowNames,
  type EvidenceDraft,
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
  message: string;
  onSave: (item: EvidenceViewItem, draft: EvidenceDraft) => void;
  onExport: () => void;
};

/**
 * The obligation tracker (ADR 0006): one table per lane, each row with its evidence
 * state, owner and reviewed-on date. Lanes, staleness and its reasons come from the
 * bridge. Without a tracker view (loading, the blank intake, or a bridge failure) the
 * report's obligation graph still shows, read-only.
 */
export function ObligationTracker({ report, view, disabled, message, onSave, onExport }: ObligationTrackerProps) {
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
      {view ? (
        <>
          {view.assessmentDate ? (
            <p className="meta">Assessment date {view.assessmentDate}.</p>
          ) : (
            <p className="meta">No assessment date: dated items without a note are listed as upcoming.</p>
          )}
          {view.lanes.map((lane) => {
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
                            key={`${evidenceKey(item)}:${item.revision}`}
                            item={item}
                            name={names.get(evidenceKey(item)) ?? item.article}
                            disabled={disabled}
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
      <p className="meta" role="status" aria-live="polite">
        {message}
      </p>
    </section>
  );
}

function EvidenceRow({
  item,
  name,
  disabled,
  onSave,
}: {
  item: EvidenceViewItem;
  name: string;
  disabled: boolean;
  onSave: (item: EvidenceViewItem, draft: EvidenceDraft) => void;
}) {
  const [draft, setDraft] = useState<EvidenceDraft>(() => draftFor(item));
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
          disabled={disabled}
          onChange={(event) => setDraft({ ...draft, reviewedOn: event.target.value })}
        />
      </td>
      <td>
        <button
          className="secondaryButton"
          type="button"
          aria-label={`Save evidence, ${name}`}
          disabled={disabled}
          onClick={() => onSave(item, draft)}
        >
          Save
        </button>
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
