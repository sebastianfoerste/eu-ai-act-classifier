import { bridgeErrorStatus } from "../../../lib/bridge-error";
import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function POST(request: Request) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 400 });
  }
  try {
    const report = await runClassifierBridge("classify", payload);
    return Response.json(report);
  } catch (error) {
    return Response.json({ error: String(error) }, { status: bridgeErrorStatus(error) });
  }
}
