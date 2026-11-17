import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { GET } from "./route";

/** The path the Python bridge writes the collaboration workspace to, read from its source. */
function collaborationStore(): string | undefined {
  const localApi = readFileSync(
    new URL("../../../../src/eu_ai_act_classifier/local_api.py", import.meta.url),
    "utf8",
  );
  return localApi.match(/Path\("(runtime-data\/[^"]+)"\)/)?.[1];
}

describe("GET /api/health", () => {
  it("names the file the collaboration bridge writes instead of claiming in-memory state", async () => {
    const store = collaborationStore();
    expect(store).toBe("runtime-data/collaboration-workspace.json");

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      status: "ok",
      service: "eu-ai-act-classifier-web",
      persistence: "local_file",
      store,
    });
  });
});
