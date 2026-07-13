"""Local collaboration, policy workflows and synthetic self-assessment portal."""

from __future__ import annotations

import hashlib
import json
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
    created_at: str
    resolved_at: str | None = None


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
    source_policy: Literal["approved_versioned_sources_only"] = "approved_versioned_sources_only"
    permitted_roles: list[Literal["reviewer", "administrator"]] = Field(
        default_factory=lambda: ["reviewer", "administrator"]
    )


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
    definition_snapshot: dict[str, object]
    classifier_version: str
    source_versions: list[str]
    decisions: list[dict[str, str]] = Field(default_factory=list)
    audit_events: list[dict[str, str]] = Field(default_factory=list)


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


def _cell(workspace: CollaborationWorkspace, target_id: str) -> ReviewCellState:
    cell = next(
        (candidate for candidate in workspace.cells if candidate.target_id == target_id), None
    )
    if cell is None:
        raise ValueError(f"unknown review cell: {target_id}")
    return cell


def add_comment(
    workspace: CollaborationWorkspace,
    *,
    target_id: str,
    body: str,
    actor: str,
    expected_revision: int,
    now: datetime,
) -> CollaborationWorkspace:
    if not body.strip():
        raise ValueError("review comments must not be empty")
    updated = workspace.model_copy(deep=True)
    cell = _cell(updated, target_id)
    if cell.revision != expected_revision:
        raise ValueError("409 Conflict: stale review cell revision")
    cell.revision += 1
    cell.comments.append(
        ReviewComment(
            id=f"comment:{target_id}:{cell.revision}",
            target_id=target_id,
            body=body.strip(),
            author=actor,
            created_at=now.isoformat(),
        )
    )
    updated.activity.append(
        {
            "event": "comment_added",
            "targetId": target_id,
            "actor": actor,
            "occurredAt": now.isoformat(),
        }
    )
    return updated


def resolve_comment(
    workspace: CollaborationWorkspace,
    *,
    target_id: str,
    comment_id: str,
    actor: str,
    expected_revision: int,
    now: datetime,
) -> CollaborationWorkspace:
    updated = workspace.model_copy(deep=True)
    cell = _cell(updated, target_id)
    if cell.revision != expected_revision:
        raise ValueError("409 Conflict: stale review cell revision")
    comment = next((item for item in cell.comments if item.id == comment_id), None)
    if comment is None:
        raise ValueError(f"unknown review comment: {comment_id}")
    if comment.status == "resolved":
        raise ValueError("review comment is already resolved")
    cell.revision += 1
    comment.status = "resolved"
    comment.resolved_at = now.isoformat()
    updated.activity.append(
        {
            "event": "comment_resolved",
            "targetId": target_id,
            "actor": actor,
            "occurredAt": now.isoformat(),
        }
    )
    return updated


def review_cell(
    workspace: CollaborationWorkspace,
    *,
    target_id: str,
    reviewer: str,
    reviewer_override: str | None,
    expected_revision: int,
    now: datetime,
) -> CollaborationWorkspace:
    updated = workspace.model_copy(deep=True)
    cell = _cell(updated, target_id)
    if cell.revision != expected_revision:
        raise ValueError("409 Conflict: stale review cell revision")
    if (
        cell.locked_by
        and cell.locked_by != reviewer
        and cell.lock_expires_at
        and datetime.fromisoformat(cell.lock_expires_at) > now
    ):
        raise ValueError(f"409 Conflict: review cell is locked by {cell.locked_by}")
    cell.revision += 1
    cell.reviewer = reviewer
    cell.reviewer_override = reviewer_override.strip() if reviewer_override else None
    updated.activity.append(
        {
            "event": "reviewed",
            "targetId": target_id,
            "actor": reviewer,
            "occurredAt": now.isoformat(),
        }
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


def export_workspace(workspace: CollaborationWorkspace) -> str:
    return workspace.model_dump_json(by_alias=True, indent=2) + "\n"


def import_workspace(payload: str, inventory: AISystemInventory) -> CollaborationWorkspace:
    workspace = CollaborationWorkspace.model_validate_json(payload)
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
                definition_snapshot=definition.model_dump(mode="json", by_alias=True),
                classifier_version="0.2.0",
                source_versions=list(inventory.sourceRefs),
                audit_events=[
                    {
                        "event": "workflow_started",
                        "occurredAt": datetime(2026, 7, 13, tzinfo=UTC).isoformat(),
                    }
                ],
            )
        )
    return definitions, runs


