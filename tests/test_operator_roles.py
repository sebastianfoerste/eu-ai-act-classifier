"""Duties attach per role. Where the profile's roles do not match the facts it screens,
the report says so in an open question and goes to review: it never returns determined
with a duty for a role the profile does not hold, or with no duty at a high-risk tier.
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import pytest
from pydantic import ValidationError

from eu_ai_act_classifier import (
    AnnexIII,
    ClassificationReport,
    Disposition,
    RiskTier,
    Role,
    SystemProfile,
    classify,
)

ROOT = Path(__file__).resolve().parent.parent

MISMATCHES = {
    "deployer with a GPAI model": {
        "roles": [Role.DEPLOYER],
        "is_gpai_model": True,
        "training_flops": 1e24,
    },
    "provider with deep fakes": {"roles": [Role.PROVIDER], "generates_deepfakes": True},
    "provider with emotion recognition": {
        "roles": [Role.PROVIDER],
        "deploys_emotion_or_biometric_categorisation": True,
    },
    "deployer with synthetic content": {
        "roles": [Role.DEPLOYER],
        "generates_synthetic_content": True,
    },
    "gpai_provider without a GPAI model": {"roles": [Role.GPAI_PROVIDER]},
    "gpai_provider alone in an Annex III area": {
        "roles": [Role.GPAI_PROVIDER],
        "annex_iii_area": AnnexIII.EMPLOYMENT_SELECTION,
    },
    "gpai_provider alone for a Section B product": {
        "roles": [Role.GPAI_PROVIDER],
        "annex_i_safety_component": True,
        "annex_i_third_party_assessment": True,
        "annex_i_section": "B",
    },
}


def _report(**facts: object) -> ClassificationReport:
    return classify(SystemProfile(name="x", **facts))


def _unheld_duties(report: ClassificationReport) -> set[tuple[str, Role]]:
    duties = {
        (ob.article, ob.applies_to)
        for ob in report.obligations
        + report.documentation_required
        + report.transparency_obligations
    }
    duties |= {(item.article, item.actor) for item in report.obligation_graph}
    return {(article, role) for article, role in duties if role not in report.roles}


@pytest.mark.parametrize("facts", MISMATCHES.values(), ids=list(MISMATCHES))
def test_a_role_mismatch_is_never_determined(facts: dict) -> None:
    report = _report(**facts)

    assert report.disposition is Disposition.REQUIRES_REVIEW
    assert report.open_questions


@pytest.mark.parametrize(
    "facts",
    [
        {"roles": [Role.PROVIDER], "interacts_with_natural_persons": True},
        {"roles": [Role.PROVIDER], "generates_synthetic_content": True},
        {"roles": [Role.DEPLOYER], "generates_deepfakes": True},
        {"roles": [Role.DEPLOYER], "deploys_emotion_or_biometric_categorisation": True},
        {
            "roles": [Role.PROVIDER, Role.DEPLOYER],
            "generates_synthetic_content": True,
            "generates_deepfakes": True,
        },
        {"roles": [Role.GPAI_PROVIDER], "is_gpai_model": True, "training_flops": 1e24},
        {
            "roles": [Role.GPAI_PROVIDER, Role.PROVIDER],
            "is_gpai_model": True,
            "training_flops": 2e25,
            "interacts_with_natural_persons": True,
        },
        {"roles": [Role.IMPORTER], "annex_iii_area": AnnexIII.CREDITWORTHINESS},
    ],
)
def test_matching_roles_stay_determined(facts: dict) -> None:
    report = _report(**facts)

    assert report.disposition is Disposition.DETERMINED, report.open_questions
    assert _unheld_duties(report) == set()


GRID_FACTS = {
    "no screen": {},
    "GPAI model": {"is_gpai_model": True, "training_flops": 1e24},
    "Art. 50(1)": {"interacts_with_natural_persons": True},
    "Art. 50(2)": {"generates_synthetic_content": True},
    "Art. 50(3)": {"deploys_emotion_or_biometric_categorisation": True},
    "Art. 50(4)": {"generates_deepfakes": True},
    "Annex III(5)(b)": {"annex_iii_area": AnnexIII.CREDITWORTHINESS},
    "Annex III(4)(a)": {"annex_iii_area": AnnexIII.EMPLOYMENT_SELECTION},
    "Annex I, Section A": {
        "annex_i_safety_component": True,
        "annex_i_third_party_assessment": True,
    },
    "Annex I, Section B": {
        "annex_i_safety_component": True,
        "annex_i_third_party_assessment": True,
        "annex_i_section": "B",
    },
    "Art. 5": {"prohibited_practices": ["5.1.a"]},
}
GRID_ROLES = [[role] for role in Role] + [list(pair) for pair in combinations(Role, 2)]


@pytest.mark.parametrize("facts", GRID_FACTS.values(), ids=list(GRID_FACTS))
def test_determined_reports_carry_only_held_duties(facts: dict) -> None:
    # The invariant the open questions protect, over every role and pair of roles.
    for roles in GRID_ROLES:
        report = _report(roles=roles, **facts)
        if report.disposition is Disposition.DETERMINED:
            assert _unheld_duties(report) == set(), roles
            if report.risk_tier is RiskTier.HIGH:
                assert report.obligations, roles


def test_no_role_question_outside_the_ai_act_scope() -> None:
    report = _report(roles=[Role.DEPLOYER], is_gpai_model=True, is_ai_system=False)

    assert report.risk_tier is RiskTier.OUT_OF_SCOPE
    assert report.disposition is Disposition.DETERMINED
    assert report.open_questions == []


def test_deployer_with_a_gpai_model_keeps_the_chapter_v_items_for_review() -> None:
    report = _report(roles=[Role.DEPLOYER], is_gpai_model=True, training_flops=1e24)

    assert report.risk_tier is RiskTier.MINIMAL
    assert report.disposition is Disposition.REQUIRES_REVIEW
    assert {ob.applies_to for ob in report.obligations} == {Role.GPAI_PROVIDER}
    (question,) = report.open_questions
    assert question.startswith("GPAI model:")
    assert "gpai_provider" in question and "is_gpai_model" in question


def test_gpai_provider_without_a_gpai_model_asks_for_is_gpai_model() -> None:
    report = _report(roles=[Role.GPAI_PROVIDER])

    assert report.risk_tier is RiskTier.MINIMAL
    assert report.disposition is Disposition.REQUIRES_REVIEW
    assert report.obligations == []
    (question,) = report.open_questions
    assert question.startswith("GPAI model:")
    assert "gpai_provider" in question and "is_gpai_model" in question


def test_provider_with_deep_fakes_keeps_the_deployer_item_for_review() -> None:
    report = _report(roles=[Role.PROVIDER], generates_deepfakes=True)

    assert report.risk_tier is RiskTier.LIMITED
    assert report.disposition is Disposition.REQUIRES_REVIEW
    assert [(ob.article, ob.applies_to) for ob in report.transparency_obligations] == [
        ("Art. 50(4) AIA", Role.DEPLOYER)
    ]
    (item,) = report.obligation_graph
    assert (item.article, item.actor) == ("Art. 50(4) AIA", Role.DEPLOYER)
    (question,) = report.open_questions
    assert question.startswith("Art. 50(4) AIA:")
    assert "deployer role" in question


def test_art_50_items_for_one_unheld_role_share_one_question() -> None:
    report = _report(
        roles=[Role.PROVIDER],
        interacts_with_natural_persons=True,
        deploys_emotion_or_biometric_categorisation=True,
        generates_deepfakes=True,
    )

    assert report.disposition is Disposition.REQUIRES_REVIEW
    (question,) = report.open_questions
    assert question.startswith("Art. 50(3) AIA and Art. 50(4) AIA:")
    assert "deployer role" in question
    assert "Art. 50(1)" not in question


def test_gpai_provider_alone_at_a_high_risk_tier_asks_for_the_operator_role() -> None:
    report = _report(roles=[Role.GPAI_PROVIDER], annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION)

    assert report.risk_tier is RiskTier.HIGH
    assert report.disposition is Disposition.REQUIRES_REVIEW
    assert report.obligations == []
    assert any(
        question.startswith("High-risk AI system:") and "operator role" in question
        for question in report.open_questions
    )


@pytest.mark.parametrize("roles", [[], ()])
def test_an_empty_roles_list_is_rejected(roles: list) -> None:
    with pytest.raises(ValidationError, match="roles"):
        SystemProfile(name="x", roles=roles, annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION)
    with pytest.raises(ValidationError, match="roles"):
        SystemProfile.model_validate({"name": "x", "roles": list(roles)})


def test_the_published_schema_requires_a_role() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "system-profile.v1.schema.json").read_text(encoding="utf-8")
    )

    assert schema["properties"]["roles"]["minItems"] == 1
