"""The guided-intake definition: questions, their order and when each is asked.

This module is the single source for every guided-intake surface. The
playground reads it from ``docs/playground/intake.json``, which
``scripts/build_playground.py`` generates; the browser only interprets the
declarative conditions below and holds no legal logic of its own.

Each question collects one characterised fact, or a small set of facts the
engine reads together. The intake never infers a fact. "I don't know" is
handled per question and never becomes ``false`` or an omitted field:

* ``{"value": ...}`` writes a fail-closed value: ``null`` for a nullable screen
  the engine routes to review, ``III.unsure`` for the Annex III point.
* ``"block"`` stops the run: counsel must characterise the fact before the
  profile can be classified.

A question is skipped only where ``tests/test_intake.py`` checks, over grids of
states the intake can reach, that no answer to it changes the classification
report, apart from the engine's own statement that a value given there is not
used. Nonbinding advisory notes are outside that check: they may still reflect a
screen the intake skips for a profile outside the AI Act's scope.
"""

from __future__ import annotations

import math
import re
from typing import Any

from .citations import POINT_C_ANNEX_I, POINT_C_ANNEX_III
from .labels import DEROGATION_LABELS, option_label
from .models import (
    AnnexIII,
    AnnexISection,
    ExcludedUse,
    ProhibitedPractice,
    Role,
    SystemProfile,
)

SCHEMA_ID = "eu-ai-act-classifier.intake.v1"
BLOCK = "block"
UNKNOWN = "unknown"

# Conditions are plain data so the browser can evaluate exactly what Python does:
#   {"field": f, "is": v}      the field equals v (v may be null)
#   {"field": f, "in": [..]}   the field equals one of the values
#   {"field": f, "has": v}     the list field contains v
#   {"field": f, "empty": b}   the list field is (not) empty
#   {"field": f, "before": d}  the date field is given and earlier than ISO date d
#   {"all": [..]}, {"any": [..]}, {"not": c}
# Fields are profile fields; "derogation.x" reads a nested Derogation flag.

IN_SCOPE = {
    "all": [
        {"not": {"field": "is_ai_system", "is": False}},
        {"not": {"field": "eu_nexus", "is": False}},
    ]
}
# Includes III.unsure: an asserted Art. 6(3) condition still adds the Art. 49(2)
# registration item there.
ANNEX_III_ANY = {"not": {"field": "annex_iii_area", "is": None}}
ANNEX_I_ROUTE = {
    "all": [
        {"field": "annex_i_safety_component", "is": True},
        {"field": "annex_i_third_party_assessment", "is": True},
    ]
}
# Facts the engine reads only once the system is high-risk (Art. 6 AIA) and not
# prohibited: a prohibited practice dominates every other tier.
HIGH_RISK_ROUTE = {
    "all": [
        IN_SCOPE,
        {"field": "prohibited_practices", "empty": True},
        {"any": [ANNEX_III_ANY, ANNEX_I_ROUTE]},
    ]
}
# Art. 27 AIA deployer status matters only where the FRIA is not already settled
# by the Annex III point: 5(b) and 5(c) always need one, point 2 never does.
FRIA_OPEN = {
    "all": [
        HIGH_RISK_ROUTE,
        {"field": "roles", "has": Role.DEPLOYER.value},
        {
            "not": {
                "field": "annex_iii_area",
                "in": [
                    AnnexIII.CRITICAL_INFRASTRUCTURE.value,
                    AnnexIII.CREDITWORTHINESS.value,
                    AnnexIII.INSURANCE_LIFE_HEALTH.value,
                ],
            }
        },
    ]
}


def _dated_before(cut_off: str) -> dict[str, Any]:
    return {
        "any": [
            {"field": "placing_on_market_date", "before": cut_off},
            {"field": "putting_into_service_date", "before": cut_off},
        ]
    }


# Art. 111(2) AIA reads a significant change only for a high-risk system placed on the
# market or put into service before its Chapter III date (transitions.change_used): the
# Annex III date for an Annex III area, else the Annex I date, never for a Section B
# product without one. The dates come from the engine's constants; the browser only
# compares them.
CHANGE_OPEN = {
    "all": [
        HIGH_RISK_ROUTE,
        {
            "any": [
                {"all": [ANNEX_III_ANY, _dated_before(POINT_C_ANNEX_III)]},
                {
                    "all": [
                        {"not": ANNEX_III_ANY},
                        {"not": {"field": "annex_i_section", "is": AnnexISection.SECTION_B.value}},
                        _dated_before(POINT_C_ANNEX_I),
                    ]
                },
            ]
        },
    ]
}

