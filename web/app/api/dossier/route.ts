import { bodyNotJsonResponse, bridgeErrorResponse } from "../../../lib/bridge-error";
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
  } catch {
    return bodyNotJsonResponse();
  }
  try {
    const dossier = await runClassifierBridge("dossier", payload);
    return Response.json(dossier);
  } catch (error) {
    return bridgeErrorResponse(error);
  }
}
