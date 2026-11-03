import errno
import io
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import eu_ai_act_classifier.inventory as inventory_module
from eu_ai_act_classifier import __version__
from eu_ai_act_classifier.collaboration_workspace import (
    add_comment,
    apply_workspace_action,
    build_collaboration_state,
    build_collaboration_workspace,
    build_self_assessment_portal,
    load_workspace,
    lock_cell,
    review_cell,
    save_workspace,
)
from eu_ai_act_classifier.inventory import build_example_inventory

ROOT = Path(__file__).resolve().parents[1]


def _without_activity(snapshot: dict[str, object]) -> dict[str, object]:
    collaboration = dict(snapshot["collaboration"])
    collaboration.pop("activity")
    return collaboration


def test_collaboration_uses_stable_cells_and_stale_revision_conflicts(tmp_path) -> None:
    inventory = build_example_inventory()
    workspace = build_collaboration_state(inventory)
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
    workspace = build_collaboration_workspace()
    assert all(
        "human_review" in definition["steps"] for definition in workspace["workflowDefinitions"]
    )
    assert workspace["selfAssessmentPortal"]["localOnly"] is True
    assert workspace["selfAssessmentPortal"]["exportAllowed"] is False
    assert any(run["status"] == "blocked" for run in workspace["workflowRuns"])
    assert all(run["definition_snapshot"] for run in workspace["workflowRuns"])
    assert all(run["source_versions"] for run in workspace["workflowRuns"])
    assert all(run["classifier_version"] == __version__ for run in workspace["workflowRuns"])


def test_comments_and_overrides_persist_without_changing_deterministic_baseline(tmp_path) -> None:
    inventory = build_example_inventory()
    workspace = build_collaboration_state(inventory)
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
    assert _without_activity(imported) == _without_activity(snapshot)
    assert imported["collaboration"]["activity"][:-1] == snapshot["collaboration"]["activity"]
    assert imported["collaboration"]["activity"][-1]["event"] == "imported"


def test_actions_given_one_clock_build_the_same_inventory(tmp_path, monkeypatch) -> None:
    # A second boundary between two inventory builds used to make the saved workspace stale.
    ticks = iter(range(60))
    monkeypatch.setattr(
        inventory_module, "_now", lambda: f"2026-07-13T00:00:{next(ticks):02d}+00:00"
    )
    now = datetime(2026, 7, 13, tzinfo=UTC)
    runtime_path = tmp_path / "workspace.json"
    target = build_collaboration_state(build_example_inventory()).cells[0].target_id
    reviewed = apply_workspace_action(
        {"action": "review", "targetId": target, "expectedRevision": 1, "actor": "Reviewer"},
        runtime_path,
        now=now,
    )
    imported = apply_workspace_action(
        {"action": "import", "workspace": reviewed["collaboration"]}, runtime_path, now=now
    )
    assert _without_activity(imported) == _without_activity(reviewed)


def test_self_assessment_missing_answers_remain_blocking(tmp_path) -> None:
    snapshot = apply_workspace_action(
        {"action": "self_assess", "answers": {"purpose": "Synthetic screening"}},
        tmp_path / "workspace.json",
        now=datetime(2026, 7, 13, tzinfo=UTC),
    )
    packet = snapshot["selfAssessmentPortal"]["draftPacket"]
    assert sorted(packet["missingAnswers"]) == ["eu_nexus", "evidence", "role"]
    assert snapshot["selfAssessmentPortal"]["exportAllowed"] is False


def test_lock_normalizes_naive_and_aware_timestamps() -> None:
    workspace = build_collaboration_state(build_example_inventory())
    target = workspace.cells[0].target_id
    locked = lock_cell(
        workspace,
        target_id=target,
        actor="Reviewer A",
        expected_revision=1,
        now=datetime(2026, 7, 13),
    )
    with pytest.raises(ValueError, match="locked by Reviewer A"):
        lock_cell(
            locked,
            target_id=target,
            actor="Reviewer B",
            expected_revision=2,
            now=datetime(2026, 7, 13, tzinfo=UTC),
        )


