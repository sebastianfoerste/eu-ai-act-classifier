"""The guided intake (src/eu_ai_act_classifier/intake.py) must never change a result.

Three guarantees back the playground's guided mode:

1. Every bundled example survives profile -> answers -> profile unchanged.
2. Every "I don't know" either blocks the run or writes a value that yields
   ``requires_review`` wherever the question is asked.
3. A question is skipped only where no answer to it changes the classification
   report, checked over grids of states the intake can reach. The one allowed
   difference is the engine's own statement that a value given there is not
   used. Advisory notes must match too, except for a profile outside the AI
   Act's scope, where they may still reflect a screen the intake skips.
"""

from __future__ import annotations

import copy
import html
import itertools
import json
import re
import time
from pathlib import Path

import pytest

from eu_ai_act_classifier import SystemProfile, classify
from eu_ai_act_classifier.intake import (
    ANNEX_III_AREAS,
    BLOCK,
    CHANGE_OPEN,
    HIGH_RISK_ROUTE,
    HIGH_RISK_ROUTE_EARLY,
    IN_SCOPE,
    NOT_ASKED,
    PUBLIC_AUTHORITY_STATUS_OPEN,
    QUESTIONS,
    answers_to_profile,
    holds,
    intake_definition,
    is_answered,
    profile_to_answers,
    question_fields,
    read_field,
    write_field,
)
from eu_ai_act_classifier.models import AnnexIII, Derogation, ProhibitedPractice
from eu_ai_act_classifier.transitions import (
    change_used,
    prohibition_applies,
    public_authority_status_used,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
EXAMPLES = {
    path.stem: json.loads(path.read_text(encoding="utf-8"))
    for path in sorted((ROOT / "examples").glob("*.json"))
    if path.stem != "classification-packet"
}


_REPORTS: dict[str, dict] = {}


def _report(profile: dict) -> dict:
    key = json.dumps(profile, sort_keys=True)
    if key not in _REPORTS:
        report = classify(SystemProfile.model_validate(profile), include_advisory=True)
        _REPORTS[key] = report.model_dump(mode="json")
    return _REPORTS[key]


def _normalised(profile: dict) -> dict:
    return SystemProfile.model_validate(profile).model_dump(mode="json")


def _condition_fields(condition) -> set[str]:
    if condition is None:
        return set()
    if "field" in condition:
        return {condition["field"]}
    nested = condition.get("all") or condition.get("any") or [condition.get("not")]
    return set().union(*(_condition_fields(c) for c in nested))


def test_every_profile_field_is_asked_exactly_once() -> None:
    asked = [field for question in QUESTIONS for field in question_fields(question)]
    expected = [
        name for name in SystemProfile.model_fields if name not in ("derogation", *NOT_ASKED)
    ]
    expected += [f"derogation.{key}" for key in Derogation.model_fields]
    assert sorted(asked) == sorted(expected)
    assert len(asked) == len(set(asked))


def test_conditions_read_only_fields_asked_earlier() -> None:
    earlier: set[str] = set()
    for question in QUESTIONS:
        assert _condition_fields(question.get("show_if")) <= earlier, question["id"]
        earlier |= set(question_fields(question))


def test_unknown_policies_are_declared() -> None:
    for question in QUESTIONS:
        policy = question.get("unknown")
        if question["kind"] in ("details", "number"):
            assert policy is None, question["id"]
            continue
        assert policy == BLOCK or set(policy) == {"value"}, question["id"]
        if policy != BLOCK:
            assert policy["value"] is not False, "I don't know must never become false"


@pytest.mark.parametrize("key", sorted(EXAMPLES))
def test_examples_round_trip_through_the_intake(key: str) -> None:
    example = EXAMPLES[key]
    profile, _asked, blocked, missing = answers_to_profile(profile_to_answers(example))
    assert not blocked
    # A model-default null on a question whose "I don't know" blocks is left for
    # the user to answer, never shown as "I don't know".
    by_id = {q["id"]: q for q in QUESTIONS}
    for question_id in missing:
        question = by_id[question_id]
        assert question["unknown"] == BLOCK and read_field(profile, question["field"]) is None
    assert _normalised(profile) == _normalised(example)
    assert _report(profile) == _report(example)


# --- A grid of earlier answers ------------------------------------------------

# Declared practices with the assessment date. The engine applies Art. 5(1)(ba) and (bb)
# AIA from 2 December 2026 and only to a placing or use role
# (transitions.prohibition_applies), so a declared point (ba) or (bb) leaves the high-risk
# route open before that date, or for a distributor, and closes it from that date or with
# no date for the other roles.
_LATER_POINTS = [
    (practices, assessment_date)
    for practices in (["5.1.ba"], ["5.1.bb"], ["5.1.ba", "5.1.bb"], ["5.1.ba", "5.1.c"])
    for assessment_date in ("2026-12-01", "2026-12-02", None)
]
_GRID_AXES = {
    "roles": [["provider"], ["deployer"], ["importer", "gpai_provider"]],
    "scope": [(True, True), (False, True), (True, False)],
    "prohibited": [([], None), (["5.1.c"], None)],
    "annex_i": [(False, False), (True, False), (True, True)],
    "annex_iii_area": [None, "III.2", "III.4.a", "III.5.b", "III.unsure"],
    "derogation": [{}, {"performs_profiling": True}, {"narrow_procedural_task": True}],
    "gpai": [(False, None, False), (True, None, False), (True, 2e25, True)],
    "outside_eu": [False, True],
}
# The same grid for the Art. 5(1)(ba) and (bb) points, with a distributor added as the
# role no point binds. Scope stays fixed, as every condition that reads the declared points
# also requires the system in scope; two derogation states and no general-purpose AI model
# keep the product small (tests/test_deployer_status.py covers the Art. 111(3) check with
# these points).
_GRID_LATER_AXES = {
    **_GRID_AXES,
    "roles": [*_GRID_AXES["roles"], ["distributor"]],
    "scope": [(True, True)],
    "prohibited": _LATER_POINTS,
    "derogation": [{}, {"narrow_procedural_task": True}],
    "gpai": [(False, None, False)],
}


def _grid(axes: dict[str, list]) -> list[dict]:
    profiles = []
    for combo in itertools.product(*axes.values()):
        roles, scope, prohibited, annex_i, annex_iii, derogation, gpai, outside_eu = combo
        profiles.append(
            {
                "name": "Grid system",
                "roles": roles,
                "is_ai_system": scope[0],
                "eu_nexus": scope[1],
                "prohibited_practices": prohibited[0],
                "assessment_date": prohibited[1],
                "annex_i_safety_component": annex_i[0],
                "annex_i_third_party_assessment": annex_i[1],
                "annex_iii_area": annex_iii,
                "derogation": dict(derogation),
                "is_gpai_model": gpai[0],
                "training_flops": gpai[1],
                "gpai_systemic_risk_designated": gpai[2],
                "provider_established_outside_eu": outside_eu,
                "deployer_public_law_body": False,
                "deployer_private_public_service": False,
                "has_authorised_representative": True,
                # Answered, as the intake requires wherever it asks; _reachable resets
                # it to its default where the intake skips it.
                "deployer_public_authority": False,
                "significant_change_after_application_date": False,
            }
        )
    return profiles


def _reachable(profile: dict) -> dict:
    """The state the intake would produce: a question it skips keeps its default."""

    state = _normalised(profile)
    defaults = intake_definition()["defaults"]
    for question in QUESTIONS:
        if not holds(question.get("show_if"), state):
            for field in question_fields(question):
                if field != "name":
                    write_field(state, field, copy.deepcopy(read_field(defaults, field)))
    return state


def _distinct(profiles: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for profile in profiles:
        seen.setdefault(json.dumps(profile, sort_keys=True), profile)
    return list(seen.values())


GRID = _distinct([_reachable(p) for p in _grid(_GRID_AXES) + _grid(_GRID_LATER_AXES)])

# The Art. 111 transitions, the Annex I section and Art. 49(3) read facts the grid
# above holds fixed, so a second grid varies them. Of the transparency flags only the
# Art. 50(2) one varies, as a legacy high-risk system's Art. 50 finding and item repeat
# the Art. 111(2) public-authority caveat; the transparency question is skipped only
# outside scope, where its own check varies them all.
_TRANSITION_AXES = {
    "roles": [["provider"], ["deployer"], ["importer"]],
    "scope": [(True, True), (False, True)],
    "prohibited": [([], None), (["5.1.c"], None)],
    "annex_i": [
        (False, False, None),
        (True, False, None),
        (True, True, None),
        (True, True, "I.A.2"),
        (True, True, "I.B.21"),
    ],
    "annex_iii_area": [None, "III.2", "III.6.a"],
    "public_authority_use": [False, True],
    "dates": [
        (None, None),
        ("2025-01-01", None),
        (None, "2028-01-01"),
        ("2028-08-02", None),
        ("2029-01-01", "2025-01-01"),
    ],
    "significant_change": [False, True],
    "gpai": [(False, None), (True, "2025-01-01")],
    "deployer_public_authority": [False, True],
    "generates_synthetic_content": [False, True],
}
# The Art. 5(1)(ba) and (bb) points as in _GRID_LATER_AXES. The change answer and the
# deployer status stay at one value: the skip check tries every answer to both, and so do
# the two checks of the "not used" sentences. The Art. 50(2) flag is set, so an unscreened
# later point stays open; the Annex I state with no third-party assessment, which opens no
# high-risk route, a general-purpose AI model, whose Art. 111(3) check with these points
# tests/test_deployer_status.py covers, and the second legacy date pair are left out.
_TRANSITION_LATER_AXES = {
    **_TRANSITION_AXES,
    "roles": [*_TRANSITION_AXES["roles"], ["distributor"]],
    "scope": [(True, True)],
    "prohibited": _LATER_POINTS,
    "annex_i": [state for state in _TRANSITION_AXES["annex_i"] if state[:2] != (True, False)],
    "dates": _TRANSITION_AXES["dates"][:4],
    "significant_change": [False],
    "gpai": [(False, None)],
    "deployer_public_authority": [False],
    "generates_synthetic_content": [True],
}


def _transition_grid(axes: dict[str, list]) -> list[dict]:
    profiles = []
    for combo in itertools.product(*axes.values()):
        roles, scope, prohibited, annex_i, annex_iii, authority, dates, change, gpai, dpa, art50 = (
            combo
        )
        profiles.append(
            {
                "name": "Grid system",
                "roles": roles,
                "is_ai_system": scope[0],
                "eu_nexus": scope[1],
                "prohibited_practices": prohibited[0],
                "assessment_date": prohibited[1],
                "annex_i_safety_component": annex_i[0],
                "annex_i_third_party_assessment": annex_i[1],
                "annex_i_legislation": annex_i[2],
                "annex_iii_area": annex_iii,
                "public_authority_use": authority,
                "placing_on_market_date": dates[0],
                "putting_into_service_date": dates[1],
                "significant_change_after_application_date": change,
                "is_gpai_model": gpai[0],
                "gpai_model_placing_on_market_date": gpai[1],
                "deployer_public_law_body": False,
                "deployer_private_public_service": False,
                "deployer_public_authority": dpa,
                "generates_synthetic_content": art50,
            }
        )
    return profiles


TRANSITION_GRID = _distinct(
    [
        _reachable(p)
        for p in _transition_grid(_TRANSITION_AXES) + _transition_grid(_TRANSITION_LATER_AXES)
    ]
)

# A skipped question may change the report only by the engine's own statement that the
# value is not used: a section without the Art. 6(1) route, a model date without a
# general-purpose AI model, a change answer without an Art. 111(2) legacy system, a
# deployer status where it cannot change the result (public_authority_status_used).
# Everything else, the disposition included, must match.
_SECTION_UNUSED = "HIGHRISK.6.1.section_unused"
_GPAI_DATE_UNUSED = (
    "Article 111(3) check: gpai_model_placing_on_market_date is given, but no general-purpose "
    "AI model is screened (is_gpai_model is false), so the date is not used."
)
_CHANGE_UNUSED = (
    "Article 111(2) check: significant_change_after_application_date is given, but it is not "
    "used: it matters only for a high-risk system that is not prohibited, placed on the "
    "market or put into service before its Chapter III date."
)
_PUBLIC_AUTHORITY_STATUS_UNUSED = (
    "Article 111(2) check: deployer_public_authority is given, but it is not used: it "
    "describes the profile's own deployer role, so it matters only where the profile holds "
    "that role for a high-risk system that is not prohibited: on an Annex III point, and on "
    "an Annex I route without one only for a system placed on the market or "
    "put into service before its Chapter III date, or undated, that is no Section B product "
    "and has no public_authority_use."
)
_UNUSED_SENTENCES = (_GPAI_DATE_UNUSED, _CHANGE_UNUSED, _PUBLIC_AUTHORITY_STATUS_UNUSED)
_NO_TRANSITION = "No transitional limitation identified from the submitted facts."


def _drop_unused(text: str) -> str:
    for sentence in _UNUSED_SENTENCES:
        text = text.replace(sentence, "")
    return " ".join(text.split())


def _without_unused_statements(report: dict) -> dict:
    # Shallow copies: only "findings" and "scope" are replaced, never mutated in place.
    scope = dict(report["scope"])
    scope["notes"] = [note for note in map(_drop_unused, scope["notes"]) if note]
    scope["transitional_status"] = _drop_unused(scope["transitional_status"]) or _NO_TRANSITION
    findings = [f for f in report["findings"] if f["rule_id"] != _SECTION_UNUSED]
    return {**report, "findings": findings, "scope": scope}


def _comparable(report: dict, *, advisory: bool) -> dict:
    report = _without_unused_statements(report)
    return report if advisory else {**report, "advisory_notes": None}


def _alternatives(question: dict) -> list[dict[str, object]]:
    """Answers to try for a question, as field -> value assignments."""

    kind = question["kind"]
    if kind == "flags":
        fields = question_fields(question)
        every = [{f: True for f in fields}]
        return every + [{f: f == chosen for f in fields} for chosen in [None, *fields]]
    if kind == "details":
        dates = [e["field"] for e in question["fields"] if e.get("type") == "date"]
        return [{f: d} for f in dates for d in ("2024-01-01", "2026-01-01", "2028-06-01")]
    field = question["field"]
    if kind == "boolean":
        nullable = field.startswith("derogation.") is False and (
            SystemProfile.model_fields[field].default is None
            or SystemProfile.model_fields[field].annotation in (bool | None,)
        )
        return [{field: value} for value in ([True, False, None] if nullable else [True, False])]
    if kind == "single":
        return [{field: None}] + [{field: o["value"]} for o in question["options"]]
    if kind == "multi":
        values = [o["value"] for o in question["options"]]
        return [{field: []}, {field: values}] + [{field: [v]} for v in values]
    if kind == "number":
        return [{field: v} for v in [None, 1e24, 2e25]]
    raise AssertionError(kind)


def _with(profile: dict, assignment: dict[str, object]) -> dict:
    changed = copy.deepcopy(profile)
    for field, value in assignment.items():
        write_field(changed, field, value)
    return changed


@pytest.mark.parametrize(
    "question", [q for q in QUESTIONS if q.get("show_if")], ids=lambda q: q["id"]
)
def test_a_skipped_question_cannot_change_the_report(question: dict) -> None:
    hidden = [p for p in GRID + TRANSITION_GRID if not holds(question["show_if"], p)]
    assert hidden, "the condition never hides the question on the grid"
    for profile in hidden:
        in_scope = holds(IN_SCOPE, profile)
        baseline = _comparable(_report(profile), advisory=in_scope)
        for assignment in _alternatives(question):
            changed = _with(profile, assignment)
            assert not holds(question["show_if"], _normalised(changed))
            report = _comparable(_report(changed), advisory=in_scope)
            assert report == baseline, (question["id"], profile, assignment)


@pytest.mark.parametrize(
    "question",
    [q for q in QUESTIONS if isinstance(q.get("unknown"), dict)],
    ids=lambda q: q["id"],
)
def test_a_fail_closed_unknown_always_yields_requires_review(question: dict) -> None:
    visible = [p for p in GRID + TRANSITION_GRID if holds(question.get("show_if"), p)]
    assert visible
    for profile in visible:
        changed = _with(profile, {question["field"]: question["unknown"]["value"]})
        assert _report(changed)["disposition"] == "requires_review", (question["id"], profile)


def test_value_unknowns_equal_a_model_default_only_where_it_fails_closed() -> None:
    # A compact profile drops a default value, so "I don't know" reads back as an
    # omitted field. That is safe only for a conditional question whose default is the
    # null that the fail-closed test above checks yields requires_review wherever the
    # question is asked (the Annex I act, the Art. 111(2) change answer and the deployer's
    # public-authority status); any other default would be read as an answer.
    defaults = intake_definition()["defaults"]
    for question in QUESTIONS:
        if isinstance(question.get("unknown"), dict):
            value = question["unknown"]["value"]
            if value == read_field(defaults, question["field"]):
                assert value is None and question.get("show_if"), question["id"]


def test_the_change_question_follows_the_engines_legacy_test() -> None:
    # The intake asks the Art. 111(2) change question exactly where the engine uses the
    # answer, with dates on both sides of both Chapter III dates.
    dates = [None, "2025-01-01", "2027-12-01", "2027-12-02", "2028-08-01", "2028-08-02"]
    routes = [
        {"annex_iii_area": None},
        {"annex_iii_area": "III.4.a"},
        {"annex_iii_area": "III.unsure"},
        *(
            {
                "annex_i_safety_component": True,
                "annex_i_third_party_assessment": True,
                "annex_i_legislation": act,
                "annex_iii_area": area,
            }
            for act in (None, "I.A.11", "I.B.21")
            for area in (None, "III.2")
        ),
    ]
    # A declared point (ba) counts only from its date and for a placing or use role.
    prohibited_states = [([], None), (["5.1.c"], None), *_LATER_POINTS[:3]]
    checked = 0
    for route, placed, served, (prohibited, assessed), held, in_scope in itertools.product(
        routes, dates, dates[:3], prohibited_states, (["provider"], ["distributor"]), (True, False)
    ):
        profile = _normalised(
            {
                "name": "x",
                **route,
                "roles": held,
                "placing_on_market_date": placed,
                "putting_into_service_date": served,
                "prohibited_practices": prohibited,
                "assessment_date": assessed,
                "is_ai_system": in_scope,
            }
        )
        expected = in_scope and change_used(SystemProfile.model_validate(profile))
        assert holds(CHANGE_OPEN, profile) is expected, profile
        checked += expected
    assert checked


def test_the_change_answer_is_reported_as_not_used_exactly_where_it_is_not_used() -> None:
    # The skip check strips the sentence before comparing, so pin where it appears:
    # for a given answer outside the Art. 111(2) legacy case, never otherwise.
    checked = 0
    for profile in TRANSITION_GRID:
        if not holds(IN_SCOPE, profile):
            continue
        used = change_used(SystemProfile.model_validate(profile))
        for change in (True, False, None):
            changed = {**profile, "significant_change_after_application_date": change}
            status = _report(changed)["scope"]["transitional_status"]
            assert (_CHANGE_UNUSED in status) is (change is not None and not used), changed
            checked += 1
    assert checked


def test_the_public_authority_question_follows_the_engines_deployer_test() -> None:
    # The intake asks for the deployer's public-authority status exactly where, in scope,
    # it can change the result (public_authority_status_used).
    routes = [
        {"annex_iii_area": None},
        {"annex_iii_area": "III.2"},
        {"annex_iii_area": "III.5.b"},
        {"annex_iii_area": "III.unsure"},
        {"annex_i_safety_component": True},
        {"annex_i_safety_component": True, "annex_i_third_party_assessment": True},
        # A Section B product as the intake records it: by its act, never by
        # annex_i_section, which the intake does not ask (NOT_ASKED).
        {
            "annex_i_safety_component": True,
            "annex_i_third_party_assessment": True,
            "annex_i_legislation": "I.B.21",
        },
    ]
    roles = [
        ["provider"],
        ["deployer"],
        ["provider", "deployer"],
        ["importer", "distributor"],
        ["gpai_provider"],
    ]
    prohibited_states = [([], None), (["5.1.c"], None), *_LATER_POINTS[:3]]
    checked = 0
    for route, held, (prohibited, assessed), in_scope in itertools.product(
        routes, roles, prohibited_states, (True, False)
    ):
        profile = _normalised(
            {
                "name": "x",
                **route,
                "roles": held,
                "prohibited_practices": prohibited,
                "assessment_date": assessed,
                "is_ai_system": in_scope,
            }
        )
        used = public_authority_status_used(SystemProfile.model_validate(profile))
        expected = in_scope and used
        assert holds(PUBLIC_AUTHORITY_STATUS_OPEN, profile) is expected, profile
        checked += expected
    assert checked


def test_the_public_authority_status_is_reported_as_not_used_exactly_where_it_is_skipped() -> None:
    # As for the change answer: the sentence appears for a given status wherever the
    # engine's deployer test fails, and exactly there the intake skips the question.
    checked = 0
    for profile in GRID + TRANSITION_GRID:
        if not holds(IN_SCOPE, profile):
            continue
        used = public_authority_status_used(SystemProfile.model_validate(profile))
        assert holds(PUBLIC_AUTHORITY_STATUS_OPEN, profile) is used, profile
        for status in (True, False, None):
            changed = {**profile, "deployer_public_authority": status}
            text = _report(changed)["scope"]["transitional_status"]
            assert (_PUBLIC_AUTHORITY_STATUS_UNUSED in text) is (status is not None and not used)
            checked += 1
    assert checked


# The grids above hold only point (c) as a point (a) to (h), so every such point is checked
# here once, alone and with a declared point (ba), on a legacy Annex III route. The two
# later points are written out here, not taken from catalog.LATER_PROHIBITIONS as the
# intake takes them.
_EARLIER_POINTS = [
    practice.value for practice in ProhibitedPractice if practice.value not in {"5.1.ba", "5.1.bb"}
]


def _earlier_point_profile(practices: list[str]) -> dict:
    return _normalised(
        {
            "name": "x",
            "roles": ["deployer"],
            "annex_iii_area": "III.4.a",
            "placing_on_market_date": "2026-07-01",
            "prohibited_practices": practices,
            "assessment_date": "2026-12-01",
        }
    )


@pytest.mark.parametrize("practice", _EARLIER_POINTS)
@pytest.mark.parametrize("with_ba", [False, True])
def test_every_earlier_point_closes_the_high_risk_route(practice: str, with_ba: bool) -> None:
    # A point (a) to (h) applies whatever the date and role, so before 2 December 2026 the
    # change and status questions stay closed, as the engine does not read the answers.
    profile = _earlier_point_profile([practice, "5.1.ba"] if with_ba else [practice])
    engine_profile = SystemProfile.model_validate(profile)
    assert prohibition_applies(engine_profile)
    assert not change_used(engine_profile)
    assert not public_authority_status_used(engine_profile)
    assert not holds(HIGH_RISK_ROUTE, profile)
    assert not holds(CHANGE_OPEN, profile)
    assert not holds(PUBLIC_AUTHORITY_STATUS_OPEN, profile)


@pytest.mark.parametrize("practice", _EARLIER_POINTS)
def test_the_early_high_risk_questions_skip_every_earlier_point(practice: str) -> None:
    # The questions asked before the assessment date keep a declared point (ba) or (bb)
    # alone, and only that: a point (a) to (h) closes them whatever the other points.
    later_only = _earlier_point_profile(["5.1.ba"])
    assert holds(HIGH_RISK_ROUTE_EARLY, later_only)
    for practices in ([practice], [practice, "5.1.ba"]):
        profile = _earlier_point_profile(practices)
        assert not holds(HIGH_RISK_ROUTE_EARLY, profile), practices
        early = [q for q in QUESTIONS if q.get("show_if") is HIGH_RISK_ROUTE_EARLY]
        assert early
        assert not any(holds(q["show_if"], profile) for q in early), practices


def test_an_unknown_change_answer_survives_a_compact_round_trip() -> None:
    legacy = {
        "name": "x",
        "annex_iii_area": "III.4.a",
        "placing_on_market_date": "2025-01-01",
    }
    answers = profile_to_answers(legacy)
    assert answers["significant_change"] == "unknown"
    profile, asked, blocked, missing = answers_to_profile(answers)
    assert "significant_change" in asked and not blocked and "significant_change" not in missing
    assert read_field(profile, "significant_change_after_application_date") is None
    report = _report(profile)
    assert report["disposition"] == "requires_review"
    assert any(q.startswith("Art. 111(2) AIA") for q in report["open_questions"])
    # Without a date before the Chapter III date the question is not asked at all.
    _profile, asked, _blocked, missing = answers_to_profile(
        profile_to_answers({**legacy, "placing_on_market_date": "2028-01-01"})
    )
    assert "significant_change" not in asked and "significant_change" not in missing


def test_blocked_unknowns_stop_the_run() -> None:
    answers = profile_to_answers(EXAMPLES["credit_scoring"])
    answers["prohibited_practices"] = "unknown"
    _profile, asked, blocked, _missing = answers_to_profile(answers)
    assert blocked == ["prohibited_practices"]
    assert "prohibited_practices" in asked


def test_annex_iii_unknown_is_unsettled_point() -> None:
    answers = profile_to_answers(EXAMPLES["spam_filter"])
    answers["annex_iii_area"] = "unknown"
    profile, _asked, blocked, _missing = answers_to_profile(answers)
    assert not blocked
    assert read_field(profile, "annex_iii_area") == "III.unsure"
    assert _report(profile)["disposition"] == "requires_review"


def test_an_unknown_fraud_purpose_is_recorded_as_unknown() -> None:
    # "I don't know" on the Annex III(5)(b) fraud question records null. True would go to
    # review as well, but the report would then say that the profile states the purpose.
    answers = profile_to_answers(EXAMPLES["credit_scoring"])
    answers["used_for_financial_fraud_detection"] = "unknown"
    profile, asked, blocked, _missing = answers_to_profile(answers)
    assert "used_for_financial_fraud_detection" in asked and not blocked
    assert read_field(profile, "used_for_financial_fraud_detection") is None
    report = _report(profile)
    assert report["disposition"] == "requires_review"
    (question,) = [q for q in report["open_questions"] if "financial fraud" in q]
    assert "the profile states" not in question


# Art. 27(1) AIA: the deployer status questions belong to the Art. 6(2) route only.
@pytest.mark.parametrize(
    "question_id", ["deployer_public_law_body", "deployer_private_public_service"]
)
def test_fria_status_is_asked_on_the_annex_iii_route_only(question_id: str) -> None:
    question = next(q for q in QUESTIONS if q["id"] == question_id)
    annex_i = {
        "name": "x",
        "roles": ["deployer"],
        "annex_i_safety_component": True,
        "annex_i_third_party_assessment": True,
    }
    annex_iii_area = AnnexIII.ESSENTIAL_PUBLIC_BENEFITS.value

    assert holds(question["show_if"], _normalised({**annex_i, "annex_iii_area": annex_iii_area}))
    assert holds(
        question["show_if"],
        _normalised({"name": "x", "roles": ["deployer"], "annex_iii_area": annex_iii_area}),
    )
    assert not holds(question["show_if"], _normalised(annex_i))
    assert not holds(question["show_if"], _normalised({**annex_i, "annex_i_section": "A"}))


# AIA-07: the establishment and representative questions are expected to be asked for
# a general-purpose AI model too, once the engine lists the Art. 54 AIA representative
# duty. Blocked until Arts. 52(1), 53(2), 54(1) and 54(6) AIA are read on EUR-Lex;
# remove the marker with the show_if change in intake.py and the engine change.
@pytest.mark.xfail(
    strict=True,
    reason="AIA-07 is blocked on the EUR-Lex reading of Arts. 52(1), 53(2), 54(1) and 54(6) AIA",
)
@pytest.mark.parametrize(
    "question_id", ["provider_established_outside_eu", "has_authorised_representative"]
)
def test_representative_questions_are_asked_for_a_gpai_model(question_id: str) -> None:
    question = next(q for q in QUESTIONS if q["id"] == question_id)
    gpai_model = {
        "name": "x",
        "roles": ["gpai_provider"],
        "is_gpai_model": True,
        "training_flops": 1e24,
        "provider_established_outside_eu": True,
    }

    assert holds(question["show_if"], _normalised(gpai_model))


def test_definition_is_json_and_defaults_match_the_model() -> None:
    definition = json.loads(json.dumps(intake_definition()))
    defaults = SystemProfile(name="x").model_dump(mode="json")
    assert definition["defaults"] == {**defaults, "name": ""}


def test_generated_intake_files_are_current() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_playground", ROOT / "scripts" / "build_playground.py"
    )
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    for path, data in (
        (ROOT / "docs" / "playground" / "intake.json", intake_definition()),
        (ROOT / "tests" / "playground" / "intake-fixtures.json", build.build_intake_fixtures()),
    ):
        assert path.read_text(encoding="utf-8") == build.render(data), f"{path.name} is stale"


def test_unanswered_questions_are_reported_not_defaulted() -> None:
    _profile, asked, blocked, missing = answers_to_profile({})
    assert "system" in missing and "roles" in missing
    assert not blocked
    assert set(missing) <= set(asked)


def test_text_answers_are_trimmed() -> None:
    answers = profile_to_answers({"name": "x"})
    answers["system"] = {"name": "  Padded name  "}
    profile, _asked, _blocked, _missing = answers_to_profile(answers)
    assert profile["name"] == "Padded name"


# The same inputs as "numbers use the same grammar as the Python interpreter" in
# tests/playground/intake.test.mjs; the generated fixtures hold both interpreters to the
# same profile for each. Only ASCII digits, and only ASCII whitespace is trimmed:
# str.strip() and String.prototype.trim() each remove characters the other keeps.
NUMBERS_ACCEPTED = ["2e25", " 2e25 ", ".5e3", "10", "\t10\n", "\v10\f\r"]
NUMBERS_ACCEPTED += ["5.", "+5", "-0", "1.e5", "5.5e-3"]
NUMBERS_REJECTED = [
    "0x10",
    "1_000",
    "1e",
    " ",
    "   ",  # whitespace alone is not a blank answer
    ".",
    "e5",
    "5..",
    "1e+",
    "Infinity",
    "\u0661\u0662",  # Arabic-Indic digits: Python's \d and float() take them
    "\uff11\uff12",  # fullwidth digits
    "\ufeff5",  # byte order mark: trim() removes it, strip() does not
    "\xa05",  # no-break space: both remove it
    "5\u2028",  # line separator
    "\u30005",  # ideographic space
    "\x1c5",  # file separator: strip() removes it, trim() does not
    "5\x1f",  # unit separator
    "5\x85",  # next line
]


@pytest.mark.parametrize("text", NUMBERS_ACCEPTED + NUMBERS_REJECTED, ids=ascii)
def test_number_answers_take_ascii_digits_and_ascii_whitespace_only(text: str) -> None:
    (question,) = [q for q in QUESTIONS if q["kind"] == "number"]
    model = {"name": "x", "roles": ["gpai_provider"], "is_gpai_model": True}
    answers = {**profile_to_answers(model), question["id"]: text}

    # Never raises, whatever the text.
    profile, asked, blocked, missing = answers_to_profile(answers)

    assert question["id"] in asked and not blocked
    if text in NUMBERS_ACCEPTED:
        assert is_answered(question, answers)
        assert question["id"] not in missing
        assert profile[question["field"]] == float(text.strip(" \t\n\v\f\r"))
    else:
        assert not is_answered(question, answers)
        assert question["id"] in missing
        assert profile[question["field"]] is None


@pytest.mark.parametrize(
    ("answer", "usable"),
    [
        (10, True),
        (2e25, True),
        (True, False),  # bool is an int in Python; a JSON true is not a number in either
        (False, False),
        (float("inf"), False),
        (float("nan"), False),
        ([10], False),
        ({"value": 10}, False),
    ],
    ids=repr,
)
def test_number_answers_that_are_not_text_count_only_as_finite_numbers(
    answer: object, usable: bool
) -> None:
    # A caller of the Python intake passes JSON values, not only the text a browser field
    # holds. isNumber in intake.mjs takes a finite number and no other non-text value.
    (question,) = [q for q in QUESTIONS if q["kind"] == "number"]
    model = {"name": "x", "roles": ["gpai_provider"], "is_gpai_model": True}
    answers = {**profile_to_answers(model), question["id"]: answer}

    profile, asked, blocked, missing = answers_to_profile(answers)

    assert question["id"] in asked and not blocked
    assert is_answered(question, answers) is usable
    assert (question["id"] in missing) is not usable
    assert profile[question["field"]] == (float(answer) if usable else None)


def test_a_long_text_that_is_not_a_number_is_refused_in_linear_time() -> None:
    # A caller can pass any text. While the pattern could read a run of digits in two
    # ways, each of the first two checks took seconds at this length.
    (question,) = [q for q in QUESTIONS if q["kind"] == "number"]
    run = 20_000
    texts = ["1" * run + "x", "1" * run + "." + "1" * run + "x", "5" + " " * run + "5"]
    started = time.perf_counter()
    for text in texts:
        assert not is_answered(question, {question["id"]: text})
    assert time.perf_counter() - started < 2


def test_an_integer_beyond_the_float_range_is_not_a_number_answer() -> None:
    # json.loads reads such a literal as an int, and math.isfinite() raises on it. The
    # browser reads the same literal as Infinity and reports the question as missing.
    (question,) = [q for q in QUESTIONS if q["kind"] == "number"]
    model = {"name": "x", "roles": ["gpai_provider"], "is_gpai_model": True}
    answers = {**profile_to_answers(model), question["id"]: 10**400}

    profile, asked, blocked, missing = answers_to_profile(answers)

    assert question["id"] in asked and not blocked
    assert not is_answered(question, answers)
    assert question["id"] in missing
    assert profile[question["field"]] is None


def test_a_question_of_an_unknown_kind_is_never_answered() -> None:
    # A definition newer than the interpreter must not pass silently (isAnswered's default).
    assert not is_answered({"id": "q", "kind": "slider"}, {"q": 5})


def test_an_unknown_condition_is_an_error_not_a_pass() -> None:
    # holds() in intake.mjs throws on the same input.
    with pytest.raises(ValueError, match="unknown condition"):
        holds({"field": "name", "matches": "x"}, {"name": "x"})


def test_question_articles_are_citations_the_engine_already_makes() -> None:
    """The intake adds no pinpoint of its own (claim ledger rule)."""

    profiles = [*EXAMPLES.values(), *GRID[::40]]
    profiles += [
        {
            "name": "x",
            "annex_iii_area": "III.2",
            "placing_on_market_date": "2025-01-01",
            "significant_change_after_application_date": False,
            "public_authority_use": True,
            "provider_established_outside_eu": True,
            "has_authorised_representative": False,
            "substantially_modifies_system": True,
            "derogation": {"narrow_procedural_task": True},
        },
        {
            "name": "x",
            "generates_synthetic_content": True,
            "deploys_emotion_or_biometric_categorisation": True,
            "is_gpai_model": True,
            "gpai_systemic_risk_designated": True,
        },
        {"name": "x", "prohibited_practices": [p.value for p in ProhibitedPractice]},
        {"name": "x", "roles": ["deployer"], "annex_iii_area": "III.6.a"},
        {"name": "x", "is_ai_system": None, "eu_nexus": None},
        {
            "name": "x",
            "annex_i_safety_component": True,
            "annex_i_third_party_assessment": True,
            "annex_i_section": "B",
        },
        *({"name": "x", "annex_iii_area": area.value} for area in AnnexIII),
    ]
    corpus = "\n".join(
        classify(SystemProfile.model_validate(p), include_advisory=True).model_dump_json()
        for p in profiles
    )
    pinpoints = re.compile(
        r"Arts?\. \d+(?:\(\w+\))*(?: to \d+)?(?: AIA)?"
        r"|Article \d+(?:\(\w+\))*"
        r"|Annex [IVX]+(?:\(\w+\))*(?:, Section [AB])?"
    )
    for question in QUESTIONS:
        texts = [question.get("article") or "", question.get("hint") or "", question["title"]]
        texts += [o.get("label", "") for o in question.get("options", [])]
        for text in texts:
            for pinpoint in pinpoints.findall(text):
                # A whole pinpoint, not the prefix of a longer one ("Art. 5" in "Art. 50").
                made = re.search(re.escape(pinpoint) + r"(?![\w(])", corpus)
                assert made, (question["id"], pinpoint)


# --- D5: the Annex III question in two steps ---------------------------------------


def _annex_iii_question() -> dict:
    return next(q for q in QUESTIONS if q["id"] == "annex_iii_area")


def test_annex_iii_groups_hold_every_point_once_under_its_own_area() -> None:
    question = _annex_iii_question()
    grouped = [value for group in question["groups"] for value in group["options"]]
    points = [o["value"] for o in question["options"] if o["value"] != AnnexIII.UNSURE.value]
    assert sorted(grouped) == sorted(points)
    assert len(grouped) == len(set(grouped))
    for group in question["groups"]:
        assert group["options"], group["value"]
        assert all(value.split(".")[1] == group["value"] for value in group["options"])
    assert [g["value"] for g in question["groups"]] == [str(n) for n in range(1, 9)]
    # The area is page state in the wizard, never a profile field: "I don't know" on
    # either page writes the point the question already writes.
    assert question["field"] == "annex_iii_area"
    assert question["unknown"] == {"value": AnnexIII.UNSURE.value}
    # The second page's heading; the wizard has no other text for it.
    assert isinstance(question["group_title"], str) and question["group_title"].strip()


def test_annex_iii_area_headings_quote_the_official_journal() -> None:
    raw = (SOURCES / "oj" / "32024R1689.en.xhtml").read_text(encoding="utf-8")
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())
    question = _annex_iii_question()
    labels = {g["value"]: g["label"] for g in question["groups"]}
    for area, heading in ANNEX_III_AREAS.items():
        assert re.search(rf"\b{area}\. {re.escape(heading)}:", text), area
        assert labels[area] == f"Annex III({area}): {heading}"
    # Every point label on the second page cites the same area.
    points = {o["value"]: o["label"] for o in question["options"]}
    for group in question["groups"]:
        for value in group["options"]:
            assert points[value].startswith(f"Annex III({group['value']})"), value
