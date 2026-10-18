from __future__ import annotations

import json

import pytest

from eu_ai_act_classifier import AnnexIII, Role, SystemProfile, classify, render_report
from eu_ai_act_classifier.artifacts import render_artifact, write_artifacts
from eu_ai_act_classifier.cli import main
from eu_ai_act_classifier.dossier import build_review_dossier, render_review_dossier_markdown
from eu_ai_act_classifier.models import (
    ObligationGraphItem,
    ReviewStatus,
    RiskTier,
    TimelineItem,
)


def test_importer_and_distributor_get_obligations() -> None:
    report = classify(
        SystemProfile(
            name="market access",
            roles=[Role.IMPORTER, Role.DISTRIBUTOR],
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
        )
    )

    articles = {ob.article for ob in report.obligations}
    assert "Art. 23 AIA" in articles
    assert "Art. 24 AIA" in articles


def test_obligation_graph_contains_product_fields() -> None:
    report = classify(
        SystemProfile(
            name="credit scoring",
            roles=[Role.PROVIDER],
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
        )
    )

    item = next(item for item in report.obligation_graph if item.article == "Art. 16 AIA")
    assert item.obligation_id
    assert item.trigger
    assert item.evidence_artifact
    assert item.source_url.startswith("https://")
    assert item.application_date
    assert item.review_status.value


def test_timeline_uses_published_binding_sources() -> None:
    report = classify(SystemProfile(name="x"))
    statuses = {item.source_status.value for item in report.timeline}

    assert statuses == {"binding_level_1"}
    assert any(item.source_id == "ai-act-amendment-2026-1744" for item in report.timeline)


HIGH_RISK_ROUTES = [
    pytest.param({"annex_iii_area": AnnexIII.CREDITWORTHINESS}, "2027-12-02", id="annex-iii"),
    pytest.param(
        {"annex_i_safety_component": True, "annex_i_third_party_assessment": True},
        "2028-08-02",
        id="annex-i",
    ),
]
# Chapter III, Section 5 and Chapter IX: outside the Art. 113, point (c) deferral.
UNDEFERRED_ARTICLES = {f"Art. {n} AIA" for n in (40, 41, 42, 43, 44, 47, 48, 49, 72, 73)}
# Chapter III, Sections 1 to 3 (Arts. 6-27): deferred by Art. 113, point (c).
DEFERRED_ARTICLES = {f"Art. {n} AIA" for n in range(6, 28)}


def _high_risk_graph(facts: dict[str, object]) -> list[ObligationGraphItem]:
    roles = [
        Role.PROVIDER,
        Role.DEPLOYER,
        Role.IMPORTER,
        Role.DISTRIBUTOR,
        Role.AUTHORIZED_REPRESENTATIVE,
    ]
    report = classify(
        SystemProfile(
            name="high-risk system",
            roles=roles,
            deployer_public_law_body=True,
            substantially_modifies_system=True,
            **facts,
        )
    )
    assert report.risk_tier is RiskTier.HIGH
    return report.obligation_graph


@pytest.mark.parametrize(("facts", "deferred_date"), HIGH_RISK_ROUTES)
def test_section_5_and_chapter_ix_items_take_the_literal_date_with_counsel_flag(
    facts: dict[str, object], deferred_date: str
) -> None:
    graph = _high_risk_graph(facts)
    flagged = [item for item in graph if item.article in UNDEFERRED_ARTICLES]

    assert {item.article for item in flagged} == UNDEFERRED_ARTICLES
    for item in flagged:
        assert item.application_date == "2026-08-02"
        assert item.review_status is ReviewStatus.REVIEW_REQUIRED
        assert item.application_date_note is not None
        assert item.application_date_note.startswith("Literal reading, confirm with counsel")
        assert f"{deferred_date} applies" in item.application_date_note


@pytest.mark.parametrize(("facts", "deferred_date"), HIGH_RISK_ROUTES)
def test_sections_1_to_3_items_keep_the_deferred_date(
    facts: dict[str, object], deferred_date: str
) -> None:
    graph = _high_risk_graph(facts)
    deferred = [item for item in graph if item.article not in UNDEFERRED_ARTICLES]

    articles = {item.article for item in deferred}
    assert articles <= DEFERRED_ARTICLES
    assert {f"Art. {n} AIA" for n in (16, 17, 22, 23, 24, 25, 26, 27)} <= articles
    assert {item.application_date for item in deferred} == {deferred_date}
    assert all(item.application_date_note is None for item in deferred)


