import { bridgeErrorBody } from "../../../lib/bridge-error";
import { rejectUnsafeLocalRead } from "../../../lib/local-request-guard";
import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const rejected = rejectUnsafeLocalRead(request);
  if (rejected) {
    return rejected;
  }
  try {
    const inventory = await runClassifierBridge("inventory");
    return Response.json(inventory);
  } catch (error) {
    return Response.json(bridgeErrorBody(error), { status: 500 });
  }
}
