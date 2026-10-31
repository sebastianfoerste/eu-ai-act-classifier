"""Art. 4 AIA (AI literacy): every provider and deployer of an in-scope AI system.

Art. 4(1), as replaced by Art. 1, point (5) of Regulation (EU) 2026/1744 (in force
27 July 2026), binds providers and deployers whatever the risk tier. Chapter I applies
from 2 February 2025 (Art. 113, third paragraph, point (a)).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eu_ai_act_classifier import (
    AnnexIII,
    Disposition,
    ReviewStatus,
    RiskTier,
    Role,
    SystemProfile,
    classify,
    render_report,
)
from eu_ai_act_classifier.catalog import ART_4
from eu_ai_act_classifier.citations import POINT_A_DATE
from eu_ai_act_classifier.cli import main
from eu_ai_act_classifier.models import ProhibitedPractice

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
COUNSEL_FLAG = "Literal reading, confirm with counsel"
SECTION_B = {
    "annex_i_safety_component": True,
    "annex_i_third_party_assessment": True,
    "annex_i_section": "B",
}


def _example(name: str) -> SystemProfile:
    return SystemProfile.model_validate_json((EXAMPLES / name).read_text(encoding="utf-8"))


def _literacy(report):
    obligations = [ob for ob in report.obligations if ob.article == ART_4]
    items = [item for item in report.obligation_graph if item.article == ART_4]
    return obligations, items


@pytest.mark.parametrize(
    ("profile", "tier", "roles"),
    [
        pytest.param(_example("spam_filter.json"), RiskTier.MINIMAL, [Role.PROVIDER], id="minimal"),
        pytest.param(
            _example("deepfake_generator.json"), RiskTier.LIMITED, [Role.DEPLOYER], id="limited"
        ),
        pytest.param(
            SystemProfile(
                name="x",
                roles=[Role.PROVIDER, Role.DEPLOYER],
                annex_iii_area=AnnexIII.CREDITWORTHINESS,
            ),
            RiskTier.HIGH,
            [Role.PROVIDER, Role.DEPLOYER],
            id="high-risk-both",
        ),
        pytest.param(
            _example("foundation_model_systemic.json"),
            RiskTier.MINIMAL,
            [Role.PROVIDER],
            id="gpai-model-and-system-provider",
        ),
    ],
)
def test_art_4_attaches_once_per_provider_or_deployer_role(
    profile: SystemProfile, tier: RiskTier, roles: list[Role]
) -> None:
    report = classify(profile)
    obligations, items = _literacy(report)

    assert report.risk_tier is tier
    assert [ob.applies_to for ob in obligations] == roles
    assert [item.actor for item in items] == roles
    assert [item.obligation_id for item in items] == [f"literacy.{r.value}.4" for r in roles]
    for item in items:
        assert item.application_date == POINT_A_DATE == "2025-02-02"
        assert item.review_status is ReviewStatus.DETERMINED
        assert item.application_date_note is None
    for text in (ob.requirement for ob in obligations):
        assert "Take measures to support the development of AI literacy" in text
        assert "No specific level of AI literacy" in text
        assert "Art. 4(1) AIA as replaced by Art. 1, point (5) of Regulation (EU) 2026/1744" in text


def test_art_4_heads_the_obligation_list_and_the_graph() -> None:
    report = classify(_example("credit_scoring.json"))

    assert report.obligations[0].article == ART_4
    assert report.obligation_graph[0].obligation_id == "literacy.provider.4"
    assert "Art. 4 AIA: AI literacy." in render_report(report)


@pytest.mark.parametrize(
    "profile",
    [
        pytest.param(SystemProfile(name="x", is_ai_system=False), id="outside-scope"),
        pytest.param(
            SystemProfile(
                name="x",
                roles=[Role.IMPORTER, Role.DISTRIBUTOR, Role.AUTHORIZED_REPRESENTATIVE],
                annex_iii_area=AnnexIII.CREDITWORTHINESS,
            ),
            id="importer-distributor-representative",
        ),
        pytest.param(_example("foundation_model_unknown_compute.json"), id="gpai-model-only"),
    ],
)
def test_no_art_4_item_outside_scope_or_for_other_roles(profile: SystemProfile) -> None:
    obligations, items = _literacy(classify(profile))

    assert obligations == []
    assert items == []


def test_prohibited_system_gets_no_art_4_item() -> None:
    # The convention for the GPAI duties: a system that may not be placed on the market,
    # put into service or used has no staff to operate it. Pinned so a change is deliberate.
    report = classify(_example("social_scoring.json"))

    assert report.risk_tier is RiskTier.PROHIBITED
    assert report.obligations == []
    assert report.obligation_graph == []
    both = classify(
        SystemProfile(
            name="x",
            roles=[Role.PROVIDER, Role.DEPLOYER],
            prohibited_practices=[ProhibitedPractice.SOCIAL_SCORING],
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
        )
    )
    assert _literacy(both) == ([], [])


def test_scope_review_keeps_the_art_4_item() -> None:
    report = classify(SystemProfile(name="x", roles=[Role.DEPLOYER], eu_nexus=None))
    obligations, items = _literacy(report)

    assert report.scope.status.value == "scope_requires_review"
    assert [ob.applies_to for ob in obligations] == [Role.DEPLOYER]
    assert [item.actor for item in items] == [Role.DEPLOYER]


def test_section_b_product_keeps_art_4_flagged_for_review() -> None:
    report = classify(SystemProfile(name="x", roles=[Role.PROVIDER, Role.DEPLOYER], **SECTION_B))
    obligations, items = _literacy(report)

    assert report.risk_tier is RiskTier.HIGH
    assert [ob.applies_to for ob in obligations] == [Role.PROVIDER, Role.DEPLOYER]
    for obligation in obligations:
        assert COUNSEL_FLAG in obligation.requirement
        assert "so on its wording Art. 4 does not apply" in obligation.requirement
        assert "keeps the Art. 4 duty as the conservative reading" in obligation.requirement
    for item in items:
        assert item.review_status is ReviewStatus.REVIEW_REQUIRED
        assert item.application_date == POINT_A_DATE
        assert item.application_date_note.startswith(COUNSEL_FLAG)
        assert "Art. 4 does not apply" in item.application_date_note


def test_section_b_product_in_an_annex_iii_area_flags_art_4_too() -> None:
    report = classify(
        SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS, **SECTION_B)
    )
    obligations, items = _literacy(report)

    assert len(obligations) == len(items) == 1
    assert COUNSEL_FLAG in obligations[0].requirement
    assert items[0].review_status is ReviewStatus.REVIEW_REQUIRED


def test_section_a_product_is_not_flagged() -> None:
    report = classify(SystemProfile(name="x", **{**SECTION_B, "annex_i_section": "A"}))
    obligations, items = _literacy(report)

    assert COUNSEL_FLAG not in obligations[0].requirement
    assert items[0].review_status is ReviewStatus.DETERMINED


def test_repeated_roles_give_one_art_4_item() -> None:
    report = classify(SystemProfile(name="x", roles=[Role.PROVIDER, Role.PROVIDER]))
    obligations, items = _literacy(report)

    assert len(obligations) == len(items) == 1


def test_minimal_risk_disposition_and_strict_exit_are_unchanged(capsys) -> None:
    report = classify(_example("spam_filter.json"))

    assert report.risk_tier is RiskTier.MINIMAL
    assert report.disposition is Disposition.DETERMINED
    assert report.open_questions == []
    assert main(["examples/spam_filter.json", "--strict"]) == 0
    assert "Art. 4 AIA: AI literacy." in capsys.readouterr().out
    assert main(["examples/social_scoring.json", "--strict"]) == 1


def test_legacy_high_risk_system_flags_art_4_like_art_50() -> None:
    # Art. 111(2) AIA applies "this Regulation" to an unchanged legacy high-risk system
    # only after a significant change in design; the item keeps its date, flagged.
    report = classify(
        SystemProfile(
            name="x",
            roles=[Role.DEPLOYER],
            annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
            putting_into_service_date="2026-09-01",
        )
    )
    (item,) = _literacy(report)[1]
    (art_50_like,) = [
        i for i in report.obligation_graph if i.obligation_id == "high-risk.deployer.26"
    ]

    assert item.application_date == POINT_A_DATE
    assert item.review_status is ReviewStatus.REVIEW_REQUIRED
    assert item.application_date_note.startswith(COUNSEL_FLAG)
    assert "so on its wording Art. 4 would apply to it only then" in item.application_date_note
    assert "keeps the Art. 4 dating as the conservative reading" in item.application_date_note
    # Not the Chapter III conditional note the Art. 26 item carries.
    assert "Whatever date this item gives" in art_50_like.application_date_note
    assert "Whatever date this item gives" not in item.application_date_note


def test_asserted_change_drops_the_legacy_flag_from_art_4() -> None:
    report = classify(
        SystemProfile(
            name="x",
            annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
            putting_into_service_date="2026-09-01",
            significant_change_after_application_date=True,
        )
    )
    (item,) = _literacy(report)[1]

    assert item.review_status is ReviewStatus.DETERMINED
    assert item.application_date_note is None
