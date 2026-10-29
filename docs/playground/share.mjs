// Share links (ADR 0005). The profile travels in the URL fragment, which the
// browser keeps out of HTTP requests and the Referer header. Encoding is not
// encryption: anyone with the link can read the profile.
import { MAX_BYTES } from "./model.mjs";

export const SHARE_LIMIT = 8000;
const COMPRESSED = "p1.";
const PLAIN = "j1.";
const BASE64URL = /^[A-Za-z0-9_-]*$/;

export class ShareError extends Error {}

export function isShareFragment(hash) {
  return /^#?[a-z]\d+\./.test(hash ?? "");
}

function toBase64Url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

function fromBase64Url(text) {
  let binary;
  try {
    if (!BASE64URL.test(text) || text.length % 4 === 1) throw new Error();
    binary = atob(text.replaceAll("-", "+").replaceAll("_", "/"));
  } catch { throw new ShareError("The share link is damaged. Ask for a new one."); }
  return Uint8Array.from(binary, char => char.charCodeAt(0));
}

// Reads a transformed stream, refusing output above `limit` bytes so a small
// link cannot expand into an oversized profile.
async function transform(bytes, stream, limit = Infinity) {
  const reader = new Blob([bytes]).stream().pipeThrough(stream).getReader();
  const chunks = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.length;
    if (size > limit) {
      await reader.cancel();
      throw new ShareError("The shared profile is larger than the 1 MB playground limit.");
    }
    chunks.push(value);
  }
  const out = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { out.set(chunk, offset); offset += chunk.length; }
  return out;
}

// Returns the fragment, without "#", for a profile object. Compresses where
// the browser can, else falls back to plain base64url JSON.
export async function encodeShare(profile, { compress = typeof CompressionStream === "function" } = {}) {
  const json = new TextEncoder().encode(JSON.stringify(profile));
  const fragment = compress
    ? COMPRESSED + toBase64Url(await transform(json, new CompressionStream("deflate-raw")))
    : PLAIN + toBase64Url(json);
  if (fragment.length > SHARE_LIMIT) {
    throw new ShareError(`This profile is too long for a share link (${fragment.length.toLocaleString("en")} characters, limit ${SHARE_LIMIT.toLocaleString("en")}). Save the profile JSON and send the file instead.`);
  }
  return fragment;
}

// Returns the profile JSON text a fragment carries. The caller validates it
// like any pasted profile before use.
export async function decodeShare(hash) {
  const fragment = (hash ?? "").replace(/^#/, "");
  if (fragment.length > SHARE_LIMIT) throw new ShareError(`The share link is longer than ${SHARE_LIMIT.toLocaleString("en")} characters, so it was not opened.`);
  let bytes;
  if (fragment.startsWith(COMPRESSED)) {
    if (typeof DecompressionStream !== "function") throw new ShareError("This browser cannot open compressed share links. Open the link in a current browser.");
    try { bytes = await transform(fromBase64Url(fragment.slice(COMPRESSED.length)), new DecompressionStream("deflate-raw"), MAX_BYTES); }
    catch (error) { throw error instanceof ShareError ? error : new ShareError("The share link is damaged. Ask for a new one."); }
  } else if (fragment.startsWith(PLAIN)) {
    bytes = fromBase64Url(fragment.slice(PLAIN.length));
    if (bytes.length > MAX_BYTES) throw new ShareError("The shared profile is larger than the 1 MB playground limit.");
  } else {
    throw new ShareError("This share link comes from a newer or unknown version of the playground.");
  }
  try { return new TextDecoder("utf-8", { fatal: true }).decode(bytes); }
  catch { throw new ShareError("The share link is damaged. Ask for a new one."); }
}
