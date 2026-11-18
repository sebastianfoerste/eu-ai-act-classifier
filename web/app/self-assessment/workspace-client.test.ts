import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { FALLBACK_DRAFT_NOTICE } from "../../lib/print";
import { type Workspace, workspaceExportPayload } from "./workspace-client";

function workspace(draftNotice?: string): Workspace {
  return {
    draftNotice,
    collaboration: { cells: [], evidence: [{ obligation_id: "high-risk.provider.9" }], activity: [] },
    workflowDefinitions: [],
    workflowRuns: [],
    selfAssessmentPortal: {
      localOnly: true,
      synthetic: true,
      questions: [],
      draftPacket: {},
      exportAllowed: false,
    },
  };
}

describe("self-assessment workspace export", () => {
  it("puts the bridge's draft notice first, then the collaboration workspace", () => {
    const payload = workspaceExportPayload(workspace("Notice from the bridge."));
    expect(Object.keys(payload)).toEqual(["draftNotice", "cells", "evidence", "activity"]);
    expect(payload.draftNotice).toBe("Notice from the bridge.");
    expect(payload.evidence).toEqual([{ obligation_id: "high-risk.provider.9" }]);
  });

  it("falls back to the engine's notice when the snapshot carries none", () => {
    expect(workspaceExportPayload(workspace()).draftNotice).toBe(FALLBACK_DRAFT_NOTICE);
    expect(workspaceExportPayload(workspace("")).draftNotice).toBe(FALLBACK_DRAFT_NOTICE);
  });
});

describe("self-assessment page", () => {
  it("renders per request, so an export carries the evidence saved since the build", () => {
    const source = readFileSync(new URL("./page.tsx", import.meta.url), "utf8");
    expect(source).toMatch(/^export const dynamic = "force-dynamic";$/m);
  });
});
