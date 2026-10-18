from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

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


# Chapter III, Section 5 and Chapter IX: outside the Art. 113, point (c) deferral.
UNDEFERRED_ARTICLES = {f"Art. {n} AIA" for n in (40, 41, 42, 43, 44, 47, 48, 49, 72, 73)}
# Chapter III, Sections 1 to 3 (Arts. 6-27): deferred by Art. 113, point (c).
DEFERRED_ARTICLES = {f"Art. {n} AIA" for n in range(6, 28)}
HIGH_RISK_ROUTES = [
    pytest.param(
        {"annex_iii_area": AnnexIII.CREDITWORTHINESS},
        "2027-12-02",
        UNDEFERRED_ARTICLES,
        id="annex-iii",
    ),
    # Art. 49(1) AIA registers only Annex III systems, so an Annex I product has no
    # Art. 49 item.
    pytest.param(
        {"annex_i_safety_component": True, "annex_i_third_party_assessment": True},
        "2028-08-02",
        UNDEFERRED_ARTICLES - {"Art. 49 AIA"},
        id="annex-i",
    ),
]


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


@pytest.mark.parametrize(("facts", "deferred_date", "undeferred"), HIGH_RISK_ROUTES)
def test_section_5_and_chapter_ix_items_take_the_literal_date_with_counsel_flag(
    facts: dict[str, object], deferred_date: str, undeferred: set[str]
) -> None:
    graph = _high_risk_graph(facts)
    flagged = [item for item in graph if item.article in UNDEFERRED_ARTICLES]

    assert {item.article for item in flagged} == undeferred
    for item in flagged:
        assert item.application_date == "2026-08-02"
        assert item.review_status is ReviewStatus.REVIEW_REQUIRED
        assert item.application_date_note is not None
        assert item.application_date_note.startswith("Literal reading, confirm with counsel")
        assert f"{deferred_date} applies" in item.application_date_note


@pytest.mark.parametrize(("facts", "deferred_date", "undeferred"), HIGH_RISK_ROUTES)
def test_sections_1_to_3_items_keep_the_deferred_date(
    facts: dict[str, object], deferred_date: str, undeferred: set[str]
) -> None:
    graph = _high_risk_graph(facts)
    deferred = [item for item in graph if item.article not in UNDEFERRED_ARTICLES]

    articles = {item.article for item in deferred}
    assert articles <= DEFERRED_ARTICLES
    assert {f"Art. {n} AIA" for n in (16, 17, 22, 23, 24, 25, 26, 27)} <= articles
    assert {item.application_date for item in deferred} == {deferred_date}
    assert all(item.application_date_note is None for item in deferred)


@pytest.mark.parametrize(
    ("facts", "registration"),
    [
        pytest.param(
            {"annex_iii_area": AnnexIII.CREDITWORTHINESS}, "Art. 49 AIA", id="annex-iii-5b"
        ),
        # Unsettled point: it may not be point 2, so the duty stays for review.
        pytest.param({"annex_iii_area": AnnexIII.UNSURE}, "Art. 49 AIA", id="annex-iii-unsure"),
        # Art. 49(1) excepts point 2; Art. 49(5) registers it at national level.
        pytest.param(
            {"annex_iii_area": AnnexIII.CRITICAL_INFRASTRUCTURE},
            "Art. 49(5) AIA",
            id="annex-iii-2",
        ),
        pytest.param(
            {"annex_i_safety_component": True, "annex_i_third_party_assessment": True},
            None,
            id="annex-i",
        ),
        pytest.param(
            {
                "annex_i_safety_component": True,
                "annex_i_third_party_assessment": True,
                "annex_iii_area": AnnexIII.CREDITWORTHINESS,
            },
            "Art. 49 AIA",
            id="annex-i-and-annex-iii",
        ),
    ],
)
def test_art_49_registration_follows_art_49_scope(
    facts: dict[str, object], registration: str | None
) -> None:
    report = classify(SystemProfile(name="high-risk system", **facts))

    assert report.risk_tier is RiskTier.HIGH
    obligations = {ob.article for ob in report.obligations}
    assert ("Art. 49 AIA" in obligations) is (registration == "Art. 49 AIA")
    assert "Art. 49(5) AIA" not in obligations
    graph = {item.article: item for item in report.obligation_graph}
    assert {"Art. 43 AIA", "Art. 47 AIA", "Art. 48 AIA"} <= graph.keys()
    assert graph.keys() & {"Art. 49 AIA", "Art. 49(5) AIA"} == (
        {registration} if registration else set()
    )
    if registration:
        item = graph[registration]
        assert item.application_date == "2026-08-02"
        assert item.review_status is ReviewStatus.REVIEW_REQUIRED
        assert item.application_date_note is not None
        assert item.application_date_note.startswith("Literal reading, confirm with counsel")
        # Registration reaches the system only through Annex III, so the deferred
        # alternative is point (c)(i), also for a system that is an Annex I product too.
        assert "2027-12-02 applies" in item.application_date_note


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
    assert all(item.application_date_note is None for item in transparency)


