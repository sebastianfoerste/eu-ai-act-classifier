import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { ThemeToggle } from "../../components/theme-toggle";
import { unsafeLocalReadReason } from "../../lib/local-request-guard";
import { runClassifierBridge } from "../../lib/python";
import { WorkspaceClient, type Workspace } from "./workspace-client";

// Rendered per request, never prerendered at build time: the page exports the local
// workspace, and an import of an export that predates the latest saves would replace
// the review cells and the obligation tracker's evidence with older ones.
export const dynamic = "force-dynamic";

export default async function SelfAssessmentPage() {
  // The page carries the workspace (reviewer names, evidence owners and dates), so it
  // gets the Host, Origin and Sec-Fetch-Site checks of GET /api/collaboration before
  // the bridge runs: a DNS-rebound name gets a 404, not the workspace.
  if (unsafeLocalReadReason(await headers())) {
    notFound();
  }
  const workspace = (await runClassifierBridge("collaboration", {
    action: "snapshot",
  })) as Workspace;
  return (
    <main className="pageShell">
      <header className="pageHeader">
        <div className="pageHeaderBar">
          <p className="eyebrow">Synthetic local demo</p>
          <ThemeToggle />
        </div>
        <h1>EU AI Act self-assessment portal</h1>
        <p className="pageLead">
          Guided intake, collaborative factor review and versioned policy workflows. Export remains
          review-gated.
        </p>
      </header>
      <WorkspaceClient initial={workspace} />
    </main>
  );
}
