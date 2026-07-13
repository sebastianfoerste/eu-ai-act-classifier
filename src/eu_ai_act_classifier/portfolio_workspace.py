"""Review-gated AI system vault, assessment workflow and fleet command center."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .inventory import AISystemInventory, AISystemInventoryRow, build_example_inventory


class AISystemVaultRecord(BaseModel):
    system_id: str
    name: str
    role: str
    risk_tier: str
    source_refs: list[str]
    artifact_refs: list[str]
    access_mode: Literal["internal_review"] = "internal_review"
    external_action_allowed: bool = False


class AISystemVault(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_id: Literal["eu-ai-act-classifier.system-vault.v1"] = Field(
        "eu-ai-act-classifier.system-vault.v1", alias="schema"
    )
    records: list[AISystemVaultRecord]
    verified_source_count: int
    open_source_count: int
    external_action_allowed: bool = Field(False, alias="externalActionAllowed")


class AssessmentWorkflowStep(BaseModel):
    key: Literal["intake", "scope", "risk", "obligations", "artifacts", "legal_review"]
    label: str
    status: Literal["complete", "review_required", "blocked"]
    evidence_refs: list[str]
    next_action: str


class AssessmentWorkflowRun(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_id: Literal["eu-ai-act-classifier.assessment-workflow.v1"] = Field(
        "eu-ai-act-classifier.assessment-workflow.v1", alias="schema"
    )
    system_id: str
    status: Literal["complete", "review_required", "blocked"]
    steps: list[AssessmentWorkflowStep]
    reviewer_sign_off_required: bool = Field(True, alias="reviewerSignOffRequired")
    deployment_allowed: bool = Field(False, alias="deploymentAllowed")


class FleetCommandCenterRow(BaseModel):
    system_id: str
    name: str
    risk_tier: str
    review_status: str
    open_fact_count: int
    obligation_count: int
    artifact_count: int
    priority: Literal["critical", "high", "standard"]
    next_action: str


class FleetCommandCenter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_id: Literal["eu-ai-act-classifier.fleet-command-center.v1"] = Field(
        "eu-ai-act-classifier.fleet-command-center.v1", alias="schema"
    )
    summary: dict[str, int]
    rows: list[FleetCommandCenterRow]
    review_notice: str = Field(alias="reviewNotice")
    external_action_allowed: bool = Field(False, alias="externalActionAllowed")


class AISystemPortfolioWorkspace(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_id: Literal["eu-ai-act-classifier.portfolio-workspace.v1"] = Field(
        "eu-ai-act-classifier.portfolio-workspace.v1", alias="schema"
    )
    vault: AISystemVault
    workflows: list[AssessmentWorkflowRun]
    command_center: FleetCommandCenter = Field(alias="commandCenter")
    draft_only: bool = Field(True, alias="draftOnly")


def build_portfolio_workspace(inventory: AISystemInventory) -> AISystemPortfolioWorkspace:
    vault = AISystemVault(
        records=[
            AISystemVaultRecord(
                system_id=system.system_id,
                name=system.name,
                role=system.role,
                risk_tier=system.risk_tier,
                source_refs=list(inventory.sourceRefs),
                artifact_refs=[f"artifact:{name}" for name in system.draft_artifacts],
            )
            for system in inventory.systems
        ],
        verified_source_count=sum(
            system.source_manifest_status == "complete" for system in inventory.systems
        ),
        open_source_count=sum(
            system.source_manifest_status != "complete" for system in inventory.systems
        ),
        externalActionAllowed=False,
    )
    workflows = [_workflow(system, inventory) for system in inventory.systems]
    rows = [_command_row(system) for system in inventory.systems]
    rows.sort(
        key=lambda row: (
            {"critical": 0, "high": 1, "standard": 2}[row.priority],
            row.name,
        )
    )
    command_center = FleetCommandCenter(
        summary={
            "systems": len(rows),
            "blocked": sum(row.review_status == "blocked" for row in rows),
            "review_required": sum(row.review_status == "review_required" for row in rows),
            "high_risk": sum(row.risk_tier == "high_risk" for row in rows),
            "open_facts": sum(row.open_fact_count for row in rows),
        },
        rows=rows,
        reviewNotice=(
            "Fleet analytics restate deterministic classifier outputs. Legal characterisation, "
            "system facts and deployment decisions require qualified human review."
        ),
        externalActionAllowed=False,
    )
    return AISystemPortfolioWorkspace(
        vault=vault,
        workflows=workflows,
        commandCenter=command_center,
        draftOnly=True,
    )


def build_example_portfolio_workspace() -> AISystemPortfolioWorkspace:
    return build_portfolio_workspace(build_example_inventory())


def _workflow(system: AISystemInventoryRow, inventory: AISystemInventory) -> AssessmentWorkflowRun:
    blocked = system.review_status == "blocked"
    review_required = system.review_status == "review_required"
    status: Literal["complete", "review_required", "blocked"] = (
        "blocked" if blocked else "review_required" if review_required else "complete"
    )
    review_rows = [row for row in inventory.reviewTable.rows if row.system_id == system.system_id]
    factor_status = {row.factor_id: row.cell_status for row in review_rows}
    steps = [
        AssessmentWorkflowStep(
            key="intake",
            label="Validate system profile",
            status="review_required" if system.open_facts else "complete",
            evidence_refs=[f"system:{system.system_id}"],
            next_action=(
                "Resolve open facts." if system.open_facts else "Profile inputs are complete."
            ),
        ),
        AssessmentWorkflowStep(
            key="scope",
            label="Determine AI Act scope",
            status=_step_status(factor_status.get("scope")),
            evidence_refs=[f"review-row:{system.system_id}:scope"],
            next_action="Confirm EU nexus and exclusions with the reviewer.",
        ),
        AssessmentWorkflowStep(
            key="risk",
            label="Run risk classification",
            status=_step_status(factor_status.get("risk_classification")),
            evidence_refs=[f"review-row:{system.system_id}:risk_classification"],
            next_action=system.next_action,
        ),
        AssessmentWorkflowStep(
            key="obligations",
            label="Build obligation graph",
            status="blocked" if blocked else "complete",
            evidence_refs=system.obligations,
            next_action="Review actor-specific obligations and application dates.",
        ),
        AssessmentWorkflowStep(
            key="artifacts",
            label="Prepare draft artifact pack",
            status="blocked" if blocked else "review_required",
            evidence_refs=[f"artifact:{name}" for name in system.draft_artifacts],
            next_action="Generate draft artifacts for reviewer sign-off.",
        ),
        AssessmentWorkflowStep(
            key="legal_review",
            label="Record legal reviewer decision",
            status="blocked" if blocked else "review_required",
            evidence_refs=[],
            next_action="A qualified reviewer must record the final decision.",
        ),
    ]
    return AssessmentWorkflowRun(
        system_id=system.system_id,
        status=status,
        steps=steps,
        reviewerSignOffRequired=True,
        deploymentAllowed=False,
    )


def _step_status(value: str | None) -> Literal["complete", "review_required", "blocked"]:
    if value == "blocked":
        return "blocked"
    if value == "complete":
        return "complete"
    return "review_required"


def _command_row(system: AISystemInventoryRow) -> FleetCommandCenterRow:
    priority: Literal["critical", "high", "standard"]
    if system.review_status == "blocked" or system.risk_tier == "prohibited":
        priority = "critical"
    elif system.risk_tier == "high_risk" or system.review_status == "review_required":
        priority = "high"
    else:
        priority = "standard"
    return FleetCommandCenterRow(
        system_id=system.system_id,
        name=system.name,
        risk_tier=system.risk_tier,
        review_status=system.review_status,
        open_fact_count=len(system.open_facts),
        obligation_count=len(system.obligations),
        artifact_count=len(system.draft_artifacts),
        priority=priority,
        next_action=system.next_action,
    )