def test_empty_inventory_and_null_payloads_fail_closed(tmp_path) -> None:
    inventory = build_example_inventory().model_copy(update={"systems": []})
    with pytest.raises(ValueError, match="empty system inventory"):
        build_self_assessment_portal(inventory)
    with pytest.raises(ValueError, match="missing workspace payload"):
        apply_workspace_action(
            {"action": "import", "workspace": None},
            tmp_path / "workspace.json",
        )


def test_workspace_survives_an_inventory_rebuilt_at_another_time(tmp_path) -> None:
    # The inventory stamps its generation time; a saved workspace must not go
    # stale just because the inventory was rebuilt a second later.
    earlier = build_example_inventory(generated_at="2026-07-13T09:00:00+00:00")
    later = build_example_inventory(generated_at="2026-07-13T09:00:01+00:00")
    path = save_workspace(build_collaboration_state(earlier), tmp_path / "workspace.json")
    loaded = load_workspace(path, later)
    assert loaded.inventory_digest == build_collaboration_state(later).inventory_digest


def _reviewed_workspace(runtime_path, now: datetime) -> dict[str, object]:
    target = build_collaboration_state(build_example_inventory()).cells[0].target_id
    return apply_workspace_action(
        {
            "action": "review",
            "targetId": target,
            "expectedRevision": 1,
            "actor": "Reviewer A",
            "reviewerOverride": "human_review_required",
        },
        runtime_path,
        now=now,
    )


def test_import_keeps_prior_activity_and_records_the_import(tmp_path) -> None:
    # An import used to replace the whole workspace, activity included: a file
    # with an empty activity list erased the trail (1 entry before, 0 after).
    runtime_path = tmp_path / "workspace.json"
    reviewed = _reviewed_workspace(runtime_path, datetime(2026, 7, 13, tzinfo=UTC))
    prior = reviewed["collaboration"]["activity"]
    assert [entry["event"] for entry in prior] == ["reviewed"]
    blank = build_collaboration_workspace()["collaboration"]
    assert blank["activity"] == []

    imported = apply_workspace_action(
        {"action": "import", "workspace": blank, "actor": "Reviewer B"},
        runtime_path,
        now=datetime(2026, 7, 14, tzinfo=UTC),
    )

    assert imported["collaboration"]["cells"] == blank["cells"]
    assert imported["collaboration"]["activity"] == [
        *prior,
        {
            "event": "imported",
            "actor": "Reviewer B",
            "occurredAt": "2026-07-14T00:00:00+00:00",
            "importedEntries": "0",
        },
    ]
    stored = load_workspace(runtime_path, build_example_inventory())
    assert stored.activity == imported["collaboration"]["activity"]


def test_import_adds_the_file_entries_the_workspace_lacks(tmp_path) -> None:
    # A file exported elsewhere carries its own history. The entries the local
    # trail lacks follow it, and the imported event counts them; entries both
    # hold are not repeated.
    runtime_path = tmp_path / "workspace.json"
    reviewed = _reviewed_workspace(runtime_path, datetime(2026, 7, 13, tzinfo=UTC))
    prior = reviewed["collaboration"]["activity"]
    elsewhere = {
        "event": "comment_added",
        "targetId": reviewed["collaboration"]["cells"][1]["target_id"],
        "actor": "Reviewer C",
        "occurredAt": "2026-07-13T12:00:00+00:00",
    }
    exported = {**reviewed["collaboration"], "activity": [*prior, elsewhere]}

    imported = apply_workspace_action(
        {"action": "import", "workspace": exported},
        runtime_path,
        now=datetime(2026, 7, 14, tzinfo=UTC),
    )

    activity = imported["collaboration"]["activity"]
    assert activity[:-1] == [*prior, elsewhere]
    assert activity[-1] == {
        "event": "imported",
        "actor": "Local reviewer",
        "occurredAt": "2026-07-14T00:00:00+00:00",
        "importedEntries": "1",
    }


