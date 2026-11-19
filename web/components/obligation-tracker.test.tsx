import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { evidenceKey, type EvidenceRowFeedback, type EvidenceView, type EvidenceViewItem } from "../lib/evidence";
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
const UNDATED = viewItem({ obligationId: "high-risk.provider.17", article: "Art. 17 AIA" });

function view(overrides: Partial<EvidenceView> = {}): EvidenceView {
  return {
    draftNotice: FALLBACK_DRAFT_NOTICE,
    schema: "cockpit.obligation-evidence.v1",
    systemId: "credit-provider",
    system: "CreditSightScore",
    classifierVersion: "0.3.0",
    assessmentDate: null,
    reportDigest: "a".repeat(64),
    counts: { not_started: 4, in_progress: 0, evidence_attached: 0, reviewed: 0, stale: 1 },
    lanes: [
      { lane: "applies_now", items: [NOW] },
      { lane: "upcoming", items: [STALE] },
      { lane: "no_assessment_date", items: [UNDATED] },
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
      feedback={{}}
      onSave={() => Promise.resolve(null)}
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
      "Applies on the assessment date (1)",
      "Applies after the assessment date (1)",
      "Dated; no assessment date set (1)",
      "Contested or open (2)",
    ]);
    expect(markup.match(/<table>/g)).toHaveLength(4);
    for (const lane of ["applies_now", "upcoming", "no_assessment_date", "contested_or_open"]) {
      expect(markup).toContain(`<section class="laneSection" aria-labelledby="tracker-lane-${lane}">`);
      expect(markup).toContain(`role="group" tabindex="0" aria-labelledby="tracker-lane-${lane}"`);
    }
    expect(markup).toContain("5 graph items: Not started 4, In progress 0, Evidence attached 0, Reviewed 0, Stale 1");
  });

  it("leaves out the lanes that cannot hold an item for the date given, unless they hold one", () => {
    const heads = (markup: string) => all(markup, /<h3 id="tracker-lane-[a-z_]+">([^<]*)<\/h3>/g);
    const undated = view({
      lanes: [
        { lane: "applies_now", items: [] },
        { lane: "upcoming", items: [] },
        { lane: "no_assessment_date", items: [UNDATED] },
        { lane: "contested_or_open", items: [OPEN] },
      ],
    });
    expect(heads(render({ view: undated }))).toEqual(["Dated; no assessment date set (1)", "Contested or open (1)"]);
    const dated = view({
      assessmentDate: "2026-11-17",
      lanes: [
        { lane: "applies_now", items: [NOW] },
        { lane: "upcoming", items: [] },
        { lane: "no_assessment_date", items: [] },
        { lane: "contested_or_open", items: [] },
      ],
    });
    expect(heads(render({ view: dated }))).toEqual([
      "Applies on the assessment date (1)",
      "Applies after the assessment date (0)",
      "Contested or open (0)",
    ]);
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
    expect(headers).toHaveLength(36);
    expect(all(markup, /<th scope="row">([^<]*)<\/th>/g)).toEqual([
      "Art. 4 AIA",
      "Art. 9 AIA",
      "Art. 17 AIA",
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

  it("states a missing assessment date exactly when there is none, and what the lanes are placed against", () => {
    const hint =
      "Lanes are placed against the assessment date; while none is set, dated items wait under \u201cDated; no assessment date set\u201d.";
    const undated = render();
    expect(undated).toContain(`No assessment date set. ${hint}`);
    expect(undated).not.toContain("listed as upcoming");
    const dated = render({ view: view({ assessmentDate: "2026-11-17" }) });
    expect(dated).not.toContain("No assessment date set.");
    expect(dated).toContain(`Assessment date 2026-11-17. ${hint}`);
  });

  it("disables every field and the export when disabled, and keeps Save focusable", () => {
    const markup = render({ disabled: true });
    const fields = markup.match(/<(select|input)\b[^>]*>/g) ?? [];
    expect(fields.length).toBe(3 * 5);
    for (const field of fields) {
      expect(field).toMatch(/disabled=""/);
    }
    expect(markup).toMatch(/aria-label="Download obligation evidence tracker" disabled=""/);
    // A disabled button would drop focus to <body> when a save starts (aria-disabled + click guard).
    const saves = markup.match(/<button[^>]*aria-label="Save evidence[^>]*>/g) ?? [];
    expect(saves).toHaveLength(5);
    for (const save of saves) {
      expect(save).toContain('aria-disabled="true"');
      expect(save).not.toMatch(/\sdisabled=""/);
    }
    expect(render()).not.toMatch(/<select[^>]*disabled=""/);
    expect(render()).not.toContain("aria-disabled");
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
    expect(markup.indexOf('role="status" aria-live="polite"')).toBeLessThan(markup.indexOf("<table>"));
    expect(markup).toMatch(/aria-label="Download obligation evidence tracker" disabled=""/);
    expect(render({ view: null, report: null })).toContain("No obligation graph available.");
  });

  it("shows an empty lane as a row of text", () => {
    const markup = render({
      view: view({
        assessmentDate: "2026-11-17",
        lanes: [
          { lane: "applies_now", items: [] },
          { lane: "upcoming", items: [STALE] },
          { lane: "no_assessment_date", items: [] },
          { lane: "contested_or_open", items: [] },
        ],
      }),
    });
    // applies_now and contested_or_open are empty; no_assessment_date is left out with a date.
    expect(markup.match(/<td colSpan="9">No items in this lane\.<\/td>/gi)).toHaveLength(2);
  });
});

describe("ObligationTracker save feedback", () => {
  const STALE_KEY = evidenceKey(STALE);

  function row(markup: string, article: string): string {
    return /<tr>(?:(?!<tr>)[\s\S])*?<\/tr>/g.exec(markup.slice(markup.indexOf(`<th scope="row">${article}</th>`) - 4))?.[0] ?? "";
  }

  function withFeedback(feedback: EvidenceRowFeedback): string {
    return render({ feedback: { [STALE_KEY]: feedback } });
  }

  it("shows a failed save in its row as an alert and marks the reviewed-on date invalid", () => {
    const markup = withFeedback({
      kind: "error",
      text: "reviewedOn must not be after the current date",
      invalidField: "reviewedOn",
    });
    const stale = row(markup, "Art. 9 AIA");
    const message = /<p id="([^"]+)" class="rowMessage error" role="alert" tabindex="-1">([^<]*)<\/p>/.exec(stale);
    expect(message?.[2]).toBe("reviewedOn must not be after the current date");
    const id = message?.[1] ?? "missing";
    expect(stale).toMatch(new RegExp(`<button[^>]*aria-label="Save evidence, Art\\. 9 AIA, Provider" aria-describedby="${id}"`));
    const date = /<input aria-label="Reviewed on, Art\. 9 AIA, Provider"[^>]*>/.exec(stale)?.[0] ?? "";
    expect(date).toContain('aria-invalid="true"');
    expect(date).toContain(`aria-describedby="${id}"`);
    // Only that row: the others keep a valid date and an empty message.
    const other = row(markup, "Art. 4 AIA");
    expect(other).not.toContain("aria-invalid");
    expect(other).toMatch(/<p id="[^"]+" class="rowMessage" role="status" tabindex="-1"><\/p>/);
    expect(markup.match(/role="alert"/g)).toHaveLength(1);
  });

  it("leaves the date valid for an error about something else", () => {
    const markup = withFeedback({ kind: "error", text: "Another save reached this item first.", invalidField: null });
    expect(row(markup, "Art. 9 AIA")).toContain('role="alert" tabindex="-1">Another save reached this item first.</p>');
    expect(markup).not.toContain("aria-invalid");
  });

  it("shows a successful save in its row as polite status text", () => {
    const markup = withFeedback({ kind: "saved", text: "Saved evidence for Art. 9 AIA, Provider.", invalidField: null });
    expect(row(markup, "Art. 9 AIA")).toMatch(
      /<p id="[^"]+" class="rowMessage" role="status" tabindex="-1">Saved evidence for Art\. 9 AIA, Provider\.<\/p>/,
    );
    expect(markup).not.toContain('role="alert"');
  });

  it("keeps a row mounted across a save, so its Save button can take focus back", () => {
    // Checked in the source, since the web tests run without a DOM.
    const tracker = readFileSync(new URL("./obligation-tracker.tsx", import.meta.url), "utf8")
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/^\s*\/\/.*$/gm, "");
    expect(tracker).toMatch(/<EvidenceRow\s+key=\{evidenceKey\(item\)\}/);
    expect(tracker).toMatch(/setDraft\(draftFor\(item\)\);\s*\}, \[item\.revision\]\);/);
    expect(tracker).toMatch(/focusAfterSave\(settled, \{ button: buttonRef\.current, message: messageRef\.current \}\)/);
    expect(tracker).toMatch(/if \(disabled\) \{\s*return;\s*\}\s*const outcome = await onSave\(item, draft\);/);
  });

  it("places the summary status above the lanes", () => {
    const markup = render({ message: "Summary" });
    expect(markup.indexOf('role="status" aria-live="polite">Summary</p>')).toBeLessThan(markup.indexOf("<h3"));
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
    // A save that ends after a newer classification or a new intake changes neither
    // that selection's view nor its messages (settleEvidenceSave returns null).
    expect(cockpit).toMatch(/isCurrent: \(\) => run === latestRun\.current,\s*\}\);\s*if \(!result\) \{\s*return null;\s*\}/);
    expect(cockpit).not.toMatch(/setEvidenceMessage\(`Saved evidence|setEvidenceMessage\("Another save/);
    expect(cockpit).toContain("feedback={evidenceFeedback}");
    expect(cockpit).toContain("onSave={saveEvidence}");
  });

  it("drops a dossier from an earlier selection, and a new intake ends the running classification", () => {
    expect(cockpit).toMatch(
      /await postJson<ReviewDossier>\("\/api\/dossier"[^;]*;\s*if \(run !== latestRun\.current\) \{\s*return;\s*\}\s*const artifactResult/,
    );
    expect(cockpit).toMatch(/catch \(classificationError\) \{\s*if \(run !== latestRun\.current\) \{\s*return;\s*\}/);
    const loadBlank = /function loadBlank\(\) \{([\s\S]*?)\n {2}\}/.exec(cockpit)?.[1] ?? "";
    expect(loadBlank).toContain("latestRun.current += 1;");
    expect(loadBlank).toContain('setStatus("Ready");');
    expect(loadBlank).toContain("setEvidenceFeedback({});");
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
