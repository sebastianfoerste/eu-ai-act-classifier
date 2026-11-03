import { bridgeErrorBody } from "../../../lib/bridge-error";
import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    const workspace = await runClassifierBridge("workspace");
    return Response.json(workspace);
  } catch (error) {
    return Response.json(bridgeErrorBody(error), { status: 500 });
  }
}
