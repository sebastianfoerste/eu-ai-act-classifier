// The cockpit's obligation tracker (ADR 0006). The Python bridge derives every lane,
// digest, retrieval date and stale reason (src/eu_ai_act_classifier/evidence_tracker.py);
// this module only shapes what the cockpit displays, posts and exports. It reads no
// clock and decides no lane or staleness.
import type { SystemProfile } from "./types";

export type SettableEvidenceState = "not_started" | "in_progress" | "evidence_attached" | "reviewed";
export type EvidenceState = SettableEvidenceState | "stale";
export type EvidenceLane = "applies_now" | "upcoming" | "contested_or_open";
export type EvidenceStaleReason = "report_changed" | "item_changed" | "reviewed_before_source_retrieval";

export type EvidenceViewItem = {
  obligationId: string;
  article: string;
  actor: string;
  evidenceArtifact: string;
  applicationDate: string | null;
  applicationDateNote: string | null;
  reviewStatus: string;
  sourceRetrievedOn: string | null;
  state: EvidenceState;
  storedState: SettableEvidenceState;
  staleReasons: EvidenceStaleReason[];
  owner: string | null;
  reviewedOn: string | null;
  revision: number;
  updatedBy: string | null;
  updatedAt: string | null;
};

export type EvidenceLaneView = { lane: EvidenceLane; items: EvidenceViewItem[] };

export type OrphanedEvidence = {
  obligationId: string;
  obligationActor: string;
  state: SettableEvidenceState;
  owner: string | null;
  reviewedOn: string | null;
  revision: number;
};

export type EvidenceView = {
  draftNotice: string;
  schema: string;
  systemId: string;
  system: string;
  classifierVersion: string;
  assessmentDate: string | null;
  reportDigest: string;
  counts: Record<EvidenceState, number>;
  lanes: EvidenceLaneView[];
  orphanedRecords: OrphanedEvidence[];
};

export type EvidenceDraft = { state: SettableEvidenceState; owner: string; reviewedOn: string };

export const SETTABLE_STATES: SettableEvidenceState[] = ["not_started", "in_progress", "evidence_attached", "reviewed"];
export const EVIDENCE_STATES: EvidenceState[] = [...SETTABLE_STATES, "stale"];

export type EvidenceTone = "neutral" | "info" | "success" | "warning";

/** The .statusPill tone for a state; the pill always carries the state's text too. */
export function evidenceTone(state: EvidenceState): EvidenceTone {
  switch (state) {
    case "in_progress":
    case "evidence_attached":
      return "info";
    case "reviewed":
      return "success";
    case "stale":
      return "warning";
    default:
      return "neutral";
  }
}

/** The editable values for a row. A stale row starts from the state it was saved with. */
export function draftFor(item: EvidenceViewItem): EvidenceDraft {
  return {
    state: item.state === "stale" ? item.storedState : item.state,
    owner: item.owner ?? "",
    reviewedOn: item.reviewedOn ?? "",
  };
}

export function evidenceViewPayload(systemId: string, profile: SystemProfile) {
  return { action: "evidence_view", systemId, profile };
}

export function evidencePayload(
  systemId: string,
  profile: SystemProfile,
  item: EvidenceViewItem,
  draft: EvidenceDraft,
) {
  return {
    action: "evidence",
    systemId,
    profile,
    obligationId: item.obligationId,
    obligationActor: item.actor,
    state: draft.state,
    owner: draft.owner.trim() || null,
    reviewedOn: draft.reviewedOn || null,
    expectedRevision: item.revision,
    actor: "Local reviewer",
  };
}

export function evidenceKey(item: Pick<EvidenceViewItem, "obligationId" | "actor">): string {
  return `${item.obligationId}|${item.actor}`;
}

/**
 * An accessible name per row: "Art. 9 AIA, Provider", with ", item n" appended where
 * the same article and actor repeat, so every control's label is unique.
 */
export function rowNames(items: EvidenceViewItem[], actorLabel: (actor: string) => string): Map<string, string> {
  const base = items.map((item) => `${item.article}, ${actorLabel(item.actor)}`);
  const totals = new Map<string, number>();
  for (const name of base) {
    totals.set(name, (totals.get(name) ?? 0) + 1);
  }
  const seen = new Map<string, number>();
  const names = new Map<string, string>();
  items.forEach((item, index) => {
    const name = base[index];
    if ((totals.get(name) ?? 0) > 1) {
      const position = (seen.get(name) ?? 0) + 1;
      seen.set(name, position);
      names.set(evidenceKey(item), `${name}, item ${position}`);
    } else {
      names.set(evidenceKey(item), name);
    }
  });
  return names;
}

/** The tracker as a JSON download; the bridge puts draftNotice first. */
export function evidenceExport(view: EvidenceView): string {
  return `${JSON.stringify(view, null, 2)}\n`;
}

export function evidenceFilename(view: EvidenceView): string {
  const slug =
    view.system
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "") || view.systemId;
  return `${slug}-obligation-evidence.json`;
}
