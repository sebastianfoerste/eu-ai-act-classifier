"""Run the legal fixtures in tests/legal/fixtures/ against the engine.

The fixtures were written from the snapshotted Official Journal texts in
sources/ before the rules were encoded. A failure here means the engine and the
source-derived expectation disagree; check the fixture against the snapshot
before touching either.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from eu_ai_act_classifier import SystemProfile, classify

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
MANIFEST = json.loads((ROOT / "sources" / "manifest.json").read_text(encoding="utf-8"))
SOURCE_IDS = {entry["source_id"] for entry in MANIFEST["sources"]}
MATRIX = {
    "applies",
    "element_fails",
    "unknown_input",
    "boundary_before",
    "boundary_on",
    "boundary_after",
    "conflict",
    "invalid_input",
    "irrelevant_input",
}


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _load() -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    cases = []
    for path in sorted(FIXTURES.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for case in data["cases"]:
            cases.append((f"{path.stem}::{case['id']}", data, case))
    return cases


CASES = _load()


def test_fixture_files_cite_snapshotted_sources() -> None:
    for path in sorted(FIXTURES.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["sources"], f"{path.name} cites no source"
        for source in data["sources"]:
            assert source["source_id"] in SOURCE_IDS, f"{path.name}: unknown source"
            assert source["pinpoint"]
        interpretation_ids = {item["id"] for item in data.get("interpretations", [])}
        ids = [case["id"] for case in data["cases"]]
        assert len(ids) == len(set(ids)), f"{path.name} repeats a case id"
        for case in data["cases"]:
            assert case["matrix"] in MATRIX, case["id"]
            assert case["facts"].strip(), case["id"]
            if "interpretation" in case:
                assert case["interpretation"] in interpretation_ids, case["id"]


LABELLED = [
    c for c in CASES if "interpretation" in c[2] and "validation_error_loc" not in c[2]["expect"]
]


@pytest.mark.parametrize(("case_id", "data", "case"), LABELLED, ids=[c[0] for c in LABELLED])
def test_interpretation_is_labelled_in_the_output(
    case_id: str, data: dict[str, Any], case: dict[str, Any]
) -> None:
    """docs/methodology.md promises that every interpretation choice a result turns
    on is labelled "interpretation" in a finding or open question; the fixtures name
    the choice each case rests on."""
    report = classify(SystemProfile.model_validate(_merge(data["base_profile"], case["profile"])))
    texts = [f.detail for f in report.findings] + report.open_questions
    assert any("interpretation" in text.lower() for text in texts), (case["interpretation"], texts)


@pytest.mark.parametrize(("case_id", "data", "case"), CASES, ids=[c[0] for c in CASES])
def test_fixture(case_id: str, data: dict[str, Any], case: dict[str, Any]) -> None:
    profile_data = _merge(data.get("base_profile", {}), case["profile"])
    expect = case["expect"]

    if "validation_error_loc" in expect:
        with pytest.raises(ValidationError) as error:
            SystemProfile.model_validate(profile_data)
        locations = {".".join(str(part) for part in e["loc"]) for e in error.value.errors()}
        assert expect["validation_error_loc"] in locations
        return

    report = classify(SystemProfile.model_validate(profile_data))
    findings = {f.rule_id: f for f in report.findings}

    if "risk_tier" in expect:
        assert report.risk_tier.value == expect["risk_tier"]
    if "disposition" in expect:
        assert report.disposition.value == expect["disposition"], report.open_questions
    for rule_id, severity in expect.get("findings", {}).items():
        assert rule_id in findings, f"missing {rule_id}; got {sorted(findings)}"
        assert findings[rule_id].severity.value == severity
    for rule_id in expect.get("findings_absent", []):
        assert rule_id not in findings, f"unexpected {rule_id}"
    for rule_id, fragment in expect.get("finding_citations", {}).items():
        assert fragment in findings[rule_id].citation
    for fragment in expect.get("open_question_contains", []):
        assert any(fragment in q for q in report.open_questions), (fragment, report.open_questions)
    if expect.get("no_open_questions"):
        assert report.open_questions == []

    articles = {ob.article for ob in report.obligations + report.documentation_required}
    for article in expect.get("obligations_include", []):
        assert article in articles
    for article in expect.get("obligations_exclude", []):
        assert article not in articles
    if "transparency_articles" in expect:
        transparency = [ob.article for ob in report.transparency_obligations]
        assert transparency == expect["transparency_articles"]

    graph = {item.article: item for item in report.obligation_graph}
    for expected in expect.get("graph", []):
        item = graph.get(expected["article"])
        assert item is not None, f"no graph item for {expected['article']}"
        for key, value in expected.items():
            assert getattr(item, key) == value, (key, getattr(item, key), value)
    for prefix in expect.get("graph_absent_prefix", []):
        assert not any(item.obligation_id.startswith(prefix) for item in report.obligation_graph)

    for row in expect.get("timeline_includes", []):
        assert any(
            t.applies_from == row["applies_from"] and row["provision_contains"] in t.provision
            for t in report.timeline
        ), row
