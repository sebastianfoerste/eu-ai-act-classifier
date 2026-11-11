"""Compare the source snapshots in sources/ with the EUR-Lex rendition of the same text.

The snapshots are byte-exact Publications Office responses. EUR-Lex serves the same
documents with a different <head> (stylesheet path, meta tags), so the bytes differ while
the text does not. This script reduces both to their body text and compares the digests:

    uv run python scripts/compare_sources.py            # fetch each eurlex_check.url
    uv run python scripts/compare_sources.py --offline  # only recompute the recorded digests

Exit 0: every text is identical. Exit 1: a text differs, review required. Exit 2: nothing
differs, but a source could not be compared (network failure, or EUR-Lex answered with a
bot challenge). An answer that is not the document never counts as a match. The script
never writes to sources/ and is not part of CI: it needs the network.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from eu_ai_act_classifier.verify_sources import (
    CHALLENGE_READ_BYTES,
    HEADERS,
    BotChallengeError,
    challenge_marker,
)

SOURCES = Path(__file__).resolve().parents[1] / "sources"
IDENTICAL, DIFFERS, UNVERIFIED = "identical", "differs", "unverified"
TIMEOUT_SECONDS = 60

_HEAD = re.compile(r"<head\b.*?</head>", re.DOTALL | re.IGNORECASE)
_NOT_TEXT = re.compile(r"<(script|style)\b.*?</\1>", re.DOTALL | re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")


def body_text(data: bytes) -> str:
    """The text of a document without its <head>, scripts, styles and markup, with
    character references resolved and whitespace collapsed. Two renditions of one legal
    text that differ only in presentation reduce to the same string."""

    text = data.decode("utf-8")
    text = _TAG.sub(" ", _NOT_TEXT.sub(" ", _HEAD.sub(" ", text)))
    return " ".join(html.unescape(text).split())


def text_sha256(data: bytes) -> str:
    return hashlib.sha256(body_text(data).encode("utf-8")).hexdigest()


def fetch(url: str) -> bytes:
    """The document at ``url``. Raises BotChallengeError for a 202 or a challenge page."""

    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        data = response.read()
        marker = challenge_marker(response.headers, data[:CHALLENGE_READ_BYTES])
        if response.status == 202 or marker:
            raise BotChallengeError(response.status, marker or "202 Accepted")
    return data


def compare(
    entries: list[dict], fetch: Callable[[str], bytes] | None = fetch
) -> list[tuple[str, str, str]]:
    """(source_id, outcome, detail) per entry. Without ``fetch`` only the recorded digest
    is recomputed from the snapshot."""

    results = []
    for entry in entries:
        check = entry["eurlex_check"]
        local = text_sha256((SOURCES / entry["file"]).read_bytes())
        if local != check["text_sha256"]:
            detail = "the snapshot's text no longer has the recorded text_sha256"
            results.append((entry["source_id"], DIFFERS, detail))
            continue
        if fetch is None:
            results.append((entry["source_id"], IDENTICAL, "recorded text_sha256 recomputed"))
            continue
        try:
            remote = text_sha256(fetch(check["url"]))
        except BotChallengeError as error:
            results.append((entry["source_id"], UNVERIFIED, str(error)))
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as error:
            results.append((entry["source_id"], UNVERIFIED, f"not fetched: {error}"))
        else:
            outcome = IDENTICAL if remote == local else DIFFERS
            detail = (
                "body text identical to EUR-Lex"
                if outcome == IDENTICAL
                else "content changed, review required"
            )
            results.append((entry["source_id"], outcome, detail))
    return results


def exit_code(results: list[tuple[str, str, str]]) -> int:
    outcomes = {outcome for _, outcome, _ in results}
    if DIFFERS in outcomes:
        return 1
    return 2 if UNVERIFIED in outcomes else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--offline", action="store_true", help="recompute the recorded digests, fetch nothing"
    )
    args = parser.parse_args(argv)
    entries = json.loads((SOURCES / "manifest.json").read_text(encoding="utf-8"))["sources"]
    results = compare(entries, None if args.offline else fetch)
    for source_id, outcome, detail in results:
        print(f"{outcome:<10} {source_id}: {detail}")
    return exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
