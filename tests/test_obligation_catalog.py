"""The obligations list and the obligation graph come from one catalog (AIA-17).

`report.obligations` used to come from the obligation sets in `catalog.py` and the graph
from its own items in `obligation_graph.py`, so the two listed different articles for
the same role: the list had Arts. 9 to 15 and no Arts. 16, 18 to 21, 40 to 42 or 44,
the graph the reverse, and only the graph had Art. 49(2), Art. 49(5), Art. 56 and
Art. 111(2). Each duty is now one catalog entry, and both lists are built from the same
entries.

Every graph item is an entry of `report.obligations`, or of
`report.transparency_obligations` for Art. 50, for the same actor, with the same
article and requirement, in the same order. A failure lists, per actor, the articles
only one side has.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest

from eu_ai_act_classifier import AnnexIII, ClassificationReport, Role, SystemProfile, classify

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
NOT_A_PROFILE = {"classification-packet.json"}

SECTION_B = {
    "annex_i_safety_component": True,
    "annex_i_third_party_assessment": True,
    "annex_i_section": "B",
}

# Branches no example reaches: one profile each, so every duty the catalog holds is
# compared at least once.
BRANCHES: dict[str, SystemProfile] = {
    "public-authority deployer, Annex III 6(a)": SystemProfile(
        name="victim risk",
        roles=[Role.DEPLOYER],
        annex_iii_area=AnnexIII.LAW_ENFORCEMENT_VICTIM_RISK,
        deployer_public_authority=True,
    ),
    "inferred public-authority deployer, Annex III 5(a)": SystemProfile(
        name="benefits",
        roles=[Role.DEPLOYER],
        annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
        deployer_public_law_body=True,
    ),
    "provider and public-authority deployer, point 2, derogation asserted": SystemProfile(
        name="grid",
        roles=[Role.PROVIDER, Role.DEPLOYER],
        annex_iii_area=AnnexIII.CRITICAL_INFRASTRUCTURE,
        deployer_public_authority=True,
        derogation={"narrow_procedural_task": True},
    ),
    "importer, distributor, representative, value chain": SystemProfile(
        name="market access",
        roles=[Role.IMPORTER, Role.DISTRIBUTOR, Role.AUTHORIZED_REPRESENTATIVE],
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        provider_established_outside_eu=True,
        has_authorised_representative=True,
        substantially_modifies_system=True,
    ),
    "legacy system intended for public authorities": SystemProfile(
        name="legacy",
        roles=[Role.PROVIDER, Role.DEPLOYER, Role.IMPORTER],
        annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
        placing_on_market_date="2025-01-01",
        public_authority_use=True,
    ),
    "Annex I, Section B product": SystemProfile(name="machinery", **SECTION_B),
    "Annex I, Section B product in an Annex III area": SystemProfile(
        name="machinery that screens workers",
        roles=[Role.PROVIDER, Role.DEPLOYER],
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        interacts_with_natural_persons=True,
        **SECTION_B,
    ),
    "GPAI model dated by the system date": SystemProfile(
        name="model",
        roles=[Role.GPAI_PROVIDER, Role.PROVIDER],
        is_gpai_model=True,
        training_flops=1e26,
        placing_on_market_date="2025-01-01",
        generates_synthetic_content=True,
    ),
    "every Art. 50 screen, provider and deployer": SystemProfile(
        name="assistant",
        roles=[Role.PROVIDER, Role.DEPLOYER],
        interacts_with_natural_persons=True,
        generates_synthetic_content=True,
        deploys_emotion_or_biometric_categorisation=True,
        generates_deepfakes=True,
    ),
}


def _profiles() -> dict[str, SystemProfile]:
    examples = {
        path.name: SystemProfile.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(EXAMPLES.glob("*.json"))
        if path.name not in NOT_A_PROFILE
    }
    return {**examples, **BRANCHES}


PROFILES = _profiles()


def _listed(report: ClassificationReport) -> list[tuple[Role, str, str]]:
    return [
        (obligation.applies_to, obligation.article, obligation.requirement)
        for obligation in report.obligations + report.transparency_obligations
    ]


def _graphed(report: ClassificationReport) -> list[tuple[Role, str, str]]:
    return [(item.actor, item.article, item.requirement) for item in report.obligation_graph]


def _articles_by_actor(entries: list[tuple[Role, str, str]]) -> dict[str, set[str]]:
    articles: dict[str, set[str]] = defaultdict(set)
    for actor, article, _ in entries:
        articles[actor.value].add(article)
    return articles


@pytest.mark.parametrize("name", PROFILES)
def test_obligations_and_graph_list_the_same_articles_per_actor(name: str) -> None:
    report = classify(PROFILES[name])
    listed, graphed = _articles_by_actor(_listed(report)), _articles_by_actor(_graphed(report))

    differences = {
        actor: {
            "only in obligations": sorted(listed[actor] - graphed[actor]),
            "only in obligation_graph": sorted(graphed[actor] - listed[actor]),
        }
        for actor in sorted(set(listed) | set(graphed))
        if listed[actor] != graphed[actor]
    }
    assert not differences, differences


@pytest.mark.parametrize("name", PROFILES)
def test_every_graph_item_is_one_listed_obligation_with_the_same_requirement(name: str) -> None:
    report = classify(PROFILES[name])

    assert _listed(report) == _graphed(report)


def test_the_branch_profiles_reach_every_kind_of_duty() -> None:
    # Guards the fixture list above: each of these articles appears in some report.
    articles = {
        item.article for profile in PROFILES.values() for item in classify(profile).obligation_graph
    }

    assert {
        "Art. 2(2) AIA",
        "Art. 22 AIA",
        "Art. 23 AIA",
        "Art. 24 AIA",
        "Art. 25 AIA",
        "Art. 26 AIA",
        "Art. 27 AIA",
        "Art. 49 AIA",
        "Art. 49(2) AIA",
        "Art. 49(3) AIA",
        "Art. 49(5) AIA",
        "Art. 50(1) AIA",
        "Art. 50(2) AIA",
        "Art. 50(3) AIA",
        "Art. 50(4) AIA",
        "Art. 53(1)(a) AIA",
        "Art. 55(1)(a) AIA",
        "Art. 56 AIA",
        "Art. 111(2) AIA",
    } <= articles
