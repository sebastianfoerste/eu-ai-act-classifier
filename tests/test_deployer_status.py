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
from eu_ai_act_classifier.intake import QUESTIONS
from eu_ai_act_classifier.models import ClassificationReport

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


def test_the_intake_records_i_dont_know_as_null() -> None:
    # tests/test_intake.py checks over its grids that null reaches review wherever the
    # question is asked, and that it is asked exactly where the engine's test holds.
    (question,) = [q for q in QUESTIONS if q["id"] == "deployer_public_authority"]

    assert question["unknown"] == {"value": None}


@pytest.mark.parametrize("name", ["credit_scoring_deployer.json", "life_insurer_pricing.json"])
def test_the_deployer_examples_state_their_status(name: str) -> None:
    profile = json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

    assert profile["deployer_public_authority"] is False
    assert classify(SystemProfile.model_validate(profile)).disposition.value == "determined"
    unset = {key: value for key, value in profile.items() if key != "deployer_public_authority"}
    report = classify(SystemProfile.model_validate(unset))
    assert report.disposition.value == "requires_review"
    assert _status_questions(report)
