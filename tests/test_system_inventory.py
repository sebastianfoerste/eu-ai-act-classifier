from __future__ import annotations

from pathlib import Path

from eu_ai_act_classifier.inventory import (
    INVENTORY_SCHEMA,
    SYSTEM_REVIEW_TABLE_SCHEMA,
    build_system_inventory,
    load_example_profiles,
)
from eu_ai_act_classifier.models import AnnexIII, ProhibitedPractice, Role, SystemProfile


def test_inventory_loads_example_profiles_and_source_manifest() -> None:
    profiles = load_example_profiles(Path("examples"))
    inventory = build_system_inventory(profiles[:4], generated_at="2026-06-27T10:00:00+00:00")

    assert inventory.schema_id == INVENTORY_SCHEMA
    assert inventory.sourceMode == "example_profiles"
    assert inventory.sourceRefs
    assert inventory.evidenceArtifacts
    assert inventory.reviewTable.schema_id == SYSTEM_REVIEW_TABLE_SCHEMA
    assert inventory.reviewTable.rows
    assert inventory.reviewTable.controlProfile.externalActionAllowed is False
    assert inventory.reviewTable.controlProfile.workflowRoutes[-1].status == "blocked"
    assert inventory.reviewTable.reviewTableScale.schema_id == (
        "eu-ai-act-classifier.system-review-table-scale.v1"
    )
    assert inventory.reviewTable.reviewTableScale.rowCount == inventory.reviewTable.summary["rows"]
    assert inventory.reviewTable.reviewTableScale.maxVaultDocuments == 100_000
    assert inventory.reviewTable.reviewTableScale.columnCount == 10
    assert (
        inventory.reviewTable.promptBrief.schema_id == "eu-ai-act-classifier.system-prompt-brief.v1"
    )
    assert inventory.reviewTable.inventoryControls.schema_id == (
        "eu-ai-act-classifier.system-inventory-controls.v1"
    )
    assert inventory.reviewTable.inventoryControls.vendorIntegration == "none"
    assert inventory.reviewTable.inventoryControls.externalActionAllowed is False
    assert inventory.reviewTable.inventoryControls.tabularReview["externalActionAllowed"] is False
    assert inventory.reviewTable.inventoryControls.portalRoom["externalGuestAccessAllowed"] is False
    assert inventory.reviewTable.inventoryControls.trustedSources["sourceMode"] == (
        "source_manifest_and_obligation_graph"
    )
    assert inventory.reviewTable.inventoryControls.securityGovernance["approvalGate"] == (
        "required_for_deployment_or_external_reliance"
    )
    assert (
        "deterministic classifier remains the boundary"
        in inventory.reviewTable.inventoryControls.reviewNotice
    )
    assert "Review gate: draft only" in inventory.reviewTable.promptBrief.suggestedPrompt
    assert {item.key for item in inventory.reviewTable.promptBrief.guidedInputs} >= {
        "system_factor",
        "obligation_graph",
        "external_use_gate",
    }
    assert len(inventory.systems) == 4
    assert all(row.pinpoint_citations for row in inventory.reviewTable.rows)
    assert {row.cell_status for row in inventory.reviewTable.rows} <= {
        "complete",
        "review_required",
        "blocked",
    }
    assert {
        citation.source_id
        for row in inventory.reviewTable.rows
        for citation in row.pinpoint_citations
    } <= set(inventory.sourceRefs)
    all_citations = [
        citation for row in inventory.reviewTable.rows for citation in row.pinpoint_citations
    ]
    assert all(citation.source_class for citation in all_citations)
    assert all(citation.quote is not None for citation in all_citations)
    assert all(
        citation.offset_start == 0 and citation.offset_end is not None for citation in all_citations
    )
    assert {row.source_manifest_status for row in inventory.systems} <= {
        "complete",
        "review_required",
        "missing",
    }


def test_inventory_uses_classifier_risk_and_obligation_metadata() -> None:
    profile = SystemProfile(
        name="HiringScreen",
        roles=[Role.PROVIDER, Role.DEPLOYER],
        purpose="Screen candidates for hiring decisions",
        sector="Employment",
        annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION,
        deployer_public_law_body=False,
        deployer_private_public_service=False,
    )
    inventory = build_system_inventory([profile], generated_at="2026-06-27T10:00:00+00:00")
    row = inventory.systems[0]

    assert row.risk_tier == "high_risk"
    assert row.disposition == "determined"
    assert row.review_status == "determined"
    assert row.obligations
    assert row.draft_artifacts
    assert row.next_action == "Prepare draft artifacts for reviewer sign-off."

    review_rows = [item for item in inventory.reviewTable.rows if item.system_id == row.system_id]
    assert {item.factor_id for item in review_rows} == {
        "artifact_pack",
        "operator_role",
        "risk_classification",
        "scope",
    }
    assert any(item.obligation_refs for item in review_rows)
    assert all(item.pinpoint_citations for item in review_rows)
    assert any(
        citation.legal_status_class == "binding_level_1"
        for item in review_rows
        for citation in item.pinpoint_citations
    )
    assert any(
        citation.source_class == "binding_law"
        for item in review_rows
        for citation in item.pinpoint_citations
    )
    assert all(item.cell_status == "complete" for item in review_rows)
    assert all(item.review_status == "determined" for item in review_rows)
    assert any(
        connector.key == "obligation-graph"
        for connector in inventory.reviewTable.controlProfile.sourceConnectors
    )


def test_inventory_blocks_prohibited_systems_and_redacts_sensitive_labels() -> None:
    profile = SystemProfile(
        name="candidate:alpha alex@example.com",
        roles=[Role.PROVIDER],
        purpose="Social scoring",
        sector="Public services",
        prohibited_practices=[ProhibitedPractice.SOCIAL_SCORING],
    )
    inventory = build_system_inventory([profile], generated_at="2026-06-27T10:00:00+00:00")
    payload = inventory.model_dump_json()

    assert inventory.reviewStatus == "blocked"
    assert inventory.exportAllowed is False
    assert inventory.externalActionAllowed is False
    assert inventory.systems[0].review_status == "blocked"
    assert inventory.reviewTable.summary["blocked"] > 0
    assert inventory.reviewTable.controlProfile.workflowRoutes[0].status == "blocked"
    assert all(row.review_status == "blocked" for row in inventory.reviewTable.rows)
    assert "prohibited" in inventory.blockers[0]
    assert "alex@example.com" not in payload
    assert "candidate:alpha" not in payload
    assert "[redacted-email]" in payload
    assert "[redacted-reference]" in payload


def test_inventory_preserves_unverified_citation_state() -> None:
    profile = SystemProfile(
        name="Ambiguous Annex III System",
        roles=[Role.PROVIDER],
        purpose="Assess eligibility for a sensitive service",
        sector="Public services",
        annex_iii_area=AnnexIII.UNSURE,
    )
    inventory = build_system_inventory([profile], generated_at="2026-06-27T10:00:00+00:00")
    risk_row = next(
        row for row in inventory.reviewTable.rows if row.factor_id == "risk_classification"
    )

    assert risk_row.source_status == "review_required"
    assert risk_row.cell_status == "review_required"
    assert any(not citation.verified for citation in risk_row.pinpoint_citations)
    assert any(
        citation.derived_from == "classifier_finding" for citation in risk_row.pinpoint_citations
    )
