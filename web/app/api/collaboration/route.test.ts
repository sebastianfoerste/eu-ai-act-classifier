import { beforeEach, describe, expect, it, vi } from "vitest";

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
});
