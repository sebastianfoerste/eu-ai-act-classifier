import { runClassifierBridge } from "../../lib/python";
import { WorkspaceClient, type Workspace } from "./workspace-client";

export default async function SelfAssessmentPage() {
  const workspace = (await runClassifierBridge("collaboration", {
    action: "snapshot",
  })) as Workspace;
  return (
    <main className="pageShell">
      <header className="pageHeader">
        <p className="eyebrow">Synthetic local demo</p>
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