@pytest.mark.parametrize(
    ("lock_time", "review_time"),
    [
        (datetime(2026, 7, 13), datetime(2026, 7, 13, tzinfo=UTC)),
        (datetime(2026, 7, 13, tzinfo=UTC), datetime(2026, 7, 13)),
    ],
    ids=["naive-lock-aware-review", "aware-lock-naive-review"],
)
def test_review_normalizes_naive_and_aware_timestamps(
    lock_time: datetime, review_time: datetime
) -> None:
    # lock_cell treats a naive time as UTC; review_cell compared the two as they
    # came and raised TypeError, which no caller turned into a 409 (AIA-26).
    workspace = build_collaboration_state(build_example_inventory())
    target = workspace.cells[0].target_id
    locked = lock_cell(
        workspace, target_id=target, actor="Reviewer A", expected_revision=1, now=lock_time
    )
    with pytest.raises(ValueError, match="409 Conflict: review cell is locked by Reviewer A"):
        review_cell(
            locked,
            target_id=target,
            reviewer="Reviewer B",
            reviewer_override="human_review_required",
            expected_revision=2,
            now=review_time,
        )


def test_review_goes_through_once_a_naive_lock_has_expired() -> None:
    workspace = build_collaboration_state(build_example_inventory())
    target = workspace.cells[0].target_id
    locked = lock_cell(
        workspace,
        target_id=target,
        actor="Reviewer A",
        expected_revision=1,
        now=datetime(2026, 7, 13),
    )

    reviewed = review_cell(
        locked,
        target_id=target,
        reviewer="Reviewer B",
        reviewer_override="human_review_required",
        expected_revision=2,
        now=datetime(2026, 7, 13, tzinfo=UTC) + timedelta(minutes=16),
    )

    assert (reviewed.cells[0].reviewer, reviewed.cells[0].revision) == ("Reviewer B", 3)


