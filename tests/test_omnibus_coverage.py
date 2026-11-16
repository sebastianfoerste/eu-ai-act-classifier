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


def test_map_and_ledger_record_what_the_corrigendum_corrects() -> None:
    # Read on 14 November 2026: only the German text of Art. 6(1b) changes.
    # Compared with whitespace collapsed: the map wraps its lines.
    text = " ".join(MAP.read_text(encoding="utf-8").split())
    ledger = (ROOT / "docs" / "REGULATORY_CLAIM_LEDGER.md").read_text(encoding="utf-8")

    for document in (text, ledger):
        assert "32026R1744R(01)" in document
        assert "Ungeachtet des Absatzes 1a" in document
        assert "Unbeschadet des Absatzes 1a" in document
    assert "| PENDING | A corrigendum" not in ledger


# A file in the last column, followed by the symbols it holds: `catalog.py`: `A`, `b`.
_CODE_REFERENCE = re.compile(r"`([\w/]+\.py)`: ((?:`[^`]+`(?:, | and |,? or )?)+)")
_IDENTIFIER = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")
# The quoted claim texts that follow "ledger row" or "ledger rows", each optionally
# followed by a parenthesis such as "(PENDING)".
_LEDGER_REFERENCE = re.compile(r'ledger rows? ((?:"[^"]+"(?: \([^)]*\))?(?:, | and )?)+)')


def _source(name: str) -> Path:
    for base in (ROOT / "src" / "eu_ai_act_classifier", ROOT):
        if (base / name).exists():
            return base / name
    raise AssertionError(f"no file {name}")


def test_every_file_and_symbol_the_map_names_exists() -> None:
    checked = 0
    for point, *_, where in _rows():
        for name, symbols in _CODE_REFERENCE.findall(where):
            text = _source(name).read_text(encoding="utf-8")
            for symbol in _IDENTIFIER.findall(symbols):
                assert re.search(rf"\b{re.escape(symbol)}\b", text), (point, name, symbol)
                checked += 1
    assert checked > 40


def _in_order(parts: list[str], text: str) -> bool:
    position = 0
    for part in parts:
        position = text.find(part, position)
        if position < 0:
            return False
        position += len(part)
    return True


def test_every_ledger_row_the_map_names_is_in_the_ledger() -> None:
    ledger = (ROOT / "docs" / "REGULATORY_CLAIM_LEDGER.md").read_text(encoding="utf-8")
    rows = [line for line in ledger.splitlines() if line.startswith("| ")]
    checked = 0
    for point, *_, where in _rows():
        for group in _LEDGER_REFERENCE.findall(where):
            for quote in re.findall(r'"([^"]+)"', group):
                parts = [p.strip(" .,") for p in quote.split("...") if p.strip(" .,")]
                assert any(_in_order(parts, row) for row in rows), (point, quote)
                checked += 1
    assert checked > 10
