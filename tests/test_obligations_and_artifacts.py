from __future__ import annotations

import json

from eu_ai_act_classifier import AnnexIII, Role, SystemProfile, classify
from eu_ai_act_classifier.artifacts import render_artifact, write_artifacts
from eu_ai_act_classifier.cli import main


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


def test_high_risk_obligation_dates_follow_regulation_2026_1744() -> None:
    annex_iii_report = classify(
        SystemProfile(name="credit scoring", annex_iii_area=AnnexIII.CREDITWORTHINESS)
    )
    product_report = classify(
        SystemProfile(
            name="safety component",
            annex_i_safety_component=True,
            annex_i_third_party_assessment=True,
        )
    )

    assert {item.application_date for item in annex_iii_report.obligation_graph} == {"2027-12-02"}
    assert {item.application_date for item in product_report.obligation_graph} == {"2028-08-02"}


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


def _provider_graph_articles(**facts) -> set[str]:
    report = classify(SystemProfile(name="x", roles=[Role.PROVIDER], **facts))
    return {item.article for item in report.obligation_graph}


def test_annex_iii_points_2_to_8_use_internal_control_without_notified_body() -> None:
    # Art. 43(2) AIA: points 2 to 8 of Annex III follow internal control (Annex VI).
    for area in (
        AnnexIII.CRITICAL_INFRASTRUCTURE,
        AnnexIII.EMPLOYMENT_SELECTION,
        AnnexIII.CREDITWORTHINESS,
        AnnexIII.INSURANCE_LIFE_HEALTH,
        AnnexIII.JUSTICE,
    ):
        articles = _provider_graph_articles(annex_iii_area=area)
        assert "Art. 43(2) AIA" in articles
        assert "Art. 44 AIA" not in articles


def test_internal_control_item_is_review_required_and_names_annex_vi() -> None:
    report = classify(
        SystemProfile(name="x", roles=[Role.PROVIDER], annex_iii_area=AnnexIII.CREDITWORTHINESS)
    )
    item = next(item for item in report.obligation_graph if item.article == "Art. 43(2) AIA")
    assert item.obligation_id == "high-risk.provider.43.2"
    assert "Annex VI" in item.requirement
    assert item.review_status.value == "review_required"


def test_notified_body_item_stays_where_a_notified_body_can_be_involved() -> None:
    # Annex III point 1 (Art. 43(1)), an unsettled Annex III point, the Annex I route,
    # and an Annex III system that is also an Annex I product (Art. 43(3)).
    for facts in (
        {"annex_iii_area": AnnexIII.BIOMETRICS_REMOTE_ID},
        {"annex_iii_area": AnnexIII.BIOMETRICS_EMOTION},
        {"annex_iii_area": AnnexIII.UNSURE},
        {"annex_i_safety_component": True, "annex_i_third_party_assessment": True},
        {
            "annex_iii_area": AnnexIII.CREDITWORTHINESS,
            "annex_i_safety_component": True,
            "annex_i_third_party_assessment": True,
        },
        # Art. 43(3), last subparagraph, does not depend on a third-party assessment.
        {"annex_iii_area": AnnexIII.CRITICAL_INFRASTRUCTURE, "annex_i_safety_component": True},
        {"annex_iii_area": AnnexIII.CREDITWORTHINESS, "annex_i_safety_component": True},
        {"annex_iii_area": AnnexIII.INSURANCE_LIFE_HEALTH, "annex_i_safety_component": True},
    ):
        articles = _provider_graph_articles(**facts)
        assert "Art. 44 AIA" in articles
        assert "Art. 43(2) AIA" not in articles


def test_report_cites_the_ai_act_as_amended_by_regulation_2026_1744() -> None:
    report = classify(SystemProfile(name="x"))
    assert report.regulation.startswith("Regulation (EU) 2024/1689 ")
    assert report.regulation.endswith(", as amended by Regulation (EU) 2026/1744")
