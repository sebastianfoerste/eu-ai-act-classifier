import contextlib
import errno
import io
import json
import os
import shutil
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import eu_ai_act_classifier.collaboration_workspace as collaboration_module
import eu_ai_act_classifier.inventory as inventory_module
from eu_ai_act_classifier import __version__
from eu_ai_act_classifier.artifacts import DRAFT_NOTICE
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
from eu_ai_act_classifier.engine import classify
from eu_ai_act_classifier.inventory import build_example_inventory
from eu_ai_act_classifier.models import SystemProfile

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
    # The inventory's own clock ticks on another day, so only the injected `now` can give
    # the inventory each action builds the same timestamp. The digest leaves the timestamp
    # out (#33), so the collaboration payloads alone would not show which clock was used.
    ticks = iter(range(60))
    monkeypatch.setattr(
        inventory_module, "_now", lambda: f"2026-07-14T00:00:{next(ticks):02d}+00:00"
    )
    built = []

    def recording_inventory(*args, **kwargs):
        inventory = build_example_inventory(*args, **kwargs)
        built.append(inventory)
        return inventory

    monkeypatch.setattr(collaboration_module, "build_example_inventory", recording_inventory)
    now = datetime(2026, 7, 13, tzinfo=UTC)
    runtime_path = tmp_path / "workspace.json"
    target = build_collaboration_state(build_example_inventory()).cells[0].target_id

    def act(payload: dict[str, object]):
        # The first inventory an action builds is the one it loads the workspace against.
        first = len(built)
        snapshot = apply_workspace_action(payload, runtime_path, now=now)
        return snapshot, built[first]

    reviewed, review_inventory = act(
        {"action": "review", "targetId": target, "expectedRevision": 1, "actor": "Reviewer"}
    )
    imported, import_inventory = act({"action": "import", "workspace": reviewed["collaboration"]})

    stamp = "2026-07-13T00:00:00+00:00"
    for inventory in (review_inventory, import_inventory):
        assert inventory.generatedAt == stamp
        assert inventory.reviewTable.generatedAt == stamp
    assert import_inventory == review_inventory
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

    # Nothing archived; only the (empty) lock file the action held sits next to it.
    assert sorted(entry.name for entry in tmp_path.iterdir()) == [
        "workspace.json",
        "workspace.json.lock",
    ]


def _workspace_with_lock_time(lock_expires_at: str) -> dict:
    workspace = json.loads(
        build_collaboration_state(build_example_inventory()).model_dump_json(by_alias=True)
    )
    workspace["cells"][0].update(locked_by="Reviewer A", lock_expires_at=lock_expires_at)
    return workspace


def test_import_rejects_a_malformed_lock_time_without_echoing_it(tmp_path) -> None:
    # A lock time that does not parse used to be accepted, then broke every later lock
    # or review of the cell with a bare ValueError that carried the value.
    from pydantic import ValidationError

    from eu_ai_act_classifier.local_api import _validation_message

    with pytest.raises(ValidationError) as caught:
        apply_workspace_action(
            {"action": "import", "workspace": _workspace_with_lock_time("SECRET-not-a-time")},
            tmp_path / "workspace.json",
        )
    message = _validation_message(caught.value)
    assert "cells.0.lock_expires_at" in message
    assert "SECRET" not in message


def test_a_stored_workspace_with_a_malformed_lock_time_is_archived(tmp_path) -> None:
    path = tmp_path / "workspace.json"
    path.write_text(json.dumps(_workspace_with_lock_time("tomorrow")), encoding="utf-8")

    result = apply_workspace_action({}, path)

    recovered = [e for e in result["collaboration"]["activity"] if e["event"] == "recovered"]
    assert [e["reason"] for e in recovered] == ["unreadable"]
    assert (tmp_path / recovered[0]["archivedAs"]).exists()


def test_import_keeps_a_well_formed_lock_time(tmp_path) -> None:
    result = apply_workspace_action(
        {"action": "import", "workspace": _workspace_with_lock_time("2026-07-13T09:15:00+00:00")},
        tmp_path / "workspace.json",
        now=datetime(2026, 7, 13, 9, 0, tzinfo=UTC),
    )
    assert result["collaboration"]["cells"][0]["lock_expires_at"] == "2026-07-13T09:15:00+00:00"