_ANSWERS = {
    "yes": "Yes",
    "no": "No",
    "unknown": "I don't know",
}


def _options(enum: type) -> list[dict[str, str]]:
    return [{"value": member.value, "label": option_label(member)} for member in enum]


QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "system",
        "kind": "details",
        "title": "About the system",
        "hint": "Plain facts for the report heading. Use synthetic or public facts in this demo.",
        "fields": [
            {"field": "name", "label": "System name", "required": True},
            {"field": "description", "label": "Short description"},
            {"field": "purpose", "label": "Intended purpose"},
            {"field": "sector", "label": "Sector"},
            {"field": "intended_purpose_source", "label": "Where the intended purpose is stated"},
        ],
    },
    {
        "id": "roles",
        "kind": "multi",
        "field": "roles",
        "title": "Which roles does your organisation hold for this system?",
        "hint": "Select every role that applies. A single company often holds several.",
        "options": _options(Role),
        "required": True,
        "unknown": BLOCK,
    },
    {
        "id": "is_ai_system",
        "kind": "boolean",
        "field": "is_ai_system",
        "title": "Is the software an AI system?",
        "hint": "As defined in the AI Act. Choose I don't know if this is not yet settled.",
        "article": "Art. 3(1) AIA",
        "unknown": {"value": None},
    },
    {
        "id": "eu_nexus",
        "kind": "boolean",
        "field": "eu_nexus",
        "title": "Is the system placed on the market, put into service or used in the EU?",
        "hint": "Including output used in the EU.",
        "article": "Art. 2 AIA",
        "unknown": {"value": None},
    },
    {
        "id": "excluded_use_flags",
        "kind": "multi",
        "field": "excluded_use_flags",
        "title": "Does any scope exclusion or carve-out possibly apply?",
        "hint": "A selection does not exclude the system. It routes the scope question to review.",
        "article": "Art. 2 AIA",
        "options": _options(ExcludedUse),
        "none_label": "None of these",
        "unknown": BLOCK,
    },
    {
        "id": "prohibited_practices",
        "kind": "multi",
        "field": "prohibited_practices",
        "title": "Does the system involve any of these practices?",
        "hint": "Each is a prohibited practice under Art. 5 AIA.",
        "article": "Art. 5 AIA",
        "options": _options(ProhibitedPractice),
        "none_label": "None of these",
        "show_if": IN_SCOPE,
        "unknown": BLOCK,
    },
    {
        "id": "annex_i_safety_component",
        "kind": "boolean",
        "field": "annex_i_safety_component",
        "title": "Is the system a product, or a safety component of a product, covered by "
        "the Union harmonisation legislation in Annex I?",
        "article": "Art. 6(1) AIA",
        "show_if": IN_SCOPE,
        "unknown": BLOCK,
    },
    {
        "id": "annex_i_third_party_assessment",
        "kind": "boolean",
        "field": "annex_i_third_party_assessment",
        "title": "Does that product need a third-party conformity assessment under that "
        "legislation?",
        "article": "Art. 6(1) AIA",
        "show_if": {"all": [IN_SCOPE, {"field": "annex_i_safety_component", "is": True}]},
        "unknown": BLOCK,
    },
    {
        "id": "annex_i_section",
        "kind": "single",
        "field": "annex_i_section",
        "title": "Which section of Annex I lists that legislation?",
        "hint": "For a Section B product only the provisions in Art. 2(2) AIA apply.",
        "article": "Art. 6(1) AIA",
        "options": _options(AnnexISection),
        # Off the Art. 6(1) route the engine reports a given section as unused.
        "show_if": {"all": [IN_SCOPE, ANNEX_I_ROUTE]},
        # A missing section is treated as Section A without routing to review.
        "unknown": BLOCK,
    },
    {
        "id": "annex_iii_area",
        "kind": "single",
        "field": "annex_iii_area",
        "title": "Is the system intended for a use listed in Annex III?",
        "hint": "Choose the point that applies. If an area applies but not which point, choose "
        "the unsettled option; it is treated as high-risk and routed to review.",
        "article": "Art. 6(2) AIA",
        "options": _options(AnnexIII),
        "none_label": "None of these",
        "show_if": IN_SCOPE,
        "unknown": {"value": AnnexIII.UNSURE.value},
    },
    {
        "id": "performs_profiling",
        "kind": "boolean",
        "field": "derogation.performs_profiling",
        "title": "Does the system perform profiling of natural persons?",
        "hint": "Profiling keeps an Annex III system high-risk.",
        "article": "Art. 6(3) AIA",
        "show_if": {"all": [IN_SCOPE, ANNEX_III_ANY]},
        "unknown": BLOCK,
    },
    {
        "id": "derogation",
        "kind": "flags",
        "title": "Does any of these Art. 6(3) conditions apply?",
        "hint": "An asserted condition never lowers the tier here. It keeps the system "
        "high-risk and routes the derogation to review.",
        "article": "Art. 6(3) AIA",
        "options": [
            {"field": f"derogation.{key}", "label": DEROGATION_LABELS[key]}
            for key in (
                "narrow_procedural_task",
                "improves_prior_human_activity",
                "detects_patterns_without_replacing_human",
                "preparatory_task",
            )
        ],
        "none_label": "None of these",
        "show_if": {
            "all": [
                IN_SCOPE,
                ANNEX_III_ANY,
                {"field": "derogation.performs_profiling", "is": False},
            ]
        },
        "unknown": BLOCK,
    },
    {
        "id": "deployer_public_law_body",
        "kind": "boolean",
        "field": "deployer_public_law_body",
        "title": "Is the deployer a body governed by public law?",
        "article": "Art. 27 AIA",
        "show_if": FRIA_OPEN,
        "unknown": BLOCK,
    },
    {
        "id": "deployer_private_public_service",
        "kind": "boolean",
        "field": "deployer_private_public_service",
        "title": "Is the deployer a private entity providing public services?",
        "article": "Art. 27 AIA",
        "show_if": FRIA_OPEN,
        "unknown": BLOCK,
    },
    {
        "id": "provider_established_outside_eu",
        "kind": "boolean",
        "field": "provider_established_outside_eu",
        "title": "Is the provider established outside the EU?",
        "article": "Art. 22 AIA",
        "show_if": HIGH_RISK_ROUTE,
        "unknown": BLOCK,
    },
    {
        "id": "has_authorised_representative",
        "kind": "boolean",
        "field": "has_authorised_representative",
        "title": "Has the provider appointed an authorised representative in the EU?",
        "article": "Art. 22 AIA",
        "show_if": {
            "all": [HIGH_RISK_ROUTE, {"field": "provider_established_outside_eu", "is": True}]
        },
        "unknown": BLOCK,
    },
    {
        "id": "value_chain",
        "kind": "flags",
        "title": "Does your organisation do either of these to the system?",
        "hint": "Either can make a distributor, importer or deployer a provider.",
        "article": "Art. 25 AIA",
        "options": [
            {
                "field": "puts_name_or_trademark_on_system",
                "label": "Puts its name or trademark on it",
            },
            {"field": "substantially_modifies_system", "label": "Substantially modifies it"},
        ],
        "none_label": "Neither",
        "show_if": HIGH_RISK_ROUTE,
        "unknown": BLOCK,
    },
    {
        "id": "is_gpai_model",
        "kind": "boolean",
        "field": "is_gpai_model",
        "title": "Is this a general-purpose AI model?",
        "show_if": IN_SCOPE,
        "unknown": BLOCK,
    },
    {
        "id": "training_flops",
        "kind": "number",
        "field": "training_flops",
        "title": "What was the cumulative training compute, in FLOP?",
        "hint": "For example 2e25. Leave blank if not disclosed; the systemic-risk status then "
        "goes to review unless the model is designated.",
        "article": "Art. 51(2) AIA",
        "show_if": {"all": [IN_SCOPE, {"field": "is_gpai_model", "is": True}]},
    },
    {
        "id": "gpai_systemic_risk_designated",
        "kind": "boolean",
        "field": "gpai_systemic_risk_designated",
        "title": "Has the Commission designated the model as having systemic risk?",
        "article": "Art. 51(1)(b) AIA",
        "show_if": {"all": [IN_SCOPE, {"field": "is_gpai_model", "is": True}]},
        "unknown": BLOCK,
    },
    {
        "id": "transparency",
        "kind": "flags",
        "title": "Does the system do any of these?",
        "article": "Art. 50 AIA",
        "options": [
            {
                "field": "interacts_with_natural_persons",
                "label": "Interacts directly with natural persons (Art. 50(1))",
            },
            {
                "field": "generates_synthetic_content",
                "label": "Generates synthetic audio, image, video or text (Art. 50(2))",
            },
            {
                "field": "deploys_emotion_or_biometric_categorisation",
                "label": "Emotion recognition or biometric categorisation (Art. 50(3))",
            },
            {
                "field": "generates_deepfakes",
                "label": "Generates or manipulates deep fakes (Art. 50(4))",
            },
        ],
        "none_label": "None of these",
        "show_if": IN_SCOPE,
        "unknown": BLOCK,
    },
    {
        "id": "public_authority_use",
        "kind": "boolean",
        "field": "public_authority_use",
        "title": "Is the system intended to be used by public authorities?",
        "unknown": BLOCK,
    },
    {
        "id": "dates",
        "kind": "details",
        "title": "Market dates",
        "hint": "YYYY-MM-DD, the AI system's dates. Leave blank if not yet placed on the "
        "market or put into service. A general-purpose AI model's own date is asked next.",
        "fields": [
            {"field": "placing_on_market_date", "label": "Placed on the market", "type": "date"},
            {"field": "putting_into_service_date", "label": "Put into service", "type": "date"},
        ],
    },
    {
        "id": "gpai_date",
        "kind": "details",
        "title": "General-purpose AI model date",
        "hint": "YYYY-MM-DD. Leave blank if not given: the model is then dated by the AI "
        "system's placing-on-market date, for review, or, if none is given, its obligations "
        "note the Art. 111(3) transition.",
        "article": "Art. 111(3) AIA",
        "fields": [
            {
                "field": "gpai_model_placing_on_market_date",
                "label": "Model placed on the market",
                "type": "date",
            }
        ],
        # For a profile that screens no general-purpose AI model the engine reports the
        # date as not used.
        "show_if": {"all": [IN_SCOPE, {"field": "is_gpai_model", "is": True}]},
    },
    {
        "id": "significant_change",
        "kind": "boolean",
        "field": "significant_change_after_application_date",
        "title": "Has the system changed significantly after the relevant application date?",
        "hint": "Asked because a date before the system's Chapter III date is given: such a "
        "system comes under the Regulation, apart from Art. 5, only once its design changes "
        "significantly.",
        "article": "Art. 111(2) AIA",
        # Elsewhere the engine reports a given answer as not used.
        "show_if": CHANGE_OPEN,
        # Where it is asked, null always raises the Art. 111(2) open question.
        "unknown": {"value": None},
    },
    {
        "id": "deployer_public_authority",
        "kind": "boolean",
        "field": "deployer_public_authority",
        "title": "Is the deployer a public authority or a Union institution, body, office or "
        "agency, or does it act on behalf of one?",
        "article": "Art. 49(3) AIA",
        # Art. 49(3) and the Art. 111(2) deployer items read it only for a high-risk
        # route; elsewhere the answered significant-change question settles the rest.
        "show_if": HIGH_RISK_ROUTE,
        # A missing status is inferred for review only in some contexts, so it blocks.
        "unknown": BLOCK,
    },
]


