export const runtime = "nodejs";

export async function GET() {
  return Response.json({
    status: "ok",
    service: "eu-ai-act-classifier-web",
    // The collaboration bridge saves reviewer names, overrides and comments to this
    // file under the repository root (src/eu_ai_act_classifier/local_api.py).
    persistence: "local_file",
    store: "runtime-data/collaboration-workspace.json",
  });
}