# Art. 111(4) AIA: systems placed on the market before 2 August 2026 comply with
# Art. 50(2) by 2 December 2026. "Before" excludes the cut-off date itself.
@pytest.mark.parametrize(
    ("placed", "application_date", "noted"),
    [
        pytest.param(None, "2026-08-02", True, id="unknown"),
        pytest.param("2026-03-01", "2026-12-02", True, id="before"),
        pytest.param("2026-08-01", "2026-12-02", True, id="day-before-cut-off"),
        pytest.param("2026-08-02", "2026-08-02", False, id="on-cut-off"),
        pytest.param("2026-09-01", "2026-08-02", False, id="after"),
    ],
)
def test_art_50_2_item_follows_the_art_111_4_transition(
    placed: str | None, application_date: str, noted: bool
) -> None:
    report = classify(
        SystemProfile(
            name="generator",
            generates_synthetic_content=True,
            placing_on_market_date=placed,
        )
    )
    item = next(item for item in report.obligation_graph if item.article == "Art. 50(2) AIA")

    assert item.application_date == application_date
    assert item.review_status is ReviewStatus.DETERMINED
    if noted:
        assert item.application_date_note is not None
        assert "Art. 111(4)" in item.application_date_note
        assert "2026-12-02" in item.application_date_note
    else:
        assert item.application_date_note is None


# Art. 111(3) AIA: GPAI models placed on the market before 2 August 2025 comply by
# 2 August 2027. The items keep the Chapter V date and carry the transition as a note.
@pytest.mark.parametrize(
    ("placed", "noted"),
    [
        pytest.param(None, True, id="unknown"),
        pytest.param("2025-03-01", True, id="before"),
        pytest.param("2025-08-01", True, id="day-before-cut-off"),
        pytest.param("2025-08-02", False, id="on-cut-off"),
        pytest.param("2026-01-01", False, id="after"),
    ],
)
def test_gpai_items_note_the_art_111_3_transition(placed: str | None, noted: bool) -> None:
    report = classify(
        SystemProfile(
            name="model",
            roles=[Role.GPAI_PROVIDER],
            is_gpai_model=True,
            gpai_systemic_risk_designated=True,
            placing_on_market_date=placed,
        )
    )
    gpai = [item for item in report.obligation_graph if item.actor is Role.GPAI_PROVIDER]

    assert {item.article for item in gpai} >= {"Art. 53(1)(a) AIA", "Art. 55(1)(d) AIA"}
    assert {item.application_date for item in gpai} == {"2025-08-02"}
    for item in gpai:
        if noted:
            assert item.application_date_note is not None
            assert item.application_date_note.startswith("Art. 111(3) AIA")
            assert "2025-08-02" in item.application_date_note
            assert "2027-08-02" in item.application_date_note
        else:
            assert item.application_date_note is None


@pytest.mark.parametrize("field", ["placing_on_market_date", "putting_into_service_date"])
@pytest.mark.parametrize(
    "value", ["August 2025", "01.09.2026", "2026-02-30", "20260801", "2026-8-1", ""]
)
def test_market_dates_must_be_iso_dates(field: str, value: str) -> None:
    with pytest.raises(ValidationError, match="ISO date"):
        SystemProfile.model_validate({"name": "x", field: value})


@pytest.mark.parametrize("field", ["placing_on_market_date", "putting_into_service_date"])
def test_market_dates_accept_iso_dates_and_null(field: str) -> None:
    assert getattr(SystemProfile.model_validate({"name": "x", field: "2026-08-01"}), field) == (
        "2026-08-01"
    )
    assert getattr(SystemProfile.model_validate({"name": "x", field: None}), field) is None


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
