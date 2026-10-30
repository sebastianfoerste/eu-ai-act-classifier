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
  /** local_api rejected the input: exit 2 and a JSON error line on stderr. */
  readonly invalidInput: boolean;

  constructor(message: string, exitCode: number | null = null, stderr = "") {
    super(message);
    this.exitCode = exitCode;
    this.invalidInput = exitCode === 2 && endsWithJsonError(stderr);
  }
}

function endsWithJsonError(stderr: string): boolean {
  const lastLine = stderr.trimEnd().split("\n").at(-1) ?? "";
  try {
    const parsed: unknown = JSON.parse(lastLine);
    return (
      typeof parsed === "object" &&
      parsed !== null &&
      typeof (parsed as { error?: unknown }).error === "string"
    );
  } catch {
    return false;
  }
}

/** HTTP status for a failed bridge call: 400 for input local_api rejected, else 500. */
export function bridgeErrorStatus(error: unknown): 400 | 500 {
  return error instanceof ClassifierBridgeError && error.invalidInput ? 400 : 500;
}
