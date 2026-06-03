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
    "law_enforcement.json": (RiskTier.HIGH, Disposition.DETERMINED),
    "ambiguous_use_case.json": (RiskTier.HIGH, Disposition.REQUIRES_REVIEW),
    "employment_derogation.json": (RiskTier.HIGH, Disposition.REQUIRES_REVIEW),
    "support_chatbot.json": (RiskTier.LIMITED, Disposition.DETERMINED),
    "deepfake_generator.json": (RiskTier.LIMITED, Disposition.DETERMINED),
    "spam_filter.json": (RiskTier.MINIMAL, Disposition.DETERMINED),
    "foundation_model_systemic.json": (RiskTier.MINIMAL, Disposition.DETERMINED),
    "foundation_model_unknown_compute.json": (RiskTier.MINIMAL, Disposition.REQUIRES_REVIEW),
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
    on_disk = {p.name for p in EXAMPLES.glob("*.json")}
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


def test_systemic_gpai_carries_article_55() -> None:
    report = classify(_load("foundation_model_systemic.json"))
    assert report.gpai_systemic is True
    assert any(ob.article.startswith("Art. 55") for ob in report.obligations)


def test_ambiguous_use_case_flags_unverified_citation() -> None:
    report = classify(_load("ambiguous_use_case.json"))
    assert any("Annex III" in c for c in report.unverified_citations)
