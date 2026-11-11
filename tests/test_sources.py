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
import hashlib
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


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["source_id"] for e in ENTRIES])
def test_snapshot_text_matches_the_digest_compared_with_eurlex(entry: dict) -> None:
    check = entry["eurlex_check"]
    data = (SOURCES / entry["file"]).read_bytes()
    assert compare_sources.text_sha256(data) == check["text_sha256"]
    assert len(compare_sources.body_text(data)) == check["text_chars"]
    assert check["url"].startswith("https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=")
    assert check["result"] == "body text identical"
    datetime.date.fromisoformat(check["checked_on"])


def test_body_text_ignores_presentation_but_not_wording() -> None:
    cellar = (
        b'<html><head><link href="oj-convex-act.css"/></head><body>'
        b'<p class="oj-normal">by 2&#160;December 2026</p></body></html>'
    )
    eurlex = (
        b'<html><head><meta name="format-detection"/><link href="./css/oj.css"/>'
        b"<title>EUR-Lex</title></head><body>\n<p>by 2\xc2\xa0December   2026</p>"
        b"<script>track()</script></body></html>"
    )
    # A no-break space, as a reference or as a character, counts as whitespace.
    assert compare_sources.body_text(cellar) == "by 2 December 2026"
    assert compare_sources.text_sha256(cellar) == compare_sources.text_sha256(eurlex)
    changed = eurlex.replace(b"2026", b"2027")
    assert compare_sources.text_sha256(changed) != compare_sources.text_sha256(cellar)


def _same(entry: dict) -> bytes:
    return (SOURCES / entry["file"]).read_bytes()


def test_comparison_passes_only_for_an_identical_text() -> None:
    by_url = {e["eurlex_check"]["url"]: e for e in ENTRIES}
    results = compare_sources.compare(ENTRIES, lambda url: _same(by_url[url]))
    assert [outcome for _, outcome, _ in results] == ["identical"] * len(ENTRIES)
    assert compare_sources.exit_code(results) == 0

    def one_changed(url: str) -> bytes:
        data = _same(by_url[url])
        return data.replace(b"</body>", b"<p>2027</p></body>") if "1744" in url else data

    results = compare_sources.compare(ENTRIES, one_changed)
    changed = {source_id: detail for source_id, outcome, detail in results if outcome == "differs"}
    assert changed == {"oj-reg-2026-1744": "content changed, review required"}
    assert compare_sources.exit_code(results) == 1


@pytest.mark.parametrize(
    "error",
    [BotChallengeError(202, "x-amzn-waf-action: challenge"), urllib.error.URLError("no route")],
    ids=["bot-challenge", "network"],
)
def test_an_answer_that_is_not_the_document_never_counts_as_a_match(error: Exception) -> None:
    def fetch(url: str) -> bytes:
        raise error

    results = compare_sources.compare(ENTRIES, fetch)
    assert {outcome for _, outcome, _ in results} == {"unverified"}
    assert compare_sources.exit_code(results) == 2
    # A text that differs outranks one that could not be compared.
    mixed = [*results, ("x", "differs", "content changed, review required")]
    assert compare_sources.exit_code(mixed) == 1


def test_offline_run_recomputes_the_recorded_digests(capsys: pytest.CaptureFixture[str]) -> None:
    assert compare_sources.main(["--offline"]) == 0
    assert capsys.readouterr().out.count("identical") == len(ENTRIES)
    drifted = [{**ENTRIES[0], "eurlex_check": {**ENTRIES[0]["eurlex_check"], "text_sha256": "0"}}]
    assert compare_sources.compare(drifted, None)[0][1] == "differs"
