"""An unknown deployer status goes to review wherever it changes the result.

Art. 49(3) AIA turns on whether the deployer is, or acts on behalf of, a public authority or
Union institution, body, office or agency; Art. 49(5) AIA registers Annex III point 2 at
national level instead; and the 2 August 2030 date in Art. 111(2), second sentence, AIA turns
on intended use by public authorities, which a public-authority deployer may indicate. A
missing deployer_public_authority used to read like "no" in some of these contexts, so the
guided intake blocked "I don't know". Each context now raises an open question, and the
intake records "I don't know" as null.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eu_ai_act_classifier import AnnexIII, Role, SystemProfile, classify
from eu_ai_act_classifier.intake import (
    CHANGE_OPEN,
    PUBLIC_AUTHORITY_STATUS_OPEN,
    QUESTIONS,
    holds,
)
from eu_ai_act_classifier.models import ClassificationReport
from eu_ai_act_classifier.rules.scope import _PUBLIC_AUTHORITY_STATUS_UNUSED
from eu_ai_act_classifier.transitions import change_used, public_authority_status_used

ROOT = Path(__file__).resolve().parents[1]
ANNEX_I = {"annex_i_safety_component": True, "annex_i_third_party_assessment": True}
# The Art. 27 facts are answered, so only the status can hold a result open.
FRIA_SETTLED = {"deployer_public_law_body": False, "deployer_private_public_service": False}


def _report(roles: tuple[Role, ...] = (Role.DEPLOYER,), **facts: object) -> ClassificationReport:
    return classify(SystemProfile(name="x", roles=list(roles), **facts))


def _status_questions(report: ClassificationReport) -> list[str]:
    return [q for q in report.open_questions if "(deployer_public_authority)" in q]


@pytest.mark.parametrize(
    "area",
    [
        AnnexIII.CREDITWORTHINESS,
        AnnexIII.INSURANCE_LIFE_HEALTH,
        AnnexIII.EMPLOYMENT_SELECTION,
        AnnexIII.UNSURE,
    ],
)
def test_an_unknown_status_on_an_annex_iii_point_asks_art_49_3(area: AnnexIII) -> None:
    report = _report(annex_iii_area=area, **FRIA_SETTLED)

    (question,) = _status_questions(report)
    assert question.startswith("Art. 49(3) AIA: the deployer's status is not given.")
    assert ("If the Annex III point is 2" in question) is (area is AnnexIII.UNSURE)
    assert report.disposition.value == "requires_review"
    # Nothing points to the status, so no registration item is inferred.
    assert "Art. 49(3) AIA" not in {i.article for i in report.obligation_graph}
    for status in (True, False):
        stated = _report(annex_iii_area=area, deployer_public_authority=status, **FRIA_SETTLED)
        assert _status_questions(stated) == []
        if area is not AnnexIII.UNSURE and status is False:
            assert stated.disposition.value == "determined"


@pytest.mark.parametrize("use", [False, True])
def test_an_unknown_status_on_point_2_asks_with_the_art_49_5_pointer(use: bool) -> None:
    facts = {"annex_iii_area": AnnexIII.CRITICAL_INFRASTRUCTURE, "public_authority_use": use}
    report = _report(**facts)

    (question,) = _status_questions(report)
    assert question.startswith("Art. 49(5) AIA:")
    assert "registered at national level" in question
    assert ("intended to be used by public authorities, but" in question) is use
    # Art. 49(5) names no addressee, so the sentence is advice, not a duty.
    assert "should check what the national procedure asks of it" in question
    assert _status_questions(_report(deployer_public_authority=False, **facts)) == []


_CUT_OFF_USED = (
    "Literal reading, confirm with counsel: this uses 2028-08-02 as the Art. 111(2) AIA "
    "cut-off. If the general date of 2026-08-02 is meant, "
)
_CONTESTED = _CUT_OFF_USED + (
    "the system is not a legacy system and the 2 August 2030 date does not apply to it."
)
_UNDATED = (
    "Give the date the system was placed on the market or put into service "
    "(placing_on_market_date, putting_into_service_date). "
    + _CUT_OFF_USED
    + "only a system placed on the market or put into service before that date is a legacy "
    "system."
)


@pytest.mark.parametrize(
    ("dates", "flag"),
    [
        pytest.param({}, _UNDATED, id="undated"),
        pytest.param({"placing_on_market_date": "2026-08-01"}, None, id="before-general-date"),
        pytest.param({"placing_on_market_date": "2026-08-02"}, _CONTESTED, id="on-general-date"),
        pytest.param({"putting_into_service_date": "2028-08-01"}, _CONTESTED, id="day-before"),
        pytest.param(
            {"placing_on_market_date": "2025-01-01", "putting_into_service_date": "2027-01-01"},
            None,
            id="earliest-before-general-date",
        ),
        pytest.param(
            {"placing_on_market_date": "2029-01-01", "putting_into_service_date": "2027-01-01"},
            _CONTESTED,
            id="only-legacy-date-in-the-window",
        ),
    ],
)
def test_the_art_111_2_status_question_flags_the_cut_off_where_the_answer_rests_on_it(
    dates: dict[str, str], flag: str | None
) -> None:
    report = _report(annex_i_legislation="I.A.2", **ANNEX_I, **dates)

    (question,) = _status_questions(report)
    assert "; a public-authority deployer may indicate that use. Confirm" in question
    if flag is None:
        assert "Literal reading" not in question
        assert question.endswith("(deployer_public_authority).")
    else:
        assert question.endswith(f"(deployer_public_authority). {flag}")


@pytest.mark.parametrize(
    ("dates", "asked"),
    [
        pytest.param({}, True, id="undated"),
        pytest.param({"placing_on_market_date": "2025-01-01"}, True, id="legacy"),
        pytest.param({"putting_into_service_date": "2028-08-01"}, True, id="day-before"),
        pytest.param({"putting_into_service_date": "2028-08-02"}, False, id="on-the-date"),
        pytest.param({"placing_on_market_date": "2028-08-03"}, False, id="day-after"),
    ],
)
def test_an_unknown_status_on_an_annex_i_route_asks_for_the_2030_date(
    dates: dict[str, str], asked: bool
) -> None:
    # Annex I, Section A (toys): the Chapter III date is 2 August 2028 (Art. 113, third
    # paragraph, point (c)(ii) AIA).
    report = _report(annex_i_legislation="I.A.2", **ANNEX_I, **dates)

    questions = _status_questions(report)
    assert bool(questions) is asked
    if asked:
        (question,) = questions
        assert question.startswith("Art. 111(2) AIA:")
        assert "2 August 2030" in question
        assert "(public_authority_use)" in question
        undated = "no placing-on-market or putting-into-service date is given to compare"
        placed_before = "and was placed on the market or put into service before 2028-08-02"
        assert (undated in question) is (not dates)
        assert (placed_before in question) is (not dates)
        assert question.startswith("Art. 111(2) AIA: the system was") is bool(dates)
        assert ("(placing_on_market_date, putting_into_service_date)" in question) is (not dates)
        # Legacy on either reading of the cut-off, so no flag; undated, the flag.
        assert ("Literal reading, confirm with counsel" in question) is (
            not dates or dates == {"putting_into_service_date": "2028-08-01"}
        )


@pytest.mark.parametrize(
    "facts",
    [
        pytest.param({**ANNEX_I, "annex_i_legislation": "I.B.21"}, id="section-b-product"),
        pytest.param(
            {**ANNEX_I, "annex_i_legislation": "I.A.2", "public_authority_use": True},
            id="public-authority-use",
        ),
        pytest.param(
            {**ANNEX_I, "annex_i_legislation": "I.A.2", "deployer_public_authority": False},
            id="status-false",
        ),
        pytest.param(
            {**ANNEX_I, "annex_i_legislation": "I.A.2", "deployer_public_authority": True},
            id="status-true",
        ),
    ],
)
def test_no_status_question_where_the_status_is_given_or_changes_nothing(
    facts: dict[str, object],
) -> None:
    assert _status_questions(_report(**facts)) == []


def test_no_status_question_without_the_deployer_role() -> None:
    report = _report((Role.PROVIDER,), annex_i_legislation="I.A.2", **ANNEX_I)

    assert _status_questions(report) == []


# Art. 5(1)(ba) and (bb) AIA apply from 2 December 2026 (Art. 113, third paragraph, point
# (a) AIA), so the engine tests the Art. 5 gate's vote, not the declared list
# (transitions.prohibition_applies).
_STATUS_UNUSED = "deployer_public_authority is given, but it is not used"
_CHANGE_UNUSED = "significant_change_after_application_date is given, but it is not used"
_NO_TRANSITION = "No transitional limitation identified from the submitted facts."
_LEGACY_ANNEX_I = {
    **ANNEX_I,
    "annex_i_legislation": "I.A.11",
    "placing_on_market_date": "2026-07-01",
}


@pytest.mark.parametrize("practice", ["5.1.ba", "5.1.bb"])
@pytest.mark.parametrize("assessed", ["2026-11-16", "2026-12-01"])
def test_a_declared_point_that_does_not_yet_apply_leaves_the_status_and_change_in_use(
    practice: str, assessed: str
) -> None:
    facts = {**_LEGACY_ANNEX_I, "prohibited_practices": [practice], "assessment_date": assessed}
    profile = SystemProfile(name="x", roles=[Role.DEPLOYER], **facts)
    unknown = _report(**facts)

    assert unknown.risk_tier.value == "high_risk"
    assert public_authority_status_used(profile) and change_used(profile)
    (question,) = _status_questions(unknown)
    assert question.startswith("Art. 111(2) AIA: the system was")
    assert any("(significant_change_after_application_date)" in q for q in unknown.open_questions)
    assert "not applied, as an Art. 5 prohibited practice" not in unknown.scope.transitional_status
    data = profile.model_dump(mode="json")
    assert holds(PUBLIC_AUTHORITY_STATUS_OPEN, data) and holds(CHANGE_OPEN, data)
    stated = {
        status: _report(
            **facts,
            deployer_public_authority=status,
            significant_change_after_application_date=status,
        )
        for status in (True, False)
    }
    for report in stated.values():
        assert _status_questions(report) == []
        assert _STATUS_UNUSED not in report.scope.transitional_status
        assert _CHANGE_UNUSED not in report.scope.transitional_status
    assert stated[True].model_dump() != stated[False].model_dump()


@pytest.mark.parametrize("assessed", ["2026-12-02", None])
def test_a_declared_point_that_applies_leaves_the_status_unused(assessed: str | None) -> None:
    facts = {**_LEGACY_ANNEX_I, "prohibited_practices": ["5.1.ba"], "assessment_date": assessed}
    unknown = _report(**facts)

    assert unknown.risk_tier.value == "prohibited"
    assert _status_questions(unknown) == []
    stated = _report(**facts, deployer_public_authority=True)
    assert _STATUS_UNUSED in stated.scope.transitional_status


def test_a_declared_point_before_its_date_asks_the_art_49_3_status() -> None:
    facts = {
        "annex_iii_area": AnnexIII.EMPLOYMENT_SELECTION,
        "prohibited_practices": ["5.1.ba"],
        "assessment_date": "2026-11-16",
        **FRIA_SETTLED,
    }
    (question,) = _status_questions(_report(**facts))

    assert question.startswith("Art. 49(3) AIA: the deployer's status is not given.")
    assert (
        _STATUS_UNUSED
        not in _report(**facts, deployer_public_authority=True).scope.transitional_status
    )


_ESTABLISHING_SCREENS = {
    "intimate_imagery": {
        "generates_material": True,
        "consent_ensured": False,
        "intended_purpose": True,
        "deployer_uses_for_that_purpose": True,
    },
    "child_sexual_abuse_material": {
        "generates_or_manipulates": True,
        "without_right_defence_applies": False,
        "intended_purpose": True,
        "deployer_uses_for_that_purpose": True,
    },
}
_ROUTES = {
    "annex-i-dated": _LEGACY_ANNEX_I,
    "annex-i-undated": {**ANNEX_I, "annex_i_legislation": "I.A.11"},
    "annex-iii": {"annex_iii_area": AnnexIII.EMPLOYMENT_SELECTION},
}


def _without_status_unused(report: ClassificationReport) -> dict:
    # The scope note repeats the transitional status, which falls back to a fixed
    # sentence when nothing else is left (as in tests/test_intake.py).
    data = report.model_dump(mode="json")
    scope = data["scope"]

    def drop(text: str) -> str:
        return " ".join(text.replace(_PUBLIC_AUTHORITY_STATUS_UNUSED, "").split())

    scope["notes"] = [note for note in map(drop, scope["notes"]) if note]
    scope["transitional_status"] = drop(scope["transitional_status"]) or _NO_TRANSITION
    return data


@pytest.mark.parametrize("screen", sorted(_ESTABLISHING_SCREENS))
@pytest.mark.parametrize("route", sorted(_ROUTES))
@pytest.mark.parametrize("assessed", ["2026-12-02", None])
def test_a_point_established_by_its_element_facts_leaves_the_status_unused(
    screen: str, route: str, assessed: str | None
) -> None:
    facts = {
        **_ROUTES[route],
        screen: _ESTABLISHING_SCREENS[screen],
        "generates_synthetic_content": True,
        "assessment_date": assessed,
    }
    profile = SystemProfile(name="x", roles=[Role.DEPLOYER], **facts)
    reports = {
        status: _report(**facts, deployer_public_authority=status) for status in (True, False, None)
    }

    assert profile.prohibited_practices == []
    assert reports[None].risk_tier.value == "prohibited"
    assert not public_authority_status_used(profile) and not change_used(profile)
    assert _status_questions(reports[None]) == []
    assert _STATUS_UNUSED in reports[True].scope.transitional_status
    compared = [_without_status_unused(report) for report in reports.values()]
    assert compared[0] == compared[1] == compared[2]
    status = reports[None].scope.transitional_status
    assert "Article 111(2) check: the system was" not in status
    assert ("Article 111(2) check: not applied, as an Art. 5 prohibited practice" in status) is (
        route == "annex-i-dated"
    )


def test_a_point_established_by_its_element_facts_skips_the_art_111_3_check() -> None:
    facts = {
        "is_gpai_model": True,
        "gpai_model_placing_on_market_date": "2025-01-01",
        "intimate_imagery": _ESTABLISHING_SCREENS["intimate_imagery"],
        "generates_synthetic_content": True,
    }
    roles = (Role.PROVIDER, Role.GPAI_PROVIDER)
    prohibited = _report(roles, **facts, assessment_date="2026-12-02")
    declared_early = _report(
        roles,
        **{k: v for k, v in facts.items() if k != "intimate_imagery"},
        prohibited_practices=["5.1.ba"],
        assessment_date="2026-12-01",
    )

    assert prohibited.risk_tier.value == "prohibited"
    assert "Article 111(3) check" not in prohibited.scope.transitional_status
    assert declared_early.risk_tier.value != "prohibited"
    assert (
        "Article 111(3) check: the general-purpose AI model was placed on the market on 2025-01-01"
        in (declared_early.scope.transitional_status)
    )


def test_the_intake_records_i_dont_know_as_null() -> None:
    # tests/test_intake.py checks over its grids that null reaches review wherever the
    # question is asked, and that it is asked exactly where the engine's test holds.
    (question,) = [q for q in QUESTIONS if q["id"] == "deployer_public_authority"]

    assert question["unknown"] == {"value": None}
    assert question["article"] == "Art. 49(3), Art. 49(5) and Art. 111(2) AIA"


@pytest.mark.parametrize("name", ["credit_scoring_deployer.json", "life_insurer_pricing.json"])
def test_the_deployer_examples_state_their_status(name: str) -> None:
    profile = json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

    assert profile["deployer_public_authority"] is False
    assert classify(SystemProfile.model_validate(profile)).disposition.value == "determined"
    unset = {key: value for key, value in profile.items() if key != "deployer_public_authority"}
    report = classify(SystemProfile.model_validate(unset))
    assert report.disposition.value == "requires_review"
    assert _status_questions(report)
