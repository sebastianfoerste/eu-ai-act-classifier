import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ClassifierBridgeError } from "../../../lib/bridge-error";
import { runClassifierBridge } from "../../../lib/python";
import { GET, POST } from "./route";

vi.mock("../../../lib/python", () => ({
  runClassifierBridge: vi.fn(),
}));

const bridge = vi.mocked(runClassifierBridge);

const COCKPIT = "http://127.0.0.1:3000";

/** A POST as the self-assessment page sends it with fetch(); `headers` overrides single headers. */
function post(payload: unknown, headers: Record<string, string> = {}): Request {
  return new Request(`${COCKPIT}/api/collaboration`, {
    method: "POST",
    headers: {
      host: "127.0.0.1:3000",
      origin: COCKPIT,
      "sec-fetch-site": "same-origin",
      "content-type": "application/json",
      ...headers,
    },
    body: JSON.stringify(payload),
  });
}

describe("local collaboration workspace route", () => {
  beforeEach(() => {
    bridge.mockReset();
    vi.stubEnv("PORT", "3000");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("loads the persisted workspace through the Python application boundary", async () => {
    bridge.mockResolvedValue({ collaboration: { schema: "review.collaboration.v1" } });

    const response = await GET();

    expect(response.status).toBe(200);
    expect(bridge).toHaveBeenCalledWith("collaboration");
    await expect(response.json()).resolves.toMatchObject({
      collaboration: { schema: "review.collaboration.v1" },
    });
  });

  it("passes mutations to the versioned local workspace", async () => {
    bridge.mockResolvedValue({ collaboration: { cells: [{ revision: 2 }] } });
    const payload = { action: "comment", targetId: "factor:role", expectedRevision: 1 };

    const response = await POST(post(payload));

    expect(response.status).toBe(200);
    expect(bridge).toHaveBeenCalledWith("collaboration", payload);
  });

  it("preserves stale-write conflicts at the web boundary", async () => {
    bridge.mockRejectedValue(new Error("409 Conflict: stale review cell revision"));

    const response = await POST(post({ action: "lock", expectedRevision: 1 }));

    expect(response.status).toBe(409);
    await expect(response.json()).resolves.toMatchObject({ error: expect.stringContaining("409 Conflict") });
  });

  it("keeps the conflict status when the bridge reports it as rejected input", async () => {
    const line = JSON.stringify({ error: "409 Conflict: stale review cell revision" });
    bridge.mockRejectedValue(new ClassifierBridgeError(line, 2, `${line}\n`));

    const response = await POST(post({ action: "lock", expectedRevision: 1 }));

    expect(response.status).toBe(409);
  });

  it("answers 400 when local_api rejects the action (exit 2)", async () => {
    const line = JSON.stringify({ error: "unknown review cell: factor:missing" });
    bridge.mockRejectedValue(new ClassifierBridgeError(line, 2, `${line}\n`));

    const response = await POST(post({ action: "lock", targetId: "factor:missing", expectedRevision: 1 }));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({
      error: expect.stringContaining("unknown review cell"),
    });
  });

  it.each([
    { failure: "a timeout", error: new ClassifierBridgeError("classifier bridge timed out") },
    {
      failure: "a crash",
      error: new ClassifierBridgeError("Traceback", 1, "Traceback\nRuntimeError: boom\n"),
    },
  ])("answers 500 for $failure instead of blaming the request", async ({ error }) => {
    bridge.mockRejectedValue(error);

    const response = await POST(post({ action: "comment", targetId: "factor:role", expectedRevision: 1 }));

    expect(response.status).toBe(500);
  });

  it("answers 500 when loading the workspace fails", async () => {
    bridge.mockRejectedValue(new ClassifierBridgeError("classifier bridge timed out"));

    const response = await GET();

    expect(response.status).toBe(500);
  });

  it("accepts a same-origin JSON POST from localhost with a charset", async () => {
    bridge.mockResolvedValue({ collaboration: { cells: [] } });
    const payload = { action: "snapshot" };

    const response = await POST(
      post(payload, {
        host: "localhost:3000",
        origin: "http://localhost:3000",
        "content-type": "application/json; charset=utf-8",
      }),
    );

    expect(response.status).toBe(200);
    expect(bridge).toHaveBeenCalledWith("collaboration", payload);
  });

  it("answers 415 for a text/plain body, without touching the workspace", async () => {
    const response = await POST(
      post({ action: "review", targetId: "factor:role", expectedRevision: 1 }, {
        "content-type": "text/plain",
      }),
    );

    expect(response.status).toBe(415);
    expect(bridge).not.toHaveBeenCalled();
  });

  // The audit's two requests: a web page posted a reviewer override and then an
  // import that emptied the activity list, both as text/plain from another site.
  it.each<{ name: string; payload: unknown; headers: Record<string, string> }>([
    {
      name: "a cross-site text/plain override",
      payload: {
        action: "review",
        targetId: "factor:role",
        expectedRevision: 1,
        actor: "Senior Partner",
        reviewerOverride: "out_of_scope",
      },
      headers: {
        origin: "https://evil.example",
        "sec-fetch-site": "cross-site",
        "content-type": "text/plain",
      },
    },
    {
      name: "a cross-site text/plain import",
      payload: { action: "import", workspace: { activity: [] } },
      headers: {
        origin: "https://evil.example",
        "sec-fetch-site": "cross-site",
        "content-type": "text/plain",
      },
    },
    {
      name: "a JSON POST from https://evil.example",
      payload: { action: "snapshot" },
      headers: { origin: "https://evil.example", "sec-fetch-site": "cross-site" },
    },
    {
      name: "a DNS-rebound host",
      payload: { action: "import", workspace: { activity: [] } },
      headers: { host: "evil.example:3000", origin: "http://evil.example:3000" },
    },
  ])("answers 403 for $name, without touching the workspace", async ({ payload, headers }) => {
    const response = await POST(post(payload, headers));

    expect(response.status).toBe(403);
    expect(bridge).not.toHaveBeenCalled();
  });
});
