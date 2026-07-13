import { runClassifierBridge } from "../../../lib/python";

export const runtime = "nodejs";

export async function GET() {
  try {
    return Response.json(await runClassifierBridge("legora"));
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    return Response.json(await runClassifierBridge("legora", payload));
  } catch (error) {
    const message = String(error);
    return Response.json(
      { error: message },
      { status: message.includes("409 Conflict") ? 409 : 400 },
    );
  }
}
