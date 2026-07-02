import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    const inventory = await runClassifierBridge("inventory");
    return Response.json(inventory);
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}
