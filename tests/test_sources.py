"""The source snapshots must stay byte-exact.

Rules and legal fixtures cite the texts in sources/. A snapshot whose digest
no longer matches the manifest has drifted, and nothing built on it can be
trusted until a reviewer records a new retrieval.

Each snapshot was also compared with EUR-Lex (scripts/compare_sources.py). The
manifest records that check with a digest of the body text, which these tests
recompute offline; the comparison itself needs the network and is not run here.
"""

from __future__ import annotations

import datetime
import email.message
import hashlib
import http.client
import importlib.util
import json
import urllib.error
from pathlib import Path

import pytest

from eu_ai_act_classifier.verify_sources import BotChallengeError

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compare_sources = _load("compare_sources", ROOT / "scripts" / "compare_sources.py")
MANIFEST = json.loads((SOURCES / "manifest.json").read_text(encoding="utf-8"))
ENTRIES = MANIFEST["sources"]


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["source_id"] for e in ENTRIES])
def test_snapshot_matches_its_digest(entry: dict) -> None:
    data = (SOURCES / entry["file"]).read_bytes()
    assert len(data) == entry["bytes"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"], "snapshot drifted"


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["source_id"] for e in ENTRIES])
def test_manifest_entry_records_its_retrieval(entry: dict) -> None:
    for key in ("celex", "request_url", "resolved_url", "retrieved_on", "text_status"):
        assert entry[key], f"{entry['source_id']} lacks {key}"
    assert entry["request_url"].startswith("https://publications.europa.eu/resource/celex/")


def test_every_snapshot_file_is_in_the_manifest() -> None:
    on_disk = {p.relative_to(SOURCES).as_posix() for p in SOURCES.rglob("*.xhtml")}
    assert on_disk == {e["file"] for e in ENTRIES}
    assert len({e["source_id"] for e in ENTRIES}) == len(ENTRIES)


# --- The EUR-Lex comparison ---------------------------------------------------


def _eurlex_uris(celex: str) -> set[str]:
    """The EUR-Lex URIs that name a CELEX document: by CELEX number, and for an act
    published in the OJ L series from 2023 on also by its OJ reference."""

    uris = {f"CELEX:{celex}"}
    if len(celex) == 10 and celex[0] == "3" and celex[5] in "RLD" and int(celex[1:5]) >= 2023:
        uris.add(f"OJ:L_{celex[1:5]}0{celex[6:]}")
    return uris


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["source_id"] for e in ENTRIES])
def test_snapshot_matches_the_digests_compared_with_eurlex(entry: dict) -> None:
    check = entry["eurlex_check"]
    data = (SOURCES / entry["file"]).read_bytes()
    assert compare_sources.is_complete_document(data)
    assert compare_sources.text_sha256(data) == check["text_sha256"]
    assert len(compare_sources.body_text(data)) == check["text_chars"]
    assert compare_sources.structure_sha256(data) == check["structure_sha256"]
    assert len(compare_sources.structure(data).splitlines()) == check["structure_tokens"]
    assert check["result"] == "text and structure identical"
    datetime.date.fromisoformat(check["checked_on"])
    # The URL names this entry's document, and the EUR-Lex response is identified.
    prefix = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri="
    assert check["url"].startswith(prefix)
    assert check["url"].removeprefix(prefix) in _eurlex_uris(entry["celex"])
    assert check["eurlex_bytes"] > len(data) // 2
    assert len(check["eurlex_sha256"]) == 64 and check["eurlex_sha256"] != entry["sha256"]


_CELLAR = (
    b'<html><head><link href="oj-convex-act.css"/></head><body>'
    b'<p class="oj-normal">10<span class="oj-super">25</span> FLOPs by 2&#160;December '
    b"2026</p></body></html>"
)
_EURLEX = (
    b'<html><head><meta name="format-detection"/><link href="./css/oj.css"/>'
    b'<title>EUR-Lex</title></head><body>\n<p class="x">10<span>25</span> FLOPs by '
    b"2\xc2\xa0December   2026</p><script>track()</script></body></html>\n"
)


def test_presentation_changes_leave_both_digests_alone() -> None:
    # A no-break space, as a reference or as a character, counts as whitespace.
    assert compare_sources.body_text(_CELLAR) == "10 25 FLOPs by 2 December 2026"
    for digest in (compare_sources.text_sha256, compare_sources.structure_sha256):
        assert digest(_CELLAR) == digest(_EURLEX)


def test_a_changed_word_changes_the_text_and_a_lost_element_the_structure() -> None:
    reworded = _EURLEX.replace(b"2026", b"2027")
    assert compare_sources.text_sha256(reworded) != compare_sources.text_sha256(_CELLAR)
    # Two paragraphs merged into one: the same words, but a boundary is gone.
    split = b"<html><body><p>Article 4</p><p>AI literacy</p></body></html>"
    merged = b"<html><body><p>Article 4 AI literacy</p></body></html>"
    assert compare_sources.text_sha256(split) == compare_sources.text_sha256(merged)
    assert compare_sources.structure_sha256(split) != compare_sources.structure_sha256(merged)


def _same(entry: dict) -> bytes:
    return (SOURCES / entry["file"]).read_bytes()


