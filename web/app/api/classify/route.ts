import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    const report = await runClassifierBridge("classify", payload);
    return Response.json(report);
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 400 });
  }
}
