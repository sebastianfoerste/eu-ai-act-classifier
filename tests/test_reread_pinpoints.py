"""The pinpoints #30 added, read in the Official Journal text on 11 November 2026.

Art. 6(1c), Art. 2(13) and the Art. 111(1) carve-out with its two dates were shown as
unverified from #59 until they were read in the Official Journal texts pinned in pull
request #40 (VERIFIED rows in docs/REGULATORY_CLAIM_LEDGER.md). These tests pin their exact
text, unchanged by the reading, their verified status in every output, the ledger rows that
record the reading, and the mechanism that flags them again if a citation is set back to
unverified.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from eu_ai_act_classifier import AnnexIII, Role, SystemProfile, classify, engine
from eu_ai_act_classifier.citations import (
    ART_2_13,
    ART_6_1C,
    ART_111_1,
    Citation,
    cite,
    flag_unless_verified,
)
from eu_ai_act_classifier.guidance_eval import load_guidance_examples
from eu_ai_act_classifier.models import ClassificationReport
from eu_ai_act_classifier.report import render_report

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
LEDGER = ROOT / "docs" / "REGULATORY_CLAIM_LEDGER.md"
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
    "(Art. 111(1) AIA)"
)
TIMELINE_TEXT = (
    "Components of the Annex X large-scale IT systems placed on the market or put into "
    "service before 2 August 2027 follow Art. 111(1) instead."
)
ANNEX_I_ROUTE = {"annex_i_safety_component": True, "annex_i_third_party_assessment": True}
PINPOINTS = ("Art. 6(1c)", "Art. 2(13)", "Art. 111(1)")
CITATIONS = {"Art. 6(1c)": ART_6_1C, "Art. 2(13)": ART_2_13, "Art. 111(1)": ART_111_1}
# The Official Journal snapshots pinned in pull request #40, by their SHA-256 digests.
OJ_2026_1744_SHA256 = "9d754652b867722807e4219c85912ce354233e58a1b4eb8c7752b4d1922993db"
OJ_2024_1689_SHA256 = "8f0b656302f9864cc87e040c371f209a9d65ae1a6cecc25ca5eb737e872d721a"


def _report(**facts: object) -> ClassificationReport:
    return classify(SystemProfile(name="x", **facts))


def _only(report: ClassificationReport, citation: str):
    findings = [f for f in report.findings if f.citation == citation]
    assert len(findings) <= 1, findings
    return findings[0] if findings else None


def test_the_three_citations_are_verified() -> None:
    assert [c.ref for c in CITATIONS.values()] == [f"{p} AIA" for p in PINPOINTS]
    assert all(c.verified for c in CITATIONS.values())


@pytest.mark.parametrize("section", [None, "A", "B"])
def test_art_6_1c_is_its_own_verified_finding_on_the_annex_i_route(
    section: str | None,
) -> None:
    report = _report(roles=[Role.PROVIDER], annex_i_section=section, **ANNEX_I_ROUTE)

    finding = _only(report, "Art. 6(1c) AIA")
    assert finding is not None
    assert finding.rule_id == "HIGHRISK.6.1c"
    assert finding.detail == ART_6_1C_TEXT
    assert finding.citation_verified is True
    assert "Art. 6(1c) AIA" not in report.unverified_citations
    rendered = render_report(report)
    assert "Art. 6(1c) AIA: Annex I route: assessment for other risks" in rendered
    assert f"Art. 6(1c) AIA {FLAG}" not in rendered
    # The Art. 6(1) finding does not state it.
    (art_6_1,) = [f for f in report.findings if f.rule_id == "HIGHRISK.6.1"]
    assert art_6_1.citation_verified is True
    assert "6(1c)" not in art_6_1.detail


@pytest.mark.parametrize("section", [None, "A", "B"])
def test_art_2_13_note_is_its_own_verified_finding_for_section_a(
    section: str | None,
) -> None:
    report = _report(roles=[Role.PROVIDER], annex_i_section=section, **ANNEX_I_ROUTE)

    finding = _only(report, "Art. 2(13) AIA")
    (art_6_1,) = [f for f in report.findings if f.rule_id == "HIGHRISK.6.1"]
    assert "2(13)" not in art_6_1.detail
    if section != "A":
        assert finding is None
        return
    assert art_6_1.detail.endswith("Annex I, Section A: the Chapter III duties apply.")
    assert finding is not None
    assert finding.rule_id == "HIGHRISK.2.13"
    assert finding.detail == ART_2_13_TEXT
    assert finding.citation_verified is True
    assert "Art. 2(13) AIA" not in report.unverified_citations
    rendered = render_report(report)
    assert "Art. 2(13) AIA: Annex I, Section A: delegated acts" in rendered
    assert f"Art. 2(13) AIA {FLAG}" not in rendered


def test_off_the_annex_i_route_neither_note_is_given() -> None:
    report = _report(annex_i_section="A", annex_iii_area=AnnexIII.CREDITWORTHINESS)

    assert _only(report, "Art. 6(1c) AIA") is None
    assert _only(report, "Art. 2(13) AIA") is None


@pytest.mark.parametrize("placing_on_market_date", ["2024-01-01", "2027-01-01"])
def test_art_111_1_carve_out_is_stated_without_a_flag(placing_on_market_date: str) -> None:
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
    assert "Art. 111(1) AIA" not in report.unverified_citations
    rendered = render_report(report)
    assert f"{ANNEX_X_TEXT}." in rendered
    assert FLAG not in rendered


def test_art_111_1_is_stated_without_a_flag_in_the_binding_timeline() -> None:
    (entry,) = [t for t in _report().timeline if "Art. 111(1)" in t.note]

    assert entry.applies_from == "2030-08-02"
    assert entry.note.endswith(f" {TIMELINE_TEXT}")


def test_the_flag_comes_back_if_a_citation_is_set_back_to_unverified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Setting verified=False in citations.py is the one change that reverses the reading."""

    assert flag_unless_verified(cite("Art. 111(1) AIA", verified=False)) == f" {FLAG}"
    assert flag_unless_verified(ART_111_1) == ""
    # The engine lists an unverified Art. 111(1) wherever the report states the carve-out.
    monkeypatch.setattr(engine, "ART_111_1", Citation("Art. 111(1) AIA", verified=False))
    report = _report(
        roles=[Role.PROVIDER],
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        placing_on_market_date="2024-01-01",
    )
    assert "Art. 111(1) AIA" in report.unverified_citations
    assert "Art. 111(1) AIA" not in _report().unverified_citations