def intake_definition() -> dict[str, Any]:
    defaults = SystemProfile(name="x").model_dump(mode="json")
    defaults["name"] = ""
    return {
        "schema": SCHEMA_ID,
        "answers": _ANSWERS,
        "defaults": defaults,
        "questions": QUESTIONS,
    }


# --- Interpreter (mirrored by docs/playground/intake.mjs) ---------------------


def read_field(profile: dict[str, Any], field: str) -> Any:
    value: Any = profile
    for part in field.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def write_field(profile: dict[str, Any], field: str, value: Any) -> None:
    *parents, last = field.split(".")
    target = profile
    for part in parents:
        target = target.setdefault(part, {})
    target[last] = value


def holds(condition: dict[str, Any] | None, profile: dict[str, Any]) -> bool:
    if condition is None:
        return True
    if "all" in condition:
        return all(holds(c, profile) for c in condition["all"])
    if "any" in condition:
        return any(holds(c, profile) for c in condition["any"])
    if "not" in condition:
        return not holds(condition["not"], profile)
    value = read_field(profile, condition["field"])
    if "is" in condition:
        return value == condition["is"] and type(value) is type(condition["is"])
    if "in" in condition:
        return value in condition["in"]
    if "has" in condition:
        return isinstance(value, list) and condition["has"] in value
    if "empty" in condition:
        return (not value) == condition["empty"]
    if "before" in condition:
        # ISO dates compare as strings; answers are validated as dates before they apply.
        return isinstance(value, str) and value < condition["before"]
    raise ValueError(f"unknown condition {condition!r}")


