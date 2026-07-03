export const runtime = "nodejs";

export async function GET() {
  return Response.json({
    status: "ok",
    service: "eu-ai-act-classifier-web",
    persistence: "local_in_memory",
  });
}
