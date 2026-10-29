import { spawn } from "node:child_process";
import { EventEmitter } from "node:events";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ClassifierBridgeError, bridgeErrorStatus } from "./bridge-error";
import { runClassifierBridge } from "./python";

vi.mock("node:child_process", () => ({ spawn: vi.fn() }));

const spawnMock = vi.mocked(spawn);

// What local_api prints on stderr when it rejects a profile (exit 2).
const VALIDATION_ERROR_LINE = JSON.stringify({
  error: "1 validation error for SystemProfile\nroles\n  Input should be a valid list",
});

class FakeChild extends EventEmitter {
  stdout = new EventEmitter();
  stderr = new EventEmitter();
  stdin = { end: vi.fn() };
  kill = vi.fn();

  exit(code: number | null, output: { stdout?: string; stderr?: string } = {}) {
    if (output.stdout) this.stdout.emit("data", Buffer.from(output.stdout));
    if (output.stderr) this.stderr.emit("data", Buffer.from(output.stderr));
    this.emit("close", code);
  }
}

function startBridge() {
  const child = new FakeChild();
  spawnMock.mockReturnValue(child as never);
  const result = runClassifierBridge("classify", { profile: { name: "x" } });
  return { child, result };
}

async function failure(result: Promise<unknown>): Promise<ClassifierBridgeError> {
  const error = await result.then(
    () => expect.unreachable("the bridge call should have failed"),
    (reason: unknown) => reason,
  );
  expect(error).toBeInstanceOf(ClassifierBridgeError);
  return error as ClassifierBridgeError;
}

describe("classifier bridge exit handling", () => {
  beforeEach(() => {
    spawnMock.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("resolves with the JSON local_api prints and sends it the payload", async () => {
    const { child, result } = startBridge();

    child.exit(0, { stdout: '{"system": "x"}\n' });

    await expect(result).resolves.toEqual({ system: "x" });
    expect(child.stdin.end).toHaveBeenCalledWith(JSON.stringify({ profile: { name: "x" } }));
  });

  it("marks exit 2 with local_api's JSON error line as invalid input", async () => {
    const { child, result } = startBridge();

    child.exit(2, { stderr: `${VALIDATION_ERROR_LINE}\n` });

    const error = await failure(result);
    expect(error.exitCode).toBe(2);
    expect(error.invalidInput).toBe(true);
    expect(error.message).toContain("validation error for SystemProfile");
    expect(bridgeErrorStatus(error)).toBe(400);
  });

  it("still finds the JSON error line after a warning from uv", async () => {
    const { child, result } = startBridge();

    child.exit(2, { stderr: `warning: VIRTUAL_ENV does not match\n${VALIDATION_ERROR_LINE}\n` });

    expect(bridgeErrorStatus(await failure(result))).toBe(400);
  });

  it("does not mistake uv's own exit 2 for invalid input", async () => {
    const { child, result } = startBridge();

    child.exit(2, { stderr: "error: Failed to spawn: `python`\n  Caused by: No such file\n" });

    const error = await failure(result);
    expect(error.exitCode).toBe(2);
    expect(error.invalidInput).toBe(false);
    expect(bridgeErrorStatus(error)).toBe(500);
  });

  it("treats a crash as a server failure", async () => {
    const { child, result } = startBridge();

    child.exit(1, {
      stderr: 'Traceback (most recent call last):\n  File "x.py"\nRuntimeError: boom\n',
    });

    const error = await failure(result);
    expect(error.exitCode).toBe(1);
    expect(bridgeErrorStatus(error)).toBe(500);
  });

  it("kills the bridge and treats a timeout as a server failure", async () => {
    vi.useFakeTimers();
    const { child, result } = startBridge();

    vi.advanceTimersByTime(20000);

    const error = await failure(result);
    expect(error.message).toBe("classifier bridge timed out");
    expect(error.exitCode).toBeNull();
    expect(child.kill).toHaveBeenCalledWith("SIGTERM");
    expect(bridgeErrorStatus(error)).toBe(500);
  });

  it("treats output that is not JSON as a server failure", async () => {
    const { child, result } = startBridge();

    child.exit(0, { stdout: "not json" });

    const error = await result.catch((reason: unknown) => reason);
    expect(error).toBeInstanceOf(SyntaxError);
    expect(bridgeErrorStatus(error)).toBe(500);
  });
});
