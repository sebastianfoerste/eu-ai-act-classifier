import { beforeEach, describe, expect, it, vi } from "vitest";

import { ClassifierBridgeError } from "../../../lib/bridge-error";
import { runClassifierBridge } from "../../../lib/python";
import { GET, POST } from "./route";

vi.mock("../../../lib/python", () => ({
  runClassifierBridge: vi.fn(),
}));

const bridge = vi.mocked(runClassifierBridge);

describe("local collaboration workspace route", () => {
  beforeEach(() => {
    bridge.mockReset();
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

    const response = await POST(new Request("http://local/api/collaboration", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    }));

    expect(response.status).toBe(200);
    expect(bridge).toHaveBeenCalledWith("collaboration", payload);
  });

  it("preserves stale-write conflicts at the web boundary", async () => {
    bridge.mockRejectedValue(new Error("409 Conflict: stale review cell revision"));

    const response = await POST(new Request("http://local/api/collaboration", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "lock", expectedRevision: 1 }),
    }));

    expect(response.status).toBe(409);
    await expect(response.json()).resolves.toMatchObject({ error: expect.stringContaining("409 Conflict") });
  });

  it("keeps the conflict status when the bridge reports it as rejected input", async () => {
    const line = JSON.stringify({ error: "409 Conflict: stale review cell revision" });
    bridge.mockRejectedValue(new ClassifierBridgeError(line, 2, `${line}\n`));

    const response = await POST(new Request("http://local/api/collaboration", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "lock", expectedRevision: 1 }),
    }));

    expect(response.status).toBe(409);
  });

  it("answers 400 when local_api rejects the action (exit 2)", async () => {
    const line = JSON.stringify({ error: "unknown review cell: factor:missing" });
    bridge.mockRejectedValue(new ClassifierBridgeError(line, 2, `${line}\n`));

    const response = await POST(new Request("http://local/api/collaboration", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "lock", targetId: "factor:missing", expectedRevision: 1 }),
    }));

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

    const response = await POST(new Request("http://local/api/collaboration", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "comment", targetId: "factor:role", expectedRevision: 1 }),
    }));

    expect(response.status).toBe(500);
  });

  it("answers 500 when loading the workspace fails", async () => {
    bridge.mockRejectedValue(new ClassifierBridgeError("classifier bridge timed out"));

    const response = await GET();

    expect(response.status).toBe(500);
  });
});