# The obligation tracker (ADR 0006). The profile is the cockpit's "credit-provider"
# sample (web/lib/samples.ts), as the cockpit posts it; the clock is injected.
EVIDENCE_NOW = datetime(2026, 11, 17, 10, 0, tzinfo=UTC)
COCKPIT_CREDIT = {
    "name": "CreditSightScore",
    "description": "Scores consumer creditworthiness for loan origination.",
    "roles": ["provider"],
    "purpose": "Consumer creditworthiness scoring",
    "sector": "Financial services",
    "intended_purpose_source": "Product requirements document",
    "annex_iii_area": "III.5.b",
    "placing_on_market_date": "2026-10-01",
}
COCKPIT_CHATBOT = {
    "name": "SupportDeskBot",
    "description": "Customer support chatbot for first-line ticket handling.",
    "roles": ["provider"],
    "purpose": "Customer support interaction",
    "sector": "SaaS operations",
    "intended_purpose_source": "Feature brief",
    "interacts_with_natural_persons": True,
}


def _evidence(
    runtime_path: Path,
    *,
    obligation_id: str = "high-risk.provider.9",
    state: str = "in_progress",
    revision: int = 0,
    system_id: str = "credit-provider",
    profile: object = None,
    actor: str = "provider",
    owner: object = None,
    reviewed_on: object = None,
    now: datetime = EVIDENCE_NOW,
) -> dict[str, object]:
    return apply_workspace_action(
        {
            "action": "evidence",
            "systemId": system_id,
            "profile": COCKPIT_CREDIT if profile is None else profile,
            "obligationId": obligation_id,
            "obligationActor": actor,
            "state": state,
            "owner": owner,
            "reviewedOn": reviewed_on,
            "expectedRevision": revision,
            "actor": "Reviewer A",
        },
        runtime_path,
        now=now,
    )


def _view(
    runtime_path: Path, profile: dict[str, object] | None = None, system_id: str = "credit-provider"
) -> dict[str, object]:
    return apply_workspace_action(
        {
            "action": "evidence_view",
            "systemId": system_id,
            "profile": COCKPIT_CREDIT if profile is None else profile,
        },
        runtime_path,
        now=EVIDENCE_NOW,
    )


def _entry(view: dict[str, object], obligation_id: str, actor: str = "provider") -> dict:
    return next(
        entry
        for lane in view["lanes"]
        for entry in lane["items"]
        if entry["obligationId"] == obligation_id and entry["actor"] == actor
    )


