import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    const dossier = await runClassifierBridge("dossier", payload);
    return Response.json(dossier);
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 400 });
  }
}
