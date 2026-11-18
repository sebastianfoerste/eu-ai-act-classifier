import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { EvidenceView, EvidenceViewItem } from "../lib/evidence";
import { FALLBACK_DRAFT_NOTICE } from "../lib/print";
import type { ClassificationReport } from "../lib/types";
import { ObligationTracker } from "./obligation-tracker";

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

const NOW = viewItem({ obligationId: "literacy.provider.4", article: "Art. 4 AIA", applicationDate: "2025-02-02" });
const STALE = viewItem({
  state: "stale",
  storedState: "reviewed",
  staleReasons: ["report_changed", "reviewed_before_source_retrieval"],
  owner: "Owner A",
  reviewedOn: "2026-10-01",
  revision: 2,
});
const OPEN = viewItem({
  obligationId: "transparency.1",
  article: "Art. 50(1) AIA",
  applicationDate: null,
  applicationDateNote: "Turns on the placing date.",
});
const OPEN_TWIN = viewItem({ obligationId: "transparency.2", article: "Art. 50(1) AIA", applicationDate: "2026-08-02" });

function view(overrides: Partial<EvidenceView> = {}): EvidenceView {
  return {
    draftNotice: FALLBACK_DRAFT_NOTICE,
    schema: "cockpit.obligation-evidence.v1",
    systemId: "credit-provider",
    system: "CreditSightScore",
    classifierVersion: "0.3.0",
    assessmentDate: null,
    reportDigest: "a".repeat(64),
    counts: { not_started: 3, in_progress: 0, evidence_attached: 0, reviewed: 0, stale: 1 },
    lanes: [
      { lane: "applies_now", items: [NOW] },
      { lane: "upcoming", items: [STALE] },
      { lane: "contested_or_open", items: [OPEN, OPEN_TWIN] },
    ],
    orphanedRecords: [],
    ...overrides,
  };
}

const REPORT = {
  obligation_graph: [
    {
      obligation_id: "high-risk.provider.9",
      article: "Art. 9 AIA",
      actor: "provider",
      evidence_artifact: "Risk management system record.",
      application_date: null,
      application_date_note: "Contested date.",
      review_status: "review_required",
    },
  ],
} as unknown as ClassificationReport;

function render(props: Partial<Parameters<typeof ObligationTracker>[0]> = {}): string {
  return renderToStaticMarkup(
    <ObligationTracker
      report={REPORT}
      view={view()}
      disabled={false}
      message=""
      onSave={() => undefined}
      onExport={() => undefined}
      {...props}
    />,
  );
}

function all(markup: string, pattern: RegExp): string[] {
  return [...markup.matchAll(pattern)].map((match) => match[1]);
}

