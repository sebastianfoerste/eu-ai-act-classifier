"use client";

import { useRef, useState } from "react";

type Cell = {
  target_id: string;
  revision: number;
  reviewer: string | null;
  reviewer_override: string | null;
  comments: Array<{ id: string; body: string; status: string }>;
};

export type Workspace = {
  collaboration: { cells: Cell[]; activity: Array<Record<string, string>> };
  workflowDefinitions: Array<{ id: string; name: string; version: number; steps: string[] }>;
  workflowRuns: Array<{ id: string; status: string; definition_snapshot: Record<string, unknown> }>;
  selfAssessmentPortal: {
    localOnly: boolean;
    synthetic: boolean;
    questions: Array<{ id: string; label: string; required: boolean }>;
    draftPacket: Record<string, unknown>;
    exportAllowed: boolean;
  };
};

async function mutate(payload: Record<string, unknown>): Promise<Workspace> {
  const response = await fetch("/api/collaboration", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let message = "Workspace update failed";
    try {
      const result = (await response.json()) as { error?: string };
      message = result.error || message;
    } catch {
      // Preserve the stable fallback when an upstream error is not JSON.
    }
    throw new Error(message);
  }
  return response.json() as Promise<Workspace>;
}

export function WorkspaceClient({ initial }: { initial: Workspace }) {
  const [workspace, setWorkspace] = useState(initial);
  const [message, setMessage] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const importInput = useRef<HTMLInputElement>(null);
  const cell = workspace.collaboration?.cells?.[0];

  async function run(payload: Record<string, unknown>) {
    try {
      setWorkspace(await mutate(payload));
      setMessage("Saved to the local versioned workspace.");
    } catch (error) {
      setMessage(String(error));
    }
  }

  function exportWorkspace() {
    const blob = new Blob([JSON.stringify(workspace.collaboration, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "eu-ai-act-review-workspace.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function importWorkspace(file: File | undefined) {
    if (!file) return;
    try {
      await run({ action: "import", workspace: JSON.parse(await file.text()) });
    } catch (error) {
      setMessage(String(error));
    }
  }

  return (
    <>
      <section className="grid gap-3 sm:grid-cols-3">
        {[
          ["Review cells", workspace.collaboration.cells.length],
          ["Workflow templates", workspace.workflowDefinitions.length],
          ["Export allowed", String(workspace.selfAssessmentPortal.exportAllowed)],
        ].map(([label, value]) => (
          <article key={label} className="rounded-lg border border-zinc-200 bg-white p-4">
            <p className="text-xs uppercase text-zinc-500">{label}</p>
            <strong>{value}</strong>
          </article>
        ))}
      </section>
      <section className="rounded-lg border border-zinc-200 bg-white p-5">
        <h2 className="font-semibold">Persisted factor review</h2>
        {cell ? (
          <p className="mt-2 text-sm text-zinc-600">{cell.target_id}, revision {cell.revision}</p>
        ) : (
          <p className="mt-2 text-sm text-zinc-500">No active review cells found.</p>
        )}
        <div className="mt-4 flex flex-wrap gap-2">
          {cell ? (
            <>
              <button className="rounded bg-zinc-900 px-3 py-2 text-sm text-white" onClick={() => run({ action: "lock", targetId: cell.target_id, expectedRevision: cell.revision, actor: "Local reviewer" })}>Lock cell</button>
              <button className="rounded border px-3 py-2 text-sm" onClick={() => run({ action: "comment", targetId: cell.target_id, expectedRevision: cell.revision, actor: "Local reviewer", body: "Confirm the factor evidence against approved sources." })}>Add review comment</button>
              <button className="rounded border px-3 py-2 text-sm" onClick={() => run({ action: "review", targetId: cell.target_id, expectedRevision: cell.revision, actor: "Local reviewer", reviewerOverride: "human_review_required" })}>Record reviewer override</button>
              {cell.comments.find((comment) => comment.status === "open") ? (
                <button className="rounded border px-3 py-2 text-sm" onClick={() => run({ action: "resolve_comment", targetId: cell.target_id, expectedRevision: cell.revision, actor: "Local reviewer", commentId: cell.comments.find((comment) => comment.status === "open")?.id })}>Resolve first comment</button>
              ) : null}
            </>
          ) : null}
          <button className="rounded border px-3 py-2 text-sm" onClick={exportWorkspace}>Export local workspace</button>
          <button className="rounded border px-3 py-2 text-sm" onClick={() => importInput.current?.click()}>Import local workspace</button>
          <input ref={importInput} hidden type="file" accept="application/json" onChange={(event) => void importWorkspace(event.target.files?.[0])} />
        </div>
        {message ? <p className="mt-3 text-sm text-zinc-600">{message}</p> : null}
      </section>
      <section className="rounded-lg border border-zinc-200 bg-white p-5">
        <h2 className="font-semibold">Guided questions</h2>
        <ol className="mt-4 space-y-3">
          {workspace.selfAssessmentPortal.questions.map((question) => (
            <li key={question.id} className="rounded bg-zinc-50 p-3">
              <strong>{question.label}</strong>
              <div className="text-xs text-zinc-500">{question.required ? "Required" : "Optional"} · evidence and legal review required</div>
              <input className="mt-2 w-full rounded border border-zinc-300 px-3 py-2 text-sm" value={answers[question.id] ?? ""} onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))} />
            </li>
          ))}
        </ol>
        <button className="mt-4 rounded bg-zinc-900 px-3 py-2 text-sm text-white" onClick={() => run({ action: "self_assess", answers })}>Update draft assessment packet</button>
      </section>
    </>
  );
}
