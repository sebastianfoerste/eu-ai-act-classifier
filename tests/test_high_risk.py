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
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        derogation=Derogation(narrow_procedural_task=True, performs_profiling=True),
    )
    report = classify(profile)
    assert report.risk_tier is RiskTier.HIGH
    assert report.disposition is Disposition.DETERMINED


def test_profiling_rule_cites_the_third_subparagraph_of_article_6_3() -> None:
    # Art. 6(3): first subparagraph is the derogation, second lists conditions (a) to (d),
    # third keeps a profiling Annex III system high-risk.
    profile = SystemProfile(
        name="x",
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        derogation=Derogation(performs_profiling=True),
    )
    details = [finding.detail for finding in classify(profile).findings]
    assert any("Art. 6(3), third subparagraph, AIA" in detail for detail in details)
    assert not any("subpara. 2" in detail for detail in details)


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


def test_credit_and_insurance_labels_are_limited_to_natural_persons() -> None:
    # Annex III(5)(b) and (c) AIA cover natural persons only.
    for area in (AnnexIII.CREDITWORTHINESS, AnnexIII.INSURANCE_LIFE_HEALTH):
        report = classify(SystemProfile(name="x", annex_iii_area=area))
        assert any("natural persons" in finding.title for finding in report.findings)


def test_credit_scoring_without_fraud_purpose_raises_no_fraud_question() -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS))
    assert report.disposition is Disposition.DETERMINED
    assert not any("financial fraud" in question for question in report.open_questions)


def test_asserted_fraud_purpose_on_credit_scoring_stays_high_risk_and_asks() -> None:
    profile = SystemProfile(
        name="x",
        annex_iii_area=AnnexIII.CREDITWORTHINESS,
        used_for_financial_fraud_detection=True,
    )
    report = classify(profile)
    assert report.risk_tier is RiskTier.HIGH
    assert report.disposition is Disposition.REQUIRES_REVIEW
    assert any(
        "Annex III(5)(b) AIA excepts AI systems used for the purpose of detecting financial fraud"
        in question
        for question in report.open_questions
    )


def test_unknown_fraud_purpose_on_credit_scoring_asks_even_with_profiling() -> None:
    profile = SystemProfile(
        name="x",
        annex_iii_area=AnnexIII.CREDITWORTHINESS,
        used_for_financial_fraud_detection=None,
        derogation=Derogation(performs_profiling=True),
    )
    report = classify(profile)
    assert report.risk_tier is RiskTier.HIGH
    assert report.disposition is Disposition.REQUIRES_REVIEW
    assert any("financial fraud" in question for question in report.open_questions)


def test_fraud_question_is_limited_to_annex_iii_5_b() -> None:
    profile = SystemProfile(
        name="x",
        annex_iii_area=AnnexIII.INSURANCE_LIFE_HEALTH,
        used_for_financial_fraud_detection=True,
    )
    report = classify(profile)
    assert not any("financial fraud" in question for question in report.open_questions)
