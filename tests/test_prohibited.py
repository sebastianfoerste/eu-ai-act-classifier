from __future__ import annotations

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
        annex_iii_area=AnnexIII.EMPLOYMENT_RECRUITMENT,
        prohibited_practices=[ProhibitedPractice.SOCIAL_SCORING],
    )
    assert classify(profile).risk_tier is RiskTier.PROHIBITED
