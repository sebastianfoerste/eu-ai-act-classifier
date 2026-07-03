from __future__ import annotations

from eu_ai_act_classifier import ExcludedUse, RiskTier, ScopeStatus, SystemProfile, classify


def test_non_ai_system_returns_outside_scope() -> None:
    report = classify(SystemProfile(name="workflow", is_ai_system=False))

    assert report.risk_tier is RiskTier.OUT_OF_SCOPE
    assert report.scope.status is ScopeStatus.OUTSIDE_SCOPE
    assert report.obligations == []


def test_missing_scope_fields_keep_examples_in_scope() -> None:
    report = classify(SystemProfile(name="x"))

    assert report.risk_tier is RiskTier.MINIMAL
    assert report.scope.status is ScopeStatus.IN_SCOPE


def test_unknown_eu_nexus_requires_scope_review() -> None:
    report = classify(SystemProfile(name="x", eu_nexus=None))

    assert report.scope.status is ScopeStatus.REQUIRES_REVIEW
    assert any("EU nexus" in question for question in report.open_questions)


def test_excluded_use_flags_are_surfaced() -> None:
    report = classify(
        SystemProfile(
            name="research sandbox",
            excluded_use_flags=[ExcludedUse.RESEARCH_DEVELOPMENT_TESTING],
        )
    )

    assert report.scope.status is ScopeStatus.REQUIRES_REVIEW
    assert any("excluded-use flags" in question for question in report.open_questions)
    assert any(f.rule_id == "SCOPE.excluded_use_flags" for f in report.findings)


def test_article_111_transition_note_for_legacy_system() -> None:
    report = classify(
        SystemProfile(
            name="legacy",
            placing_on_market_date="2026-01-01",
            significant_change_after_application_date=False,
        )
    )

    assert "Article 111" in report.scope.transitional_status
