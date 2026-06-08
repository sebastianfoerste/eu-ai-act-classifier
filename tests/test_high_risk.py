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


def test_critical_infrastructure_deployer_has_no_fria_question() -> None:
    profile = SystemProfile(
        name="grid monitor",
        roles=[Role.DEPLOYER],
        annex_iii_area=AnnexIII.CRITICAL_INFRASTRUCTURE,
    )
    report = classify(profile)

    assert "Art. 27 AIA" not in {ob.article for ob in report.obligations}
    assert not any("Art. 27 AIA" in question for question in report.open_questions)


def test_life_health_insurance_deployer_requires_fria() -> None:
    profile = SystemProfile(
        name="insurance pricing",
        roles=[Role.DEPLOYER],
        annex_iii_area=AnnexIII.INSURANCE_LIFE_HEALTH,
    )
    report = classify(profile)

    assert "Art. 27 AIA" in {ob.article for ob in report.obligations}


def test_public_law_deployer_requires_fria() -> None:
    profile = SystemProfile(
        name="public service triage",
        roles=[Role.DEPLOYER],
        annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
        deployer_public_law_body=True,
    )
    report = classify(profile)

    assert "Art. 27 AIA" in {ob.article for ob in report.obligations}


def test_private_public_service_deployer_requires_fria() -> None:
    profile = SystemProfile(
        name="public transport triage",
        roles=[Role.DEPLOYER],
        annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
        deployer_private_public_service=True,
    )
    report = classify(profile)

    assert "Art. 27 AIA" in {ob.article for ob in report.obligations}