def test_a_pre_s4_workspace_file_loads_with_no_evidence(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    _reviewed_workspace(runtime_path, datetime(2026, 7, 13, tzinfo=UTC))
    stored = json.loads(runtime_path.read_text(encoding="utf-8"))
    stored.pop("evidence")
    runtime_path.write_text(json.dumps(stored), encoding="utf-8")

    loaded = load_workspace(runtime_path, build_example_inventory())
    snapshot = apply_workspace_action({"action": "snapshot"}, runtime_path, now=EVIDENCE_NOW)

    assert loaded.evidence == []
    assert snapshot["collaboration"]["evidence"] == []
    assert [entry["event"] for entry in snapshot["collaboration"]["activity"]] == ["reviewed"]
    # Not archived: only the workspace and the lock file the snapshot held.
    assert sorted(tmp_path.iterdir()) == [runtime_path, tmp_path / "workspace.json.lock"]


def test_evidence_is_saved_per_system_obligation_and_actor_with_revisions(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    first = _evidence(runtime_path, owner="Owner A")
    assert _entry(first, "high-risk.provider.9")["revision"] == 1
    second = _evidence(runtime_path, state="evidence_attached", revision=1, owner="Owner A")

    entry = _entry(second, "high-risk.provider.9")
    assert (entry["state"], entry["storedState"], entry["revision"]) == (
        "evidence_attached",
        "evidence_attached",
        2,
    )
    assert (entry["owner"], entry["updatedBy"], entry["updatedAt"]) == (
        "Owner A",
        "Reviewer A",
        EVIDENCE_NOW.isoformat(),
    )
    assert _entry(_view(runtime_path), "high-risk.provider.9") == entry
    stored = load_workspace(runtime_path, build_example_inventory())
    assert len(stored.evidence) == 1
    assert stored.activity[-1] == {
        "event": "evidence_updated",
        "targetId": "evidence:credit-provider:high-risk.provider.9:provider",
        "actor": "Reviewer A",
        "state": "evidence_attached",
        "occurredAt": EVIDENCE_NOW.isoformat(),
    }


def test_evidence_rejects_a_stale_revision_as_a_conflict(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path)
    before = runtime_path.read_bytes()

    with pytest.raises(ValueError, match=r"^409 Conflict: stale evidence revision$"):
        _evidence(runtime_path, state="evidence_attached", revision=0)

    assert runtime_path.read_bytes() == before


def test_evidence_keys_do_not_collide_across_systems_and_actors(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    deployer_profile = {**COCKPIT_CREDIT, "roles": ["provider", "deployer"]}
    _evidence(runtime_path, profile=deployer_profile, obligation_id="literacy.provider.4")
    deployer = next(
        item.obligation_id
        for item in classify(SystemProfile.model_validate(deployer_profile)).obligation_graph
        if item.actor.value == "deployer"
    )
    _evidence(runtime_path, profile=deployer_profile, obligation_id=deployer, actor="deployer")
    _evidence(
        runtime_path,
        system_id="chatbot",
        profile=COCKPIT_CHATBOT,
        obligation_id="transparency.1",
        state="reviewed",
        reviewed_on="2026-11-01",
    )

    stored = load_workspace(runtime_path, build_example_inventory())
    assert [record.key() for record in stored.evidence] == [
        ("credit-provider", "literacy.provider.4", "provider"),
        ("credit-provider", deployer, "deployer"),
        ("chatbot", "transparency.1", "provider"),
    ]
    credit = _view(runtime_path, deployer_profile)
    assert credit["counts"]["in_progress"] == 2
    assert credit["orphanedRecords"] == []
    chatbot = _view(runtime_path, COCKPIT_CHATBOT, "chatbot")
    assert chatbot["counts"]["reviewed"] == 1
    assert chatbot["orphanedRecords"] == []


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"state": "stale"}, "stale is derived"),
        ({"state": "done"}, "validation error"),
        ({"system_id": "new"}, "the blank intake keeps no evidence"),
        ({"system_id": "../x"}, "systemId is not a cockpit system id"),
        ({"system_id": "a:b"}, "systemId is not a cockpit system id"),
        ({"obligation_id": "high-risk.provider.999"}, "unknown obligation graph item"),
        ({"actor": "lawyer"}, "unknown obligation graph item"),
        ({"reviewed_on": "2026-13-01"}, "validation error"),
        ({"owner": "x" * 121}, "validation error"),
        ({"owner": 7}, "owner must be text"),
        ({"reviewed_on": ["2026-11-01"]}, "reviewedOn must be text"),
        ({"profile": "CreditSightScore"}, "profile must be a JSON object"),
    ],
)
def test_evidence_rejects_invalid_input(tmp_path, changes: dict, message: str) -> None:
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path, obligation_id="high-risk.provider.10")
    before = runtime_path.read_bytes()

    with pytest.raises(ValueError, match=message):
        _evidence(runtime_path, **changes)

    assert runtime_path.read_bytes() == before


@pytest.fixture
def local_zone(monkeypatch):
    """Set the process's local time zone for one test and restore it afterwards."""

    if not hasattr(time, "tzset"):
        pytest.skip("time.tzset is not available on this platform")

    def set_zone(zone: str, offset_hours: int) -> None:
        monkeypatch.setenv("TZ", zone)
        time.tzset()
        if datetime(2026, 11, 18, tzinfo=UTC).astimezone().utcoffset() != timedelta(
            hours=offset_hours
        ):
            pytest.skip(f"time zone {zone} is not installed")

    yield set_zone
    monkeypatch.undo()
    time.tzset()


