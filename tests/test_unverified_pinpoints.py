"""Pinpoints #30 added without a primary-source record stay visibly unverified.

Art. 6(1c), Art. 2(13) and the two Art. 111(1) dates were not re-read on EUR-Lex (PENDING
rows in docs/REGULATORY_CLAIM_LEDGER.md). These tests pin their exact text, unchanged, and
the flag every output gives them: an unverified citation on their own finding, the entry
in ``unverified_citations``, and "[noch zu verifizieren]" in the rendered report and next to
the Art. 111(1) carve-out wherever it is stated in prose.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from eu_ai_act_classifier import AnnexIII, Role, SystemProfile, classify
from eu_ai_act_classifier.models import ClassificationReport
from eu_ai_act_classifier.report import render_report

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
FLAG = "[noch zu verifizieren]"

ART_6_1C_TEXT = (
    "A third-party conformity assessment required solely for risks other than risks to "
    "health and safety, such as radio spectrum or electromagnetic interference, does not "
    "meet Art. 6(1)(b) (Art. 6(1c) AIA)."
)
ART_2_13_TEXT = (
    "Delegated acts under Art. 2(13) AIA, due by 2 August 2027, may limit Arts. 9 to 15 and "
    "17 to 25 where the Section A legislation gives an equivalent or higher level of "
    "protection and the limitation does not reduce the overall level of protection provided "
    "for by the AI Act."
)
ANNEX_X_TEXT = (
    "components of the Annex X large-scale IT systems placed on the market or put into "
    "service before 2 August 2027, which are brought into compliance by 31 December 2030 "
    "(Art. 111(1) AIA) [noch zu verifizieren]"
)
TIMELINE_TEXT = (
    "Components of the Annex X large-scale IT systems placed on the market or put into "
    "service before 2 August 2027 follow Art. 111(1) instead [noch zu verifizieren]."
)
ANNEX_I_ROUTE = {"annex_i_safety_component": True, "annex_i_third_party_assessment": True}
# Unverified pinpoints and how the output names them.
UNVERIFIED_PINPOINTS = ("Art. 6(1c)", "Art. 2(13)", "Art. 111(1)")


def _report(**facts: object) -> ClassificationReport:
    return classify(SystemProfile(name="x", **facts))


def _only(report: ClassificationReport, citation: str):
    findings = [f for f in report.findings if f.citation == citation]
    assert len(findings) <= 1, findings
    return findings[0] if findings else None


@pytest.mark.parametrize("section", [None, "A", "B"])
def test_art_6_1c_is_its_own_unverified_finding_on_the_annex_i_route(
    section: str | None,
) -> None:
    report = _report(roles=[Role.PROVIDER], annex_i_section=section, **ANNEX_I_ROUTE)

    finding = _only(report, "Art. 6(1c) AIA")
    assert finding is not None
    assert finding.rule_id == "HIGHRISK.6.1c"
    assert finding.detail == ART_6_1C_TEXT
    assert finding.citation_verified is False
    assert "Art. 6(1c) AIA" in report.unverified_citations
    assert f"Art. 6(1c) AIA {FLAG}: " in render_report(report)
    # The Art. 6(1) finding, whose citation is verified, no longer states it.
    (art_6_1,) = [f for f in report.findings if f.rule_id == "HIGHRISK.6.1"]
    assert art_6_1.citation_verified is True
    assert "6(1c)" not in art_6_1.detail


@pytest.mark.parametrize("section", [None, "A", "B"])
def test_art_2_13_note_is_its_own_unverified_finding_for_section_a(
    section: str | None,
) -> None:
    report = _report(roles=[Role.PROVIDER], annex_i_section=section, **ANNEX_I_ROUTE)

    finding = _only(report, "Art. 2(13) AIA")
    (art_6_1,) = [f for f in report.findings if f.rule_id == "HIGHRISK.6.1"]
    assert "2(13)" not in art_6_1.detail
    if section != "A":
        assert finding is None
        assert "Art. 2(13) AIA" not in report.unverified_citations
        return
    assert art_6_1.detail.endswith("Annex I, Section A: the Chapter III duties apply.")
    assert finding is not None
    assert finding.rule_id == "HIGHRISK.2.13"
    assert finding.detail == ART_2_13_TEXT
    assert finding.citation_verified is False
    assert "Art. 2(13) AIA" in report.unverified_citations
    assert f"Art. 2(13) AIA {FLAG}: " in render_report(report)


def test_off_the_annex_i_route_neither_note_is_given() -> None:
    report = _report(annex_i_section="A", annex_iii_area=AnnexIII.CREDITWORTHINESS)

    assert _only(report, "Art. 6(1c) AIA") is None
    assert _only(report, "Art. 2(13) AIA") is None


@pytest.mark.parametrize("placing_on_market_date", ["2024-01-01", "2027-01-01"])
def test_art_111_1_carve_out_is_stated_with_its_flag(placing_on_market_date: str) -> None:
    report = _report(
        roles=[Role.PROVIDER, Role.DEPLOYER],
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        placing_on_market_date=placing_on_market_date,
    )

    assert f"Art. 111(2) excludes {ANNEX_X_TEXT}." in report.scope.transitional_status
    items = [i for i in report.obligation_graph if i.article == "Art. 111(2) AIA"]
    assert [i.actor for i in items] == [Role.PROVIDER, Role.DEPLOYER]
    for item in items:
        assert f"other than {ANNEX_X_TEXT}. " in (item.application_date_note or "")
    assert "Art. 111(1) AIA" in report.unverified_citations
    rendered = render_report(report)
    assert f"{ANNEX_X_TEXT}." in rendered
    assert "  - Art. 111(1) AIA\n" in rendered[rendered.index("Citations pending verification") :]


def test_art_111_1_is_flagged_in_the_binding_timeline() -> None:
    (entry,) = [t for t in _report().timeline if "Art. 111(1)" in t.note]

    assert entry.applies_from == "2030-08-02"
    assert entry.note.endswith(f" {TIMELINE_TEXT}")


def _profiles() -> list[tuple[str, SystemProfile]]:
    profiles = [
        (path.name, SystemProfile.model_validate_json(path.read_text(encoding="utf-8")))
        for path in sorted(EXAMPLES.glob("*.json"))
        if path.name != "classification-packet.json"
    ]
    legacy = {"placing_on_market_date": "2024-01-01", "public_authority_use": True}
    roles = [Role.PROVIDER, Role.DEPLOYER, Role.IMPORTER]
    synthetic = {
        "annex-i-a": {**ANNEX_I_ROUTE, "annex_i_section": "A"},
        "annex-i-b": {**ANNEX_I_ROUTE, "annex_i_section": "B"},
        "annex-i-unset-legacy": {**ANNEX_I_ROUTE, **legacy},
        "annex-iii-legacy": {"annex_iii_area": AnnexIII.CREDITWORTHINESS, **legacy},
        "annex-iii-undated": {"annex_iii_area": AnnexIII.CREDITWORTHINESS},
    }
    profiles += [
        (key, SystemProfile(name=key, roles=roles, **facts)) for key, facts in synthetic.items()
    ]
    return profiles


PROFILES = _profiles()


@pytest.mark.parametrize("profile", [p for _key, p in PROFILES], ids=[k for k, _p in PROFILES])
def test_no_output_states_an_unverified_pinpoint_without_the_flag(profile: SystemProfile) -> None:
    report = classify(profile, include_advisory=True)

    for finding in report.findings:
        if any(p in finding.citation + finding.detail for p in UNVERIFIED_PINPOINTS):
            assert finding.citation_verified is False, finding.rule_id
            assert finding.citation in report.unverified_citations
    # In prose, every mention of Art. 111(1) carries the flag before its sentence ends.
    prose = [report.scope.transitional_status, *report.open_questions]
    prose += [t.note for t in report.timeline]
    for item in report.obligation_graph:
        prose += [item.trigger, item.requirement, item.application_date_note or ""]
    for text in prose:
        for mention in re.finditer(re.escape("Art. 111(1)"), text):
            sentence = text[mention.end() :].split(". ", 1)[0]
            assert FLAG in sentence, text
    per_system = prose[:1] + [i.application_date_note or "" for i in report.obligation_graph]
    if any("Art. 111(1)" in text for text in per_system):
        assert "Art. 111(1) AIA" in report.unverified_citations
    # The dates themselves never appear without the flag.
    dump = json.dumps(report.model_dump(mode="json"))
    assert dump.count("31 December 2030") == dump.count(
        f"31 December 2030 (Art. 111(1) AIA) {FLAG}"
    )
