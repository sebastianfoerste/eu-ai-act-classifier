from datetime import UTC, datetime

import pytest

from eu_ai_act_classifier.inventory import build_example_inventory
from eu_ai_act_classifier.legora_workspace import (
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
