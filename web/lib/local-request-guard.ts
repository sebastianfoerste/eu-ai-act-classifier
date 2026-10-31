/**
 * Guard for the cockpit's POST routes: same-origin JSON from the loopback address only.
 *
 * The cockpit is a local tool. Its POST routes run the Python bridge, and
 * /api/collaboration writes reviewer names, overrides and comments to runtime-data/.
 * Any web page the reviewer has open could otherwise post to them:
 *
 * - A cross-site form or fetch with a CORS-safelisted Content-Type (text/plain, a form
 *   encoding) needs no preflight, and Request.json() parses a text/plain body. Only
 *   application/json is accepted, so such a request answers 415.
 * - A browser marks a request from another site with Sec-Fetch-Site and Origin. Anything
 *   but a same-origin request answers 403.
 * - A DNS-rebound name resolves to 127.0.0.1 and makes the page's requests same-origin,
 *   but the browser still sends that name as Host and Origin. Host and Origin must name
 *   localhost or 127.0.0.1 at the port the server listens on, so such a request answers
 *   403 too.
 *
 * A client outside the browser, such as curl, sends no Origin or Sec-Fetch-Site and is
 * judged by Host and Content-Type alone.
 */

const LOOPBACK_HOSTNAMES = ["localhost", "127.0.0.1"] as const;
/** Next's default port. `next dev` and `next start` set PORT to the port they listen on. */
const DEFAULT_PORT = "3000";
/** Sec-Fetch-Site values a request from the cockpit's own page can carry. */
const SAME_ORIGIN_FETCH_SITES = new Set(["same-origin", "none"]);

/**
 * Returns the error response for a POST the cockpit must not act on, or null to proceed.
 *
 * Call it first in every POST route, before the body is read.
 */
export function rejectUnsafeLocalPost(request: Request): Response | null {
  const reason = crossSiteReason(request, process.env.PORT || DEFAULT_PORT);
  if (reason) {
    return Response.json({ error: `Forbidden: ${reason}` }, { status: 403 });
  }
  if (mediaType(request.headers.get("content-type")) !== "application/json") {
    return Response.json(
      { error: "Unsupported Media Type: send the request body as application/json" },
      { status: 415 },
    );
  }
  return null;
}

function crossSiteReason(request: Request, port: string): string | null {
  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite !== null && !SAME_ORIGIN_FETCH_SITES.has(fetchSite.trim().toLowerCase())) {
    return `the cockpit accepts same-origin requests only (Sec-Fetch-Site: ${fetchSite})`;
  }
  const host = (request.headers.get("host") ?? new URL(request.url).host).toLowerCase();
  if (!localHosts(port).includes(host)) {
    return `the cockpit answers on ${localHosts(port).join(" and ")} only`;
  }
  const origin = request.headers.get("origin");
  if (origin !== null && !localOrigins(port).includes(origin.toLowerCase())) {
    return `the cockpit accepts requests from ${localOrigins(port).join(" and ")} only`;
  }
  return null;
}

/** The Host values a browser sends for the loopback names; it leaves out port 80. */
function localHosts(port: string): string[] {
  return LOOPBACK_HOSTNAMES.map((hostname) => (port === "80" ? hostname : `${hostname}:${port}`));
}

function localOrigins(port: string): string[] {
  return localHosts(port).map((host) => `http://${host}`);
}

function mediaType(contentType: string | null): string | null {
  return contentType?.split(";")[0].trim().toLowerCase() || null;
}
