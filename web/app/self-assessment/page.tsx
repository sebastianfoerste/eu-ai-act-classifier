import { runClassifierBridge } from "../../lib/python";

type Workspace = { collaboration: { cells: unknown[] }; workflowDefinitions: Array<{ id: string; name: string; version: number; steps: string[] }>; workflowRuns: Array<{ id: string; status: string }>; selfAssessmentPortal: { localOnly: boolean; synthetic: boolean; questions: Array<{ id: string; label: string; required: boolean }>; draftPacket: Record<string, unknown>; exportAllowed: boolean } };

export default async function SelfAssessmentPage() {
  const workspace = await runClassifierBridge("legora") as Workspace;
  return <main className="mx-auto max-w-5xl space-y-6 p-6">
    <header><p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Synthetic local demo</p><h1 className="mt-1 text-2xl font-semibold">EU AI Act self-assessment portal</h1><p className="mt-2 text-sm text-zinc-600">Guided intake, collaborative factor review and versioned policy workflows. Export remains review-gated.</p></header>
    <section className="grid gap-3 sm:grid-cols-3">{[["Review cells", workspace.collaboration.cells.length],["Workflow templates", workspace.workflowDefinitions.length],["Export allowed", String(workspace.selfAssessmentPortal.exportAllowed)]].map(([label,value])=><article key={label} className="rounded-lg border border-zinc-200 bg-white p-4"><p className="text-xs uppercase text-zinc-500">{label}</p><strong>{value}</strong></article>)}</section>
    <section className="rounded-lg border border-zinc-200 bg-white p-5"><h2 className="font-semibold">Guided questions</h2><ol className="mt-4 space-y-3">{workspace.selfAssessmentPortal.questions.map((question)=><li key={question.id} className="rounded bg-zinc-50 p-3"><strong>{question.label}</strong><div className="text-xs text-zinc-500">{question.required ? "Required" : "Optional"} · evidence and legal review required</div></li>)}</ol></section>
  </main>;
}
