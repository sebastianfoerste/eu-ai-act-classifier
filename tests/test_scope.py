from __future__ import annotations

import pytest

from eu_ai_act_classifier import (
    AnnexIII,
    ExcludedUse,
    RiskTier,
    ScopeStatus,
    SystemProfile,
    classify,
)


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


def test_no_dates_and_no_transition_facts_keep_the_default_status() -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS))

    assert report.scope.transitional_status == (
        "No transitional limitation identified from the submitted facts."
    )


@pytest.mark.parametrize(
    ("facts", "cut_off", "point"),
    [
        pytest.param({"annex_iii_area": AnnexIII.CREDITWORTHINESS}, "2027-12-02", "(c)(i)"),
        pytest.param(
            {"annex_i_safety_component": True, "annex_i_third_party_assessment": True},
            "2028-08-02",
            "(c)(ii)",
        ),
        # Also an Annex I product, but still classified under Art. 6(2) and Annex III.
        pytest.param(
            {
                "annex_i_safety_component": True,
                "annex_i_third_party_assessment": True,
                "annex_iii_area": AnnexIII.CREDITWORTHINESS,
            },
            "2027-12-02",
            "(c)(i)",
        ),
    ],
)
def test_transitional_status_compares_both_dates_with_the_chapter_iii_date(
    facts: dict[str, object], cut_off: str, point: str
) -> None:
    status = classify(
        SystemProfile(
            name="legacy",
            placing_on_market_date="2025-05-01",
            putting_into_service_date="2025-06-01",
            significant_change_after_application_date=False,
            **facts,
        )
    ).scope.transitional_status

    assert status.startswith("Article 111(2) check: the system was placed on the market on ")
    assert "placed on the market on 2025-05-01 and put into service on 2025-06-01" in status
    assert f"before {cut_off}, when Chapter III, Sections 1 to 3 apply" in status
    assert f"point {point} AIA" in status
    assert "No significant change in design is asserted".lower() in status.lower()
    assert "Literal reading" not in status


def test_transitional_status_says_when_the_transition_does_not_apply() -> None:
    status = classify(
        SystemProfile(
            name="new system",
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            putting_into_service_date="2027-12-02",
        )
    ).scope.transitional_status

    assert "put into service on 2027-12-02, not before 2027-12-02" in status
    assert "the Art. 111(2) transition does not apply" in status


def test_transitional_status_flags_a_date_between_the_two_readings() -> None:
    status = classify(
        SystemProfile(
            name="legacy",
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            placing_on_market_date="2026-09-01",
        )
    ).scope.transitional_status

    assert "before 2027-12-02" in status
    flag = status[status.index("Literal reading") :]
    assert flag.startswith("Literal reading, confirm with counsel: Art. 111(2) AIA refers to")
    assert "general date of 2026-08-02" in flag


def test_transitional_status_adds_the_public_authority_deadline() -> None:
    profile = SystemProfile(
        name="benefits triage",
        annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
        public_authority_use=True,
    )
    undated = classify(profile).scope.transitional_status
    dated = classify(
        profile.model_copy(update={"placing_on_market_date": "2026-01-15"})
    ).scope.transitional_status

    assert "no placing-on-market or putting-into-service date is given" in undated
    assert "If the system was placed on the market or put into service before" in undated
    assert "deployers comply by 2 August 2030 in any case" in undated
    assert "placed on the market on 2026-01-15, before 2027-12-02" in dated
    assert "deployers comply by 2 August 2030 in any case" in dated


def test_transitional_status_without_a_high_risk_route() -> None:
    status = classify(
        SystemProfile(
            name="legacy",
            placing_on_market_date="2026-01-01",
            significant_change_after_application_date=False,
        )
    ).scope.transitional_status

    assert "placed on the market on 2026-01-01" in status
    assert "no high-risk route is screened" in status


def test_transitional_status_for_a_section_b_product() -> None:
    status = classify(
        SystemProfile(
            name="AI-enabled machinery",
            annex_i_safety_component=True,
            annex_i_third_party_assessment=True,
            annex_i_section="B",
            placing_on_market_date="2026-01-01",
        )
    ).scope.transitional_status

    assert "Annex I, Section B product" in status
    assert "Art. 2(2) AIA" in status
    assert "Art. 111 is among them" in status
    assert "no Chapter III duty attaches" in status


def test_transitional_status_names_only_the_earlier_date_as_before() -> None:
    status = classify(
        SystemProfile(
            name="x",
            annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
            placing_on_market_date="2027-12-01",
            putting_into_service_date="2029-01-01",
        )
    ).scope.transitional_status

    assert "placed on the market on 2027-12-01, before 2027-12-02" in status
    assert "and put into service on 2029-01-01:" in status
    assert "put into service on 2029-01-01, before" not in status


@pytest.mark.parametrize(
    ("change", "wording"),
    [
        (True, "A significant change in design is asserted, so the Regulation applies"),
        (False, "No significant change in design is asserted. If the system was placed"),
        (None, "If the system was placed on the market or put into service before that date"),
    ],
)
def test_undated_transitional_status_follows_the_significant_change_fact(
    change: bool | None, wording: str
) -> None:
    status = classify(
        SystemProfile(
            name="x",
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            significant_change_after_application_date=change,
            public_authority_use=change is None,
        )
    ).scope.transitional_status

    assert status.startswith("Article 111(2) check: no placing-on-market")
    assert wording in status


def test_dated_transitional_status_with_an_asserted_change() -> None:
    status = classify(
        SystemProfile(
            name="x",
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            placing_on_market_date="2026-01-01",
            significant_change_after_application_date=True,
        )
    ).scope.transitional_status

    assert "a significant change in design as from that date is asserted" in status
    assert "the Regulation applies to the changed system" in status


@pytest.mark.parametrize(
    ("facts", "wording"),
    [
        ({"significant_change_after_application_date": True}, "a significant change in design"),
        ({"public_authority_use": True}, "public-authority use is asserted"),
        ({}, None),
    ],
)
def test_transitional_status_without_dates_or_a_high_risk_route(
    facts: dict[str, object], wording: str | None
) -> None:
    status = classify(SystemProfile(name="x", **facts)).scope.transitional_status

    if wording is None:
        assert status == "No transitional limitation identified from the submitted facts."
    else:
        assert status.startswith("Article 111(2) check:")
        assert wording in status
