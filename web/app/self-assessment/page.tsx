import { runClassifierBridge } from "../../lib/python";
import { WorkspaceClient, type Workspace } from "./workspace-client";

export default async function SelfAssessmentPage() {
  const workspace = await runClassifierBridge("legora", { action: "snapshot" }) as Workspace;
  return <main className="mx-auto max-w-5xl space-y-6 p-6">
    <header><p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Synthetic local demo</p><h1 className="mt-1 text-2xl font-semibold">EU AI Act self-assessment portal</h1><p className="mt-2 text-sm text-zinc-600">Guided intake, collaborative factor review and versioned policy workflows. Export remains review-gated.</p></header>
    <WorkspaceClient initial={workspace} />
  </main>;
}
