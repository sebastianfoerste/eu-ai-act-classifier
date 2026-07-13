"""Local collaboration, policy workflows and synthetic self-assessment portal."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .inventory import AISystemInventory, build_example_inventory


class ReviewComment(BaseModel):
    id: str
    target_id: str
    body: str
    author: str
    status: Literal["open", "resolved"] = "open"


class ReviewCellState(BaseModel):
    target_id: str
    deterministic_status: str
    reviewer_override: str | None = None
    reviewer: str | None = None
    revision: int = 1
    locked_by: str | None = None
    lock_expires_at: str | None = None
    comments: list[ReviewComment] = Field(default_factory=list)


class CollaborationWorkspace(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    schema_id: Literal["review.collaboration.v1"] = Field("review.collaboration.v1", alias="schema")
    inventory_digest: str
    cells: list[ReviewCellState]
    activity: list[dict[str, str]] = Field(default_factory=list)
    external_action_allowed: bool = Field(False, alias="externalActionAllowed")


class PolicyWorkflowDefinition(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    schema_id: Literal["workflow.definition.v1"] = Field("workflow.definition.v1", alias="schema")
    id: str
    version: int = Field(ge=1)
    name: str
    status: Literal["draft", "active", "retired"]
    steps: list[
        Literal[
            "classification",
            "prohibited_screen",
            "obligations",
            "fria",
            "transparency",
            "policy_draft",
            "human_review",
        ]
    ]


class PolicyWorkflowRun(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    schema_id: Literal["workflow.run.v1"] = Field("workflow.run.v1", alias="schema")
    id: str
    definition_id: str
    definition_version: int
    system_id: str
    status: Literal["blocked", "review_required", "approved"]
    artifacts: list[str]
    source_refs: list[str]
    export_allowed: bool = Field(alias="exportAllowed")


class SelfAssessmentPortal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    schema_id: Literal["eu-ai-act.self-assessment-portal.v1"] = Field(
        "eu-ai-act.self-assessment-portal.v1", alias="schema"
    )
    local_only: bool = Field(True, alias="localOnly")
    synthetic: bool = True
    questions: list[dict[str, object]]
    draft_packet: dict[str, object] = Field(alias="draftPacket")
    export_allowed: bool = Field(False, alias="exportAllowed")
    external_action_allowed: bool = Field(False, alias="externalActionAllowed")


def _inventory_digest(inventory: AISystemInventory) -> str:
    payload = inventory.model_dump_json(by_alias=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def build_collaboration_workspace(inventory: AISystemInventory) -> CollaborationWorkspace:
    return CollaborationWorkspace(
        inventory_digest=_inventory_digest(inventory),
        cells=[
            ReviewCellState(
                target_id=f"cell:{row.system_id}:{row.factor_id}",
                deterministic_status=row.cell_status,
            )
            for row in inventory.reviewTable.rows
        ],
        externalActionAllowed=False,
    )


def lock_cell(
    workspace: CollaborationWorkspace,
    *,
    target_id: str,
    actor: str,
    expected_revision: int,
    now: datetime,
) -> CollaborationWorkspace:
    updated = workspace.model_copy(deep=True)
    cell = next(
        (candidate for candidate in updated.cells if candidate.target_id == target_id), None
    )
    if cell is None:
        raise ValueError(f"unknown review cell: {target_id}")
    if cell.revision != expected_revision:
        raise ValueError(
            f"409 Conflict: expected revision {expected_revision}, received {cell.revision}"
        )
    if (
        cell.locked_by
        and cell.locked_by != actor
        and cell.lock_expires_at
        and datetime.fromisoformat(cell.lock_expires_at) > now
    ):
        raise ValueError(f"409 Conflict: review cell is locked by {cell.locked_by}")
    cell.revision += 1
    cell.locked_by = actor
    cell.lock_expires_at = (now + timedelta(minutes=15)).isoformat()
    updated.activity.append(
        {"event": "locked", "targetId": target_id, "actor": actor, "occurredAt": now.isoformat()}
    )
    return updated


def save_workspace(workspace: CollaborationWorkspace, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(workspace.model_dump_json(by_alias=True, indent=2) + "\n", encoding="utf-8")
    return path


def load_workspace(path: Path, inventory: AISystemInventory) -> CollaborationWorkspace:
    workspace = CollaborationWorkspace.model_validate_json(path.read_text(encoding="utf-8"))
    if workspace.inventory_digest != _inventory_digest(inventory):
        raise ValueError("workspace state is stale for the current deterministic inventory")
    return workspace


def build_policy_workflows(
    inventory: AISystemInventory,
) -> tuple[list[PolicyWorkflowDefinition], list[PolicyWorkflowRun]]:
    definitions = [
        PolicyWorkflowDefinition(
            id="workflow:classification-fria",
            version=1,
            name="Classification and FRIA",
            status="active",
            steps=["classification", "prohibited_screen", "obligations", "fria", "human_review"],
        ),
        PolicyWorkflowDefinition(
            id="workflow:transparency-policy",
            version=1,
            name="Transparency and policy drafting",
            status="active",
            steps=["classification", "transparency", "policy_draft", "human_review"],
        ),
    ]
    runs = []
    for system in inventory.systems:
        definition = definitions[0]
        blocked = system.review_status == "blocked"
        runs.append(
            PolicyWorkflowRun(
                id=f"run:{system.system_id}",
                definition_id=definition.id,
                definition_version=definition.version,
                system_id=system.system_id,
                status="blocked" if blocked else "review_required",
                artifacts=list(system.draft_artifacts),
                source_refs=list(inventory.sourceRefs),
                exportAllowed=False,
            )
        )
    return definitions, runs


def build_self_assessment_portal(inventory: AISystemInventory) -> SelfAssessmentPortal:
    first = inventory.systems[0]
    blockers = [
        system.system_id for system in inventory.systems if system.review_status == "blocked"
    ]
    return SelfAssessmentPortal(
        questions=[
            {"id": "purpose", "label": "Describe the intended purpose", "required": True},
            {"id": "role", "label": "Select the operator role", "required": True},
            {
                "id": "eu_nexus",
                "label": "Describe the EU market or affected-person nexus",
                "required": True,
            },
            {
                "id": "evidence",
                "label": "List approved public or synthetic evidence references",
                "required": True,
            },
        ],
        draftPacket={
            "systemId": first.system_id,
            "deterministicRiskTier": first.risk_tier,
            "missingFacts": list(first.open_facts),
            "blockers": blockers,
            "nextAction": first.next_action,
            "reviewStatus": "draft_only_human_review_required",
        },
        exportAllowed=False,
        externalActionAllowed=False,
    )


def build_legora_workspace() -> dict[str, object]:
    inventory = build_example_inventory()
    definitions, runs = build_policy_workflows(inventory)
    return {
        "schema": "eu-ai-act.legora-workspace.v1",
        "collaboration": build_collaboration_workspace(inventory).model_dump(
            mode="json", by_alias=True
        ),
        "workflowDefinitions": [
            item.model_dump(mode="json", by_alias=True) for item in definitions
        ],
        "workflowRuns": [item.model_dump(mode="json", by_alias=True) for item in runs],
        "selfAssessmentPortal": build_self_assessment_portal(inventory).model_dump(
            mode="json", by_alias=True
        ),
        "generatedAt": datetime(2026, 7, 13, tzinfo=UTC).isoformat(),
    }
