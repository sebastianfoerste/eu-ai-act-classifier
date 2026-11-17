/**
 * A failed run of the Python bridge, `python -m eu_ai_act_classifier.local_api`.
 *
 * local_api rejects invalid input by exiting 2 with one JSON line, {"error": "..."}, on
 * stderr. `uv run` also exits 2 when uv itself fails, but prints plain text, so the JSON
 * line is what marks invalid input. A timeout, a crash or any other failure is the
 * server's, not the caller's.
 */
export class ClassifierBridgeError extends Error {
  /** The bridge's exit code; null when it never exited on its own, as on a timeout. */
  readonly exitCode: number | null;
  /** local_api's message when it rejected the input, read from its JSON line; else null. */
  readonly inputError: string | null;
  /** local_api rejected the input: exit 2 and a JSON error line on stderr. */
  readonly invalidInput: boolean;

  constructor(message: string, exitCode: number | null = null, stderr = "") {
    super(message);
    this.exitCode = exitCode;
    this.inputError = exitCode === 2 ? lastJsonError(stderr) : null;
    this.invalidInput = this.inputError !== null;
  }
}

/** The text of {"error": "..."} when it is the last line of `stderr`, else null. */
function lastJsonError(stderr: string): string | null {
  const lastLine = stderr.trimEnd().split("\n").at(-1) ?? "";
  try {
    const parsed: unknown = JSON.parse(lastLine);
    if (typeof parsed === "object" && parsed !== null) {
      const error = (parsed as { error?: unknown }).error;
      return typeof error === "string" ? error : null;
    }
    return null;
  } catch {
    return null;
  }
}

export const BRIDGE_TIMED_OUT = "classifier bridge timed out";
export const BRIDGE_FAILED = "classifier bridge failed";
export const BODY_NOT_JSON = "request body is not valid JSON";

/**
 * The error for a bridge run that exited with `code`. Its message is local_api's own
 * message when it rejected the input, else only the exit code: stderr can hold a
 * traceback, absolute paths and the values being processed.
 */
export function bridgeExitError(code: number | null, stderr: string): ClassifierBridgeError {
  const inputError = code === 2 ? lastJsonError(stderr) : null;
  return new ClassifierBridgeError(inputError ?? `classifier bridge exited with ${code}`, code, stderr);
}

/** HTTP status for a failed bridge call: 400 for input local_api rejected, else 500. */
export function bridgeErrorStatus(error: unknown): 400 | 500 {
  return error instanceof ClassifierBridgeError && error.invalidInput ? 400 : 500;
}

/**
 * The JSON body a route answers for a failed bridge call: local_api's message for input
 * it rejected, else a fixed text. Never stderr, an exception's own message or the request.
 */
export function bridgeErrorBody(error: unknown): { error: string } {
  if (error instanceof ClassifierBridgeError) {
    if (error.inputError !== null) {
      return { error: error.inputError };
    }
    if (error.exitCode === null && error.message === BRIDGE_TIMED_OUT) {
      return { error: BRIDGE_TIMED_OUT };
    }
  }
  return { error: BRIDGE_FAILED };
}

/** The response for a failed bridge call (see bridgeErrorBody and bridgeErrorStatus). */
export function bridgeErrorResponse(error: unknown): Response {
  return Response.json(bridgeErrorBody(error), { status: bridgeErrorStatus(error) });
}

/** The response for a request body that is not JSON. The parser's message quotes the body. */
export function bodyNotJsonResponse(): Response {
  return Response.json({ error: BODY_NOT_JSON }, { status: 400 });
}