def test_reviewed_evidence_needs_a_date_not_after_the_bridge_date(tmp_path, local_zone) -> None:
    local_zone("UTC", 0)
    runtime_path = tmp_path / "workspace.json"
    with pytest.raises(ValueError, match="a reviewed item needs a reviewed-on date"):
        _evidence(runtime_path, state="reviewed")
    with pytest.raises(ValueError, match="reviewedOn must not be after the current date"):
        _evidence(runtime_path, state="reviewed", reviewed_on="2026-11-18")
    assert (
        not runtime_path.exists()
        or load_workspace(runtime_path, build_example_inventory()).evidence == []
    )

    view = _evidence(runtime_path, state="reviewed", reviewed_on="2026-11-17")
    assert _entry(view, "high-risk.provider.9")["state"] == "reviewed"


def test_the_future_date_check_uses_the_bridge_local_date(tmp_path, local_zone) -> None:
    # The cockpit's date input gives the reviewer's local day. At 23:30 UTC it is
    # already the next day in Tokyo: that day is today there, not a future date.
    local_zone("Asia/Tokyo", 9)
    runtime_path = tmp_path / "workspace.json"
    late_utc = datetime(2026, 11, 18, 23, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="reviewedOn must not be after the current date"):
        _evidence(runtime_path, state="reviewed", reviewed_on="2026-11-20", now=late_utc)
    view = _evidence(runtime_path, state="reviewed", reviewed_on="2026-11-19", now=late_utc)

    assert _entry(view, "high-risk.provider.9")["reviewedOn"] == "2026-11-19"