def test_the_annex_i_guidance_example_carries_the_verified_art_6_1c_finding() -> None:
    (example,) = [
        e for e in load_guidance_examples() if e["id"] == "draft-guidance-machinery-safety-stop"
    ]
    report = classify(SystemProfile.model_validate(example["profile"]))

    assert example["profile"]["annex_i_section"] == "B"
    assert [(f.rule_id, f.citation_verified) for f in report.findings] == [
        ("HIGHRISK.6.1", True),
        ("HIGHRISK.6.1c", True),
    ]
    assert report.unverified_citations == []
    # The guidance evaluation compares only these, and they are unchanged.
    assert report.risk_tier.value == example["expected"]["risk_tier"]
    assert report.disposition.value == example["expected"]["disposition"]


def _ledger_rows() -> list[list[str]]:
    rows = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.startswith("| ") and not line.startswith(("| Status", "| ---")):
            rows.append([cell.strip() for cell in line.strip("|").split(" | ")])
    return rows


@pytest.mark.parametrize(
    ("pinpoint", "provision", "digest"),
    [
        (
            "Art. 6(1c)",
            "Art. 6(1c), inserted by Art. 1, point (8) of Regulation (EU) 2026/1744",
            OJ_2026_1744_SHA256,
        ),
        (
            "Art. 2(13)",
            "Art. 2(13), added by Art. 1, point (3) of Regulation (EU) 2026/1744",
            OJ_2026_1744_SHA256,
        ),
        (
            "Art. 111(1)",
            "Art. 111(1), original text, not amended by Regulation (EU) 2026/1744",
            OJ_2024_1689_SHA256,
        ),
    ],
)
def test_the_ledger_records_the_reading_of_each_pinpoint(
    pinpoint: str, provision: str, digest: str
) -> None:
    """The citation is verified only with a ledger row that names the source, the pinpoint
    and the access date (claim ledger rule)."""

    rows = [r for r in _ledger_rows() if r[4].startswith(provision)]
    assert len(rows) == 1, rows
    status, _claim, _actor, source, _provision, access_date, note = rows[0]
    assert status == "VERIFIED"
    assert CITATIONS[pinpoint].verified is True
    assert access_date == "11 November 2026"
    assert "pull request #40" in source
    assert digest in LEDGER.read_text(encoding="utf-8")
    assert "tests/test_reread_pinpoints.py" in note
    # No row still calls it unverified.
    stale = [r for r in _ledger_rows() if r[1].startswith("Not verified") and pinpoint in r[1]]
    assert stale == []


def _profiles() -> list[tuple[str, SystemProfile]]:
    profiles = [
        (path.name, SystemProfile.model_validate_json(path.read_text(encoding="utf-8")))
        for path in sorted(EXAMPLES.glob("*.json"))
        if path.name != "classification-packet.json"
    ]
    # The Commission guidance examples; one of them takes the Annex I, Section B route.
    profiles += [
        (example["id"], SystemProfile.model_validate(example["profile"]))
        for example in load_guidance_examples()
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
def test_every_output_states_the_pinpoints_as_verified(profile: SystemProfile) -> None:
    report = classify(profile, include_advisory=True)

    for finding in report.findings:
        if any(p in finding.citation + finding.detail for p in PINPOINTS):
            assert finding.citation_verified is True, finding.rule_id
    assert not any(c.startswith(PINPOINTS) for c in report.unverified_citations)
    # In prose, no mention of the three carries the flag before its sentence ends.
    prose = [report.scope.transitional_status, *report.open_questions]
    prose += [t.note for t in report.timeline]
    for item in report.obligation_graph:
        prose += [item.trigger, item.requirement, item.application_date_note or ""]
    prose += [f.detail for f in report.findings]
    for text in prose:
        for pinpoint in PINPOINTS:
            for mention in re.finditer(re.escape(pinpoint), text):
                sentence = text[mention.end() :].split(". ", 1)[0]
                assert FLAG not in sentence, text
    # The Art. 111(1) dates appear only in the carve-out, with their citation.
    dump = json.dumps(report.model_dump(mode="json"))
    assert dump.count("31 December 2030") == dump.count("31 December 2030 (Art. 111(1) AIA)")
