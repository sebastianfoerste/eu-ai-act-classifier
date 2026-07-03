import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    const schema = await runClassifierBridge("schema");
    return Response.json(schema);
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}
