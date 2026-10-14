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


# Regression: with no role that places the system on the market, puts it into
# service or uses it, the Art. 5(1)(ba) result must stay UNKNOWN while the use
# limb (Art. 5(1a)(b)) is met; it used to read "not met" because only the
# placing limb was tested (INT-5-routes-by-role).
_USE_LIMB_MET = {
    "generates_material": True,
    "consent_ensured": False,
    "intended_purpose": False,
    "foreseeable_and_reproducible": False,
    "deployer_uses_for_that_purpose": True,
}


@pytest.mark.parametrize("roles", [[], ["distributor"], ["authorized_representative"]])
def test_no_covered_role_keeps_a_met_use_limb_open(roles: list[str]) -> None:
    profile = SystemProfile.model_validate(
        {
            "name": "x",
            "roles": roles,
            "assessment_date": "2026-12-03",
            "intimate_imagery": _USE_LIMB_MET,
            "child_sexual_abuse_material": {"generates_or_manipulates": False},
        }
    )
    report = classify(profile)
    rule_ids = {finding.rule_id for finding in report.findings}
    assert "PROHIBITED.5.1.ba.unknown" in rule_ids
    assert "PROHIBITED.5.1.ba.not_met" not in rule_ids
    assert report.disposition is Disposition.REQUIRES_REVIEW
    assert any("roles" in question for question in report.open_questions)


def test_no_covered_role_is_not_met_when_both_limbs_fail() -> None:
    profile = SystemProfile.model_validate(
        {
            "name": "x",
            "roles": ["distributor"],
            "assessment_date": "2026-12-03",
            "intimate_imagery": {**_USE_LIMB_MET, "deployer_uses_for_that_purpose": False},
            "child_sexual_abuse_material": {"generates_or_manipulates": False},
        }
    )
    rule_ids = {finding.rule_id for finding in classify(profile).findings}
    assert "PROHIBITED.5.1.ba.not_met" in rule_ids
