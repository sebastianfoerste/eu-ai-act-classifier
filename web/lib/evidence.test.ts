import { readFileSync } from "node:fs";
import { describe, expect, it, vi } from "vitest";

import {
  EVIDENCE_STATES,
  SAVE_CONFLICT_RELOADED,
  SETTABLE_STATES,
  draftFor,
  evidenceExport,
  evidenceFilename,
  evidenceKey,
  evidencePayload,
  evidenceTone,
  evidenceViewPayload,
  focusAfterSave,
  rowNames,
  settleEvidenceSave,
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
      { lane: "upcoming", items: [] },
      { lane: "no_assessment_date", items: [viewItem()] },
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
      ["evidence_lane", ["applies_now", "upcoming", "no_assessment_date", "contested_or_open"]],
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

describe("settleEvidenceSave", () => {
  const saved = evidenceView({ reportDigest: "b".repeat(64) });
  const reloaded = evidenceView({ reportDigest: "c".repeat(64) });
  const conflict = () => Promise.reject(new Error("409 Conflict: stale evidence revision"));

  function steps(overrides: Partial<Parameters<typeof settleEvidenceSave>[0]> = {}) {
    return {
      name: "Art. 9 AIA, Provider",
      save: () => Promise.resolve(saved),
      reload: () => Promise.resolve(reloaded),
      isCurrent: () => true,
      ...overrides,
    };
  }

  it("returns the saved view and a success message for the row", async () => {
    expect(await settleEvidenceSave(steps())).toEqual({
      view: saved,
      feedback: { kind: "saved", text: "Saved evidence for Art. 9 AIA, Provider.", invalidField: null },
    });
  });

  it("reloads the tracker on a 409 and says so", async () => {
    expect(await settleEvidenceSave(steps({ save: conflict }))).toEqual({
      view: reloaded,
      feedback: { kind: "error", text: SAVE_CONFLICT_RELOADED, invalidField: null },
    });
  });

  it("says the tracker could not reload when the reload after a 409 fails", async () => {
    const result = await settleEvidenceSave(
      steps({ save: conflict, reload: () => Promise.reject(new Error("classifier bridge timed out")) }),
    );
    expect(result).toEqual({
      view: null,
      feedback: {
        kind: "error",
        text: "Another save reached this item first, and the tracker could not reload: classifier bridge timed out. Classify again to refresh.",
        invalidField: null,
      },
    });
    expect(result?.feedback.text).not.toContain("was reloaded");
  });

  it.each([
    ["reviewedOn must not be after the current date", "reviewedOn"],
    ["Art. 9 AIA: a reviewed item needs a reviewed-on date; enter the date of review", "reviewedOn"],
    ["reviewed_on: Input should be a valid date", "reviewedOn"],
    ["unknown obligation graph item for this report", null],
  ])("marks the reviewed-on input invalid only for a date error: %s", async (message, field) => {
    const result = await settleEvidenceSave(steps({ save: () => Promise.reject(new Error(message)) }));
    expect(result).toEqual({ view: null, feedback: { kind: "error", text: message, invalidField: field } });
  });

  it.each([
    ["a save", {}],
    ["a 409", { save: conflict }],
    ["a failed reload", { save: conflict, reload: () => Promise.reject(new Error("boom")) }],
    ["an error", { save: () => Promise.reject(new Error("reviewedOn must not be after the current date")) }],
  ])("drops %s that settles after a newer classification", async (_name, overrides) => {
    let current = true;
    const save = vi.fn((overrides as { save?: () => Promise<EvidenceView> }).save ?? (() => Promise.resolve(saved)));
    const result = settleEvidenceSave(
      steps({
        ...overrides,
        save: () => {
          // The reviewer picks another system while the save runs.
          current = false;
          return save();
        },
        isCurrent: () => current,
      }),
    );
    expect(await result).toBeNull();
    expect(save).toHaveBeenCalledOnce();
  });
});

describe("focusAfterSave", () => {
  function targets() {
    return { button: { focus: vi.fn() }, message: { focus: vi.fn() } };
  }

  it("returns focus to the row's Save button after a save", () => {
    const row = targets();
    expect(focusAfterSave({ kind: "saved", text: "Saved.", invalidField: null }, row)).toBe("button");
    expect(row.button.focus).toHaveBeenCalledOnce();
    expect(row.message.focus).not.toHaveBeenCalled();
  });

  it("moves focus to the row's message after a failure", () => {
    const row = targets();
    expect(focusAfterSave({ kind: "error", text: "No.", invalidField: "reviewedOn" }, row)).toBe("message");
    expect(row.message.focus).toHaveBeenCalledOnce();
    expect(row.button.focus).not.toHaveBeenCalled();
  });

  it("falls back to the button, and to nothing once the row is gone", () => {
    const button = { focus: vi.fn() };
    expect(focusAfterSave({ kind: "error", text: "No.", invalidField: null }, { button, message: null })).toBe("button");
    expect(button.focus).toHaveBeenCalledOnce();
    expect(focusAfterSave({ kind: "saved", text: "Saved.", invalidField: null }, { button: null, message: null })).toBeNull();
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
