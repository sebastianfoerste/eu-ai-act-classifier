"""docs/omnibus-coverage.md maps every amending point of Regulation (EU) 2026/1744."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs" / "omnibus-coverage.md"
STATUSES = ("encoded", "flagged for review", "outside the classifier's scope", "not encoded (gap)")
POINTS = [f"({n})" for n in range(1, 44)] + ["Art. 2", "Art. 3", "Art. 4"]


def _rows() -> list[list[str]]:
    rows = []
    for line in MAP.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| Point") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split(" | ")]
        rows.append(cells)
    return rows


def test_every_amending_point_and_each_closing_article_has_exactly_one_row() -> None:
    rows = _rows()
    assert all(len(row) == 5 for row in rows), [row[0] for row in rows if len(row) != 5]
    assert [row[0] for row in rows] == POINTS


def test_every_row_uses_the_allowed_statuses_and_says_where() -> None:
    for point, provision, effect, status, where in _rows():
        assert provision and effect and where, point
        found = [name for name in STATUSES if name in status]
        assert found, (point, status)
        # Whatever the classifier applies must be traceable to code or to the ledger.
        if status.startswith("encoded"):
            assert re.search(r"`[\w/]+\.py`", where), (point, where)
            assert "ledger row" in where, (point, where)


def test_map_is_linked_from_the_docs_index_and_the_ledger() -> None:
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    ledger = (ROOT / "docs" / "REGULATORY_CLAIM_LEDGER.md").read_text(encoding="utf-8")

    assert "](omnibus-coverage.md)" in index
    assert "omnibus-coverage.md" in ledger
    assert "32026R1744R(01)" in ledger


def test_map_names_the_corrigendum_without_claiming_to_have_read_it() -> None:
    text = MAP.read_text(encoding="utf-8")

    assert "32026R1744R(01)" in text
    assert "not read" in text
