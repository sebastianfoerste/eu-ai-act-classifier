import { bridgeErrorBody } from "../../../lib/bridge-error";
import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    const schema = await runClassifierBridge("schema");
    return Response.json(schema);
  } catch (error) {
    return Response.json(bridgeErrorBody(error), { status: 500 });
  }
}