def test_gpai_and_transparency_items_keep_their_chapter_dates() -> None:
    report = classify(
        SystemProfile(
            name="model and chatbot",
            roles=[Role.PROVIDER, Role.GPAI_PROVIDER],
            is_gpai_model=True,
            gpai_systemic_risk_designated=True,
            interacts_with_natural_persons=True,
        )
    )
    gpai = [item for item in report.obligation_graph if item.actor is Role.GPAI_PROVIDER]
    transparency = [item for item in report.obligation_graph if item.article.startswith("Art. 50")]

    assert gpai and {item.application_date for item in gpai} == {"2025-08-02"}
    assert transparency and {item.application_date for item in transparency} == {"2026-08-02"}
    assert all(item.application_date_note is None for item in report.obligation_graph)


def test_art_50_2_item_notes_the_art_111_4_transition() -> None:
    report = classify(SystemProfile(name="generator", generates_synthetic_content=True))
    item = next(item for item in report.obligation_graph if item.article == "Art. 50(2) AIA")

    assert item.application_date == "2026-08-02"
    assert item.review_status is ReviewStatus.DETERMINED
    assert "Art. 111(4)" in item.application_date_note
    assert "2026-12-02" in item.application_date_note


def test_art_111_4_note_is_dropped_when_placed_on_the_market_after_the_cut_off() -> None:
    report = classify(
        SystemProfile(
            name="generator",
            generates_synthetic_content=True,
            placing_on_market_date="2026-09-01",
        )
    )
    item = next(item for item in report.obligation_graph if item.article == "Art. 50(2) AIA")

    assert item.application_date == "2026-08-02"
    assert item.application_date_note is None


def test_counsel_flag_is_visible_in_text_report_dossier_and_artifacts() -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS))
    flag = "Literal reading, confirm with counsel"

    assert render_report(report).count(flag) == len(UNDEFERRED_ARTICLES)
    dossier = render_review_dossier_markdown(build_review_dossier(report))
    assert dossier.count(flag) == len(UNDEFERRED_ARTICLES)
    assert flag in render_artifact("post-market-monitoring-plan", report)


def test_timeline_encodes_every_art_113_limb_and_art_111_4() -> None:
    timeline = classify(SystemProfile(name="x")).timeline
    dates = [item.applies_from for item in timeline]
    by_date: dict[str, list[TimelineItem]] = {}
    for item in timeline:
        by_date.setdefault(item.applies_from, []).append(item)

    assert dates == sorted(dates)
    # Point (b): Chapter V, and Chapter III Section 4, Chapters VII and XII, Art. 78.
    point_b = " | ".join(item.provision for item in by_date["2025-08-02"])
    assert "Chapter V" in point_b
    for part in (
        "Chapter III Section 4",
        "Chapter VII",
        "Chapter XII",
        "Art. 78",
        "(except Art. 101)",
    ):
        assert part in point_b
    # Point (d): Arts. 102 to 110 from the amending regulation's entry into force.
    (point_d,) = by_date["2026-07-27"]
    assert "Arts. 102-110" in point_d.provision
    assert point_d.source_id == "ai-act-amendment-2026-1744"
    # General date carries the literal-reading flag for Section 5 and Chapter IX.
    (general,) = by_date["2026-08-02"]
    assert "Literal reading, confirm with counsel" in general.note
    # Point (a) exception and Art. 111(4), both 2 December 2026.
    late = by_date["2026-12-02"]
    assert any("Art. 5(1)(ba) and (bb)" in item.provision for item in late)
    assert any("Art. 50(2)" in item.provision and "Art. 111(4)" in item.note for item in late)
    assert {item.source_id for item in late} == {"ai-act-amendment-2026-1744"}
    # Point (c): Chapter III, Sections 1 to 3.
    (annex_iii,) = by_date["2027-12-02"]
    (annex_i,) = by_date["2028-08-02"]
    assert "point (c)(i)" in annex_iii.note
    assert "point (c)(ii)" in annex_i.note


def test_artifact_rendering_contains_review_notice_and_sources() -> None:
    report = classify(
        SystemProfile(
            name="shift sorter",
            annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        )
    )
    artifact = render_artifact("art-6-4-assessment", report)

    assert "Draft only" in artifact
    assert "Source Manifest" in artifact
    assert "Open Questions" in artifact


def test_artifact_writes_only_when_directory_is_supplied(tmp_path) -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS))

    paths = write_artifacts("fria", tmp_path, report)

    assert len(paths) == 1
    assert paths[0].exists()


def test_cli_artifact_requires_directory() -> None:
    assert main(["examples/credit_scoring.json", "--artifact", "fria"]) == 2


def test_cli_sources_outputs_source_manifest(capsys) -> None:
    assert main(["examples/credit_scoring.json", "--sources"]) == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert any(source["source_id"] == "ai-act-2024-1689" for source in data)
    assert any(source["source_id"] == "ai-act-amendment-2026-1744" for source in data)
