import { runClassifierBridge } from "../../lib/python";

type Workspace = {
  vault: {
    records: Array<{ system_id: string; name: string; role: string; risk_tier: string; artifact_refs: string[] }>;
    verified_source_count: number;
    open_source_count: number;
  };
  workflows: Array<{
    system_id: string;
    status: string;
    steps: Array<{ key: string; label: string; status: string; next_action: string }>;
  }>;
  commandCenter: {
    summary: Record<string, number>;
    rows: Array<{
      system_id: string;
      name: string;
      risk_tier: string;
      review_status: string;
      priority: string;
      next_action: string;
    }>;
    reviewNotice: string;
  };
};

export default async function PortfolioWorkspacePage() {
  const workspace = (await runClassifierBridge("workspace")) as Workspace;
  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">AI system portfolio</p>
        <h1 className="mt-1 text-2xl font-semibold">System vault and fleet command center</h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-600">Deterministic inventory analytics, guided assessment workflows and draft-only evidence packs for qualified review.</p>
      </header>

      <section className="grid gap-3 sm:grid-cols-4">
        {Object.entries(workspace.commandCenter.summary).map(([label, value]) => (
          <article key={label} className="rounded-lg border border-zinc-200 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-500">{label.replaceAll("_", " ")}</p>
            <p className="mt-1 text-xl font-semibold">{value}</p>
          </article>
        ))}
      </section>

      <section className="overflow-x-auto rounded-lg border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 p-4"><h2 className="font-semibold">Fleet command center</h2></div>
        <table className="w-full min-w-[820px] text-left text-sm">
          <thead className="bg-zinc-50 text-xs text-zinc-500"><tr><th className="p-3">System</th><th className="p-3">Risk</th><th className="p-3">Review</th><th className="p-3">Priority</th><th className="p-3">Next action</th></tr></thead>
          <tbody className="divide-y divide-zinc-200">
            {workspace.commandCenter.rows.map((row) => (
              <tr key={row.system_id}><td className="p-3 font-medium">{row.name}</td><td className="p-3">{row.risk_tier}</td><td className="p-3">{row.review_status}</td><td className="p-3">{row.priority}</td><td className="p-3 text-zinc-600">{row.next_action}</td></tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-lg border border-zinc-200 bg-white p-4">
          <h2 className="font-semibold">AI system vault</h2>
          <p className="mt-1 text-sm text-zinc-600">{workspace.vault.records.length} systems, {workspace.vault.verified_source_count} complete source manifests, {workspace.vault.open_source_count} open.</p>
          <ul className="mt-4 space-y-2 text-sm">{workspace.vault.records.map((record) => <li key={record.system_id} className="rounded bg-zinc-50 p-3"><strong>{record.name}</strong><div className="text-xs text-zinc-500">{record.role} · {record.artifact_refs.length} draft artifacts</div></li>)}</ul>
        </article>
        <article className="rounded-lg border border-zinc-200 bg-white p-4">
          <h2 className="font-semibold">Assessment workflows</h2>
          <ul className="mt-4 space-y-2 text-sm">{workspace.workflows.map((workflow) => <li key={workflow.system_id} className="rounded bg-zinc-50 p-3"><strong>{workflow.system_id}</strong><div className="text-xs text-zinc-500">{workflow.status} · {workflow.steps.length} guided steps · deployment blocked</div></li>)}</ul>
        </article>
      </section>
      <p className="text-xs text-zinc-500">{workspace.commandCenter.reviewNotice}</p>
    </main>
  );
}
