from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from eu_ai_act_classifier import AnnexIII, Role, SystemProfile, classify, render_report
from eu_ai_act_classifier.artifacts import render_artifact, write_artifacts
from eu_ai_act_classifier.cli import main
from eu_ai_act_classifier.dossier import build_review_dossier, render_review_dossier_markdown
from eu_ai_act_classifier.models import (
    Derogation,
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
    # Still "classified as high-risk pursuant to Article 6(2) and Annex III", so
    # point (c)(i) dates Sections 1 to 3, not point (c)(ii).
    pytest.param(
        {
            "annex_i_safety_component": True,
            "annex_i_third_party_assessment": True,
            "annex_iii_area": AnnexIII.CREDITWORTHINESS,
        },
        "2027-12-02",
        UNDEFERRED_ARTICLES,
        id="annex-i-and-annex-iii",
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


# Art. 49(2) AIA: a provider relying on the Art. 6(3) derogation registers in the EU
# database. Unlike Art. 49(1), it has no exception for Annex III point 2.
@pytest.mark.parametrize(
    ("area", "high_risk_registration"),
    [
        pytest.param(AnnexIII.CRITICAL_INFRASTRUCTURE, "Art. 49(5) AIA", id="annex-iii-2"),
        pytest.param(AnnexIII.EMPLOYMENT_SELECTION, "Art. 49 AIA", id="annex-iii-4a"),
    ],
)
def test_derogation_adds_art_49_2_registration_item(
    area: AnnexIII, high_risk_registration: str
) -> None:
    report = classify(
        SystemProfile(
            name="derogation",
            annex_iii_area=area,
            derogation=Derogation(preparatory_task=True),
        )
    )

    assert report.risk_tier is RiskTier.HIGH
    graph = {item.article: item for item in report.obligation_graph}
    assert {"Art. 49(2) AIA", high_risk_registration} <= graph.keys()
    item = graph["Art. 49(2) AIA"]
    assert item.obligation_id == "high-risk.provider.49.2"
    assert item.application_date == "2026-08-02"
    assert item.review_status is ReviewStatus.REVIEW_REQUIRED
    assert item.application_date_note is not None
    assert item.application_date_note.startswith("Literal reading, confirm with counsel")
    assert "Chapter III, Section 5 duty" in item.application_date_note
    assert "2027-12-02 applies" in item.application_date_note
    assert "Art. 49(2) AIA" not in {ob.article for ob in report.obligations}


@pytest.mark.parametrize(
    "derogation",
    [
        pytest.param({}, id="none-asserted"),
        # Profiling forecloses the derogation (Art. 6(3), third subparagraph).
        pytest.param({"preparatory_task": True, "performs_profiling": True}, id="profiling"),
    ],
)
def test_no_art_49_2_item_without_an_available_derogation(derogation: dict[str, bool]) -> None:
    report = classify(
        SystemProfile(
            name="no derogation",
            annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
            derogation=Derogation(**derogation),
        )
    )

    assert "Art. 49(2) AIA" not in {item.article for item in report.obligation_graph}


def test_art_6_4_artifact_lists_the_art_49_2_item_for_a_point_2_derogation() -> None:
    report = classify(
        SystemProfile(
            name="grid balancer",
            annex_iii_area=AnnexIII.CRITICAL_INFRASTRUCTURE,
            derogation=Derogation(preparatory_task=True),
        )
    )
    artifact = render_artifact("art-6-4-assessment", report)
    graph_section = artifact.split("## Relevant Obligation Graph Items")[1].split("## ")[0]

    assert "- Art. 49(2) AIA (provider): If the provider concludes under Art. 6(3)" in (
        graph_section
    )
    assert "Literal reading, confirm with counsel" in graph_section
    assert "No directly matching graph item" not in graph_section
    assert "Art. 49(5) AIA" not in graph_section


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
# 2 August 2027. Dated like Art. 50(2) under Art. 111(4): an unknown date keeps the
# Chapter V date with the transition as a condition.
ART_111_3_CASES = [
    pytest.param(None, "2025-08-02", True, id="unknown"),
    pytest.param("2025-03-01", "2027-08-02", True, id="before"),
    pytest.param("2025-08-01", "2027-08-02", True, id="day-before-cut-off"),
    pytest.param("2025-08-02", "2025-08-02", False, id="on-cut-off"),
    pytest.param("2026-01-01", "2025-08-02", False, id="after"),
]


def _gpai_items(**dates: str | None) -> list[ObligationGraphItem]:
    report = classify(
        SystemProfile(
            name="model",
            roles=[Role.GPAI_PROVIDER],
            is_gpai_model=True,
            gpai_systemic_risk_designated=True,
            **dates,
        )
    )
    gpai = [item for item in report.obligation_graph if item.actor is Role.GPAI_PROVIDER]
    assert {item.article for item in gpai} >= {
        "Art. 53(1)(a) AIA",
        "Art. 55(1)(d) AIA",
        "Art. 56 AIA",
    }
    return gpai


@pytest.mark.parametrize(("placed", "application_date", "noted"), ART_111_3_CASES)
def test_gpai_items_follow_the_art_111_3_transition(
    placed: str | None, application_date: str, noted: bool
) -> None:
    gpai = _gpai_items(gpai_model_placing_on_market_date=placed)

    assert {item.application_date for item in gpai} == {application_date}
    for item in gpai:
        if noted:
            assert item.application_date_note is not None
            assert item.application_date_note.startswith("Art. 111(3) AIA")
            assert "2025-08-02" in item.application_date_note
            assert "2027-08-02" in item.application_date_note
        else:
            assert item.application_date_note is None


@pytest.mark.parametrize(("placed", "application_date", "noted"), ART_111_3_CASES[1:])
def test_gpai_items_fall_back_to_the_system_date_with_a_review_note(
    placed: str, application_date: str, noted: bool
) -> None:
    # Backwards compatible: only placing_on_market_date given, so the old dating stays,
    # and every item says the model was dated by the AI system's date.
    gpai = _gpai_items(placing_on_market_date=placed)

    assert {item.application_date for item in gpai} == {application_date}
    for item in gpai:
        assert item.application_date_note is not None
        assert item.application_date_note.startswith("Art. 111(3) AIA")
        assert ("2027-08-02" in item.application_date_note) is noted
        assert "no gpai_model_placing_on_market_date is given" in item.application_date_note
        assert item.application_date_note.endswith("give the model's own date.")


def test_model_date_drives_art_111_3_and_system_date_drives_art_111_4() -> None:
    report = classify(
        SystemProfile(
            name="model in a generator",
            roles=[Role.PROVIDER, Role.GPAI_PROVIDER],
            is_gpai_model=True,
            gpai_systemic_risk_designated=True,
            generates_synthetic_content=True,
            gpai_model_placing_on_market_date="2025-03-01",
            placing_on_market_date="2026-09-01",
        )
    )
    gpai = [item for item in report.obligation_graph if item.actor is Role.GPAI_PROVIDER]
    (art_50_2,) = [item for item in report.obligation_graph if item.article == "Art. 50(2) AIA"]

    # The model predates 2 August 2025 (Art. 111(3)); the system does not predate
    # 2 August 2026 (Art. 111(4)).
    assert {item.application_date for item in gpai} == {"2027-08-02"}
    assert all(
        "gpai_model_placing_on_market_date" not in item.application_date_note for item in gpai
    )
    assert art_50_2.application_date == "2026-08-02"
    assert art_50_2.application_date_note is None


MARKET_DATE_FIELDS = [
    "placing_on_market_date",
    "putting_into_service_date",
    "gpai_model_placing_on_market_date",
]


@pytest.mark.parametrize("field", MARKET_DATE_FIELDS)
@pytest.mark.parametrize(
    "value", ["August 2025", "01.09.2026", "2026-02-30", "20260801", "2026-8-1", ""]
)
def test_market_dates_must_be_iso_dates(field: str, value: str) -> None:
    with pytest.raises(ValidationError, match="ISO date"):
        SystemProfile.model_validate({"name": "x", field: value})


@pytest.mark.parametrize("field", MARKET_DATE_FIELDS)
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


def test_timeline_encodes_every_art_113_limb_and_art_111_3_and_4() -> None:
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
    # Art. 111(3), original text: GPAI models already on the market before 2 August 2025.
    (art_111_3,) = by_date["2027-08-02"]
    assert "Art. 111(3)" in art_111_3.provision
    assert "general-purpose AI models" in art_111_3.provision
    assert "before 2 August 2025" in art_111_3.note
    assert art_111_3.source_id == "ai-act-2024-1689"
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


# --- Art. 111(2) AIA: high-risk systems already on the market ------------------------
def _legacy_items(**facts: object) -> list[ObligationGraphItem]:
    report = classify(SystemProfile(name="legacy", **facts))
    assert report.risk_tier is RiskTier.HIGH
    return [item for item in report.obligation_graph if item.article == "Art. 111(2) AIA"]


@pytest.mark.parametrize(
    ("facts", "cut_off"),
    [
        pytest.param({"annex_iii_area": AnnexIII.CREDITWORTHINESS}, "2027-12-02", id="annex-iii"),
        pytest.param(
            {"annex_i_safety_component": True, "annex_i_third_party_assessment": True},
            "2028-08-02",
            id="annex-i",
        ),
    ],
)
@pytest.mark.parametrize(
    ("dates", "legacy"),
    [
        pytest.param({}, False, id="no-dates"),
        pytest.param({"placing_on_market_date": "2025-06-01"}, True, id="placed-before"),
        pytest.param({"putting_into_service_date": "2025-06-01"}, True, id="in-service-before"),
        pytest.param(
            {"placing_on_market_date": "2029-01-01", "putting_into_service_date": "2025-06-01"},
            True,
            id="either-date-counts",
        ),
        pytest.param({"placing_on_market_date": "2029-01-01"}, False, id="after"),
    ],
)
def test_art_111_2_item_only_for_a_system_on_the_market_before_its_chapter_iii_date(
    facts: dict[str, object], cut_off: str, dates: dict[str, str], legacy: bool
) -> None:
    items = _legacy_items(roles=[Role.PROVIDER, Role.DEPLOYER], **facts, **dates)

    if not legacy:
        assert items == []
        return
    assert [item.obligation_id for item in items] == [
        "high-risk.provider.111.2",
        "high-risk.deployer.111.2",
    ]
    for item in items:
        assert item.application_date == cut_off
        assert item.review_status is ReviewStatus.REVIEW_REQUIRED
        assert f"before {cut_off}" in item.trigger
        assert f"significantly as from {cut_off}" in item.requirement
        # Before 2 August 2026 the system is a legacy system on either reading of the
        # Chapter III date, so the cut-off is not contested.
        assert item.application_date_note is not None
        assert item.application_date_note.startswith("Art. 111(2) AIA")
        assert "Annex X" in item.application_date_note


def test_art_111_2_public_authority_systems_comply_by_2_august_2030() -> None:
    items = _legacy_items(
        roles=[Role.PROVIDER, Role.DEPLOYER],
        annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
        placing_on_market_date="2026-03-01",
        significant_change_after_application_date=False,
        public_authority_use=True,
    )

    assert {item.actor for item in items} == {Role.PROVIDER, Role.DEPLOYER}
    for item in items:
        assert item.application_date == "2030-08-02"
        assert "No significant change in design is asserted" in item.requirement
        assert "by 2 August 2030 in any case" in item.requirement


def test_art_111_2_significant_change_keeps_the_chapter_iii_date_for_public_authorities() -> None:
    # The changed system is covered as from the Chapter III date; 2 August 2030 is only
    # the outer limit for an unchanged one.
    (item,) = _legacy_items(
        annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
        placing_on_market_date="2026-03-01",
        significant_change_after_application_date=True,
        public_authority_use=True,
    )

    assert item.application_date == "2027-12-02"
    assert "the Regulation applies to the changed system" in item.requirement
    assert "by 2 August 2030 in any case" in item.requirement


@pytest.mark.parametrize(
    ("change", "wording"),
    [
        (None, "Confirm whether it has"),
        (False, "No significant change in design is asserted"),
        (True, "the Regulation applies to the changed system"),
    ],
)
def test_art_111_2_requirement_follows_the_significant_change_fact(
    change: bool | None, wording: str
) -> None:
    (item,) = _legacy_items(
        annex_iii_area=AnnexIII.CREDITWORTHINESS,
        placing_on_market_date="2026-03-01",
        significant_change_after_application_date=change,
    )

    assert wording in item.requirement


@pytest.mark.parametrize(
    ("placed", "contested"),
    [
        pytest.param("2026-08-01", False, id="before-general-date"),
        pytest.param("2026-08-02", True, id="on-general-date"),
        pytest.param("2027-12-01", True, id="day-before-chapter-iii-date"),
    ],
)
def test_art_111_2_cut_off_is_flagged_where_the_reading_decides(
    placed: str, contested: bool
) -> None:
    # Art. 113 gives Chapter III no single date: between the general date and the
    # point (c) date the result turns on which date Art. 111(2) means.
    (item,) = _legacy_items(annex_iii_area=AnnexIII.CREDITWORTHINESS, placing_on_market_date=placed)
    note = item.application_date_note
    assert note is not None

    assert note.startswith("Literal reading, confirm with counsel") is contested
    if contested:
        assert "the date of application of Chapter III referred to in Article 113" in note
        assert "2027-12-02" in note and "2026-08-02" in note


def test_art_111_2_names_the_operator_when_neither_provider_nor_deployer() -> None:
    (item,) = _legacy_items(
        roles=[Role.IMPORTER],
        annex_iii_area=AnnexIII.CREDITWORTHINESS,
        placing_on_market_date="2026-03-01",
    )

    assert item.actor is Role.IMPORTER
    assert item.obligation_id == "high-risk.importer.111.2"


def test_timeline_carries_the_art_111_2_public_authority_deadline() -> None:
    timeline = classify(SystemProfile(name="x")).timeline
    (item,) = [item for item in timeline if item.applies_from == "2030-08-02"]

    assert "Art. 111(2)" in item.provision
    assert "public authorities" in item.note
    assert "Art. 1, point (39)" in item.note
    assert item.source_id == "ai-act-amendment-2026-1744"


# --- Art. 49(3) AIA: registration of use by public-authority deployers ----------------
@pytest.mark.parametrize(
    ("facts", "registered"),
    [
        pytest.param({"annex_iii_area": AnnexIII.ESSENTIAL_PUBLIC_BENEFITS}, True, id="5a"),
        # The point may not be point 2, so the duty stays, as for Art. 49(1).
        pytest.param({"annex_iii_area": AnnexIII.UNSURE}, True, id="unsure"),
        # Art. 49(3) excepts point 2, which Art. 49(5) registers at national level.
        pytest.param({"annex_iii_area": AnnexIII.CRITICAL_INFRASTRUCTURE}, False, id="point-2"),
        # Art. 49(3) covers Annex III systems only.
        pytest.param(
            {"annex_i_safety_component": True, "annex_i_third_party_assessment": True},
            False,
            id="annex-i",
        ),
    ],
)
def test_art_49_3_public_authority_deployer_registers_its_use(
    facts: dict[str, object], registered: bool
) -> None:
    report = classify(
        SystemProfile(
            name="benefits triage",
            roles=[Role.DEPLOYER],
            public_authority_use=True,
            **facts,
        )
    )
    graph = {item.article: item for item in report.obligation_graph}

    assert ("Art. 49(3) AIA" in graph) is registered
    assert ("Art. 49(3) AIA" in {ob.article for ob in report.obligations}) is registered
    if registered:
        item = graph["Art. 49(3) AIA"]
        assert item.obligation_id == "high-risk.deployer.49.3"
        assert item.actor is Role.DEPLOYER
        assert "register its use in the EU database" in item.requirement
        # Chapter III, Section 5: the literal date, flagged, with the point (c)(i) date.
        assert item.application_date == "2026-08-02"
        assert item.review_status is ReviewStatus.REVIEW_REQUIRED
        assert item.application_date_note is not None
        assert item.application_date_note.startswith("Literal reading, confirm with counsel")
        assert "2027-12-02 applies" in item.application_date_note


@pytest.mark.parametrize(
    "facts",
    [
        pytest.param({"roles": [Role.PROVIDER], "public_authority_use": True}, id="provider"),
        pytest.param({"roles": [Role.DEPLOYER]}, id="not-public-authority"),
    ],
)
def test_no_art_49_3_item_without_a_public_authority_deployer(facts: dict[str, object]) -> None:
    report = classify(
        SystemProfile(name="x", annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS, **facts)
    )

    assert "Art. 49(3) AIA" not in {item.article for item in report.obligation_graph}


@pytest.mark.parametrize(
    ("area", "secure_section"),
    [
        (AnnexIII.LAW_ENFORCEMENT_REOFFENDING_RISK, "Register in the secure non-public section"),
        (AnnexIII.MIGRATION_RISK_ASSESSMENT, "Register in the secure non-public section"),
        (AnnexIII.BIOMETRICS_REMOTE_ID, "Where used in law enforcement, migration"),
        (AnnexIII.EDUCATION_ACCESS, None),
    ],
)
def test_art_49_3_item_notes_the_art_49_4_secure_section(
    area: AnnexIII, secure_section: str | None
) -> None:
    report = classify(
        SystemProfile(
            name="x", roles=[Role.DEPLOYER], public_authority_use=True, annex_iii_area=area
        )
    )
    (item,) = [item for item in report.obligation_graph if item.article == "Art. 49(3) AIA"]

    if secure_section:
        assert secure_section in item.requirement
        assert "Art. 49(4) AIA" in item.requirement
    else:
        assert "Art. 49(4)" not in item.requirement


# --- Annex I, Section B: Art. 2(2) AIA ------------------------------------------------
SECTION_B = {
    "annex_i_safety_component": True,
    "annex_i_third_party_assessment": True,
    "annex_i_section": "B",
}


def test_section_b_product_gets_only_the_art_2_2_provisions() -> None:
    report = classify(
        SystemProfile(
            name="AI-enabled machinery",
            roles=[Role.PROVIDER, Role.DEPLOYER, Role.IMPORTER],
            placing_on_market_date="2026-03-01",
            public_authority_use=True,
            **SECTION_B,
        )
    )

    # Still classified high-risk under Art. 6(1), but no Chapter III duty attaches.
    assert report.risk_tier is RiskTier.HIGH
    assert [ob.article for ob in report.obligations] == ["Art. 2(2) AIA"]
    assert report.documentation_required == []
    (item,) = report.obligation_graph
    assert item.obligation_id == "high-risk.section-b.2.2"
    assert item.actor is Role.PROVIDER
    assert "Art. 6(1), Art. 60a and Arts. 102 to 112" in item.requirement
    assert "Arts. 57, 58 and 59" in item.requirement
    assert item.application_date == "2028-08-02"
    assert item.application_date_note is not None
    assert not item.application_date_note.startswith("Literal reading")
    (finding,) = [f for f in report.findings if f.rule_id == "HIGHRISK.6.1"]
    assert "Annex I, Section B" in finding.detail
    assert "Art. 2(2) AIA" in report.scope.transitional_status


@pytest.mark.parametrize("section", [None, "A"])
def test_section_a_or_unknown_keeps_the_chapter_iii_set(section: str | None) -> None:
    report = classify(
        SystemProfile(
            name="medical device software",
            annex_i_safety_component=True,
            annex_i_third_party_assessment=True,
            annex_i_section=section,
        )
    )

    articles = {ob.article for ob in report.obligations}
    assert {"Art. 9 AIA", "Art. 43 AIA", "Art. 72 AIA"} <= articles
    assert "Art. 2(2) AIA" not in articles
    assert "Art. 2(2) AIA" not in {item.article for item in report.obligation_graph}
    (finding,) = [f for f in report.findings if f.rule_id == "HIGHRISK.6.1"]
    if section is None:
        # The reviewer is told that machinery moved to Section B.
        assert "Regulation (EU) 2023/1230" in finding.detail
        assert "treated as Section A" in finding.detail
    else:
        assert "Annex I, Section A" in finding.detail


def test_section_b_product_in_an_annex_iii_area_keeps_annex_iii_duties_flagged() -> None:
    report = classify(
        SystemProfile(
            name="AI-enabled machinery that screens workers",
            roles=[Role.PROVIDER],
            annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
            **SECTION_B,
        )
    )
    graph = {item.article: item for item in report.obligation_graph}

    assert {"Art. 16 AIA", "Art. 49 AIA", "Art. 2(2) AIA"} <= graph.keys()
    assert graph["Art. 16 AIA"].application_date == "2027-12-02"
    note = graph["Art. 2(2) AIA"].application_date_note
    assert note is not None
    assert note.startswith("Literal reading, confirm with counsel")
    assert "also classified high-risk under Art. 6(2) and Annex III" in note


def test_annex_i_section_rejects_other_values() -> None:
    with pytest.raises(ValidationError):
        SystemProfile.model_validate({"name": "x", "annex_i_section": "C"})


@pytest.mark.parametrize(
    ("status", "public_authority_use", "trigger"),
    [
        pytest.param(True, False, "Deployer that is, or acts on behalf of", id="confirmed"),
        # The system is meant for public authorities but the deployer's own status is
        # not established: the item asks the reviewer to confirm it.
        pytest.param(None, True, "Confirm that the deployer is", id="to-confirm"),
        pytest.param(False, True, None, id="not-a-public-authority"),
        pytest.param(None, False, None, id="unknown"),
    ],
)
def test_art_49_3_turns_on_the_deployers_own_status(
    status: bool | None, public_authority_use: bool, trigger: str | None
) -> None:
    report = classify(
        SystemProfile(
            name="x",
            roles=[Role.DEPLOYER],
            annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
            deployer_public_authority=status,
            public_authority_use=public_authority_use,
        )
    )
    items = [item for item in report.obligation_graph if item.article == "Art. 49(3) AIA"]

    assert ("Art. 49(3) AIA" in {ob.article for ob in report.obligations}) is bool(trigger)
    if trigger is None:
        assert items == []
    else:
        (item,) = items
        assert item.trigger.startswith(trigger) or trigger in item.trigger


def test_art_49_3_obligation_also_names_the_secure_section() -> None:
    report = classify(
        SystemProfile(
            name="x",
            roles=[Role.DEPLOYER],
            deployer_public_authority=True,
            annex_iii_area=AnnexIII.LAW_ENFORCEMENT_REOFFENDING_RISK,
        )
    )
    (obligation,) = [ob for ob in report.obligations if ob.article == "Art. 49(3) AIA"]

    assert "secure non-public section (Art. 49(4) AIA)" in obligation.requirement


def test_art_111_2_public_authority_deadline_binds_only_providers_and_deployers() -> None:
    (item,) = _legacy_items(
        roles=[Role.IMPORTER],
        annex_iii_area=AnnexIII.ESSENTIAL_PUBLIC_BENEFITS,
        placing_on_market_date="2026-03-01",
        public_authority_use=True,
    )

    assert item.actor is Role.IMPORTER
    assert item.application_date == "2027-12-02"
    assert "2 August 2030" not in item.requirement


def test_art_111_2_names_no_actor_the_profile_does_not_hold() -> None:
    report = classify(
        SystemProfile(
            name="x",
            roles=[Role.GPAI_PROVIDER],
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            placing_on_market_date="2026-03-01",
        )
    )

    assert "Art. 111(2) AIA" not in {item.article for item in report.obligation_graph}


def test_art_111_2_note_states_the_annex_x_carve_out_and_the_first_unit() -> None:
    (item,) = _legacy_items(
        annex_iii_area=AnnexIII.CREDITWORTHINESS, placing_on_market_date="2026-03-01"
    )

    assert "Annex X large-scale IT systems placed on the market or put into service before" in (
        item.application_date_note
    )
    assert "lawfully placed on the market" in item.application_date_note


@pytest.mark.parametrize("change", [None, False])
def test_chapter_iii_items_of_a_legacy_system_say_they_are_conditional(
    change: bool | None,
) -> None:
    report = classify(
        SystemProfile(
            name="legacy",
            roles=[Role.PROVIDER, Role.DEPLOYER],
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            putting_into_service_date="2026-09-15",
            significant_change_after_application_date=change,
            deployer_public_authority=True,
            public_authority_use=True,
        )
    )
    graph = {item.article: item for item in report.obligation_graph}
    condition = "attaches only once its design changes significantly, and by 2 August 2030"

    # Sections 1 to 3 keep their date but say it is conditional.
    assert condition in graph["Art. 16 AIA"].application_date_note
    # Section 5 items keep the counsel flag first, then the condition.
    for article in ("Art. 43 AIA", "Art. 49(3) AIA"):
        note = graph[article].application_date_note
        assert note.startswith("Literal reading, confirm with counsel")
        assert condition in note
    # The Art. 111(2) item itself states the transition and carries no extra condition.
    assert "attaches only once" not in graph["Art. 111(2) AIA"].application_date_note


def test_no_conditional_notes_once_a_significant_change_is_asserted() -> None:
    report = classify(
        SystemProfile(
            name="changed",
            annex_iii_area=AnnexIII.CREDITWORTHINESS,
            placing_on_market_date="2026-03-01",
            significant_change_after_application_date=True,
        )
    )

    assert not any(
        "attaches only once" in (item.application_date_note or "")
        for item in report.obligation_graph
    )


def test_section_b_dual_item_states_the_literal_reading_it_departs_from() -> None:
    report = classify(
        SystemProfile(
            name="AI-enabled machinery that screens workers",
            annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
            **SECTION_B,
        )
    )
    (item,) = [item for item in report.obligation_graph if item.article == "Art. 2(2) AIA"]

    assert item.requirement.startswith("Through the Art. 6(1) route, only Art. 6(1)")
    assert "on its wording Art. 2(2) AIA covers any AI system" in item.application_date_note
    assert "keeps the Annex III duties as the conservative reading" in item.application_date_note


def test_section_b_item_dates_every_listed_provision() -> None:
    (item,) = classify(SystemProfile(name="machinery", **SECTION_B)).obligation_graph

    for part in ("from 2028-08-02", "Arts. 102 to 110 from 2026-07-27", "Art. 60a, Arts. 111"):
        assert part in item.application_date_note
    assert "only through the sectoral legislation" in item.requirement


def test_section_b_transparency_duties_are_kept_and_flagged() -> None:
    report = classify(
        SystemProfile(
            name="in-vehicle assistant",
            interacts_with_natural_persons=True,
            generates_synthetic_content=True,
            placing_on_market_date="2026-03-01",
            **SECTION_B,
        )
    )
    transparency = [item for item in report.obligation_graph if item.article.startswith("Art. 50")]

    assert {item.article for item in transparency} == {"Art. 50(1) AIA", "Art. 50(2) AIA"}
    for item in transparency:
        assert item.application_date_note.startswith("Literal reading, confirm with counsel")
        assert "Art. 50 does not apply" in item.application_date_note
    (art_50_2,) = [item for item in transparency if item.article == "Art. 50(2) AIA"]
    assert "Art. 111(4)" in art_50_2.application_date_note


def test_section_b_product_without_an_operator_role_gets_no_item() -> None:
    report = classify(SystemProfile(name="x", roles=[Role.GPAI_PROVIDER], **SECTION_B))

    assert report.risk_tier is RiskTier.HIGH
    assert report.obligations == []
    assert report.obligation_graph == []


@pytest.mark.parametrize(
    "artifact",
    ["fria", "annex-iv-checklist", "post-market-monitoring-plan", "serious-incident-register"],
)
def test_section_b_artifacts_surface_art_2_2(artifact: str) -> None:
    report = classify(SystemProfile(name="machinery", **SECTION_B))
    graph_section = render_artifact(artifact, report).split("## Relevant Obligation Graph Items")[1]

    assert "- Art. 2(2) AIA (provider): Only Art. 6(1), Art. 60a" in graph_section
    assert "No directly matching graph item" not in graph_section.split("## ")[0]


def test_section_b_appears_in_the_text_report_and_dossier() -> None:
    report = classify(SystemProfile(name="machinery", **SECTION_B))

    assert "high-risk.section-b.2.2: Art. 2(2) AIA (provider)" in render_report(report)
    dossier = render_review_dossier_markdown(build_review_dossier(report))
    assert "high-risk.section-b.2.2: Art. 2(2) AIA (provider)" in dossier
