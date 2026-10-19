"""Re-render docs/demo.png from the real CLI output.

    uv run python scripts/render_demo_png.py

Runs the command the caption in docs/sample-output.md names, keeps the first
SHOWN_LINES output lines plus a cut marker that counts the lines left out, and
screenshots that text in a terminal frame with headless Chromium. Rendering
needs Node 22 and the `playwright` npm package with its Chromium (for example
`npm install -g playwright && npx playwright install chromium`); neither is a
project dependency.

The exact text drawn is stored in the PNG as an iTXt chunk, so
tests/test_docs.py can check the image's cut marker against the current CLI
output and the caption's line count without a browser.
"""

from __future__ import annotations

import html
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_PNG = ROOT / "docs" / "demo.png"
EXAMPLE = "examples/credit_scoring.json"
MODULE = "src.eu_ai_act_classifier.cli"
COMMAND = f"uv run python -m {MODULE} {EXAMPLE}"
SHOWN_LINES = 30
TEXT_KEYWORD = b"eu-ai-act-classifier terminal text"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><style>
html, body {{ margin: 0; background: #0d1117; }}
.window {{ width: 1100px; border: 1px solid #30363d; border-radius: 10px;
  background: #161b22; overflow: hidden; }}
.bar {{ height: 31px; padding: 0 14px; background: #21262d;
  border-bottom: 1px solid #30363d; color: #8b949e;
  font: 13px/31px "DejaVu Sans Mono", monospace; }}
pre {{ margin: 0; padding: 16px 18px; color: #dcdfe4; white-space: pre;
  font: 13.5px/1.45 "Liberation Mono", monospace; }}
.cmd {{ color: #7ee787; }}
</style></head><body><div class="window"><div class="bar">eu-ai-act-classifier</div>
<pre><span class="cmd">{command}</span>
{output}</pre></div></body></html>
"""

# Screenshots the .window element at device scale 2 (2204 px wide).
SCREENSHOT_JS = """
const { chromium } = require("playwright");
const [, , pagePath, outPath] = process.argv;
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1200, height: 800 },
    deviceScaleFactor: 2,
  });
  await page.goto("file://" + pagePath);
  await page.locator(".window").screenshot({ path: outPath });
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""


def cli_output() -> str:
    """The output of COMMAND, run from the repository root."""
    result = subprocess.run(
        [sys.executable, "-m", MODULE, EXAMPLE],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def terminal_text(output: str) -> str:
    """The text the image shows: the prompt, the first SHOWN_LINES lines, the cut marker."""
    lines = output.splitlines()
    shown = [f"$ {COMMAND}", *lines[:SHOWN_LINES]]
    hidden = len(lines) - SHOWN_LINES
    if hidden > 0:
        shown.append(f"[… {hidden} more lines not shown]")
    return "\n".join(shown)


def _chunks(png: bytes) -> list[tuple[bytes, bytes]]:
    if not png.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG file")
    chunks, offset = [], len(PNG_SIGNATURE)
    while offset < len(png):
        (length,) = struct.unpack(">I", png[offset : offset + 4])
        kind = png[offset + 4 : offset + 8]
        chunks.append((kind, png[offset + 8 : offset + 8 + length]))
        offset += 12 + length
    return chunks


def _chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def drawn_text(png: bytes) -> str | None:
    """The terminal text recorded in the PNG by with_drawn_text, or None."""
    for kind, data in _chunks(png):
        if kind != b"iTXt":
            continue
        keyword, _, rest = data.partition(b"\0")
        if keyword != TEXT_KEYWORD or rest[:2] != b"\0\0":
            continue
        _language, _, rest = rest[2:].partition(b"\0")
        _translated, _, text = rest.partition(b"\0")
        return text.decode("utf-8")
    return None


def with_drawn_text(png: bytes, text: str) -> bytes:
    """Record the drawn text in an uncompressed iTXt chunk just before IEND."""
    # keyword, separator, compression flag and method (none), empty language tag
    # and empty translated keyword, each NUL-terminated, then the UTF-8 text.
    data = TEXT_KEYWORD + b"\0" + b"\0\0" + b"\0" + b"\0" + text.encode("utf-8")
    out = [PNG_SIGNATURE]
    for kind, body in _chunks(png):
        if kind == b"iTXt" and body.partition(b"\0")[0] == TEXT_KEYWORD:
            continue
        if kind == b"IEND":
            out.append(_chunk(b"iTXt", data))
        out.append(_chunk(kind, body))
    return b"".join(out)


def _node_env() -> dict[str, str]:
    env = dict(os.environ)
    npm = shutil.which("npm")
    if "NODE_PATH" not in env and npm:
        root = subprocess.run([npm, "root", "-g"], capture_output=True, text=True, check=True)
        env["NODE_PATH"] = root.stdout.strip()
    return env


def render(text: str) -> bytes:
    """Screenshot the terminal frame showing text and return the PNG bytes."""
    command, _, output = text.partition("\n")
    page = PAGE.format(command=html.escape(command), output=html.escape(output))
    with tempfile.TemporaryDirectory() as tmp:
        page_path = Path(tmp) / "demo.html"
        script_path = Path(tmp) / "screenshot.cjs"
        out_path = Path(tmp) / "demo.png"
        page_path.write_text(page, encoding="utf-8")
        script_path.write_text(SCREENSHOT_JS, encoding="utf-8")
        subprocess.run(
            ["node", str(script_path), str(page_path), str(out_path)],
            check=True,
            env=_node_env(),
        )
        return out_path.read_bytes()


def main() -> int:
    output = cli_output()
    text = terminal_text(output)
    DEMO_PNG.write_bytes(with_drawn_text(render(text), text))
    total = len(output.splitlines())
    print(f"{DEMO_PNG.relative_to(ROOT)}: first {min(SHOWN_LINES, total)} of {total} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
