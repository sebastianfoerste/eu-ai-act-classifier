import { bodyNotJsonResponse, bridgeErrorBody, bridgeErrorStatus } from "../../../lib/bridge-error";
import { rejectUnsafeLocalPost } from "../../../lib/local-request-guard";
import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    return Response.json(await runClassifierBridge("collaboration"));
  } catch (error) {
    return Response.json(bridgeErrorBody(error), { status: 500 });
  }
}

export async function POST(request: Request) {
  const rejected = rejectUnsafeLocalPost(request);
  if (rejected) {
    return rejected;
  }
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return bodyNotJsonResponse();
  }
  try {
    return Response.json(await runClassifierBridge("collaboration", payload));
  } catch (error) {
    // A stale revision or a lock is local_api rejecting the action with a 409 message.
    const body = bridgeErrorBody(error);
    const status = bridgeErrorStatus(error);
    return Response.json(body, {
      status: status === 400 && body.error.startsWith("409 Conflict") ? 409 : status,
    });
  }
}
