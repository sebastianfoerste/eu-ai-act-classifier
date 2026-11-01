"""The source snapshots must stay byte-exact.

Rules and legal fixtures cite the texts in sources/. A snapshot whose digest
no longer matches the manifest has drifted, and nothing built on it can be
trusted until a reviewer records a new retrieval.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

SOURCES = Path(__file__).resolve().parents[1] / "sources"
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