def question_fields(question: dict[str, Any]) -> list[str]:
    if question["kind"] in ("details", "flags"):
        key = "fields" if question["kind"] == "details" else "options"
        return [entry["field"] for entry in question[key]]
    return [question["field"]]


def _base_profile() -> dict[str, Any]:
    profile = intake_definition()["defaults"]
    return {
        key: (dict(value) if isinstance(value, dict) else value) for key, value in profile.items()
    }


# One grammar for both interpreters (NUMBER in intake.mjs): a decimal with an
# optional exponent, so "2e25" passes and "0x10" or "1_000" do not, in either.
_NUMBER = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int | float):
        return math.isfinite(value)
    return (
        isinstance(value, str)
        and bool(_NUMBER.match(value.strip()))
        and (math.isfinite(float(value)))
    )


def is_answered(question: dict[str, Any], answers: dict[str, Any]) -> bool:
    """Whether the question has a usable answer (mirrors ``isAnswered`` in intake.mjs)."""

    present = question["id"] in answers
    answer = answers.get(question["id"])
    kind = question["kind"]
    if kind == "details":
        values = answer if isinstance(answer, dict) else {}
        return all(
            not entry.get("required") or str(values.get(entry["field"]) or "").strip()
            for entry in question["fields"]
        )
    if kind == "boolean":
        return answer in ("yes", "no")
    if kind == "single":
        return (answer == "none" and bool(question.get("none_label"))) or any(
            o["value"] == answer for o in question["options"]
        )
    if kind == "multi":
        values = {o["value"] for o in question["options"]}
        return (
            isinstance(answer, list)
            and (not question.get("required") or bool(answer))
            and all(v in values for v in answer)
        )
    if kind == "flags":
        return isinstance(answer, list)
    if kind == "number":
        return present and (answer in ("", None) or _is_number(answer))
    return False