class _FullDisk:
    """A text file that takes half of what is written and then fails as a full disk does."""

    def __init__(self, handle) -> None:
        self._handle = handle

    def write(self, text: str) -> int:
        self._handle.write(text[: len(text) // 2])
        self._handle.flush()
        raise OSError(errno.ENOSPC, "No space left on device")

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> bool:
        self._handle.close()
        return False

    def __getattr__(self, name: str):
        return getattr(self._handle, name)


def test_a_failed_save_keeps_the_previous_workspace(tmp_path, monkeypatch) -> None:
    # save_workspace wrote over the file in place, so a write that stopped halfway
    # left half a JSON document, and every later action failed on it (AIA-22).
    inventory = build_example_inventory()
    path = tmp_path / "workspace.json"
    previous = build_collaboration_state(inventory)
    save_workspace(previous, path)
    updated = add_comment(
        previous,
        target_id=previous.cells[0].target_id,
        body="Confirm the factor evidence against approved sources.",
        actor="Reviewer",
        expected_revision=1,
        now=datetime(2026, 7, 13, tzinfo=UTC),
    )
    real_open = io.open

    def full_disk_open(file, mode="r", *args, **kwargs):
        handle = real_open(file, mode, *args, **kwargs)
        return _FullDisk(handle) if "w" in mode else handle

    with monkeypatch.context() as patch:
        patch.setattr(io, "open", full_disk_open)
        with pytest.raises(OSError, match="No space left"):
            save_workspace(updated, path)

    assert load_workspace(path, inventory) == previous
    assert [entry.name for entry in tmp_path.iterdir()] == ["workspace.json"]


def test_a_save_leaves_only_the_workspace_file(tmp_path) -> None:
    path = save_workspace(
        build_collaboration_state(build_example_inventory()), tmp_path / "runtime" / "ws.json"
    )

    assert [entry.name for entry in path.parent.iterdir()] == ["ws.json"]


TRUNCATED = '{\n  "schema": "review.collaboration.v1",\n  "inventory_dig'


def test_an_unreadable_workspace_is_archived_and_a_new_one_started(tmp_path) -> None:
    # A half-written or hand-edited file used to fail every action, the page load
    # included, until someone deleted it by hand (AIA-22).
    runtime_path = tmp_path / "workspace.json"
    runtime_path.write_text(TRUNCATED, encoding="utf-8")

    snapshot = apply_workspace_action(
        {"action": "snapshot"}, runtime_path, now=datetime(2026, 7, 13, 9, 30, tzinfo=UTC)
    )

    archive = tmp_path / "workspace.unreadable-20260713T093000Z.json"
    assert archive.read_text(encoding="utf-8") == TRUNCATED
    fresh = build_collaboration_state(build_example_inventory())
    assert snapshot["collaboration"]["cells"] == fresh.model_dump(mode="json")["cells"]
    assert snapshot["collaboration"]["activity"] == [
        {
            "event": "recovered",
            "reason": "unreadable",
            "archivedAs": archive.name,
            "occurredAt": "2026-07-13T09:30:00+00:00",
        }
    ]
    # The new workspace is saved at once, so the next request reads it and the record.
    stored = load_workspace(runtime_path, build_example_inventory())
    assert stored.activity == snapshot["collaboration"]["activity"]


def test_a_workspace_gone_stale_after_an_examples_change_is_archived(tmp_path, monkeypatch) -> None:
    # Editing an example changes the inventory digest, and the saved workspace then
    # failed as stale on every action (AIA-22).
    shutil.copytree(ROOT / "examples", tmp_path / "examples")
    monkeypatch.chdir(tmp_path)
    runtime_path = Path("runtime-data/collaboration-workspace.json")
    reviewed = _reviewed_workspace(runtime_path, datetime(2026, 7, 13, tzinfo=UTC))
    stored_before = runtime_path.read_text(encoding="utf-8")
    spam_filter = Path("examples/spam_filter.json")
    profile = json.loads(spam_filter.read_text(encoding="utf-8"))
    spam_filter.write_text(json.dumps({**profile, "name": "InboxGuard 2"}), encoding="utf-8")
    target = reviewed["collaboration"]["cells"][0]["target_id"]

    result = apply_workspace_action(
        {
            "action": "comment",
            "targetId": target,
            "expectedRevision": 1,
            "actor": "Reviewer B",
            "body": "Re-check after the examples changed.",
        },
        runtime_path,
        now=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
    )

    archive = Path("runtime-data/collaboration-workspace.stale-20260714T080000Z.json")
    assert archive.read_text(encoding="utf-8") == stored_before
    assert [
        (entry["event"], entry.get("reason"), entry.get("archivedAs"))
        for entry in result["collaboration"]["activity"]
    ] == [("recovered", "stale", archive.name), ("comment_added", None, None)]
    cell = next(c for c in result["collaboration"]["cells"] if c["target_id"] == target)
    assert (cell["revision"], cell["reviewer_override"]) == (2, None)
    assert (
        load_workspace(runtime_path, build_example_inventory()).activity
        == (result["collaboration"]["activity"])
    )


def test_recovery_never_overwrites_an_earlier_archive(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    now = datetime(2026, 7, 13, 9, 30)
    runtime_path.write_text(TRUNCATED, encoding="utf-8")
    apply_workspace_action({"action": "snapshot"}, runtime_path, now=now)
    runtime_path.write_text("not json", encoding="utf-8")

    second = apply_workspace_action({"action": "snapshot"}, runtime_path, now=now)

    first_archive = tmp_path / "workspace.unreadable-20260713T093000Z.json"
    second_archive = tmp_path / "workspace.unreadable-20260713T093000Z-2.json"
    assert first_archive.read_text(encoding="utf-8") == TRUNCATED
    assert second_archive.read_text(encoding="utf-8") == "not json"
    assert second["collaboration"]["activity"][0]["archivedAs"] == second_archive.name


def test_a_workspace_that_cannot_be_read_from_disk_is_not_archived(tmp_path) -> None:
    # Only content that is not a current workspace is archived. A file the process
    # cannot read at all (here a directory) is an operator problem, so it fails as before.
    runtime_path = tmp_path / "workspace.json"
    runtime_path.mkdir()

    with pytest.raises(OSError):
        apply_workspace_action({"action": "snapshot"}, runtime_path)

    assert [entry.name for entry in tmp_path.iterdir()] == ["workspace.json"]
