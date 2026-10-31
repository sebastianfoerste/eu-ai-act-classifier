from __future__ import annotations

import pytest

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
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        derogation=Derogation(narrow_procedural_task=True, performs_profiling=True),
    )
    report = classify(profile)
    assert report.risk_tier is RiskTier.HIGH
    assert report.disposition is Disposition.DETERMINED


def test_derogation_triggers_review() -> None:
    profile = SystemProfile(
        name="x",
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
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


# AIA-06: Art. 27 AIA is expected to reach only the high-risk systems referred to in
# Art. 6(2), so a system that is high-risk only through Annex I carries no FRIA. The
# change is blocked until Art. 27(1) is read on EUR-Lex and recorded in
# docs/REGULATORY_CLAIM_LEDGER.md. Remove this marker with the engine change.
ART_27_ANNEX_III_ONLY = pytest.mark.xfail(
    strict=True,
    reason="AIA-06 is blocked on the EUR-Lex reading of Art. 27(1) AIA",
)


@ART_27_ANNEX_III_ONLY
@pytest.mark.parametrize("section", [None, "A"])
@pytest.mark.parametrize(
    "deployer_status", ["deployer_public_law_body", "deployer_private_public_service"]
)
def test_annex_i_only_deployer_gets_no_fria(section: str | None, deployer_status: str) -> None:
    profile = SystemProfile(
        name="machine safety monitor",
        roles=[Role.DEPLOYER],
        annex_i_safety_component=True,
        annex_i_third_party_assessment=True,
        annex_i_section=section,
        **{deployer_status: True},
    )
    report = classify(profile)
    articles = {ob.article for ob in report.obligations}

    assert report.risk_tier is RiskTier.HIGH
    assert "Art. 26 AIA" in articles
    assert "Art. 27 AIA" not in articles
    assert "high-risk.deployer.27" not in {item.obligation_id for item in report.obligation_graph}
    assert not any("Art. 27 AIA" in question for question in report.open_questions)


def test_annex_i_product_in_an_annex_iii_area_keeps_the_fria() -> None:
    profile = SystemProfile(
        name="public benefits triage device",
        roles=[Role.DEPLOYER],
        annex_i_safety_component=True,
        annex_i_third_party_assessment=True,
        annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
        deployer_public_law_body=True,
    )
    report = classify(profile)

    assert "Art. 27 AIA" in {ob.article for ob in report.obligations}
    assert "high-risk.deployer.27" in {item.obligation_id for item in report.obligation_graph}
