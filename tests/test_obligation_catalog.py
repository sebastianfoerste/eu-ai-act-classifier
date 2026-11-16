"""One source for both lists: ``report.obligations`` is ``report.obligation_graph``
without the Art. 50 items, entry by entry and in the same order.

The requirement of an entry is the item's, except where the entry repeats a counsel flag
that the item carries in its date note (Art. 4 AIA for a Section B product or a prohibited
system; Art. 2(2) AIA for a Section B product in an Annex III area).
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from eu_ai_act_classifier import AnnexIII, Role, SystemProfile, classify
from eu_ai_act_classifier.catalog import ART_2_2, ART_4, DUTY_TITLES

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
FLAG = "Literal reading, confirm with counsel"

SECTION_A = {"annex_i_safety_component": True, "annex_i_third_party_assessment": True}
SECTION_B = {**SECTION_A, "annex_i_section": "B"}
FACTS = [
    {},
    {"placing_on_market_date": "2025-01-10"},
    {"derogation": {"narrow_procedural_task": True}},
    {"deployer_public_authority": True, "deployer_public_law_body": True},
    {"provider_established_outside_eu": True, "substantially_modifies_system": True},
    {"is_gpai_model": True, "training_flops": 1e26},
    {"interacts_with_natural_persons": True, "generates_deepfakes": True},
    {"prohibited_practices": ["5.1.a"]},
]


def _profiles() -> list[SystemProfile]:
    profiles = [
        SystemProfile.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(EXAMPLES.glob("*.json"))
        if path.name != "classification-packet.json"
    ]
    role_sets = [[role] for role in Role] + [[Role.PROVIDER, Role.DEPLOYER]]
    areas = [None, AnnexIII.CRITICAL_INFRASTRUCTURE, AnnexIII.CREDITWORTHINESS, AnnexIII.UNSURE]
    for roles, area, annex_i, facts in itertools.product(
        role_sets, areas, ({}, SECTION_A, SECTION_B), FACTS
    ):
        profiles.append(
            SystemProfile(name="x", roles=roles, annex_iii_area=area, **annex_i, **facts)
        )
    return profiles


def test_the_obligations_list_is_the_graph_without_the_art_50_items() -> None:
    seen: set[str] = set()
    for profile in _profiles():
        report = classify(profile)
        items = [
            item
            for item in report.obligation_graph
            if not item.obligation_id.startswith("transparency.")
        ]
        assert [(ob.applies_to, ob.article) for ob in report.obligations] == [
            (item.actor, item.article) for item in items
        ], profile
        for obligation, item in zip(report.obligations, items, strict=True):
            assert obligation.title == DUTY_TITLES[item.article]
            if obligation.requirement != item.requirement:
                # Only a repeated counsel flag may set the two apart.
                assert item.article in {ART_4, ART_2_2}, item.obligation_id
                assert FLAG in obligation.requirement
                assert FLAG in (item.application_date_note or "")
            seen.add(item.article)
        # The Art. 50 items are the transparency obligations, one for one.
        assert [
            (item.actor, item.article, item.requirement)
            for item in report.obligation_graph
            if item.obligation_id.startswith("transparency.")
        ] == [(ob.applies_to, ob.article, ob.requirement) for ob in report.transparency_obligations]
    assert seen == set(DUTY_TITLES), "a title no profile here reaches, or a duty without one"


@pytest.mark.parametrize("article", range(9, 16))
def test_a_high_risk_provider_gets_the_section_2_items_in_both_lists(article: int) -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS))
    name = f"Art. {article} AIA"
    item = next(item for item in report.obligation_graph if item.article == name)

    assert item.obligation_id == f"high-risk.provider.{article}"
    # Chapter III, Section 2: the point (c)(i) date for an Annex III system.
    assert item.application_date == "2027-12-02"
    assert name in {ob.article for ob in report.obligations}
