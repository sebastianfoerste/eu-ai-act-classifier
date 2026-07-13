import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    const workspace = await runClassifierBridge("workspace");
    return Response.json(workspace);
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}
