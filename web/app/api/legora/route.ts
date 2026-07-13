import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    return Response.json(await runClassifierBridge("legora"));
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}
