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
import re
from pathlib import Path

import pytest

from eu_ai_act_classifier import SystemProfile, classify
from eu_ai_act_classifier.intake import (
    BLOCK,
    QUESTIONS,
    answers_to_profile,
    holds,
    intake_definition,
    profile_to_answers,
    question_fields,
    read_field,
    write_field,
)
from eu_ai_act_classifier.models import Derogation, ProhibitedPractice

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = {
    path.stem: json.loads(path.read_text(encoding="utf-8"))
    for path in sorted((ROOT / "examples").glob("*.json"))
    if path.stem != "classification-packet"
}


_REPORTS: dict[str, dict] = {}


def _report(profile: dict) -> dict:
    key = json.dumps(profile, sort_keys=True)
    if key not in _REPORTS:
        _REPORTS[key] = classify(SystemProfile.model_validate(profile)).model_dump(mode="json")
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
                # Answered, as the intake requires wherever it asks; where it skips the
                # question, its own skip check shows the value does not matter.
                "deployer_public_authority": False,
            }
        )
    return profiles


GRID = _grid()

# The Art. 111 transitions, the Annex I section and Art. 49(3) read facts the grid
# above holds fixed, so a second grid varies them.
_TRANSITION_AXES = {
    "roles": [["provider"], ["deployer"]],
    "scope": [(True, True), (False, True)],
    "prohibited_practices": [[], ["5.1.c"]],
    "annex_i": [(False, False, None), (True, False, None), (True, True, None), (True, True, "B")],
    "annex_iii_area": [None, "III.2", "III.6.a"],
    "public_authority_use": [False, True],
    "dates": [(None, None), ("2025-01-01", None), (None, "2028-01-01")],
    "significant_change": [None, True],
    "gpai": [(False, None), (True, "2025-01-01")],
}


def _transition_grid() -> list[dict]:
    profiles = []
    for combo in itertools.product(*_TRANSITION_AXES.values()):
        roles, scope, prohibited, annex_i, annex_iii, authority, dates, change, gpai = combo
        profiles.append(
            {
                "name": "Grid system",
                "roles": roles,
                "is_ai_system": scope[0],
                "eu_nexus": scope[1],
                "prohibited_practices": prohibited,
                "annex_i_safety_component": annex_i[0],
                "annex_i_third_party_assessment": annex_i[1],
                "annex_i_section": annex_i[2],
                "annex_iii_area": annex_iii,
                "public_authority_use": authority,
                "placing_on_market_date": dates[0],
                "putting_into_service_date": dates[1],
                "significant_change_after_application_date": change,
                "is_gpai_model": gpai[0],
                "gpai_model_placing_on_market_date": gpai[1],
                "deployer_public_law_body": False,
                "deployer_private_public_service": False,
                "deployer_public_authority": False,
            }
        )
    return profiles


TRANSITION_GRID = _transition_grid()

# A skipped question may change the report only by the engine's own statement that the
# value is not used: a section without the Art. 6(1) route, a model date without a
# general-purpose AI model. Everything else, the disposition included, must match.
_SECTION_UNUSED = "HIGHRISK.6.1.section_unused"
_GPAI_DATE_UNUSED = (
    "Article 111(3) check: gpai_model_placing_on_market_date is given, but no general-purpose "
    "AI model is screened (is_gpai_model is false), so the date is not used."
)
_NO_TRANSITION = "No transitional limitation identified from the submitted facts."


def _without_unused_statements(report: dict) -> dict:
    # Shallow copies: only "findings" and "scope" are replaced, never mutated in place.
    scope = dict(report["scope"])
    notes = (" ".join(note.replace(_GPAI_DATE_UNUSED, "").split()) for note in scope["notes"])
    scope["notes"] = [note for note in notes if note]
    status = " ".join(scope["transitional_status"].replace(_GPAI_DATE_UNUSED, "").split())
    scope["transitional_status"] = status or _NO_TRANSITION
    findings = [f for f in report["findings"] if f["rule_id"] != _SECTION_UNUSED]
    return {**report, "findings": findings, "scope": scope}


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
    hidden = [p for p in GRID + TRANSITION_GRID if not holds(question["show_if"], _normalised(p))]
    assert hidden, "the condition never hides the question on the grid"
    for profile in hidden:
        baseline = _without_unused_statements(_report(profile))
        for assignment in _alternatives(question):
            changed = _with(profile, assignment)
            assert not holds(question["show_if"], _normalised(changed))
            report = _without_unused_statements(_report(changed))
            assert report == baseline, (question["id"], profile, assignment)


@pytest.mark.parametrize(
    "question",
    [q for q in QUESTIONS if isinstance(q.get("unknown"), dict)],
    ids=lambda q: q["id"],
)
def test_a_fail_closed_unknown_always_yields_requires_review(question: dict) -> None:
    visible = [p for p in GRID + TRANSITION_GRID if holds(question.get("show_if"), _normalised(p))]
    assert visible
    for profile in visible:
        changed = _with(profile, {question["field"]: question["unknown"]["value"]})
        assert _report(changed)["disposition"] == "requires_review", (question["id"], profile)


def test_value_unknowns_are_never_a_model_default() -> None:
    # Otherwise the compact profile would drop the value and "I don't know" would
    # be indistinguishable from an omitted field.
    defaults = intake_definition()["defaults"]
    for question in QUESTIONS:
        if isinstance(question.get("unknown"), dict):
            assert question["unknown"]["value"] != read_field(defaults, question["field"])


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
    ]
    corpus = "\n".join(
        classify(SystemProfile.model_validate(p), include_advisory=True).model_dump_json()
        for p in profiles
    )
    pinpoints = re.compile(r"Art\. \d+(?:\(\w+\))*(?: AIA)?")
    for question in QUESTIONS:
        texts = [question.get("article") or "", question.get("hint") or "", question["title"]]
        texts += [o.get("label", "") for o in question.get("options", [])]
        for text in texts:
            for pinpoint in pinpoints.findall(text):
                assert pinpoint in corpus, (question["id"], pinpoint)
