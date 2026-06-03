from __future__ import annotations

from eu_ai_act_classifier import (
    AnnexIII,
    Derogation,
    Disposition,
    RiskTier,
    Role,
    SystemProfile,
    classify,
)


def test_annex_iii_is_high_risk() -> None:
    profile = SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS)
    assert classify(profile).risk_tier is RiskTier.HIGH


def test_annex_i_product_safety_route() -> None:
    profile = SystemProfile(
        name="x", annex_i_safety_component=True, annex_i_third_party_assessment=True
    )
    assert classify(profile).risk_tier is RiskTier.HIGH


def test_profiling_forecloses_derogation() -> None:
    profile = SystemProfile(
        name="x",
        annex_iii_area=AnnexIII.EMPLOYMENT_RECRUITMENT,
        derogation=Derogation(narrow_procedural_task=True, performs_profiling=True),
    )
    report = classify(profile)
    assert report.risk_tier is RiskTier.HIGH
    assert report.disposition is Disposition.DETERMINED


def test_derogation_triggers_review() -> None:
    profile = SystemProfile(
        name="x",
        annex_iii_area=AnnexIII.EMPLOYMENT_RECRUITMENT,
        derogation=Derogation(narrow_procedural_task=True),
    )
    report = classify(profile)
    assert report.risk_tier is RiskTier.HIGH
    assert report.disposition is Disposition.REQUIRES_REVIEW


def test_provider_gets_full_obligation_set() -> None:
    profile = SystemProfile(
        name="x", roles=[Role.PROVIDER], annex_iii_area=AnnexIII.CREDITWORTHINESS
    )
    articles = {ob.article for ob in classify(profile).obligations}
    assert {"Art. 9 AIA", "Art. 11 AIA", "Art. 43 AIA", "Art. 72 AIA"} <= articles


def test_unsure_area_is_conservative_high_and_review() -> None:
    profile = SystemProfile(name="x", annex_iii_area=AnnexIII.UNSURE)
    report = classify(profile)
    assert report.risk_tier is RiskTier.HIGH
    assert report.disposition is Disposition.REQUIRES_REVIEW
