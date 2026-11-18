"""Local collaboration, policy workflows and synthetic self-assessment portal."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from . import __version__
from .artifacts import DRAFT_NOTICE
from .engine import classify
from .evidence_tracker import (
    EvidenceRecord,
    build_evidence_view,
    check_system_id,
    find_item,
    item_digest,
    report_digest,
)
from .inventory import AISystemInventory, build_example_inventory
from .models import ClassificationReport, SystemProfile


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

    @field_validator("lock_expires_at")
    @classmethod
    def _lock_time_is_iso(cls, value: str | None) -> str | None:
        # A lock time that does not parse would make every later lock or review of
        # the cell fail; reject it when a file is imported or loaded instead.
        if value is not None:
            try:
                datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("lock_expires_at must be an ISO 8601 date and time") from None
        return value


class CollaborationWorkspace(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    schema_id: Literal["review.collaboration.v1"] = Field("review.collaboration.v1", alias="schema")
    inventory_digest: str
    cells: list[ReviewCellState]
    # The obligation tracker's records (ADR 0006). Additive: a file saved before the
    # tracker existed loads with none, under the same schema id.
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    activity: list[dict[str, str]] = Field(default_factory=list)
    external_action_allowed: bool = Field(False, alias="externalActionAllowed")

    @model_validator(mode="after")
    def _evidence_keys_are_unique(self) -> CollaborationWorkspace:
        keys = [record.key() for record in self.evidence]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate evidence record")
        return self


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
    # The generation timestamps change on every rebuild without changing the
    # inventory's content, so they stay out of the digest.
    payload = inventory.model_dump_json(
        by_alias=True, exclude={"generatedAt": True, "reviewTable": {"generatedAt"}}
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class StaleWorkspaceError(ValueError):
    """A workspace built for another inventory than the current one.

    ``workspace`` is the parsed file, so a recovery can carry over what does not depend
    on the inventory (the evidence records).
    """

    def __init__(self, message: str, workspace: CollaborationWorkspace | None = None) -> None:
        super().__init__(message)
        self.workspace = workspace


def _as_utc(moment: datetime) -> datetime:
    """``moment`` with a time zone: a naive time counts as UTC."""

    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def _locked_by_another(cell: ReviewCellState, actor: str, now: datetime) -> bool:
    """Whether a lock held by someone other than ``actor`` is still running at ``now``.

    The lock time and ``now`` may each be naive or aware, as an imported file or a
    direct caller gives them; a naive time counts as UTC on both sides.
    """

    if not (cell.locked_by and cell.locked_by != actor and cell.lock_expires_at):
        return False
    return _as_utc(datetime.fromisoformat(cell.lock_expires_at)) > _as_utc(now)


def build_collaboration_state(inventory: AISystemInventory) -> CollaborationWorkspace:
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
    if _locked_by_another(cell, actor, now):
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
    if _locked_by_another(cell, reviewer, now):
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
    """Write the workspace to ``path`` in one step.

    The JSON goes to a temporary file next to ``path``, which then replaces ``path``.
    A write that fails partway leaves the previous file as it was and removes the
    temporary file, so ``path`` never holds half a workspace.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = workspace.model_dump_json(by_alias=True, indent=2) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return path


def load_workspace(path: Path, inventory: AISystemInventory) -> CollaborationWorkspace:
    """The workspace saved at ``path``.

    Raises a ValueError when the file is not a valid workspace, and
    StaleWorkspaceError when it was built for another inventory.
    """

    workspace = CollaborationWorkspace.model_validate_json(path.read_text(encoding="utf-8"))
    if workspace.inventory_digest != _inventory_digest(inventory):
        raise StaleWorkspaceError(
            "workspace state is stale for the current deterministic inventory", workspace
        )
    return workspace


def _archive_path(path: Path, reason: str, now: datetime) -> Path:
    """A free name next to ``path`` that records why and when the file was set aside."""

    stamp = _as_utc(now).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    candidate = path.with_name(f"{path.stem}.{reason}-{stamp}{path.suffix}")
    counter = 2
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}.{reason}-{stamp}-{counter}{path.suffix}")
        counter += 1
    return candidate


