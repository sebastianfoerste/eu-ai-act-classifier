# 0005 URL state encoding

Status: Proposed

## Context

Playgrounds share state either in the URL hash (TypeScript with a compression library, Svelte with the browser's native compression) or through a server. The playground must stay static, and "nothing you paste leaves the page" must stay true.

## Decision

On "Create share link" only, serialise the compact profile, compress it with `CompressionStream("deflate-raw")`, encode it as base64url and write `#p1.<data>` with `history.replaceState`. Fall back to plain base64url JSON (`#j1.`) where compression is unavailable. Refuse above 8,000 characters and offer a JSON download. On load, decode and validate before use and never classify automatically. Next to the button, warn that browser history sync and chat services keep links and that encoding is not encryption.

## Consequences

- No server and no dependency; supported in current Chromium, Firefox and Safari.
- The fragment is not sent in HTTP requests or the Referer header, but it is visible in browser history.
