"""The eval set: every example file must classify as documented.

A rule change that moves any example is caught here. The expectations mirror
`examples/README.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eu_ai_act_classifier import Disposition, RiskTier, SystemProfile, classify

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

EXPECTATIONS: dict[str, tuple[RiskTier, Disposition]] = {
    "social_scoring.json": (RiskTier.PROHIBITED, Disposition.DETERMINED),
    "emotion_hiring.json": (RiskTier.PROHIBITED, Disposition.DETERMINED),
    "cv_screening.json": (RiskTier.HIGH, Disposition.DETERMINED),
    "credit_scoring.json": (RiskTier.HIGH, Disposition.DETERMINED),
    "proctoring_education.json": (RiskTier.HIGH, Disposition.DETERMINED),
    "credit_scoring_deployer.json": (RiskTier.HIGH, Disposition.DETERMINED),
    "life_insurer_pricing.json": (RiskTier.HIGH, Disposition.DETERMINED),
    "law_enforcement.json": (RiskTier.HIGH, Disposition.DETERMINED),
    "ambiguous_use_case.json": (RiskTier.HIGH, Disposition.REQUIRES_REVIEW),
    "employment_derogation.json": (RiskTier.HIGH, Disposition.REQUIRES_REVIEW),
    "support_chatbot.json": (RiskTier.LIMITED, Disposition.DETERMINED),
    "deepfake_generator.json": (RiskTier.LIMITED, Disposition.DETERMINED),
    "spam_filter.json": (RiskTier.MINIMAL, Disposition.DETERMINED),
    "foundation_model_systemic.json": (RiskTier.MINIMAL, Disposition.DETERMINED),
    "foundation_model_unknown_compute.json": (RiskTier.MINIMAL, Disposition.REQUIRES_REVIEW),
    "gpai_non_systemic.json": (RiskTier.MINIMAL, Disposition.DETERMINED),
    "gpai_systemic_by_flops.json": (RiskTier.MINIMAL, Disposition.DETERMINED),
    "gpai_systemic_designated.json": (RiskTier.MINIMAL, Disposition.DETERMINED),
}


def _load(filename: str) -> SystemProfile:
    return SystemProfile.model_validate_json((EXAMPLES / filename).read_text(encoding="utf-8"))


@pytest.mark.parametrize(("filename", "expected"), EXPECTATIONS.items())
def test_example_classification(filename: str, expected: tuple[RiskTier, Disposition]) -> None:
    report = classify(_load(filename))
    expected_tier, expected_disposition = expected
    assert report.risk_tier is expected_tier
    assert report.disposition is expected_disposition


def test_every_example_has_an_expectation() -> None:
    on_disk = {p.name for p in EXAMPLES.glob("*.json") if p.name != "classification-packet.json"}
    assert on_disk == set(EXPECTATIONS), "add new example files to EXPECTATIONS"


def test_prohibited_lists_no_obligations() -> None:
    report = classify(_load("social_scoring.json"))
    assert report.obligations == []
    assert any(f.severity.value == "blocker" for f in report.findings)


def test_credit_deployer_requires_fria() -> None:
    report = classify(_load("credit_scoring_deployer.json"))
    articles = {ob.article for ob in report.obligations}
    assert "Art. 26 AIA" in articles
    assert "Art. 27 AIA" in articles
    # docs/worked-examples/bank-credit-scoring.md states the date of both graph items.
    assert [item.application_date for item in report.obligation_graph] == ["2027-12-02"] * 2


def test_life_insurer_carries_provider_and_deployer_duties() -> None:
    report = classify(_load("life_insurer_pricing.json"))
    articles = {ob.article for ob in report.obligations}
    assert {"Art. 9 AIA", "Art. 43 AIA", "Art. 26 AIA", "Art. 27 AIA"} <= articles
    graph = {item.article for item in report.obligation_graph}
    assert "Art. 43(2) AIA" in graph
    assert "Art. 44 AIA" not in graph
    assert {item.application_date for item in report.obligation_graph} == {"2027-12-02"}
    # Counts stated in docs/worked-examples/life-insurer-pricing.md.
    assert len([ob for ob in report.obligations if ob.applies_to.value == "provider"]) == 14
    assert len(report.documentation_required) == 5
    assert len(report.obligation_graph) == 18
    assert (
        sum(item.review_status.value == "review_required" for item in report.obligation_graph) == 10
    )


def test_systemic_gpai_carries_article_55() -> None:
    report = classify(_load("foundation_model_systemic.json"))
    assert report.gpai_systemic is True
    assert any(ob.article.startswith("Art. 55") for ob in report.obligations)


def test_ambiguous_use_case_flags_unverified_citation() -> None:
    report = classify(_load("ambiguous_use_case.json"))
    assert any("Annex III" in c for c in report.unverified_citations)
