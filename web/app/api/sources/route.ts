import { bridgeErrorBody } from "../../../lib/bridge-error";
import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    const sources = await runClassifierBridge("sources");
    return Response.json(sources);
  } catch (error) {
    return Response.json(bridgeErrorBody(error), { status: 500 });
  }
}