def answers_to_profile(
    answers: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[str], list[str]]:
    """Apply answers in question order.

    Returns (profile, asked ids, blocked ids, missing ids). A question is asked only
    if its condition holds on the profile built from the answers before it; a
    missing answer leaves its fields at their defaults and is reported, never
    filled in.
    """

    profile = _base_profile()
    asked: list[str] = []
    blocked: list[str] = []
    missing: list[str] = []
    for question in QUESTIONS:
        if not holds(question.get("show_if"), profile):
            continue
        asked.append(question["id"])
        answer = answers.get(question["id"])
        if answer == UNKNOWN:
            policy = question.get("unknown")
            if policy == BLOCK or policy is None:
                blocked.append(question["id"])
            else:
                write_field(profile, question["field"], policy["value"])
            continue
        if not is_answered(question, answers):
            missing.append(question["id"])
            continue
        kind = question["kind"]
        if kind == "details":
            for entry in question["fields"]:
                text = str((answer or {}).get(entry["field"]) or "").strip()
                is_date = entry.get("type") == "date"
                write_field(profile, entry["field"], (text or None) if is_date else text)
        elif kind == "boolean":
            write_field(profile, question["field"], answer == "yes")
        elif kind == "single":
            write_field(profile, question["field"], None if answer == "none" else answer)
        elif kind == "multi":
            write_field(profile, question["field"], list(answer))
        elif kind == "flags":
            for option in question["options"]:
                write_field(profile, option["field"], option["field"] in answer)
        elif kind == "number":
            write_field(profile, question["field"], None if answer in ("", None) else float(answer))
    return profile, asked, blocked, missing


def profile_to_answers(profile: dict[str, Any]) -> dict[str, Any]:
    """The answers that reproduce ``profile``: used to open an example in the intake."""

    full = _base_profile()
    for key, value in profile.items():
        if key == "derogation":
            full["derogation"].update(value)
        elif key != "$schema":
            full[key] = value
    answers: dict[str, Any] = {}
    for question in QUESTIONS:
        kind = question["kind"]
        if kind == "details":
            answers[question["id"]] = {
                entry["field"]: read_field(full, entry["field"]) or ""
                for entry in question["fields"]
            }
        elif kind == "flags":
            answers[question["id"]] = [
                option["field"]
                for option in question["options"]
                if read_field(full, option["field"])
            ]
        else:
            value = read_field(full, question["field"])
            if kind == "boolean":
                # null is "I don't know" only where that answer writes null; any
                # other null (a model default) is left unanswered for the user.
                if value is not None:
                    answers[question["id"]] = "yes" if value else "no"
                elif question.get("unknown") == {"value": None}:
                    answers[question["id"]] = UNKNOWN
            elif kind == "single":
                if value is not None:
                    answers[question["id"]] = value
                elif question.get("none_label"):
                    answers[question["id"]] = "none"
            elif kind == "multi":
                answers[question["id"]] = list(value)
            elif kind == "number":
                answers[question["id"]] = "" if value is None else value
    return answers
