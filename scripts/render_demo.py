"""Render docs/demo.png from real CLI output with headless Chrome.

    uv run python scripts/render_demo.py

Runs the CLI on examples/credit_scoring.json, lays the text out as a terminal
window that wraps at a fixed column like a terminal does, and screenshots it.
Needs Google Chrome or Chromium; set CHROME to its path if it is not on PATH.
No test compares the drawn text with the CLI output, so rerun this whenever the
CLI text changes. tests/test_docs.py only checks that the image has the size
window_size gives for the current output, which catches a change in the number
of wrapped lines but not a change of text within a line.
"""

from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "demo.png"
COMMAND = ["eu-ai-act-classify", "examples/credit_scoring.json"]

# Seconds before a stuck CLI run or browser is killed, so the script cannot hang.
TIMEOUT_S = 120
COLUMNS = 120
FONT_PX = 13
LINE_PX = 18
CHAR_PX = 0.6 * FONT_PX  # advance width of Liberation Mono and DejaVu Sans Mono
PAD_PX = 20
TITLE_PX = 32

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><style>
html, body {{ margin: 0; background: #0d1117; }}
.window {{ margin: 0; border: 1px solid #30363d; border-radius: 10px; overflow: hidden;
  background: #161b22; }}
.title {{ height: {title}px; background: #21262d; color: #8b949e;
  font: 12px/{title}px "Liberation Sans", "DejaVu Sans", sans-serif; text-align: center; }}
pre {{ margin: 0; padding: {pad}px; color: #dcdfe4; white-space: pre;
  font: {font}px/{line}px "Liberation Mono", "DejaVu Sans Mono", monospace; }}
.prompt {{ color: #7ee787; }}
</style></head><body><div class="window"><div class="title">{title_text}</div>
<pre><span class="prompt">$ {command}</span>
{body}</pre></div></body></html>
"""


def _wrap(text: str) -> list[str]:
    """Hard-wrap at COLUMNS characters, as a terminal of that width shows it."""

    lines: list[str] = []
    for line in text.splitlines():
        lines.extend(line[i : i + COLUMNS] for i in range(0, max(len(line), 1), COLUMNS))
    return lines


def terminal_lines(output: str) -> list[str]:
    """The lines drawn below the prompt: the CLI output, hard-wrapped at COLUMNS."""

    return _wrap(output.rstrip("\n"))


def window_size(lines: list[str]) -> tuple[int, int]:
    """Width and height in pixels of the screenshot that shows the prompt and ``lines``."""

    width = round(COLUMNS * CHAR_PX) + 2 * PAD_PX + 2
    height = TITLE_PX + (len(lines) + 1) * LINE_PX + 2 * PAD_PX + 2
    return width, height


def _chrome() -> str:
    for name in (os.environ.get("CHROME"), "google-chrome", "chromium", "chromium-browser"):
        if name and (path := shutil.which(name)):
            return path
    raise SystemExit("Chrome not found; set CHROME to the browser binary")


def main() -> int:
    output = subprocess.run(
        ["uv", "run", *COMMAND],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S,
    ).stdout
    lines = terminal_lines(output)
    command = " ".join(COMMAND)
    page = PAGE.format(
        title=TITLE_PX,
        pad=PAD_PX,
        font=FONT_PX,
        line=LINE_PX,
        title_text=html.escape(command),
        command=html.escape(command),
        body=html.escape("\n".join(lines)),
    )
    width, height = window_size(lines)
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "demo.html"
        source.write_text(page, encoding="utf-8")
        subprocess.run(
            [
                _chrome(),
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                f"--window-size={width},{height}",
                f"--screenshot={OUT}",
                source.as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=TIMEOUT_S,
        )
    print(f"wrote {OUT.relative_to(ROOT)} ({width}x{height}, {len(lines)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
