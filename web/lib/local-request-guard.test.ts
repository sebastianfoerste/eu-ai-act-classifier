import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import packageJson from "../package.json";
import { rejectUnsafeLocalPost } from "./local-request-guard";

type HeaderMap = Record<string, string>;
type Case = { name: string; headers: HeaderMap };

/** A POST as the cockpit page at http://127.0.0.1:3000 sends it with fetch(). */
function cockpitPost(headers: HeaderMap = {}, url = "http://127.0.0.1:3000/api/classify"): Request {
  return new Request(url, {
    method: "POST",
    headers: {
      host: "127.0.0.1:3000",
      origin: "http://127.0.0.1:3000",
      "sec-fetch-site": "same-origin",
      "content-type": "application/json",
      ...headers,
    },
    body: "{}",
  });
}

describe("rejectUnsafeLocalPost", () => {
  beforeEach(() => {
    vi.stubEnv("PORT", "3000");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it.each<Case>([
    { name: "the cockpit on 127.0.0.1", headers: {} },
    {
      name: "the cockpit on localhost",
      headers: { host: "localhost:3000", origin: "http://localhost:3000" },
    },
    { name: "a JSON charset parameter", headers: { "content-type": "application/json; charset=utf-8" } },
    { name: "an upper-case media type", headers: { "content-type": "Application/JSON" } },
  ])("lets a same-origin JSON POST from $name through", ({ headers }) => {
    expect(rejectUnsafeLocalPost(cockpitPost(headers))).toBeNull();
  });

  it("lets a local client without Origin or Sec-Fetch-Site through, as curl sends it", () => {
    const request = new Request("http://127.0.0.1:3000/api/classify", {
      method: "POST",
      headers: { host: "127.0.0.1:3000", "content-type": "application/json" },
      body: "{}",
    });

    expect(rejectUnsafeLocalPost(request)).toBeNull();
  });

  it.each([
    { name: "text/plain", contentType: "text/plain" },
    { name: "text/plain with a charset", contentType: "text/plain;charset=UTF-8" },
    { name: "a form encoding", contentType: "application/x-www-form-urlencoded" },
    { name: "a multipart form", contentType: "multipart/form-data; boundary=x" },
    { name: "a JSON-like media type", contentType: "application/json-patch+json" },
  ])("answers 415 for $name", async ({ contentType }) => {
    const response = rejectUnsafeLocalPost(cockpitPost({ "content-type": contentType }));

    expect(response?.status).toBe(415);
    await expect(response?.json()).resolves.toMatchObject({
      error: expect.stringContaining("application/json"),
    });
  });

  it("answers 415 when the Content-Type is missing", () => {
    const request = new Request("http://127.0.0.1:3000/api/classify", {
      method: "POST",
      headers: { host: "127.0.0.1:3000", origin: "http://127.0.0.1:3000" },
      body: new TextEncoder().encode("{}"),
    });

    expect(rejectUnsafeLocalPost(request)?.status).toBe(415);
  });

  it.each<Case>([
    { name: "a cross-site fetch", headers: { "sec-fetch-site": "cross-site" } },
    { name: "a same-site fetch from another port", headers: { "sec-fetch-site": "same-site" } },
    { name: "a foreign Origin", headers: { origin: "https://evil.example" } },
    { name: "an opaque Origin", headers: { origin: "null" } },
    { name: "an Origin on another local port", headers: { origin: "http://127.0.0.1:4000" } },
    { name: "an Origin with another scheme", headers: { origin: "https://127.0.0.1:3000" } },
    {
      name: "a DNS-rebound host",
      headers: { host: "evil.example:3000", origin: "http://evil.example:3000" },
    },
    { name: "a Host on another port", headers: { host: "127.0.0.1:4000" } },
    { name: "a network address as Host", headers: { host: "192.0.2.2:3000" } },
    { name: "a Host with user info", headers: { host: "evil.example@127.0.0.1:3000" } },
  ])("answers 403 for $name", async ({ headers }) => {
    const response = rejectUnsafeLocalPost(cockpitPost(headers));

    expect(response?.status).toBe(403);
    await expect(response?.json()).resolves.toMatchObject({ error: expect.any(String) });
  });

  it("answers 403, not 415, for the cross-site text/plain POST a web page can send", () => {
    const response = rejectUnsafeLocalPost(
      cockpitPost({
        origin: "https://evil.example",
        "sec-fetch-site": "cross-site",
        "content-type": "text/plain",
      }),
    );

    expect(response?.status).toBe(403);
  });

  it("checks Host and Origin against the port the server listens on", () => {
    vi.stubEnv("PORT", "3917");

    expect(
      rejectUnsafeLocalPost(
        cockpitPost(
          { host: "127.0.0.1:3917", origin: "http://127.0.0.1:3917" },
          "http://127.0.0.1:3917/api/classify",
        ),
      ),
    ).toBeNull();
    expect(rejectUnsafeLocalPost(cockpitPost())?.status).toBe(403);
  });

  it("uses Next's default port 3000 when PORT is unset", () => {
    vi.stubEnv("PORT", undefined);

    expect(rejectUnsafeLocalPost(cockpitPost())).toBeNull();
    expect(
      rejectUnsafeLocalPost(cockpitPost({ host: "127.0.0.1:3917", origin: "http://127.0.0.1:3917" }))
        ?.status,
    ).toBe(403);
  });

  it("falls back to the request URL when no Host header is set", () => {
    const local = new Request("http://localhost:3000/api/classify", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{}",
    });
    const foreign = new Request("http://evil.example:3000/api/classify", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{}",
    });

    expect(rejectUnsafeLocalPost(local)).toBeNull();
    expect(rejectUnsafeLocalPost(foreign)?.status).toBe(403);
  });
});

describe("cockpit server scripts", () => {
  // next dev and next start bind 0.0.0.0 unless told otherwise, which puts the
  // routes on every network the machine joins.
  it.each(["dev", "start"] as const)("binds `npm run %s` to the loopback address", (script) => {
    expect(packageJson.scripts[script].split(/\s+/)).toEqual(
      expect.arrayContaining(["-H", "127.0.0.1"]),
    );
    expect(packageJson.scripts[script]).toMatch(/(^|\s)-H 127\.0\.0\.1(\s|$)/);
  });
});
