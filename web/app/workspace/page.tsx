import { formatLabel, labelFor } from "../../lib/labels";
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
    <main className="pageShell">
      <header className="pageHeader">
        <p className="eyebrow">AI system portfolio</p>
        <h1>System vault and fleet command center</h1>
        <p className="pageLead">Deterministic inventory analytics, guided assessment workflows and draft-only evidence packs for qualified review.</p>
      </header>

      <section className="metricGrid" aria-label="Portfolio summary">
        {Object.entries(workspace.commandCenter.summary).map(([label, value]) => (
          <article key={label} className="metricCard">
            <p>{formatLabel(label)}</p>
            <strong>{value}</strong>
          </article>
        ))}
      </section>

      <section className="card" aria-labelledby="fleet-heading">
        <h2 id="fleet-heading">Fleet command center</h2>
        <div className="scrollX" tabIndex={0} role="region" aria-labelledby="fleet-heading">
          <table className="dataTable">
            <thead><tr><th scope="col">System</th><th scope="col">Risk</th><th scope="col">Review</th><th scope="col">Priority</th><th scope="col">Next action</th></tr></thead>
            <tbody>
              {workspace.commandCenter.rows.map((row) => (
                <tr key={row.system_id}><td><strong>{row.name}</strong></td><td>{labelFor("risk_tier", row.risk_tier)}</td><td>{labelFor("review_status", row.review_status)}</td><td>{formatLabel(row.priority)}</td><td>{row.next_action}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="cardGrid">
        <article className="card">
          <h2>AI system vault</h2>
          <p className="meta">{workspace.vault.records.length} systems, {workspace.vault.verified_source_count} complete source manifests, {workspace.vault.open_source_count} open.</p>
          <ul className="plainList">{workspace.vault.records.map((record) => <li key={record.system_id}><strong>{record.name}</strong><p className="meta">{record.role.split(", ").map((role) => labelFor("roles", role)).join(", ")} · {record.artifact_refs.length} draft artifacts</p></li>)}</ul>
        </article>
        <article className="card">
          <h2>Assessment workflows</h2>
          <ul className="plainList">{workspace.workflows.map((workflow) => <li key={workflow.system_id}><strong>{workflow.system_id}</strong><p className="meta">{formatLabel(workflow.status)} · {workflow.steps.length} guided steps · deployment blocked</p></li>)}</ul>
        </article>
      </section>
      <p className="footnote">{workspace.commandCenter.reviewNotice}</p>
    </main>
  );
}