def test_comparison_passes_only_for_an_identical_document() -> None:
    by_url = {e["eurlex_check"]["url"]: e for e in ENTRIES}
    results = compare_sources.compare(ENTRIES, lambda url: _same(by_url[url]))
    assert [outcome for _, outcome, _ in results] == ["identical"] * len(ENTRIES)
    assert compare_sources.exit_code(results) == 0

    def one_changed(url: str) -> bytes:
        data = _same(by_url[url])
        return data.replace(b"</body>", b"<p>2027</p></body>") if "1744" in url else data

    results = compare_sources.compare(ENTRIES, one_changed)
    changed = {source_id: detail for source_id, outcome, detail in results if outcome == "differs"}
    assert changed == {"oj-reg-2026-1744": "text changed, review required"}
    assert compare_sources.exit_code(results) == 1

    def one_merged(url: str) -> bytes:
        # The same words, with the first paragraph boundary of the body removed.
        data = _same(by_url[url])
        if "2274" not in url:
            return data
        body = data.index(b"<body")
        end, start = data.index(b"</p>", body), data.index(b"<p", data.index(b"</p>", body))
        merged = data[:end] + b" " + data[data.index(b">", start) + 1 :]
        assert compare_sources.text_sha256(merged) == compare_sources.text_sha256(data)
        return merged

    results = compare_sources.compare(ENTRIES, one_merged)
    changed = {source_id: detail for source_id, outcome, detail in results if outcome == "differs"}
    assert changed == {"oj-dec-impl-2026-2274": "structure changed, review required"}


@pytest.mark.parametrize(
    "error",
    [
        BotChallengeError(202, "x-amzn-waf-action: challenge"),
        compare_sources.NotADocumentError("the answer (0 bytes) is not a complete document"),
        urllib.error.URLError("no route"),
        TimeoutError("timed out"),
        ConnectionResetError("reset by peer"),
        http.client.RemoteDisconnected("closed"),
        http.client.IncompleteRead(b"<html>", 1000),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
    ],
    ids=[
        "bot-challenge",
        "not-a-document",
        "url",
        "timeout",
        "reset",
        "disconnected",
        "incomplete",
        "decode",
    ],
)
def test_an_answer_that_is_not_the_document_never_counts_as_a_match(error: Exception) -> None:
    def fetch(url: str) -> bytes:
        raise error

    results = compare_sources.compare(ENTRIES, fetch)
    assert {outcome for _, outcome, _ in results} == {"unverified"}
    assert compare_sources.exit_code(results) == 2
    # A text that differs outranks one that could not be compared.
    mixed = [*results, ("x", "differs", "text changed, review required")]
    assert compare_sources.exit_code(mixed) == 1


class _Response:
    def __init__(self, status: int, body: bytes, headers: dict[str, str] | None = None):
        self.status, self._body = status, body
        self.headers = email.message.Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value

    def read(self, size: int = -1) -> bytes:
        return self._body

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


_DOCUMENT = _same(ENTRIES[-1])


@pytest.mark.parametrize(
    ("response", "raises"),
    [
        (_Response(200, _DOCUMENT), None),
        (_Response(202, _DOCUMENT), BotChallengeError),
        (_Response(200, _DOCUMENT, {"x-amzn-waf-action": "challenge"}), BotChallengeError),
        (_Response(200, b"<html><body>gokuProps = {}</body></html>"), BotChallengeError),
        (_Response(200, b""), compare_sources.NotADocumentError),
        (_Response(200, b"<html><body><p>Service unavailable"), compare_sources.NotADocumentError),
        (_Response(200, _DOCUMENT[: len(_DOCUMENT) // 2]), compare_sources.NotADocumentError),
    ],
    ids=["document", "202", "waf-header", "challenge-body", "empty", "stub", "truncated"],
)
def test_fetch_returns_only_a_complete_document(
    monkeypatch: pytest.MonkeyPatch, response: _Response, raises: type[Exception] | None
) -> None:
    seen = []

    def urlopen(request, timeout):
        seen.append((request.full_url, request.get_header("User-agent"), timeout))
        return response

    monkeypatch.setattr(compare_sources.urllib.request, "urlopen", urlopen)
    url = ENTRIES[-1]["eurlex_check"]["url"]
    if raises is None:
        assert compare_sources.fetch(url) == _DOCUMENT
    else:
        with pytest.raises(raises):
            compare_sources.fetch(url)
    assert seen == [(url, compare_sources.HEADERS["User-Agent"], compare_sources.TIMEOUT_SECONDS)]


def test_the_default_run_fetches_every_source(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    by_url = {e["eurlex_check"]["url"]: e for e in ENTRIES}
    fetched = []

    def fetch(url: str) -> bytes:
        fetched.append(url)
        return _same(by_url[url])

    monkeypatch.setattr(compare_sources, "fetch", fetch)
    monkeypatch.setattr(compare_sources.compare, "__defaults__", (fetch,))
    assert compare_sources.main([]) == 0
    assert sorted(fetched) == sorted(by_url)
    lines = capsys.readouterr().out.splitlines()
    assert [line.split()[0] for line in lines] == ["identical"] * len(ENTRIES)


def test_offline_run_compares_nothing_and_says_so(capsys: pytest.CaptureFixture[str]) -> None:
    assert compare_sources.main(["--offline"]) == 0
    out = capsys.readouterr().out
    assert [line.split()[0] for line in out.splitlines()] == ["recorded"] * len(ENTRIES)
    assert "identical" not in out
    assert out.count("not compared with EUR-Lex") == len(ENTRIES)
    drifted = [{**ENTRIES[0], "eurlex_check": {**ENTRIES[0]["eurlex_check"], "text_sha256": "0"}}]
    assert compare_sources.compare(drifted, None)[0][1] == "differs"
    with pytest.raises(ValueError, match="no sources"):
        compare_sources.compare([], None)
    assert compare_sources.exit_code([]) == 1


def test_eurlex_uris_name_the_document() -> None:
    assert _eurlex_uris("32026R1744") == {"CELEX:32026R1744", "OJ:L_202601744"}
    assert _eurlex_uris("32011L0093") == {"CELEX:32011L0093"}
    assert _eurlex_uris("02024R1689-20260727") == {"CELEX:02024R1689-20260727"}
