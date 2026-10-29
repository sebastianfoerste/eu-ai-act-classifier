import { bridgeErrorStatus } from "../../../lib/bridge-error";
import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    return Response.json(await runClassifierBridge("collaboration"));
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}

export async function POST(request: Request) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 400 });
  }
  try {
    return Response.json(await runClassifierBridge("collaboration", payload));
  } catch (error) {
    const message = String(error);
    return Response.json(
      { error: message },
      { status: message.includes("409 Conflict") ? 409 : bridgeErrorStatus(error) },
    );
  }
}
