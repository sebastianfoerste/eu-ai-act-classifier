"""docs/omnibus-coverage.md maps every amending point of Regulation (EU) 2026/1744."""

from __future__ import annotations

import functools
import re
from pathlib import Path

from eu_ai_act_classifier import SystemProfile, classify

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs" / "omnibus-coverage.md"
LEDGER = ROOT / "docs" / "REGULATORY_CLAIM_LEDGER.md"
STATUSES = ("encoded", "flagged for review", "outside the classifier's scope", "not encoded (gap)")
POINTS = [f"({n})" for n in range(1, 44)] + ["Art. 2", "Art. 3", "Art. 4"]
CORRIGENDUM_DIGEST = "9d00a2f906dda5dc9d9aac22ee948c4a6bac1472706385b373f53d3d33d30d47"


def _rows() -> list[list[str]]:
    rows = []
    for line in MAP.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| Point") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split(" | ")]
        rows.append(cells)
    return rows


def _ledger_rows() -> list[str]:
    return [
        line for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.startswith("| ")
    ]


def _strip_trailing_parenthesis(text: str) -> str:
    """``text`` without its last balanced parenthesis, if it ends with one."""

    depth = 0
    for index in range(len(text) - 1, -1, -1):
        depth += text[index] == ")"
        depth -= text[index] == "("
        if depth == 0:
            return text[:index].rstrip()
    return text


def _top_level_parts(status: str) -> list[str]:
    """``status`` split at the semicolons that stand outside parentheses."""

    parts, depth, start = [], 0, 0
    for index, char in enumerate(status):
        depth += (char == "(") - (char == ")")
        if char == ";" and depth == 0:
            parts.append(status[start:index])
            start = index + 1
    return [*parts, status[start:]]


def _statuses(status: str) -> list[str]:
    """Each part of a status, split at top-level semicolons, with its qualifying parentheses
    removed until it is one of STATUSES (which "not encoded (gap)" itself ends with)."""

    parts = []
    for part in (p.strip() for p in _top_level_parts(status)):
        while part not in STATUSES and part.endswith(")"):
            shorter = _strip_trailing_parenthesis(part)
            if shorter == part:
                break
            part = shorter
        parts.append(part)
    return parts


def test_every_amending_point_and_each_closing_article_has_exactly_one_row() -> None:
    rows = _rows()
    assert all(len(row) == 5 for row in rows), [row[0] for row in rows if len(row) != 5]
    assert [row[0] for row in rows] == POINTS


def test_every_row_uses_the_allowed_statuses_and_says_where() -> None:
    for point, provision, effect, status, where in _rows():
        assert provision and effect and where, point
        assert all(part in STATUSES for part in _statuses(status)), (point, status)
        # Whatever the classifier applies must be traceable to code or to the ledger.
        if status.startswith("encoded"):
            assert re.search(r"`[\w/]+\.py`", where), (point, where)
            assert "ledger row" in where, (point, where)


def test_status_parsing_rejects_values_outside_the_four() -> None:
    assert _statuses("not encoded (gap) (the rest)") == ["not encoded (gap)"]
    assert _statuses("encoded (Art. 2(2)); outside the classifier's scope (Art. 2(7))") == [
        "encoded",
        "outside the classifier's scope",
    ]
    assert _statuses("flagged for review (stated; not applied)") == ["flagged for review"]
    assert _statuses("outside the classifier's scope; named in an item") == [
        "outside the classifier's scope",
        "named in an item",
    ]
    assert _statuses("partly encoded") == ["partly encoded"]
    assert "partly encoded" not in STATUSES


def test_map_is_linked_from_the_docs_index_and_the_ledger() -> None:
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    ledger = LEDGER.read_text(encoding="utf-8")

    assert "](omnibus-coverage.md)" in index
    assert "omnibus-coverage.md" in ledger
    assert "32026R1744R(01)" in ledger