def _load_or_recover(
    path: Path, inventory: AISystemInventory, now: datetime
) -> CollaborationWorkspace:
    """The saved workspace, or a new one when the saved file cannot be used.

    A file that is not a valid workspace (cut off by a failed write, or edited by
    hand) or that was built for another inventory (an example changed) used to fail
    every action until someone deleted it. Such a file is now renamed, not deleted:
    it stays next to ``path`` as ``<name>.unreadable-<UTC time>.json`` or
    ``<name>.stale-<UTC time>.json``. A new workspace whose activity starts with a
    "recovered" event naming that file is saved at once. A file the process cannot
    read at all (an OSError) is an operator problem and still fails.

    A stale file's evidence records are carried into the new workspace, since their key
    (cockpit system, obligation and actor) does not depend on the inventory; the
    recovered event then counts them as "evidenceCarried". An unreadable file carries
    nothing.
    """

    if not path.exists():
        return build_collaboration_state(inventory)
    carried: list[EvidenceRecord] = []
    try:
        return load_workspace(path, inventory)
    except StaleWorkspaceError as stale:
        reason = "stale"
        carried = list(stale.workspace.evidence) if stale.workspace is not None else []
    except ValueError:
        # Invalid JSON or not a workspace (a pydantic ValidationError), or not UTF-8.
        reason = "unreadable"
    archive = _archive_path(path, reason, now)
    path.replace(archive)
    workspace = build_collaboration_state(inventory)
    workspace.evidence = carried
    recovered = {
        "event": "recovered",
        "reason": reason,
        "archivedAs": archive.name,
        "occurredAt": now.isoformat(),
    }
    if carried:
        recovered["evidenceCarried"] = str(len(carried))
    workspace.activity.append(recovered)
    save_workspace(workspace, path)
    return workspace


def export_workspace(workspace: CollaborationWorkspace) -> str:
    return workspace.model_dump_json(by_alias=True, indent=2) + "\n"


def import_workspace(payload: str, inventory: AISystemInventory) -> CollaborationWorkspace:
    workspace = CollaborationWorkspace.model_validate_json(payload)
    if workspace.inventory_digest != _inventory_digest(inventory):
        raise StaleWorkspaceError(
            "workspace state is stale for the current deterministic inventory", workspace
        )
    return workspace


