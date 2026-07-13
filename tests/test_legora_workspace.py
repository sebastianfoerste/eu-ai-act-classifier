from datetime import UTC, datetime

import pytest

from eu_ai_act_classifier.inventory import build_example_inventory
from eu_ai_act_classifier.legora_workspace import (
    add_comment,
    apply_workspace_action,
    build_collaboration_workspace,
    build_legora_workspace,
    load_workspace,
    lock_cell,
    save_workspace,
)


def test_collaboration_uses_stable_cells_and_stale_revision_conflicts(tmp_path) -> None:
    inventory = build_example_inventory()
    workspace = build_collaboration_workspace(inventory)
    locked = lock_cell(
        workspace,
        target_id=workspace.cells[0].target_id,
        actor="Reviewer",
        expected_revision=1,
        now=datetime(2026, 7, 13, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="409 Conflict"):
        lock_cell(
            locked,
            target_id=locked.cells[0].target_id,
            actor="Other",
            expected_revision=1,
            now=datetime(2026, 7, 13, tzinfo=UTC),
        )
    path = save_workspace(locked, tmp_path / "workspace.json")
    assert load_workspace(path, inventory) == locked


def test_workflows_and_portal_remain_review_gated() -> None:
    workspace = build_legora_workspace()
    assert all(
        "human_review" in definition["steps"] for definition in workspace["workflowDefinitions"]
    )
    assert workspace["selfAssessmentPortal"]["localOnly"] is True
    assert workspace["selfAssessmentPortal"]["exportAllowed"] is False
    assert any(run["status"] == "blocked" for run in workspace["workflowRuns"])
    assert all(run["definition_snapshot"] for run in workspace["workflowRuns"])
    assert all(run["source_versions"] for run in workspace["workflowRuns"])


def test_comments_and_overrides_persist_without_changing_deterministic_baseline(tmp_path) -> None:
    inventory = build_example_inventory()
    workspace = build_collaboration_workspace(inventory)
    target = workspace.cells[0].target_id
    original = workspace.cells[0].deterministic_status
    commented = add_comment(
        workspace,
        target_id=target,
        body="Verify approved source version.",
        actor="Reviewer",
        expected_revision=1,
        now=datetime(2026, 7, 13, tzinfo=UTC),
    )
    assert commented.cells[0].deterministic_status == original
    runtime_path = tmp_path / "runtime-data" / "workspace.json"
    snapshot = apply_workspace_action(
        {
            "action": "review",
            "targetId": target,
            "expectedRevision": 1,
            "actor": "Reviewer",
            "reviewerOverride": "human_review_required",
        },
        runtime_path,
        now=datetime(2026, 7, 13, tzinfo=UTC),
    )
    assert snapshot["collaboration"]["cells"][0]["deterministic_status"] == original
    assert snapshot["collaboration"]["cells"][0]["reviewer_override"] == "human_review_required"
    imported = apply_workspace_action(
        {"action": "import", "workspace": snapshot["collaboration"]},
        runtime_path,
        now=datetime(2026, 7, 13, tzinfo=UTC),
    )
    assert imported["collaboration"] == snapshot["collaboration"]


def test_self_assessment_missing_answers_remain_blocking(tmp_path) -> None:
    snapshot = apply_workspace_action(
        {"action": "self_assess", "answers": {"purpose": "Synthetic screening"}},
        tmp_path / "workspace.json",
        now=datetime(2026, 7, 13, tzinfo=UTC),
    )
    packet = snapshot["selfAssessmentPortal"]["draftPacket"]
    assert sorted(packet["missingAnswers"]) == ["eu_nexus", "evidence", "role"]
    assert snapshot["selfAssessmentPortal"]["exportAllowed"] is False
