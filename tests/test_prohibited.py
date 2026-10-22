from __future__ import annotations

import pytest

from eu_ai_act_classifier import (
    AnnexIII,
    Disposition,
    ProhibitedPractice,
    RiskTier,
    SystemProfile,
    classify,
)


def test_single_prohibited_practice() -> None:
    profile = SystemProfile(name="x", prohibited_practices=[ProhibitedPractice.SOCIAL_SCORING])
    report = classify(profile)
    assert report.risk_tier is RiskTier.PROHIBITED
    assert report.disposition is Disposition.DETERMINED
    assert report.obligations == []


def test_prohibited_dominates_high_risk() -> None:
    profile = SystemProfile(
        name="x",
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        prohibited_practices=[ProhibitedPractice.SOCIAL_SCORING],
    )
    assert classify(profile).risk_tier is RiskTier.PROHIBITED


# Art. 5(1)(ba) and (bb) AIA, inserted by Regulation (EU) 2026/1744, apply from
# 2 December 2026 (Art. 113, third paragraph, point (a)). The finding says so in every
# run, so the output does not depend on the date it is produced.
@pytest.mark.parametrize(
    ("practice", "citation", "title", "quoted", "art_5_1b"),
    [
        (
            ProhibitedPractice.NON_CONSENSUAL_INTIMATE_IMAGERY,
            "Art. 5(1)(ba) AIA",
            "Generating or manipulating realistic intimate material of an identifiable person "
            "without consent",
            "of an identifiable natural person's intimate parts, or of an identifiable natural "
            "person engaged in sexually explicit activities, without that person's "
            "freely-given, specific, informed, unambiguous and explicit consent",
            True,
        ),
        (
            ProhibitedPractice.CHILD_SEXUAL_ABUSE_MATERIAL,
            "Art. 5(1)(bb) AIA",
            "Generating or manipulating child sexual abuse material under Directive 2011/93/EU, "
            "save a 'without right' defence under national law",
            "material or performance within the meaning of Article 2, points (c) and (e), of "
            "Directive 2011/93/EU, except where a 'without right' defence applies under "
            "national law",
            False,
        ),
    ],
)
def test_later_prohibitions_are_dated_from_2_december_2026(
    practice: ProhibitedPractice, citation: str, title: str, quoted: str, art_5_1b: bool
) -> None:
    report = classify(SystemProfile(name="x", prohibited_practices=[practice]))
    (finding,) = report.findings

    assert citation == f"Art. 5(1)({practice.value.removeprefix('5.1.')}) AIA"
    assert report.risk_tier is RiskTier.PROHIBITED
    assert finding.rule_id == f"PROHIBITED.{practice.value}"
    assert finding.citation == citation
    assert finding.title == f"{title} (prohibited from 2 December 2026)"
    assert finding.detail.startswith(
        "Prohibited practice under Art. 5 AIA from 2 December 2026 (2026-12-02;"
    )
    assert quoted in finding.detail
    assert "no transition for systems already on the market" in finding.detail
    # Art. 5(1a) and (1b) are quoted, not paraphrased.
    assert (
        'Art. 5(1a): "(a) the placing on the market or putting into service of an AI system'
        in finding.detail
    )
    assert (
        "taking into account reasonably foreseeable misuse, and to correct observed or "
        "reported misuse" in finding.detail
    )
    assert ('Art. 5(1b): "an AI system that manipulates material' in finding.detail) is art_5_1b
    assert "Literal reading" not in finding.detail
    assert any(
        item.applies_from == "2026-12-02" and "Art. 5(1)(ba) and (bb)" in item.provision
        for item in report.timeline
    )


def test_original_prohibitions_keep_their_undated_detail() -> None:
    (finding,) = classify(
        SystemProfile(name="x", prohibited_practices=[ProhibitedPractice.SOCIAL_SCORING])
    ).findings

    assert "2 December 2026" not in finding.title + finding.detail


def test_advisory_note_says_the_guidelines_predate_the_new_bans() -> None:
    def detail(practice: ProhibitedPractice) -> str:
        report = classify(
            SystemProfile(name="x", prohibited_practices=[practice]), include_advisory=True
        )
        (note,) = [n for n in report.advisory_notes if n.note_id == "guidance.prohibited-practices"]
        return note.detail

    assert "predates Art. 5(1)(ba) and (bb)" in detail(
        ProhibitedPractice.CHILD_SEXUAL_ABUSE_MATERIAL
    )
    assert "predates" not in detail(ProhibitedPractice.SOCIAL_SCORING)
