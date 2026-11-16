"""Compare the source snapshots in sources/ with the EUR-Lex rendition of the same text.

The snapshots are byte-exact Publications Office responses. EUR-Lex serves the same
documents with presentation changes: meta tags and stylesheet links in the <head>, scripts
appended to the <body>, link and image targets rewritten to EUR-Lex paths, and a class
added to some tables. The bytes differ while no text node does. This script reduces both
renditions to two forms and compares their digests:

- the body text: <head>, scripts, styles and markup removed, character references
  resolved, whitespace collapsed;
- the structure: the same, but every element boundary kept as a marker with the element
  name, so a lost superscript, merged paragraphs or a moved table cell also differ. The
  attributes EUR-Lex rewrites (href, src, class) and all others are left out.

    uv run python scripts/compare_sources.py            # fetch each eurlex_check.url
    uv run python scripts/compare_sources.py --offline  # only recompute the recorded digests

Exit 0: every text and structure is identical to EUR-Lex (online), or every snapshot still
has its recorded digests (--offline, which compares nothing with EUR-Lex). Exit 1: a text
or structure differs, or a snapshot lost its recorded digest: review required. Exit 2:
nothing differs, but a source could not be compared (a network failure, a bot challenge,
or an answer that is not a complete document). An answer that is not the document never
counts as a match. The script never writes to sources/ and is not part of CI: it needs the
network.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import http.client
import json
import re
import urllib.request
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path
from typing import ClassVar

from eu_ai_act_classifier.verify_sources import (
    CHALLENGE_READ_BYTES,
    HEADERS,
    BotChallengeError,
    challenge_marker,
)

SOURCES = Path(__file__).resolve().parents[1] / "sources"
IDENTICAL, RECORDED, DIFFERS, UNVERIFIED = "identical", "recorded", "differs", "unverified"
TIMEOUT_SECONDS = 60

_HEAD = re.compile(r"<head\b.*?</head>", re.DOTALL | re.IGNORECASE)
_NOT_TEXT = re.compile(r"<(script|style)\b.*?</\1>", re.DOTALL | re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")


class NotADocumentError(Exception):
    """A 200 answer that is not a complete HTML document, so nothing can be compared."""


def body_text(data: bytes) -> str:
    """The text of a document without its <head>, scripts, styles and markup, with
    character references resolved and whitespace collapsed. Two renditions of one legal
    text that differ only in presentation reduce to the same string."""

    text = data.decode("utf-8")
    text = _TAG.sub(" ", _NOT_TEXT.sub(" ", _HEAD.sub(" ", text)))
    return " ".join(html.unescape(text).split())


class _Structure(HTMLParser):
    """Element boundaries and text nodes of the <body>, without attributes, scripts or
    styles. ``tokens`` holds "<name", ">name" and the whitespace-collapsed text."""

    _SKIP: ClassVar[set[str]] = {"head", "script", "style"}
    _VOID: ClassVar[set[str]] = {"br", "img", "hr", "meta", "link", "input", "col", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[str] = []
        self._skipping: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if self._skipping or tag in self._SKIP:
            if tag in self._SKIP:
                self._skipping.append(tag)
            return
        self.tokens.append(f"<{tag}")
        if tag in self._VOID:
            self.tokens.append(f">{tag}")

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        if not self._skipping and tag not in self._SKIP:
            self.tokens += [f"<{tag}", f">{tag}"]

    def handle_endtag(self, tag: str) -> None:
        if self._skipping:
            if tag == self._skipping[-1]:
                self._skipping.pop()
            return
        if tag not in self._VOID:
            self.tokens.append(f">{tag}")

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text and not self._skipping:
            self.tokens.append(text)


def structure(data: bytes) -> str:
    """The body's element names and text nodes in document order, one per line."""

    parser = _Structure()
    parser.feed(data.decode("utf-8"))
    parser.close()
    return "\n".join(parser.tokens)


def text_sha256(data: bytes) -> str:
    return hashlib.sha256(body_text(data).encode("utf-8")).hexdigest()


def structure_sha256(data: bytes) -> str:
    return hashlib.sha256(structure(data).encode("utf-8")).hexdigest()


def is_complete_document(data: bytes) -> bool:
    """Whether an answer looks like a whole HTML document: it has a <body> and ends with
    the closing </html> tag, so an error stub or a cut-off transfer is not compared."""

    head, tail = data[:CHALLENGE_READ_BYTES].lower(), data.rstrip()[-64:].lower()
    return b"<body" in data.lower() and tail.endswith(b"</html>") and b"<html" in head


def fetch(url: str) -> bytes:
    """The document at ``url``. Raises BotChallengeError for a 202 or a challenge page and
    NotADocumentError for an answer that is not a complete HTML document."""

    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        data = response.read()
        marker = challenge_marker(response.headers, data[:CHALLENGE_READ_BYTES])
        if response.status == 202 or marker:
            raise BotChallengeError(response.status, marker or "202 Accepted")
    if not is_complete_document(data):
        raise NotADocumentError(f"the answer ({len(data)} bytes) is not a complete document")
    return data


def _recorded(entry: dict) -> str | None:
    """Why a snapshot no longer has its recorded digests, or None."""

    check, data = entry["eurlex_check"], (SOURCES / entry["file"]).read_bytes()
    if text_sha256(data) != check["text_sha256"]:
        return "the snapshot's text no longer has the recorded text_sha256"
    if structure_sha256(data) != check["structure_sha256"]:
        return "the snapshot's structure no longer has the recorded structure_sha256"
    return None


# Errors that mean "not compared": a network failure (OSError covers URLError, timeouts
# and dropped connections), a malformed or cut-off HTTP answer, or a page that is not text.
_NOT_COMPARED = (
    BotChallengeError,
    NotADocumentError,
    OSError,
    http.client.HTTPException,
    UnicodeDecodeError,
)


def compare(
    entries: list[dict], fetch: Callable[[str], bytes] | None = fetch
) -> list[tuple[str, str, str]]:
    """(source_id, outcome, detail) per entry. Without ``fetch`` nothing is compared with
    EUR-Lex: only the recorded digests are recomputed from the snapshot ("recorded")."""

    if not entries:
        raise ValueError("the manifest lists no sources, so there is nothing to compare")
    results = []
    for entry in entries:
        source_id, check = entry["source_id"], entry["eurlex_check"]
        if drift := _recorded(entry):
            results.append((source_id, DIFFERS, drift))
            continue
        if fetch is None:
            detail = "snapshot has its recorded digests; not compared with EUR-Lex"
            results.append((source_id, RECORDED, detail))
            continue
        try:
            remote = fetch(check["url"])
            same_text = text_sha256(remote) == check["text_sha256"]
            same_structure = structure_sha256(remote) == check["structure_sha256"]
        except _NOT_COMPARED as error:
            results.append((source_id, UNVERIFIED, f"not compared: {error}"))
            continue
        if same_text and same_structure:
            results.append((source_id, IDENTICAL, "text and structure identical to EUR-Lex"))
        else:
            part = "text" if not same_text else "structure"
            results.append((source_id, DIFFERS, f"{part} changed, review required"))
    return results


def exit_code(results: list[tuple[str, str, str]]) -> int:
    outcomes = {outcome for _, outcome, _ in results}
    if not outcomes or DIFFERS in outcomes:
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