describe("ObligationTracker", () => {
  it("renders one headed table per lane, in order, with counts", () => {
    const markup = render();
    expect(all(markup, /<h3 id="tracker-lane-[a-z_]+">([^<]*)<\/h3>/g)).toEqual([
      "Applies now (1)",
      "Upcoming (1)",
      "Contested or open (2)",
    ]);
    expect(markup.match(/<table>/g)).toHaveLength(3);
    for (const lane of ["applies_now", "upcoming", "contested_or_open"]) {
      expect(markup).toContain(`<section class="laneSection" aria-labelledby="tracker-lane-${lane}">`);
      expect(markup).toContain(`role="group" tabindex="0" aria-labelledby="tracker-lane-${lane}"`);
    }
    expect(markup).toContain("4 graph items: Not started 3, In progress 0, Evidence attached 0, Reviewed 0, Stale 1");
  });

  it("heads every lane table with the nine columns", () => {
    const markup = render();
    const headers = all(markup, /<th scope="col">([^<]*)<\/th>/g);
    expect(headers.slice(0, 9)).toEqual([
      "Article",
      "Actor",
      "Evidence artifact",
      "Due",
      "Status",
      "Evidence state",
      "Owner",
      "Reviewed on",
      "Save",
    ]);
    expect(headers).toHaveLength(27);
    expect(all(markup, /<th scope="row">([^<]*)<\/th>/g)).toEqual([
      "Art. 4 AIA",
      "Art. 9 AIA",
      "Art. 50(1) AIA",
      "Art. 50(1) AIA",
    ]);
  });

  it("gives every control a unique name with the article and actor", () => {
    const labels = all(render(), /aria-label="([^"]*)"/g);
    expect(new Set(labels).size).toBe(labels.length);
    expect(labels).toContain("Evidence state, Art. 9 AIA, Provider");
    expect(labels).toContain("Owner, Art. 50(1) AIA, Provider, item 1");
    expect(labels).toContain("Reviewed on, Art. 50(1) AIA, Provider, item 2");
    expect(labels).toContain("Save evidence, Art. 4 AIA, Provider");
    expect(labels).toContain("Download obligation evidence tracker");
  });

  it("offers the four settable states and never Stale", () => {
    const markup = render();
    const select = /<select aria-label="Evidence state, Art. 9 AIA, Provider"[^>]*>([\s\S]*?)<\/select>/.exec(markup)?.[1] ?? "";
    expect(all(select, /<option [^>]*>([^<]*)<\/option>/g)).toEqual([
      "Not started",
      "In progress",
      "Evidence attached",
      "Reviewed",
    ]);
    // The stale row's draft starts from the state it was saved with.
    expect(select).toMatch(/<option value="reviewed" selected="">Reviewed<\/option>/);
    expect(markup).not.toMatch(/<option[^>]*>Stale<\/option>/);
  });

  it("shows a stale row's state and reasons as text", () => {
    const markup = render();
    expect(markup).toContain('<span class="statusPill warning">Stale</span>');
    expect(markup).toContain("<small>Report changed since saved</small>");
    expect(markup).toContain("<small>Reviewed before the source was retrieved</small>");
    expect(markup).toContain('value="Owner A"');
    expect(markup).toContain('type="date" value="2026-10-01"');
    expect(markup).toContain("<small>Turns on the placing date.</small>");
    expect(markup).toContain("Open: see note");
  });

  it("states a missing assessment date exactly when there is none", () => {
    const notice = "No assessment date: dated items without a note are listed as upcoming.";
    expect(render()).toContain(notice);
    const dated = render({ view: view({ assessmentDate: "2026-11-17" }) });
    expect(dated).not.toContain(notice);
    expect(dated).toContain("Assessment date 2026-11-17.");
  });

  it("disables every control and the export when disabled", () => {
    const markup = render({ disabled: true });
    const controls = markup.match(/<(select|input|button)\b[^>]*>/g) ?? [];
    expect(controls.length).toBe(1 + 4 * 4);
    for (const control of controls) {
      expect(control).toMatch(/disabled=""/);
    }
    expect(render()).not.toMatch(/<select[^>]*disabled=""/);
  });

  it("lists saved evidence for items no longer in the report", () => {
    const markup = render({
      view: view({
        orphanedRecords: [
          {
            obligationId: "high-risk.provider.111.2",
            obligationActor: "provider",
            state: "in_progress",
            owner: "Owner A",
            reviewedOn: null,
            revision: 1,
          },
        ],
      }),
    });
    expect(markup).toContain("<summary>Saved evidence for items not in this report (1)</summary>");
    expect(markup).toContain("high-risk.provider.111.2, Provider: In progress, owner Owner A, revision 1");
    expect(render()).not.toContain("<details");
  });

  it("falls back to the read-only graph without a tracker view", () => {
    const markup = render({ view: null, message: "The evidence tracker could not load: boom" });
    expect(markup).toContain("1 graph items</p>");
    expect(markup).toContain("<td>Art. 9 AIA</td>");
    expect(markup).toContain("<small>Contested date.</small>");
    expect(markup).not.toContain("<select");
    expect(markup).toContain('<p class="meta" role="status" aria-live="polite">The evidence tracker could not load: boom</p>');
    expect(markup).toMatch(/aria-label="Download obligation evidence tracker" disabled=""/);
    expect(render({ view: null, report: null })).toContain("No obligation graph available.");
  });

  it("shows an empty lane as a row of text", () => {
    const markup = render({
      view: view({
        lanes: [
          { lane: "applies_now", items: [] },
          { lane: "upcoming", items: [STALE] },
          { lane: "contested_or_open", items: [] },
        ],
      }),
    });
    expect(markup.match(/<td colSpan="9">No items in this lane\.<\/td>/gi)).toHaveLength(2);
  });
});

describe("cockpit tracker wiring", () => {
  // Checked in the source, since the web tests run without a DOM.
  const cockpit = readFileSync(new URL("./cockpit.tsx", import.meta.url), "utf8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");

  it("saves with the profile that produced the report on screen", () => {
    expect(cockpit).toMatch(/postJson<EvidenceView>\("\/api\/collaboration", evidencePayload\([^)]*profileOnScreen/);
    expect(cockpit).toMatch(/const profileOnScreen = classifiedProfile;/);
    // A save that ends after a newer classification leaves that run's view alone.
    expect(cockpit).toMatch(/if \(run === latestRun\.current\) \{\s*setEvidenceView\(view\);\s*\}\s*setEvidenceMessage\(`Saved evidence/);
  });

  it("loads the tracker for the system passed in, with the cleaned profile", () => {
    expect(cockpit).toContain("evidenceViewPayload(systemId, clean)");
    expect(cockpit).toMatch(/runClassification\(nextProfile = profile, advisory = includeAdvisory, systemId = selectedId\)/);
    expect(cockpit).toContain("void runClassification(cloned, includeAdvisory, item.id);");
    expect(cockpit).toMatch(/if \(run === latestRun\.current\) \{\s*setEvidenceView\(view\);/);
  });

  it("places the tracker before the printable section and disables it for the blank intake", () => {
    const tracker = cockpit.indexOf("<ObligationTracker");
    expect(tracker).toBeGreaterThan(cockpit.indexOf("<SystemInventoryPanel"));
    expect(tracker).toBeLessThan(cockpit.indexOf('<div className="lowerGrid">'));
    expect(tracker).toBeLessThan(cockpit.indexOf("<PrintableArtifact doc={printable} />"));
    expect(cockpit).toContain('disabled={isClassifying || evidenceBusy || selectedId === "new"}');
  });

  it("normalises the assessment date like the other dates", () => {
    expect(cockpit).toContain("assessment_date: normalizeOptional(profile.assessment_date ?? null),");
    expect(cockpit).toMatch(/=> updateProfile\("assessment_date", value\)/);
  });
});
