/**
 * Guards for the cockpit's API routes: same-origin requests to the loopback address only,
 * and for POST routes JSON bodies only.
 *
 * The cockpit is a local tool. Its POST routes run the Python bridge, and
 * /api/collaboration writes reviewer names, overrides and comments, and the obligation
 * tracker's evidence states, owners and reviewed-on dates, to runtime-data/.
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
 * The same rebinding lets a page read what a GET route returns, so the routes that
 * return the inventory, the review workspace (reviewer names, overrides, comments,
 * evidence states, owners and reviewed-on dates) or other bridge output call
 * rejectUnsafeLocalRead, which applies the Sec-Fetch-Site, Host and Origin checks
 * without the body check. The /self-assessment page renders the workspace per request,
 * so it applies the same checks to its own request headers through unsafeLocalReadReason.
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
  const reason = requestReason(request);
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

/**
 * Returns the 403 response for a GET the cockpit must not answer, or null to proceed.
 *
 * Call it first in every GET route that returns bridge output.
 */
export function rejectUnsafeLocalRead(request: Request): Response | null {
  const reason = requestReason(request);
  return reason ? Response.json({ error: `Forbidden: ${reason}` }, { status: 403 }) : null;
}

/**
 * Why a read with these request headers must not be answered, or null to proceed: the
 * Sec-Fetch-Site, Host and Origin checks of rejectUnsafeLocalRead, for a server-rendered
 * page, which has the headers (next/headers) but no Request. A missing Host fails.
 */
export function unsafeLocalReadReason(headers: Pick<Headers, "get">): string | null {
  return crossSiteReason(headers, "", process.env.PORT || DEFAULT_PORT);
}

function requestReason(request: Request): string | null {
  return crossSiteReason(request.headers, new URL(request.url).host, process.env.PORT || DEFAULT_PORT);
}

function crossSiteReason(headers: Pick<Headers, "get">, fallbackHost: string, port: string): string | null {
  const fetchSite = headers.get("sec-fetch-site");
  if (fetchSite !== null && !SAME_ORIGIN_FETCH_SITES.has(fetchSite.trim().toLowerCase())) {
    return `the cockpit accepts same-origin requests only (Sec-Fetch-Site: ${fetchSite})`;
  }
  const host = (headers.get("host") ?? fallbackHost).toLowerCase();
  if (!localHosts(port).includes(host)) {
    return `the cockpit answers on ${localHosts(port).join(" and ")} only`;
  }
  const origin = headers.get("origin");
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
