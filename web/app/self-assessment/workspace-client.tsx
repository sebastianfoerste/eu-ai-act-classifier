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
      <section className="metricGrid" aria-label="Workspace summary">
        {[
          ["Review cells", workspace.collaboration.cells.length],
          ["Workflow templates", workspace.workflowDefinitions.length],
          ["Export allowed", String(workspace.selfAssessmentPortal.exportAllowed)],
        ].map(([label, value]) => (
          <article key={label} className="metricCard">
            <p>{label}</p>
            <strong>{value}</strong>
          </article>
        ))}
      </section>
      <section className="card">
        <h2>Persisted factor review</h2>
        {cell ? (
          <p className="meta">{cell.target_id}, revision {cell.revision}</p>
        ) : (
          <p className="meta">No active review cells found.</p>
        )}
        <div className="buttonRow">
          {cell ? (
            <>
              <button type="button" className="primaryButton" onClick={() => run({ action: "lock", targetId: cell.target_id, expectedRevision: cell.revision, actor: "Local reviewer" })}>Lock cell</button>
              <button type="button" className="secondaryButton" onClick={() => run({ action: "comment", targetId: cell.target_id, expectedRevision: cell.revision, actor: "Local reviewer", body: "Confirm the factor evidence against approved sources." })}>Add review comment</button>
              <button type="button" className="secondaryButton" onClick={() => run({ action: "review", targetId: cell.target_id, expectedRevision: cell.revision, actor: "Local reviewer", reviewerOverride: "human_review_required" })}>Record reviewer override</button>
              {cell.comments.find((comment) => comment.status === "open") ? (
                <button type="button" className="secondaryButton" onClick={() => run({ action: "resolve_comment", targetId: cell.target_id, expectedRevision: cell.revision, actor: "Local reviewer", commentId: cell.comments.find((comment) => comment.status === "open")?.id })}>Resolve first comment</button>
              ) : null}
            </>
          ) : null}
          <button type="button" className="secondaryButton" onClick={exportWorkspace}>Export local workspace</button>
          <button type="button" className="secondaryButton" onClick={() => importInput.current?.click()}>Import local workspace</button>
          <input ref={importInput} hidden aria-label="Import local workspace file" type="file" accept="application/json" onChange={(event) => void importWorkspace(event.target.files?.[0])} />
        </div>
        {message ? <p className="meta" role="status">{message}</p> : null}
      </section>
      <section className="card">
        <h2>Guided questions</h2>
        <ol className="questionList">
          {workspace.selfAssessmentPortal.questions.map((question) => (
            <li key={question.id}>
              <label htmlFor={`question-${question.id}`}>{question.label}</label>
              <p className="meta" id={`question-${question.id}-hint`}>{question.required ? "Required" : "Optional"} · evidence and legal review required</p>
              <input id={`question-${question.id}`} aria-describedby={`question-${question.id}-hint`} className="textInput" value={answers[question.id] ?? ""} onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))} />
            </li>
          ))}
        </ol>
        <div className="buttonRow"><button type="button" className="primaryButton" onClick={() => run({ action: "self_assess", answers })}>Update draft assessment packet</button></div>
      </section>
    </>
  );
}
