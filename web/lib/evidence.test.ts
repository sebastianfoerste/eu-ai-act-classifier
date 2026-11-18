import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import {
  EVIDENCE_STATES,
  SETTABLE_STATES,
  draftFor,
  evidenceExport,
  evidenceFilename,
  evidenceKey,
  evidencePayload,
  evidenceTone,
  evidenceViewPayload,
  rowNames,
  type EvidenceView,
  type EvidenceViewItem,
} from "./evidence";
import catalog from "./labels.json";
import { formatLabel, labelFor } from "./labels";
import { FALLBACK_DRAFT_NOTICE } from "./print";
import { baseProfile } from "./samples";

function viewItem(overrides: Partial<EvidenceViewItem> = {}): EvidenceViewItem {
  return {
    obligationId: "high-risk.provider.9",
    article: "Art. 9 AIA",
    actor: "provider",
    evidenceArtifact: "Risk management system record.",
    applicationDate: "2027-12-02",
    applicationDateNote: null,
    reviewStatus: "review_required",
    sourceRetrievedOn: "2026-10-18",
    state: "not_started",
    storedState: "not_started",
    staleReasons: [],
    owner: null,
    reviewedOn: null,
    revision: 0,
    updatedBy: null,
    updatedAt: null,
    ...overrides,
  };
}

function evidenceView(overrides: Partial<EvidenceView> = {}): EvidenceView {
  return {
    draftNotice: FALLBACK_DRAFT_NOTICE,
    schema: "cockpit.obligation-evidence.v1",
    systemId: "credit-provider",
    system: "CreditSightScore",
    classifierVersion: "0.3.0",
    assessmentDate: null,
    reportDigest: "a".repeat(64),
    counts: { not_started: 1, in_progress: 0, evidence_attached: 0, reviewed: 0, stale: 0 },
    lanes: [
      { lane: "applies_now", items: [] },
      { lane: "upcoming", items: [viewItem()] },
      { lane: "contested_or_open", items: [] },
    ],
    orphanedRecords: [],
    ...overrides,
  };
}

describe("evidence states", () => {
  it("gives every state a tone", () => {
    for (const state of EVIDENCE_STATES) {
      expect(["neutral", "info", "success", "warning"]).toContain(evidenceTone(state));
    }
    expect(evidenceTone("stale")).toBe("warning");
    expect(evidenceTone("reviewed")).toBe("success");
    expect(SETTABLE_STATES).not.toContain("stale");
  });

  it("labels every state, lane and stale reason from the catalog", () => {
    const cases: Array<[Parameters<typeof labelFor>[0], string[]]> = [
      ["evidence_state", [...EVIDENCE_STATES]],
      ["evidence_lane", ["applies_now", "upcoming", "contested_or_open"]],
      ["evidence_stale_reason", ["report_changed", "item_changed", "reviewed_before_source_retrieval"]],
    ];
    // From the catalog, not the formatLabel fallback ("reviewed" and "stale" would read
    // the same either way, so the catalog entry itself is checked).
    const namespaces = catalog.namespaces as Record<string, Record<string, string>>;
    for (const [namespace, values] of cases) {
      expect(Object.keys(namespaces[namespace])).toEqual(values);
      for (const value of values) {
        expect(labelFor(namespace, value)).toBe(namespaces[namespace][value]);
      }
    }
    expect(labelFor("evidence_state", "evidence_attached")).not.toBe(formatLabel("evidence_attached"));
    expect(labelFor("evidence_stale_reason", "item_changed")).toBe("This obligation changed since saved");
  });
});

describe("evidence payloads", () => {
  it("trims the owner, sends empty values as null and the row's revision", () => {
    const item = viewItem({ revision: 3 });
    const payload = evidencePayload("credit-provider", baseProfile, item, {
      state: "in_progress",
      owner: "  Owner A ",
      reviewedOn: "",
    });
    expect(payload).toEqual({
      action: "evidence",
      systemId: "credit-provider",
      profile: baseProfile,
      obligationId: "high-risk.provider.9",
      obligationActor: "provider",
      state: "in_progress",
      owner: "Owner A",
      reviewedOn: null,
      expectedRevision: 3,
      actor: "Local reviewer",
    });
    expect(evidencePayload("x", baseProfile, item, { state: "not_started", owner: "   ", reviewedOn: "2026-10-18" })).toMatchObject({
      owner: null,
      reviewedOn: "2026-10-18",
    });
    expect(evidenceViewPayload("chatbot", baseProfile)).toEqual({
      action: "evidence_view",
      systemId: "chatbot",
      profile: baseProfile,
    });
  });

  it("drafts a stale row from the state it was saved with", () => {
    const stale = viewItem({ state: "stale", storedState: "reviewed", owner: "Owner A", reviewedOn: "2026-10-01" });
    expect(draftFor(stale)).toEqual({ state: "reviewed", owner: "Owner A", reviewedOn: "2026-10-01" });
    expect(draftFor(viewItem())).toEqual({ state: "not_started", owner: "", reviewedOn: "" });
  });

  it("keeps row names unique where an article and actor repeat", () => {
    const items = [
      viewItem({ obligationId: "transparency.1", article: "Art. 50(1) AIA" }),
      viewItem({ obligationId: "transparency.2", article: "Art. 50(1) AIA" }),
      viewItem({ obligationId: "high-risk.provider.9" }),
      viewItem({ obligationId: "high-risk.deployer.26", actor: "deployer", article: "Art. 26 AIA" }),
    ];
    const names = rowNames(items, (actor) => labelFor("roles", actor));
    expect([...names.values()]).toEqual([
      "Art. 50(1) AIA, Provider, item 1",
      "Art. 50(1) AIA, Provider, item 2",
      "Art. 9 AIA, Provider",
      "Art. 26 AIA, Deployer",
    ]);
    expect(names.get(evidenceKey(items[3]))).toBe("Art. 26 AIA, Deployer");
  });
});

describe("evidence export", () => {
  it("starts with the draft notice and names the file after the system", () => {
    const text = evidenceExport(evidenceView());
    expect(Object.keys(JSON.parse(text))[0]).toBe("draftNotice");
    expect(JSON.parse(text).draftNotice).toBe(FALLBACK_DRAFT_NOTICE);
    expect(evidenceFilename(evidenceView())).toBe("creditsightscore-obligation-evidence.json");
    expect(evidenceFilename(evidenceView({ system: "  " }))).toBe("credit-provider-obligation-evidence.json");
  });
});

describe("no dates or lane logic in the browser", () => {
  it.each(["./evidence.ts", "../components/obligation-tracker.tsx"])("%s reads no clock and compares no dates", (path) => {
    const source = readFileSync(new URL(path, import.meta.url), "utf8")
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/^\s*\/\/.*$/gm, "");
    expect(source).not.toMatch(/\bDate\b|toISOString|Date\.now|localeCompare/);
  });
});
