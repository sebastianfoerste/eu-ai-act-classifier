"""The guided intake (src/eu_ai_act_classifier/intake.py) must never change a result.

Three guarantees back the playground's guided mode:

1. Every bundled example survives profile -> answers -> profile unchanged.
2. Every "I don't know" either blocks the run or writes a value that yields
   ``requires_review`` wherever the question is asked.
3. A question is skipped only where no answer to it can change the report,
   checked over a grid of earlier answers.
"""

from __future__ import annotations

import copy
import itertools
import json
from pathlib import Path

import pytest

from eu_ai_act_classifier import SystemProfile, classify
from eu_ai_act_classifier.intake import (
    BLOCK,
    QUESTIONS,
    REVIEW_EXEMPT_UNKNOWNS,
    answers_to_profile,
    holds,
    intake_definition,
    profile_to_answers,
    question_fields,
    read_field,
    write_field,
)
from eu_ai_act_classifier.models import Derogation

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = {
    path.stem: json.loads(path.read_text(encoding="utf-8"))
    for path in sorted((ROOT / "examples").glob("*.json"))
    if path.stem != "classification-packet"
}


def _report(profile: dict) -> dict:
    return classify(SystemProfile.model_validate(profile)).model_dump(mode="json")


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
    expected = [name for name in SystemProfile.model_fields if name != "derogation"]
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
    profile, _asked, blocked = answers_to_profile(profile_to_answers(example))
    assert not blocked
    assert _normalised(profile) == _normalised(example)
    assert _report(profile) == _report(example)


# --- A grid of earlier answers ------------------------------------------------

_GRID_AXES = {
    "roles": [["provider"], ["deployer"], ["importer", "gpai_provider"]],
    "scope": [(True, True), (False, True), (True, False)],
    "prohibited_practices": [[], ["5.1.c"]],
    "annex_i": [(False, False), (True, False), (True, True)],
    "annex_iii_area": [None, "III.2", "III.4.a", "III.5.b", "III.unsure"],
    "derogation": [{}, {"performs_profiling": True}, {"narrow_procedural_task": True}],
    "gpai": [(False, None, False), (True, None, False), (True, 2e25, True)],
    "outside_eu": [False, True],
}


def _grid() -> list[dict]:
    profiles = []
    for combo in itertools.product(*_GRID_AXES.values()):
        roles, scope, prohibited, annex_i, annex_iii, derogation, gpai, outside_eu = combo
        profiles.append(
            {
                "name": "Grid system",
                "roles": roles,
                "is_ai_system": scope[0],
                "eu_nexus": scope[1],
                "prohibited_practices": prohibited,
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
            }
        )
    return profiles


GRID = _grid()


def _alternatives(question: dict) -> list[dict[str, object]]:
    """Answers to try for a question, as field -> value assignments."""

    kind = question["kind"]
    if kind == "flags":
        fields = question_fields(question)
        return [{f: f == chosen for f in fields} for chosen in [None, *fields]]
    if kind == "details":
        return []
    field = question["field"]
    if kind == "boolean":
        nullable = field.startswith("derogation.") is False and (
            SystemProfile.model_fields[field].default is None
            or SystemProfile.model_fields[field].annotation in (bool | None,)
        )
        return [{field: value} for value in ([True, False, None] if nullable else [True, False])]
    if kind == "single":
        return [{field: v} for v in [None, "III.2", "III.4.a", "III.5.b", "III.unsure"]]
    if kind == "multi":
        return [{field: []}] + [{field: [o["value"]]} for o in question["options"][:4]]
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
    hidden = [p for p in GRID if not holds(question["show_if"], _normalised(p))]
    assert hidden, "the condition never hides the question on the grid"
    for profile in hidden:
        baseline = _report(profile)
        for assignment in _alternatives(question):
            changed = _with(profile, assignment)
            assert not holds(question["show_if"], _normalised(changed))
            assert _report(changed) == baseline, (question["id"], profile, assignment)


@pytest.mark.parametrize(
    "question",
    [
        q
        for q in QUESTIONS
        if isinstance(q.get("unknown"), dict) and q["id"] not in REVIEW_EXEMPT_UNKNOWNS
    ],
    ids=lambda q: q["id"],
)
def test_a_fail_closed_unknown_always_yields_requires_review(question: dict) -> None:
    visible = [p for p in GRID if holds(question.get("show_if"), _normalised(p))]
    assert visible
    for profile in visible:
        changed = _with(profile, {question["field"]: question["unknown"]["value"]})
        assert _report(changed)["disposition"] == "requires_review", (question["id"], profile)


def test_review_exemptions_are_only_for_nullable_defaults() -> None:
    by_id = {q["id"]: q for q in QUESTIONS}
    for question_id in REVIEW_EXEMPT_UNKNOWNS:
        question = by_id[question_id]
        assert question["unknown"] == {"value": None}
        assert SystemProfile.model_fields[question["field"]].default is None


def test_blocked_unknowns_stop_the_run() -> None:
    answers = profile_to_answers(EXAMPLES["credit_scoring"])
    answers["prohibited_practices"] = "unknown"
    _profile, asked, blocked = answers_to_profile(answers)
    assert blocked == ["prohibited_practices"]
    assert "prohibited_practices" in asked


def test_annex_iii_unknown_is_unsettled_point() -> None:
    answers = profile_to_answers(EXAMPLES["spam_filter"])
    answers["annex_iii_area"] = "unknown"
    profile, _asked, blocked = answers_to_profile(answers)
    assert not blocked
    assert read_field(profile, "annex_iii_area") == "III.unsure"
    assert _report(profile)["disposition"] == "requires_review"


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