def _record_import(
    current: CollaborationWorkspace,
    imported: CollaborationWorkspace,
    *,
    actor: str,
    now: datetime,
) -> CollaborationWorkspace:
    """Take the imported cells and keep the activity trail.

    The imported file replaces the review cells. It replaces the evidence records only
    when it carries an ``evidence`` key; a file exported before the tracker existed
    keeps the current records. The activity list only grows: the entries already
    recorded stay, the file's entries the trail lacks follow them, and an "imported"
    event closes the import and counts the entries it added.
    """

    added = [entry for entry in imported.activity if entry not in current.activity]
    activity = [
        *current.activity,
        *added,
        {
            "event": "imported",
            "actor": actor,
            "occurredAt": now.isoformat(),
            "importedEntries": str(len(added)),
        },
    ]
    evidence = imported.evidence if "evidence" in imported.model_fields_set else current.evidence
    return imported.model_copy(update={"activity": activity, "evidence": evidence})


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
                classifier_version=__version__,
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
    if not inventory.systems:
        raise ValueError("cannot build self-assessment portal with an empty system inventory")
    first = inventory.systems[0]
    blockers = [
        system.system_id for system in inventory.systems if system.review_status == "blocked"
    ]
    submitted = answers or {}
    missing_answers = sorted(
        question_id
        for question_id in {"purpose", "role", "eu_nexus", "evidence"}
        if not str(submitted.get(question_id) or "").strip()
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


def build_collaboration_workspace(
    *,
    collaboration: CollaborationWorkspace | None = None,
    assessment_answers: dict[str, object] | None = None,
) -> dict[str, object]:
    inventory = build_example_inventory()
    definitions, runs = build_policy_workflows(inventory)
    return {
        "schema": "eu-ai-act.collaboration-workspace.v1",
        "draftNotice": DRAFT_NOTICE,
        "collaboration": (collaboration or build_collaboration_state(inventory)).model_dump(
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


def _inventory_timestamp(now: datetime | None) -> str | None:
    """Stamp the inventory with the injected clock, as the inventory's own clock would.

    This keeps the inventory, and so the returned payload, reproducible for a given
    `now`. Without `now` the inventory reads the clock, as before. The digest leaves the
    timestamp out either way (see `_inventory_digest`).
    """

    if now is None:
        return None
    return _as_utc(now).astimezone(UTC).replace(microsecond=0).isoformat()


def _expected_revision(payload: dict[str, object]) -> int:
    try:
        return int(payload.get("expectedRevision", 0))
    except (TypeError, ValueError, OverflowError):
        # int() names the rejected value in its message; this one does not.
        raise ValueError("expectedRevision must be an integer") from None


def set_evidence(
    workspace: CollaborationWorkspace,
    *,
    system_id: str,
    report: ClassificationReport,
    obligation_id: str,
    obligation_actor: str,
    state: str,
    owner: str | None,
    reviewed_on: str | None,
    actor: str,
    expected_revision: int,
    now: datetime,
) -> CollaborationWorkspace:
    """Record the evidence state of one obligation graph item of one cockpit system.

    The record stores the digests of ``report`` and of the item, so a later change to
    either marks it stale. ``now`` is the bridge's clock: a reviewed-on date after its
    day is rejected.
    """

    check_system_id(system_id)
    item = find_item(report, obligation_id, obligation_actor)
    if item is None:
        raise ValueError("unknown obligation graph item for this report")
    if state == "stale":
        raise ValueError("stale is derived from the report and the source dates and cannot be set")
    updated = workspace.model_copy(deep=True)
    key = (system_id, obligation_id, obligation_actor)
    index = next((i for i, record in enumerate(updated.evidence) if record.key() == key), None)
    current_revision = updated.evidence[index].revision if index is not None else 0
    if current_revision != expected_revision:
        raise ValueError("409 Conflict: stale evidence revision")
    record = EvidenceRecord.model_validate(
        {
            "system_id": system_id,
            "obligation_id": obligation_id,
            "obligation_actor": obligation_actor,
            "state": state,
            "owner": (owner or "").strip() or None,
            "reviewed_on": reviewed_on or None,
            "report_digest": report_digest(report),
            "item_digest": item_digest(item),
            "revision": current_revision + 1,
            "updated_by": actor,
            "updated_at": now.isoformat(),
        }
    )
    if record.reviewed_on is not None and record.reviewed_on > _as_utc(now).date().isoformat():
        raise ValueError("reviewedOn must not be after the current date")
    if index is None:
        updated.evidence.append(record)
    else:
        updated.evidence[index] = record
    updated.activity.append(
        {
            "event": "evidence_updated",
            "targetId": f"evidence:{system_id}:{obligation_id}:{obligation_actor}",
            "actor": actor,
            "state": state,
            "occurredAt": now.isoformat(),
        }
    )
    return updated


def _evidence_report(payload: dict[str, object]) -> ClassificationReport:
    """The report for the profile the cockpit classified, without the advisory overlay."""

    profile = payload.get("profile")
    if not isinstance(profile, dict):
        raise ValueError("profile must be a JSON object")
    return classify(SystemProfile.model_validate(profile))


def _evidence_view(
    current: CollaborationWorkspace, system_id: str, report: ClassificationReport
) -> dict[str, object]:
    return build_evidence_view(
        system_id=system_id,
        report=report,
        records=[record for record in current.evidence if record.system_id == system_id],
        draft_notice=DRAFT_NOTICE,
    )


def _optional_text(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{key} must be text")
    return value


def apply_workspace_action(
    payload: dict[str, object], runtime_path: Path, *, now: datetime | None = None
) -> dict[str, object]:
    """Apply one local mutation against the fixed ignored runtime workspace.

    The inventory is stamped with ``now`` (or the clock). The digest the stored
    workspace is checked against leaves that timestamp out, so actions at different
    times operate on the same workspace. A stored file that is unreadable or stale is
    set aside and a new workspace started (see ``_load_or_recover``).

    "evidence_view" and "evidence" classify the payload's ``profile`` (the one the
    cockpit shows) and return the obligation tracker for ``systemId`` instead of the
    workspace snapshot; "evidence_view" saves nothing.
    """

    inventory = build_example_inventory(generated_at=_inventory_timestamp(now))
    occurred_at = now or datetime.now(UTC)
    current = _load_or_recover(runtime_path, inventory, occurred_at)
    action = str(payload.get("action", "snapshot"))
    if action == "snapshot":
        return build_collaboration_workspace(collaboration=current)
    target_id = str(payload.get("targetId", ""))
    expected_revision = _expected_revision(payload)
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
            body=str(payload.get("body") or ""),
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
    elif action == "evidence_view":
        system_id = check_system_id(str(payload.get("systemId", "")))
        return _evidence_view(current, system_id, _evidence_report(payload))
    elif action == "evidence":
        system_id = check_system_id(str(payload.get("systemId", "")))
        report = _evidence_report(payload)
        current = set_evidence(
            current,
            system_id=system_id,
            report=report,
            obligation_id=str(payload.get("obligationId", "")),
            obligation_actor=str(payload.get("obligationActor", "")),
            state=str(payload.get("state", "")),
            owner=_optional_text(payload, "owner"),
            reviewed_on=_optional_text(payload, "reviewedOn"),
            actor=actor,
            expected_revision=expected_revision,
            now=occurred_at,
        )
        save_workspace(current, runtime_path)
        return _evidence_view(current, system_id, report)
    elif action == "import":
        raw = payload.get("workspace")
        if raw is None:
            raise ValueError("missing workspace payload for import action")
        current = _record_import(
            current,
            import_workspace(json.dumps(raw) if not isinstance(raw, str) else raw, inventory),
            actor=actor,
            now=occurred_at,
        )
    elif action == "self_assess":
        answers = payload.get("answers", {})
        if not isinstance(answers, dict):
            raise ValueError("answers must be a JSON object")
        return build_collaboration_workspace(
            collaboration=current,
            assessment_answers=dict(answers),
        )
    else:
        raise ValueError(f"unsupported workspace action: {action}")
    save_workspace(current, runtime_path)
    return build_collaboration_workspace(collaboration=current)
