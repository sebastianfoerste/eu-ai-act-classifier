"""One source for both lists: ``report.obligations`` is ``report.obligation_graph``
without the Art. 50 items and the review tasks in ``GRAPH_ONLY_ITEMS`` (Arts. 40, 42, 44
and 56), entry by entry and in the same order.

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
from eu_ai_act_classifier.obligation_graph import GRAPH_ONLY_ITEMS

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


def test_the_obligations_list_is_the_graph_without_the_art_50_items_and_review_tasks() -> None:
    seen: set[str] = set()
    for profile in _profiles():
        report = classify(profile)
        items = [
            item
            for item in report.obligation_graph
            if not item.obligation_id.startswith("transparency.")
            and item.obligation_id not in GRAPH_ONLY_ITEMS
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


# Arts. 40(1) and 42 grant presumptions of conformity, Art. 44 governs notified bodies'
# certificates and Art. 56 addresses the AI Office and the Board: none puts a duty on the
# provider (sources/oj/32024R1689.en.xhtml), so the list leaves them out. Art. 41(5) does
# put one on the provider, so Art. 41 stays listed.
NOT_PROVIDER_DUTIES = {"Art. 40 AIA", "Art. 42 AIA", "Art. 44 AIA", "Art. 56 AIA"}


def test_review_tasks_without_a_provider_duty_stay_in_the_graph_only() -> None:
    graph_articles: set[str] = set()
    for profile in _profiles():
        report = classify(profile)
        assert not NOT_PROVIDER_DUTIES & {ob.article for ob in report.obligations}, profile
        graph_articles |= {item.article for item in report.obligation_graph}
    # The grid reaches every one of them, so the check above is not vacuous.
    assert graph_articles >= NOT_PROVIDER_DUTIES


def test_art_18_entry_names_what_art_18_1_requires_and_not_the_logs() -> None:
    report = classify(
        SystemProfile(name="x", roles=[Role.PROVIDER], annex_iii_area=AnnexIII.CREDITWORTHINESS)
    )
    (entry,) = [ob for ob in report.obligations if ob.article == "Art. 18 AIA"]
    # Art. 18(1): ten years, at the disposal of the national competent authorities; the
    # logs are Art. 19's.
    assert "10 years" in entry.requirement
    assert "national competent authorities" in entry.requirement
    assert "EU declaration of conformity" in entry.requirement
    # Art. 18(1)(c) and (d), each "where applicable".
    assert "where applicable the changes approved by" in entry.requirement
    assert "documents issued by notified bodies" in entry.requirement
    assert "logs" not in entry.requirement


def test_art_41_entry_states_the_art_41_5_justification_duty() -> None:
    report = classify(
        SystemProfile(name="x", roles=[Role.PROVIDER], annex_iii_area=AnnexIII.CREDITWORTHINESS)
    )
    (entry,) = [ob for ob in report.obligations if ob.article == "Art. 41 AIA"]
    assert "Art. 41(5)" in entry.requirement
    assert "justify" in entry.requirement
    (item,) = [i for i in report.obligation_graph if i.article == "Art. 41 AIA"]
    assert item.review_status.value == "review_required"


@pytest.mark.parametrize(
    ("flops", "expected"),
    [(1e24, {"Art. 53(4) AIA"}), (1e26, {"Art. 53(4) AIA", "Art. 55(2) AIA"})],
)
def test_gpai_provider_lists_the_alternative_means_duty(flops: float, expected: set) -> None:
    # Art. 53(4) and Art. 55(2), third sentence each: a provider that does not adhere to an
    # approved code of practice or does not comply with a harmonised standard demonstrates
    # alternative adequate means of compliance. Art. 56 itself stays a graph-only task.
    report = classify(
        SystemProfile(
            name="m",
            roles=[Role.GPAI_PROVIDER],
            is_gpai_model=True,
            training_flops=flops,
            gpai_model_placing_on_market_date="2025-09-01",
        )
    )
    listed = {ob.article for ob in report.obligations}
    assert {"Art. 53(4) AIA", "Art. 55(2) AIA"} & listed == expected
    assert "Art. 56 AIA" not in listed
    for item in report.obligation_graph:
        if item.article in expected:
            assert item.review_status.value == "review_required"
            assert "alternative adequate means of compliance" in item.requirement


def test_gpai_provider_lists_the_art_41_5_chapter_v_duty() -> None:
    # Art. 41(5) binds "providers of high-risk AI systems or general-purpose AI models"; for
    # the latter the duty is to justify compliance with Chapter V, Sections 2 and 3.
    report = classify(
        SystemProfile(
            name="m",
            roles=[Role.GPAI_PROVIDER],
            is_gpai_model=True,
            training_flops=1e24,
            gpai_model_placing_on_market_date="2025-09-01",
        )
    )
    (entry,) = [
        ob
        for ob in report.obligations
        if ob.article == "Art. 41 AIA" and ob.applies_to is Role.GPAI_PROVIDER
    ]
    assert "Chapter V, Sections 2 and 3" in entry.requirement
    assert "Art. 41(5)" in entry.requirement
    (item,) = [i for i in report.obligation_graph if i.obligation_id == "gpai.provider.41"]
    assert item.review_status.value == "review_required"
