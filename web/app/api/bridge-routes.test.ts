import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ClassifierBridgeError } from "../../lib/bridge-error";
import { runClassifierBridge } from "../../lib/python";
import { POST as artifactsPOST } from "./artifacts/route";
import { POST as classifyPOST } from "./classify/route";
import { POST as dossierPOST } from "./dossier/route";

vi.mock("../../lib/python", () => ({
  runClassifierBridge: vi.fn(),
}));

const bridge = vi.mocked(runClassifierBridge);

const VALIDATION_ERROR_LINE = JSON.stringify({
  error: "1 validation error for SystemProfile\nroles\n  Input should be a valid list",
});

const COCKPIT = "http://127.0.0.1:3000";

/** A POST as the cockpit page sends it with fetch(); `headers` overrides single headers. */
function post(url: string, body: string, headers: Record<string, string> = {}): Request {
  return new Request(url, {
    method: "POST",
    headers: {
      host: "127.0.0.1:3000",
      origin: COCKPIT,
      "sec-fetch-site": "same-origin",
      "content-type": "application/json",
      ...headers,
    },
    body,
  });
}

describe.each([
  ["classify", classifyPOST],
  ["artifacts", artifactsPOST],
  ["dossier", dossierPOST],
] as const)("POST /api/%s", (command, POST) => {
  const url = `${COCKPIT}/api/${command}`;
  const payload = { profile: { name: "x" }, artifact: "fria" };

  beforeEach(() => {
    bridge.mockReset();
    vi.stubEnv("PORT", "3000");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("passes the payload to the Python bridge", async () => {
    bridge.mockResolvedValue({ system: "x" });

    const response = await POST(post(url, JSON.stringify(payload)));

    expect(response.status).toBe(200);
    expect(bridge).toHaveBeenCalledWith(command, payload);
    await expect(response.json()).resolves.toEqual({ system: "x" });
  });

  it("answers 400 when local_api rejects the input (exit 2)", async () => {
    bridge.mockRejectedValue(
      new ClassifierBridgeError(VALIDATION_ERROR_LINE, 2, `${VALIDATION_ERROR_LINE}\n`),
    );

    const response = await POST(post(url, JSON.stringify({ profile: { roles: "bogus" } })));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({
      error: expect.stringContaining("validation error for SystemProfile"),
    });
  });

  it.each([
    { failure: "a timeout", error: new ClassifierBridgeError("classifier bridge timed out") },
    {
      failure: "a crash",
      error: new ClassifierBridgeError("Traceback", 1, "Traceback\nRuntimeError: boom\n"),
    },
    {
      failure: "uv failing before Python starts",
      error: new ClassifierBridgeError("error: Failed to spawn", 2, "error: Failed to spawn\n"),
    },
    { failure: "uv missing", error: new Error("spawn uv ENOENT") },
    { failure: "unreadable output", error: new SyntaxError("Unexpected token 'n'") },
  ])("answers 500 for $failure", async ({ error }) => {
    bridge.mockRejectedValue(error);

    const response = await POST(post(url, JSON.stringify(payload)));

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({ error: String(error) });
  });

  it("answers 400 for a request body that is not JSON, without running the bridge", async () => {
    const response = await POST(post(url, "{not json"));

    expect(response.status).toBe(400);
    expect(bridge).not.toHaveBeenCalled();
  });

  it("accepts a same-origin JSON POST from localhost with a charset", async () => {
    bridge.mockResolvedValue({ system: "x" });

    const response = await POST(
      post(url, JSON.stringify(payload), {
        host: "localhost:3000",
        origin: "http://localhost:3000",
        "content-type": "application/json; charset=utf-8",
      }),
    );

    expect(response.status).toBe(200);
    expect(bridge).toHaveBeenCalledWith(command, payload);
  });

  it("answers 415 for a text/plain body, without running the bridge", async () => {
    const response = await POST(post(url, JSON.stringify(payload), { "content-type": "text/plain" }));

    expect(response.status).toBe(415);
    expect(bridge).not.toHaveBeenCalled();
  });

  it.each<{ name: string; headers: Record<string, string> }>([
    {
      name: "a cross-site text/plain POST",
      headers: {
        origin: "https://evil.example",
        "sec-fetch-site": "cross-site",
        "content-type": "text/plain",
      },
    },
    {
      name: "a JSON POST from https://evil.example",
      headers: { origin: "https://evil.example", "sec-fetch-site": "cross-site" },
    },
    {
      name: "a DNS-rebound host",
      headers: { host: "evil.example:3000", origin: "http://evil.example:3000" },
    },
  ])("answers 403 for $name, without running the bridge", async ({ headers }) => {
    const response = await POST(post(url, JSON.stringify(payload), headers));

    expect(response.status).toBe(403);
    expect(bridge).not.toHaveBeenCalled();
  });
});
