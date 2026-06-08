import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    const sources = await runClassifierBridge("sources");
    return Response.json(sources);
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}