def build_self_assessment_portal(
    inventory: AISystemInventory, answers: dict[str, object] | None = None
) -> SelfAssessmentPortal:
    first = inventory.systems[0]
    blockers = [
        system.system_id for system in inventory.systems if system.review_status == "blocked"
    ]
    submitted = answers or {}
    missing_answers = sorted(
        question_id
        for question_id in {"purpose", "role", "eu_nexus", "evidence"}
        if not str(submitted.get(question_id, "")).strip()
    )
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
            "missingAnswers": missing_answers,
            "blockers": blockers,
            "nextAction": first.next_action,
            "reviewStatus": "draft_only_human_review_required",
        },
        exportAllowed=False,
        externalActionAllowed=False,
    )


def build_legora_workspace(
    *,
    collaboration: CollaborationWorkspace | None = None,
    assessment_answers: dict[str, object] | None = None,
) -> dict[str, object]:
    inventory = build_example_inventory()
    definitions, runs = build_policy_workflows(inventory)
    return {
        "schema": "eu-ai-act.legora-workspace.v1",
        "collaboration": (collaboration or build_collaboration_workspace(inventory)).model_dump(
            mode="json", by_alias=True
        ),
        "workflowDefinitions": [
            item.model_dump(mode="json", by_alias=True) for item in definitions
        ],
        "workflowRuns": [item.model_dump(mode="json", by_alias=True) for item in runs],
        "selfAssessmentPortal": build_self_assessment_portal(
            inventory, assessment_answers
        ).model_dump(mode="json", by_alias=True),
        "generatedAt": datetime(2026, 7, 13, tzinfo=UTC).isoformat(),
    }


def apply_workspace_action(
    payload: dict[str, object], runtime_path: Path, *, now: datetime | None = None
) -> dict[str, object]:
    """Apply one local mutation against the fixed ignored runtime workspace."""

    inventory = build_example_inventory()
    current = (
        load_workspace(runtime_path, inventory)
        if runtime_path.exists()
        else build_collaboration_workspace(inventory)
    )
    action = str(payload.get("action", "snapshot"))
    occurred_at = now or datetime.now(UTC)
    if action == "snapshot":
        return build_legora_workspace(collaboration=current)
    target_id = str(payload.get("targetId", ""))
    expected_revision = int(payload.get("expectedRevision", 0))
    actor = str(payload.get("actor", "Local reviewer")).strip() or "Local reviewer"
    if action == "lock":
        current = lock_cell(
            current,
            target_id=target_id,
            actor=actor,
            expected_revision=expected_revision,
            now=occurred_at,
        )
    elif action == "comment":
        current = add_comment(
            current,
            target_id=target_id,
            body=str(payload.get("body", "")),
            actor=actor,
            expected_revision=expected_revision,
            now=occurred_at,
        )
    elif action == "resolve_comment":
        current = resolve_comment(
            current,
            target_id=target_id,
            comment_id=str(payload.get("commentId", "")),
            actor=actor,
            expected_revision=expected_revision,
            now=occurred_at,
        )
    elif action == "review":
        current = review_cell(
            current,
            target_id=target_id,
            reviewer=actor,
            reviewer_override=(
                str(payload["reviewerOverride"]) if payload.get("reviewerOverride") else None
            ),
            expected_revision=expected_revision,
            now=occurred_at,
        )
    elif action == "import":
        raw = payload.get("workspace")
        current = import_workspace(
            json.dumps(raw) if not isinstance(raw, str) else raw,
            inventory,
        )
    elif action == "self_assess":
        return build_legora_workspace(
            collaboration=current,
            assessment_answers=dict(payload.get("answers", {})),
        )
    else:
        raise ValueError(f"unsupported workspace action: {action}")
    save_workspace(current, runtime_path)
    return build_legora_workspace(collaboration=current)
