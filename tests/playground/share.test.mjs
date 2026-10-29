import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { SHARE_LIMIT, ShareError, decodeShare, encodeShare, isShareFragment } from "../../docs/playground/share.mjs";

const { profiles } = JSON.parse(readFileSync(new URL("../../docs/playground/samples.json", import.meta.url), "utf8"));

async function deflated(bytes) {
  return new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream("deflate-raw"))).arrayBuffer());
}
const base64url = bytes => Buffer.from(bytes).toString("base64url");

test("every bundled example round-trips through a short compressed link", async () => {
  for (const [key, profile] of Object.entries(profiles)) {
    const fragment = await encodeShare(profile);
    assert.ok(fragment.startsWith("p1."), key);
    assert.ok(fragment.length < 400, `${key}: ${fragment.length} characters`);
    assert.ok(isShareFragment(`#${fragment}`), key);
    assert.deepEqual(JSON.parse(await decodeShare(`#${fragment}`)), profile, key);
  }
});

test("the plain fallback round-trips where compression is unavailable", async () => {
  const profile = { name: "Zoë's système ✓", roles: ["deployer"] };
  const fragment = await encodeShare(profile, { compress: false });
  assert.ok(fragment.startsWith("j1."));
  assert.deepEqual(JSON.parse(await decodeShare(fragment)), profile);
});

test("only versioned fragments count as share links", async () => {
  for (const hash of ["", "#", "#workspace", "#results-heading"]) assert.equal(isShareFragment(hash), false, hash);
  await assert.rejects(decodeShare("#p9.AAAA"), ShareError);
  await assert.rejects(decodeShare("#x1.AAAA"), /unknown version/);
});

test("links above the size cap are refused both ways", async () => {
  // Random text does not compress, so the link outgrows the cap.
  let seed = 1;
  const noise = Array.from({ length: 9000 }, () => String.fromCharCode(33 + ((seed = (seed * 48271) % 2147483647) % 90))).join("");
  await assert.rejects(encodeShare({ name: "Long", description: noise }), error => error instanceof ShareError && /8,000/.test(error.message));
  await assert.rejects(decodeShare(`#j1.${"A".repeat(SHARE_LIMIT)}`), /longer than 8,000/);
});

test("damaged links are refused with a plain message", async () => {
  const good = await encodeShare(profiles.credit_scoring);
  for (const bad of ["#p1.@@@@", "#p1.A", `#${good.slice(0, -12)}`, "#j1.!!", `#j1.${base64url(Uint8Array.of(0xff, 0xfe))}`]) {
    await assert.rejects(decodeShare(bad), error => error instanceof ShareError && /damaged/.test(error.message), bad);
  }
});

test("a small link cannot expand past the 1 MB profile limit", async () => {
  const bomb = await deflated(new TextEncoder().encode(`{"name":"x","description":"${" ".repeat(2 * 1024 * 1024)}"}`));
  const fragment = `p1.${base64url(bomb)}`;
  assert.ok(fragment.length < SHARE_LIMIT);
  await assert.rejects(decodeShare(fragment), /1 MB/);
});

test("decoding returns text for the caller to validate, not a parsed object", async () => {
  const fragment = `j1.${base64url(new TextEncoder().encode("[1, 2]"))}`;
  assert.equal(await decodeShare(fragment), "[1, 2]");
});
