import { bridgeErrorStatus } from "../../../lib/bridge-error";
import { rejectUnsafeLocalPost } from "../../../lib/local-request-guard";
import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const rejected = rejectUnsafeLocalPost(request);
  if (rejected) {
    return rejected;
  }
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