def test_map_and_ledger_record_what_the_corrigendum_corrects() -> None:
    # Read on 14 November 2026: only the German text of Art. 6(1b) changes, from
    # "Unbeschadet" to "Ungeachtet". Compared with whitespace collapsed: the map wraps.
    text = " ".join(MAP.read_text(encoding="utf-8").split())
    corrected = "begins „Ungeachtet des Absatzes 1a“ instead of „Unbeschadet des Absatzes 1a“"
    (row,) = [row for row in _ledger_rows() if "32026R1744R(01)" in row]

    assert corrected in text
    assert corrected in row
    assert row.startswith("| CORRECTED |")
    assert CORRIGENDUM_DIGEST in text
    assert CORRIGENDUM_DIGEST in row


@functools.cache
def _corpus() -> str:
    """The source and the classifier's output for every bundled profile: item, finding,
    note and source ids are built at run time, so they are looked up in the output."""

    texts = [path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py")]
    texts += [path.read_text(encoding="utf-8") for path in (ROOT / "scripts").glob("*.py")]
    for path in sorted((ROOT / "examples").rglob("*.json")):
        try:
            profile = SystemProfile.model_validate_json(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        texts.append(classify(profile, include_advisory=True).model_dump_json())
    # No bundled profile takes an Annex I route, which some findings the map quotes need.
    for section in ("A", "B"):
        profile = SystemProfile(
            name="x",
            roles=["provider", "deployer"],
            annex_i_safety_component=True,
            annex_i_third_party_assessment=True,
            annex_i_section=section,
        )
        texts.append(classify(profile, include_advisory=True).model_dump_json())
    return "\n".join(texts)


def _in_order(parts: list[str], text: str) -> bool:
    position = 0
    for part in parts:
        position = text.find(part, position)
        if position < 0:
            return False
        position += len(part)
    return True


def _parts(quote: str) -> list[str]:
    """A quotation with "..." for left-out text, split into the parts it keeps."""

    return [part.strip(" .,") for part in quote.split("...") if part.strip(" .,")]


def _exists(token: str) -> bool:
    if token.endswith((".py", ".md", ".json")):
        bases = (ROOT / "src" / "eu_ai_act_classifier", ROOT, ROOT / "docs")
        return any((base / token).exists() for base in bases)
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
        return re.search(rf"\b{re.escape(token)}\b", _corpus()) is not None
    if "..." in token:
        return _in_order(_parts(token), _corpus())
    # A whole id or text: not part of a longer one (I.A.1 is not found in I.A.10).
    pattern = rf"(?<![\w.-]){re.escape(token)}(?![\w-]|\.\w)"
    return re.search(pattern, _corpus()) is not None


def test_every_code_token_the_map_names_exists() -> None:
    checked = 0
    for point, *_, where in _rows():
        for token in re.findall(r"`([^`]+)`", where):
            assert _exists(token), (point, token)
            checked += 1
    assert checked > 100


def _ledger_quotes(cell: str) -> list[str]:
    """Every quoted claim text that follows "ledger row" or "ledger rows", up to the first
    text that is neither a separator nor a (possibly nested) parenthesis."""

    quotes = []
    for match in re.finditer(r"ledger rows? ", cell):
        index = match.end()
        while True:
            while index < len(cell):
                rest = cell[index:]
                if rest.startswith((", ", " and ")):
                    index += 2 if rest.startswith(", ") else 5
                elif rest[0] == " ":
                    index += 1
                elif rest[0] == "(":
                    depth = 0
                    while index < len(cell):
                        depth += cell[index] == "("
                        depth -= cell[index] == ")"
                        index += 1
                        if depth == 0:
                            break
                else:
                    break
            if index < len(cell) and cell[index] == '"':
                end = cell.index('"', index + 1)
                quotes.append(cell[index + 1 : end])
                index = end + 1
            else:
                break
    return quotes


def test_ledger_reference_scanner_reads_lists_and_nested_parentheses() -> None:
    cell = 'ledger rows "First claim (PENDING)" (see (a)), "Second claim" and "Third"; "not this"'
    assert _ledger_quotes(cell) == ["First claim (PENDING)", "Second claim", "Third"]


def test_every_ledger_row_the_map_names_is_in_the_ledger() -> None:
    rows = _ledger_rows()
    checked = 0
    for point, *_, where in _rows():
        for quote in _ledger_quotes(where):
            assert any(_in_order(_parts(quote), row) for row in rows), (point, quote)
            checked += 1
    assert checked > 30