def test_two_concurrent_saves_of_one_row_give_one_conflict(tmp_path, monkeypatch) -> None:
    # Both requests hold revision 1. Without the workspace lock both read revision 1,
    # both passed the check and both saved, and one write was lost without a 409.
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path)
    barrier = threading.Barrier(2, timeout=0.5)
    real_load = collaboration_module._load_or_recover

    def load_then_meet(*args):
        workspace = real_load(*args)
        # Unlocked, both threads meet here holding revision 1. Locked, the second
        # cannot load until the first has saved, so the wait times out instead.
        with contextlib.suppress(threading.BrokenBarrierError):
            barrier.wait()
        return workspace

    monkeypatch.setattr(collaboration_module, "_load_or_recover", load_then_meet)
    outcomes: list[str] = []

    def save(owner: str) -> None:
        try:
            _evidence(runtime_path, state="evidence_attached", revision=1, owner=owner)
            outcomes.append("saved")
        except ValueError as error:
            outcomes.append(str(error))

    threads = [threading.Thread(target=save, args=(owner,)) for owner in ("A", "B")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sorted(outcomes) == ["409 Conflict: stale evidence revision", "saved"]
    stored = load_workspace(runtime_path, build_example_inventory())
    assert [record.revision for record in stored.evidence] == [2]
    assert [entry["event"] for entry in stored.activity] == ["evidence_updated"] * 2


def test_evidence_owner_is_trimmed_and_a_blank_owner_cleared(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    view = _evidence(runtime_path, owner="  Owner A  ", reviewed_on="")
    entry = _entry(view, "high-risk.provider.9")
    assert (entry["owner"], entry["reviewedOn"]) == ("Owner A", None)

    view = _evidence(runtime_path, owner="   ", revision=1)
    assert _entry(view, "high-risk.provider.9")["owner"] is None


def test_a_changed_profile_marks_items_stale_with_reasons(tmp_path) -> None:
    # Answering the Art. 111(2) significant-change question changes the report and,
    # of the items, only the Art. 111(2) item.
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path, obligation_id="high-risk.provider.9")
    _evidence(runtime_path, obligation_id="high-risk.provider.111.2", state="evidence_attached")
    unchanged = _view(runtime_path)
    assert unchanged["counts"]["stale"] == 0

    changed = _view(
        runtime_path, {**COCKPIT_CREDIT, "significant_change_after_application_date": False}
    )

    assert changed["reportDigest"] != unchanged["reportDigest"]
    art_9 = _entry(changed, "high-risk.provider.9")
    art_111 = _entry(changed, "high-risk.provider.111.2")
    assert (art_9["state"], art_9["storedState"], art_9["staleReasons"]) == (
        "stale",
        "in_progress",
        ["report_changed"],
    )
    assert (art_111["state"], art_111["staleReasons"]) == (
        "stale",
        ["report_changed", "item_changed"],
    )
    assert changed["counts"]["stale"] == 2
    # Saving the row again stores the current digests and clears the reasons.
    resaved = _evidence(
        runtime_path,
        profile={**COCKPIT_CREDIT, "significant_change_after_application_date": False},
        revision=1,
    )
    assert _entry(resaved, "high-risk.provider.9")["staleReasons"] == []


def test_a_removed_item_is_listed_as_orphaned_and_kept(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path, obligation_id="high-risk.provider.111.2", owner="Owner A")

    view = _view(runtime_path, {**COCKPIT_CREDIT, "placing_on_market_date": None})

    assert [record["obligationId"] for record in view["orphanedRecords"]] == [
        "high-risk.provider.111.2"
    ]
    assert len(load_workspace(runtime_path, build_example_inventory()).evidence) == 1


def test_entering_an_assessment_date_does_not_stale_evidence(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path)

    view = _view(runtime_path, {**COCKPIT_CREDIT, "assessment_date": "2026-11-17"})

    assert view["assessmentDate"] == "2026-11-17"
    assert view["counts"]["stale"] == 0
    assert _entry(view, "high-risk.provider.9")["state"] == "in_progress"


def test_an_old_reviewed_on_date_marks_the_item_stale(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    old = _evidence(runtime_path, state="reviewed", reviewed_on="2026-10-01")
    entry = _entry(old, "high-risk.provider.9")
    assert entry["sourceRetrievedOn"] == "2026-10-18"
    assert (entry["state"], entry["staleReasons"]) == (
        "stale",
        ["reviewed_before_source_retrieval"],
    )

    same_day = _evidence(runtime_path, state="reviewed", reviewed_on="2026-10-18", revision=1)
    assert _entry(same_day, "high-risk.provider.9")["state"] == "reviewed"


def test_evidence_view_saves_nothing(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path)
    before = runtime_path.read_bytes()

    view = _view(runtime_path)

    assert runtime_path.read_bytes() == before
    assert view["draftNotice"] == DRAFT_NOTICE
    assert not (tmp_path / "fresh.json").exists()
    _view(tmp_path / "fresh.json")
    assert not (tmp_path / "fresh.json").exists()


@pytest.mark.parametrize("stored", ["unreadable", "stale"])
def test_evidence_view_leaves_an_unusable_store_untouched(tmp_path, stored: str) -> None:
    # evidence_view only reads: it neither archives nor rewrites the store. The next
    # saving action recovers it as before.
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path, owner="Owner A")
    if stored == "unreadable":
        runtime_path.write_text(TRUNCATED, encoding="utf-8")
    else:
        data = json.loads(runtime_path.read_text(encoding="utf-8"))
        data["inventory_digest"] = "0" * 64
        runtime_path.write_text(json.dumps(data), encoding="utf-8")
    before = runtime_path.read_bytes()
    listing = sorted(tmp_path.iterdir())

    view = _view(runtime_path)

    assert runtime_path.read_bytes() == before
    assert sorted(tmp_path.iterdir()) == listing
    assert view["orphanedRecords"] == []
    total = sum(len(lane["items"]) for lane in view["lanes"])
    entry = _entry(view, "high-risk.provider.9")
    if stored == "unreadable":
        # Recovery carries nothing from an unreadable file, so the view shows nothing.
        assert view["counts"]["not_started"] == total
        assert entry["revision"] == 0
    else:
        # Recovery carries a stale file's evidence, so the view shows it: a save based
        # on the view is checked against the same revision.
        assert view["counts"]["not_started"] == total - 1
        assert (entry["owner"], entry["revision"]) == ("Owner A", 1)
        saved = _evidence(runtime_path, owner="Owner B", revision=entry["revision"])
        assert _entry(saved, "high-risk.provider.9")["owner"] == "Owner B"


def test_recovery_goes_on_when_another_process_archived_the_file_first(
    tmp_path, monkeypatch
) -> None:
    runtime_path = tmp_path / "workspace.json"
    runtime_path.write_text(TRUNCATED, encoding="utf-8")
    real_archive_path = collaboration_module._archive_path

    def moved_meanwhile(path: Path, reason: str, now: datetime) -> Path:
        candidate = real_archive_path(path, reason, now)
        path.rename(tmp_path / "set-aside-by-another-process.json")
        return candidate

    monkeypatch.setattr(collaboration_module, "_archive_path", moved_meanwhile)

    snapshot = apply_workspace_action({"action": "snapshot"}, runtime_path, now=EVIDENCE_NOW)

    assert [entry["event"] for entry in snapshot["collaboration"]["activity"]] == ["recovered"]
    stored = load_workspace(runtime_path, build_example_inventory())
    assert stored.activity == snapshot["collaboration"]["activity"]


def test_a_lone_surrogate_in_profile_text_still_gives_a_view(tmp_path) -> None:
    # The engine copies intended_purpose_source into the report; JSON "\ud800" parses
    # to a lone surrogate, which plain UTF-8 encoding of the digest input refused.
    runtime_path = tmp_path / "workspace.json"
    profile = {**COCKPIT_CREDIT, "intended_purpose_source": "Brief \ud800"}

    view = _view(runtime_path, profile)
    saved = _evidence(runtime_path, profile=profile)

    assert len(view["reportDigest"]) == 64
    assert saved["reportDigest"] == view["reportDigest"]
    assert _entry(saved, "high-risk.provider.9")["state"] == "in_progress"


def test_evidence_survives_a_stale_workspace_recovery(tmp_path, monkeypatch) -> None:
    shutil.copytree(ROOT / "examples", tmp_path / "examples")
    monkeypatch.chdir(tmp_path)
    runtime_path = Path("runtime-data/collaboration-workspace.json")
    _reviewed_workspace(runtime_path, datetime(2026, 7, 13, tzinfo=UTC))
    _evidence(runtime_path, owner="Owner A")
    stored_before = runtime_path.read_text(encoding="utf-8")
    spam_filter = Path("examples/spam_filter.json")
    profile = json.loads(spam_filter.read_text(encoding="utf-8"))
    spam_filter.write_text(json.dumps({**profile, "name": "InboxGuard 2"}), encoding="utf-8")

    snapshot = apply_workspace_action(
        {"action": "snapshot"}, runtime_path, now=datetime(2026, 11, 17, 11, 0, tzinfo=UTC)
    )

    archive = Path("runtime-data/collaboration-workspace.stale-20261117T110000Z.json")
    assert archive.read_text(encoding="utf-8") == stored_before
    assert snapshot["collaboration"]["activity"] == [
        {
            "event": "recovered",
            "reason": "stale",
            "archivedAs": archive.name,
            "occurredAt": "2026-11-17T11:00:00+00:00",
            "evidenceCarried": "1",
        }
    ]
    assert all(cell["revision"] == 1 for cell in snapshot["collaboration"]["cells"])
    assert all(cell["reviewer"] is None for cell in snapshot["collaboration"]["cells"])
    assert [record["owner"] for record in snapshot["collaboration"]["evidence"]] == ["Owner A"]
    assert _entry(_view(runtime_path), "high-risk.provider.9")["revision"] == 1


def test_import_without_evidence_keeps_the_current_evidence(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path)
    blank = build_collaboration_workspace()["collaboration"]
    blank.pop("evidence")

    imported = apply_workspace_action(
        {"action": "import", "workspace": blank}, runtime_path, now=EVIDENCE_NOW
    )

    assert [record["obligation_id"] for record in imported["collaboration"]["evidence"]] == [
        "high-risk.provider.9"
    ]


def test_import_with_evidence_replaces_it(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    exported = _evidence(runtime_path, obligation_id="high-risk.provider.10")
    assert exported["counts"]["in_progress"] == 1
    file = apply_workspace_action({"action": "snapshot"}, runtime_path)["collaboration"]
    _evidence(runtime_path, obligation_id="high-risk.provider.9")

    imported = apply_workspace_action(
        {"action": "import", "workspace": file}, runtime_path, now=EVIDENCE_NOW
    )
    assert [record["obligation_id"] for record in imported["collaboration"]["evidence"]] == [
        "high-risk.provider.10"
    ]

    emptied = apply_workspace_action(
        {"action": "import", "workspace": {**file, "evidence": []}}, runtime_path, now=EVIDENCE_NOW
    )
    assert emptied["collaboration"]["evidence"] == []


def test_import_ignores_a_draft_notice_key(tmp_path) -> None:
    # The self-assessment page's export puts draftNotice first in the file.
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path)
    collaboration = apply_workspace_action({"action": "snapshot"}, runtime_path)["collaboration"]
    exported = {"draftNotice": DRAFT_NOTICE, **collaboration}

    imported = apply_workspace_action(
        {"action": "import", "workspace": exported}, runtime_path, now=EVIDENCE_NOW
    )

    assert "draftNotice" not in imported["collaboration"]
    assert len(imported["collaboration"]["evidence"]) == 1
    assert "draftNotice" not in json.loads(runtime_path.read_text(encoding="utf-8"))


def test_duplicate_evidence_records_make_a_stored_file_unreadable(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    _evidence(runtime_path)
    stored = json.loads(runtime_path.read_text(encoding="utf-8"))
    stored["evidence"].append(dict(stored["evidence"][0]))
    runtime_path.write_text(json.dumps(stored), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate evidence record"):
        load_workspace(runtime_path, build_example_inventory())
    snapshot = apply_workspace_action({"action": "snapshot"}, runtime_path, now=EVIDENCE_NOW)
    assert [entry["reason"] for entry in snapshot["collaboration"]["activity"]] == ["unreadable"]
    assert "evidenceCarried" not in snapshot["collaboration"]["activity"][0]
    assert snapshot["collaboration"]["evidence"] == []


def test_evidence_leaves_cells_workflows_and_portal_unchanged(tmp_path) -> None:
    runtime_path = tmp_path / "workspace.json"
    before = apply_workspace_action({"action": "snapshot"}, runtime_path, now=EVIDENCE_NOW)
    _evidence(runtime_path)

    after = apply_workspace_action({"action": "snapshot"}, runtime_path, now=EVIDENCE_NOW)

    for key in ("workflowDefinitions", "workflowRuns", "selfAssessmentPortal"):
        assert after[key] == before[key]
    assert after["collaboration"]["cells"] == before["collaboration"]["cells"]
    assert after["collaboration"]["inventory_digest"] == before["collaboration"]["inventory_digest"]
    assert len(after["collaboration"]["evidence"]) == 1


def test_snapshot_carries_the_draft_notice() -> None:
    snapshot = build_collaboration_workspace()
    assert snapshot["draftNotice"] == DRAFT_NOTICE
    assert snapshot["collaboration"]["evidence"] == []


def test_a_save_waits_for_a_reader_that_briefly_blocks_the_replace(tmp_path, monkeypatch) -> None:
    # On Windows an open reader (an unlocked evidence_view) makes os.replace fail with
    # PermissionError for the length of one read; the save retries instead of failing.
    runtime_path = tmp_path / "workspace.json"
    real_replace = os.replace
    failures = iter([True, True])

    def busy_then_free(source, target):
        if next(failures, False):
            raise PermissionError(13, "The process cannot access the file")
        real_replace(source, target)

    monkeypatch.setattr(collaboration_module, "_REPLACE_PAUSE", 0)
    monkeypatch.setattr(collaboration_module.os, "replace", busy_then_free)
    _evidence(runtime_path, owner="Owner A")

    assert _entry(_view(runtime_path), "high-risk.provider.9")["owner"] == "Owner A"


def test_a_replace_that_stays_blocked_still_fails(tmp_path, monkeypatch) -> None:
    runtime_path = tmp_path / "workspace.json"
    calls: list[object] = []

    def always_busy(source, target):
        calls.append(target)
        raise PermissionError(13, "The process cannot access the file")

    monkeypatch.setattr(collaboration_module, "_REPLACE_PAUSE", 0)
    monkeypatch.setattr(collaboration_module.os, "replace", always_busy)
    with pytest.raises(PermissionError):
        _evidence(runtime_path, owner="Owner A")
    assert len(calls) == collaboration_module._REPLACE_ATTEMPTS
    assert not runtime_path.exists()
    assert not list(tmp_path.glob(".workspace.json.*.tmp"))
