from __future__ import annotations

import pytest

from eu_ai_act_classifier import (
    AnnexIII,
    ExcludedUse,
    RiskTier,
    Role,
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
    assert "Art. 111(2) excludes components of the Annex X large-scale IT systems" in status
    # Art. 111(2) uses one date twice: before 2026-08-02 the system is a legacy system on
    # either reading, but the change window ("as from that date") opens on 2026-08-02 on
    # the general-date reading, so the result is still flagged.
    flag = status[status.index("Literal reading") :]
    assert flag.startswith("Literal reading, confirm with counsel: Art. 111(2) AIA refers to")
    assert "a significant change in design made on or after that date already counts" in flag
    assert "not a legacy system" not in flag


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

    # Art. 111(2), second sentence: "in any case ... take the necessary steps to comply
    # ... by 2 August 2030", for a system placed before the Chapter III date. Undated, that
    # is a condition, not a fact.
    duty = "in any case take the necessary steps to comply with the requirements"
    assert "no placing-on-market or putting-into-service date is given" in undated
    assert (
        "if it was placed on the market or put into service before that date, its providers "
        f"and deployers {duty}"
    ) in undated
    assert "by 2 August 2030" in undated
    assert "placed on the market on 2026-01-15, before 2027-12-02" in dated
    assert f"its providers and deployers {duty}" in dated
    assert "by 2 August 2030" in dated
    # Both rest on the contested Chapter III date.
    for status in (undated, dated):
        assert "Literal reading, confirm with counsel: Art. 111(2) AIA refers to" in status


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


@pytest.mark.parametrize("change", [True, False, None])
def test_undated_transitional_status_reports_a_change_answer_as_not_used(
    change: bool | None,
) -> None:
    # Without a date the profile cannot show a legacy system, so the check states the
    # condition and does not use a change answer (the guided intake does not ask it).
    status = classify(
        SystemProfile(
            name="x",
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            significant_change_after_application_date=change,
            public_authority_use=True,
        )
    ).scope.transitional_status

    assert status.startswith("Article 111(2) check: no placing-on-market")
    assert "If the system was placed on the market or put into service before that date" in status
    assert "design is asserted" not in status
    assert "the asserted change counts" not in status
    unused = "significant_change_after_application_date is given, but it is not used"
    assert (unused in status) is (change is not None)
    # Undated, both uses of the contested date are open: the legacy status and the window.
    flag = status[status.index("Literal reading") :]
    assert flag.startswith("Literal reading, confirm with counsel: Art. 111(2) AIA refers to")
    assert "on or after that date is not a legacy system, and for an earlier system" in flag


def test_dated_transitional_status_with_an_asserted_change() -> None:
    status = classify(
        SystemProfile(
            name="x",
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            placing_on_market_date="2026-01-01",
            significant_change_after_application_date=True,
        )
    ).scope.transitional_status

    # Whether the change counts turns on which date "as from that date" means, so the text
    # does not date it; the flag states both candidates.
    assert "a significant change in design is asserted, so the Regulation applies" in status
    assert "the Regulation applies to the changed system" in status
    assert "as from that date is asserted" not in status
    assert "Literal reading, confirm with counsel" in status


@pytest.mark.parametrize(
    ("facts", "wording"),
    [
        (
            {"significant_change_after_application_date": True},
            "significant_change_after_application_date is given, but it is not used",
        ),
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


@pytest.mark.parametrize(
    ("facts", "applied"),
    [
        ({"deployer_public_authority": True}, False),
        ({"significant_change_after_application_date": False}, False),
        ({"placing_on_market_date": "2025-01-01"}, True),
        ({"public_authority_use": True}, True),
    ],
)
def test_prohibited_transitional_status_needs_a_fact_the_check_compares(
    facts: dict[str, object], applied: bool
) -> None:
    status = classify(
        SystemProfile(name="x", prohibited_practices=["5.1.c"], **facts)
    ).scope.transitional_status

    assert ("not applied, as an Art. 5 prohibited practice is screened" in status) is applied


def test_transitional_status_for_a_system_only_put_into_service_before_the_date() -> None:
    status = classify(
        SystemProfile(
            name="in-house tool",
            roles=[Role.DEPLOYER],
            annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
            putting_into_service_date="2025-06-01",
        )
    ).scope.transitional_status

    assert status.startswith(
        "Article 111(2) check: the system was put into service on 2025-06-01, before 2027-12-02"
    )
    assert "placed on the market" not in status.split(", when Chapter III")[0]
    assert "Literal reading, confirm with counsel" in status


@pytest.mark.parametrize(
    ("placed", "legacy"),
    [
        pytest.param("2028-08-01", True, id="day-before"),
        pytest.param("2028-08-02", False, id="same-day"),
    ],
)
def test_transitional_status_at_the_annex_i_date(placed: str, legacy: bool) -> None:
    status = classify(
        SystemProfile(
            name="AI-enabled lift controller",
            annex_i_safety_component=True,
            annex_i_third_party_assessment=True,
            placing_on_market_date=placed,
        )
    ).scope.transitional_status

    if legacy:
        assert f"placed on the market on {placed}, before 2028-08-02" in status
        # Between the general date and the point (c)(ii) date the legacy status itself
        # turns on the reading.
        assert "on or after that date is not a legacy system" in status
    else:
        assert f"placed on the market on {placed}, not before 2028-08-02" in status
        assert "the Art. 111(2) transition does not apply" in status


def test_transitional_status_on_the_same_day_as_the_annex_iii_date() -> None:
    # "Before" excludes the date itself.
    status = classify(
        SystemProfile(
            name="x",
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            placing_on_market_date="2027-12-02",
        )
    ).scope.transitional_status

    assert "placed on the market on 2027-12-02, not before 2027-12-02" in status
    assert "the Art. 111(2) transition does not apply" in status


@pytest.mark.parametrize(
    ("placed", "legacy_as_classified"),
    [
        pytest.param("2028-01-01", False, id="legacy-only-if-derogation-holds"),
        pytest.param("2027-01-01", True, id="legacy-either-way"),
    ],
)
def test_transitional_status_names_the_date_an_asserted_derogation_would_give(
    placed: str, legacy_as_classified: bool
) -> None:
    # Annex I (Section A) product also in an Annex III area: as classified, point (c)(i)
    # dates it; if the Art. 6(3) derogation is established only Art. 6(1) and Annex I
    # classify it, so point (c)(ii) does (Art. 113, third paragraph, point (c)).
    report = classify(
        SystemProfile(
            name="x",
            annex_i_safety_component=True,
            annex_i_third_party_assessment=True,
            annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
            derogation={"narrow_procedural_task": True},
            placing_on_market_date=placed,
        )
    )
    status = report.scope.transitional_status

    assert "If the asserted Art. 6(3) derogation is established" in status
    assert "its Chapter III date is 2028-08-02" in status
    if legacy_as_classified:
        assert f"placed on the market on {placed}, before 2027-12-02" in status
    else:
        assert f"placed on the market on {placed}, not before 2027-12-02" in status
        assert "the Art. 111(2) transition would apply to it" in status
        # On the general date it is no legacy system on either route, so the result
        # rests on the contested cut-off (Art. 111(2) with Art. 113).
        flag = (
            "Literal reading, confirm with counsel: this uses 2028-08-02 as the Art. 111(2) "
            "AIA cut-off. If the general date of 2026-08-02 is meant, the system is not a "
            "legacy system on either route."
        )
        assert flag in status
        (question,) = [
            q
            for q in report.open_questions
            if q.startswith("Art. 111(2) AIA:") and "derogation" in q
        ]
        assert flag in question


@pytest.mark.parametrize(
    ("facts", "wording"),
    [
        pytest.param(
            {"gpai_model_placing_on_market_date": "2025-03-01"},
            "the general-purpose AI model was placed on the market on 2025-03-01, before "
            "2025-08-02, so its provider takes the necessary steps to comply with the "
            "obligations laid down in this Regulation by 2027-08-02",
            id="model-date-only",
        ),
        pytest.param(
            {"gpai_model_placing_on_market_date": "2025-09-01"},
            "not before 2025-08-02, so the Art. 111(3) transition does not apply",
            id="model-after-cut-off",
        ),
        pytest.param(
            {"placing_on_market_date": "2025-03-01"},
            "dated by the AI system's placing_on_market_date, 2025-03-01, before 2025-08-02",
            id="fallback",
        ),
    ],
)
def test_transitional_status_counts_the_gpai_model_date(
    facts: dict[str, object], wording: str
) -> None:
    status = classify(
        SystemProfile(name="model", roles=[Role.GPAI_PROVIDER], is_gpai_model=True, **facts)
    ).scope.transitional_status

    assert "Article 111(3) check:" in status
    assert wording in status
    assert status != "No transitional limitation identified from the submitted facts."


@pytest.mark.parametrize(
    ("placed", "wording"),
    [
        pytest.param(
            "2026-05-01",
            "before 2026-08-02, so its provider takes the necessary steps to comply with "
            "Art. 50(2) by 2026-12-02",
            id="before",
        ),
        pytest.param(
            "2026-08-02",
            "not before 2026-08-02, so the Art. 111(4) transition does not apply",
            id="same-day",
        ),
    ],
)
def test_transitional_status_names_art_111_4_for_synthetic_content(
    placed: str, wording: str
) -> None:
    status = classify(
        SystemProfile(
            name="image generator", generates_synthetic_content=True, placing_on_market_date=placed
        )
    ).scope.transitional_status

    assert f"Article 111(4) check: the system was placed on the market on {placed}" in status
    assert wording in status


def test_transitional_status_says_a_model_date_without_a_model_is_not_used() -> None:
    status = classify(
        SystemProfile(name="x", gpai_model_placing_on_market_date="2025-03-01")
    ).scope.transitional_status

    assert "is_gpai_model is false" in status
    assert "the date is not used" in status
