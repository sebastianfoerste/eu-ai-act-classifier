from __future__ import annotations

import io
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

import eu_ai_act_classifier.collaboration_workspace as collaboration_workspace_module
import eu_ai_act_classifier.inventory as inventory_module
from eu_ai_act_classifier import SystemProfile, classify
from eu_ai_act_classifier.artifacts import write_artifacts
from eu_ai_act_classifier.local_api import (
    artifacts_payload,
    classify_payload,
    dossier_payload,
    main,
    schema_payload,
    sources_payload,
)

ROOT = Path(__file__).resolve().parents[1]


def test_local_api_schema_exposes_cockpit_contract() -> None:
    schema = schema_payload()

    assert "provider" in schema["roles"]
    assert schema["annex_i_sections"] == ["A", "B"]
    assert {"5.1.ba", "5.1.bb"} <= set(schema["prohibited_practices"])
    assert "fria" in schema["artifacts"]
    assert schema["dossier_schema"] == "eu-ai-act.review-dossier.v1"
    assert schema["review_posture"] == "draft_only_human_review_required"


def test_local_api_classify_returns_report_json() -> None:
    payload = classify_payload({"profile": {"name": "x"}})

    assert payload["system"] == "x"
    assert payload["scope"]["status"] == "in_scope"


def test_local_api_artifacts_preview_is_draft_only() -> None:
    payload = artifacts_payload({"profile": {"name": "x"}, "artifact": "fria"})

    assert payload["review_status"] == "draft_only_human_review_required"
    assert payload["artifacts"][0]["name"] == "fria"
    assert "Draft only" in payload["artifacts"][0]["content"]
    assert payload["source_manifest"]


def test_local_api_sources_payload_keeps_legal_status_visible() -> None:
    payload = sources_payload()

    assert payload
    assert {source["legal_status"] for source in payload}
    assert all(source["url"].startswith("https://") for source in payload)


def test_local_api_artifacts_all_returns_named_review_pack() -> None:
    payload = artifacts_payload({"profile": {"name": "x"}, "artifact": "all"})

    artifact_names = {artifact["name"] for artifact in payload["artifacts"]}
    assert {"fria", "annex-iv-checklist"}.issubset(artifact_names)
    assert payload["review_status"] == "draft_only_human_review_required"


def test_local_api_artifact_filenames_are_the_ones_the_cli_writes(tmp_path) -> None:
    profile = {"name": "Provider A / CV screening (v2)"}

    payload = artifacts_payload({"profile": profile, "artifact": "all"})
    written = write_artifacts("all", tmp_path, classify(SystemProfile.model_validate(profile)))

    filenames = [artifact["filename"] for artifact in payload["artifacts"]]
    assert filenames == [path.name for path in written]
    assert "provider-a-cv-screening-v2.fria.md" in filenames
    assert not any("/" in name or " " in name for name in filenames)


def test_local_api_rejects_invalid_input_with_exit_2_and_a_json_error_line(
    monkeypatch, capsys
) -> None:
    # web/lib/bridge-error.ts answers HTTP 400 only for this exit code and stderr shape.
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"profile": {"roles": "bogus"}})))

    assert main(["classify"]) == 2

    out, err = capsys.readouterr()
    assert out == ""
    lines = err.strip().splitlines()
    assert len(lines) == 1
    assert "roles" in json.loads(lines[0])["error"].splitlines()


def test_local_api_dossier_returns_review_bundle() -> None:
    payload = dossier_payload({"profile": {"name": "x"}, "artifact": "fria"})

    assert payload["schema"] == "eu-ai-act.review-dossier.v1"
    assert payload["review_status"] == "draft_only_human_review_required"
    assert payload["classification_report"]["system"] == "x"
    assert payload["source_manifest"]
    assert payload["artifacts"][0]["name"] == "fria"


def test_local_api_dossier_all_is_a_single_authoritative_cockpit_snapshot() -> None:
    payload = dossier_payload({"profile": {"name": "Authoritative cockpit"}, "artifact": "all"})

    assert payload["classification_report"]["system"] == payload["system"]
    assert payload["source_manifest"] == payload["classification_report"]["source_manifest"]
    assert {artifact["name"] for artifact in payload["artifacts"]} >= {
        "fria",
        "annex-iv-checklist",
    }


def _run_local_api(
    monkeypatch, capsys, command: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    # Pipe the payload through stdin and read stdout, as web/lib/python.ts does.
    monkeypatch.setattr("sys.stdin", io.StringIO("" if payload is None else json.dumps(payload)))
    code = main([command])
    out, err = capsys.readouterr()
    assert (code, err) == (0, ""), err
    return json.loads(out)


def _cell(result: dict[str, Any], target_id: str) -> dict[str, Any]:
    return next(cell for cell in result["collaboration"]["cells"] if cell["target_id"] == target_id)


def test_local_api_collaboration_survives_a_clock_tick_between_actions(
    tmp_path, monkeypatch, capsys
) -> None:
    # The cockpit runs the bridge from the repository root and injects no clock, so
    # every action rebuilds the inventory stamped with the current second. A tick
    # between two actions used to make the saved workspace stale.
    shutil.copytree(ROOT / "examples", tmp_path / "examples")
    monkeypatch.chdir(tmp_path)
    clock = [datetime(2026, 7, 13, 9, 0, 0, tzinfo=UTC)]

    class SteppedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            # Same contract as datetime.now: aware in tz, or naive local time without one.
            current = clock[0].astimezone(tz)
            return current if tz is not None else current.replace(tzinfo=None)

    # inventory._now() stamps generatedAt and apply_workspace_action stamps the
    # actions from these module-level datetime names. Swapping the class rather
    # than _now keeps _now's own formatting in the path.
    monkeypatch.setattr(inventory_module, "datetime", SteppedClock)
    monkeypatch.setattr(collaboration_workspace_module, "datetime", SteppedClock)

    cells = _run_local_api(monkeypatch, capsys, "collaboration")["collaboration"]["cells"]
    assert cells, "the copied examples/ produced no collaboration cells"
    target = cells[0]
    locked = _run_local_api(
        monkeypatch,
        capsys,
        "collaboration",
        {
            "action": "lock",
            "targetId": target["target_id"],
            "expectedRevision": target["revision"],
            "actor": "Local reviewer",
        },
    )
    locked_cell = _cell(locked, target["target_id"])
    assert (locked_cell["revision"], locked_cell["locked_by"]) == (
        target["revision"] + 1,
        "Local reviewer",
    )
    assert locked_cell["lock_expires_at"] == "2026-07-13T09:15:00+00:00"
    assert _run_local_api(monkeypatch, capsys, "inventory")["generatedAt"] == (
        "2026-07-13T09:00:00+00:00"
    )

    clock[0] += timedelta(seconds=1)
    assert _run_local_api(monkeypatch, capsys, "inventory")["generatedAt"] == (
        "2026-07-13T09:00:01+00:00"
    )
    commented = _run_local_api(
        monkeypatch,
        capsys,
        "collaboration",
        {
            "action": "comment",
            "targetId": target["target_id"],
            "expectedRevision": locked_cell["revision"],
            "actor": "Local reviewer",
            "body": "Confirm the factor evidence against approved sources.",
        },
    )

    cell = _cell(commented, target["target_id"])
    assert (cell["revision"], cell["locked_by"]) == (
        locked_cell["revision"] + 1,
        "Local reviewer",
    )
    assert [(comment["body"], comment["created_at"]) for comment in cell["comments"]] == [
        ("Confirm the factor evidence against approved sources.", "2026-07-13T09:00:01+00:00")
    ]
    stored = Path("runtime-data/collaboration-workspace.json").read_text(encoding="utf-8")
    assert json.loads(stored) == commented["collaboration"]

    # A page load after the tick reads the stored workspace back with the comment.
    snapshot = _run_local_api(monkeypatch, capsys, "collaboration")
    assert _cell(snapshot, target["target_id"]) == cell


def _run_local_api_error(
    monkeypatch, capsys, command: str, payload: dict[str, Any]
) -> tuple[int, str]:
    # A failing run: nothing on stdout and exactly one JSON line on stderr.
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    code = main([command])
    out, err = capsys.readouterr()
    assert out == ""
    lines = err.strip().splitlines()
    assert len(lines) == 1, err
    return code, json.loads(lines[0])["error"]


def test_local_api_validation_error_names_the_field_but_not_the_value(monkeypatch, capsys) -> None:
    # Pydantic's message carried the rejected value (input_value=...) and a docs link,
    # and the cockpit returned it to the HTTP client (AIA-21).
    code, error = _run_local_api_error(
        monkeypatch,
        capsys,
        "classify",
        {"profile": {"name": "Confidential system", "roles": "bogus-SECRET-VALUE"}},
    )

    assert code == 2
    assert error == "1 validation error for SystemProfile\nroles\n  Input should be a valid list"
    assert "SECRET" not in error
    assert "input_value" not in error
    assert "errors.pydantic.dev" not in error


def test_local_api_counts_every_validation_error(monkeypatch, capsys) -> None:
    code, error = _run_local_api_error(
        monkeypatch,
        capsys,
        "classify",
        {"profile": {"name": "x", "roles": "bogus", "placing_on_market_date": "13.07.2026"}},
    )

    assert code == 2
    assert error.splitlines()[0] == "2 validation errors for SystemProfile"
    assert "bogus" not in error
    assert "13.07.2026" not in error


def test_local_api_internal_failure_prints_a_generic_error_without_traceback(
    monkeypatch, capsys
) -> None:
    # Any exception other than invalid input printed a traceback, with absolute paths and
    # the failing values, which the cockpit passed on to the HTTP client (AIA-21).
    def crash(*args, **kwargs):
        raise RuntimeError(f"boom in {ROOT} with SECRET-VALUE")

    monkeypatch.setattr("eu_ai_act_classifier.local_api.classify", crash)

    code, error = _run_local_api_error(monkeypatch, capsys, "classify", {"profile": {"name": "x"}})

    assert code == 1
    assert error == "the classifier bridge failed"


def _collaboration_checkout(tmp_path, monkeypatch) -> None:
    # The cockpit runs the bridge from the repository root, where examples/ and
    # runtime-data/ live.
    shutil.copytree(ROOT / "examples", tmp_path / "examples")
    monkeypatch.chdir(tmp_path)


@pytest.mark.parametrize("revision", [{}, [1], "two-SECRET", None])
def test_local_api_collaboration_rejects_a_revision_that_is_not_a_number(
    revision, tmp_path, monkeypatch, capsys
) -> None:
    # The audit's probe: expectedRevision {} raised TypeError and printed a traceback.
    _collaboration_checkout(tmp_path, monkeypatch)
    target = _run_local_api(monkeypatch, capsys, "collaboration")["collaboration"]["cells"][0]

    code, error = _run_local_api_error(
        monkeypatch,
        capsys,
        "collaboration",
        {"action": "lock", "targetId": target["target_id"], "expectedRevision": revision},
    )

    assert (code, error) == (2, "expectedRevision must be an integer")


def test_local_api_collaboration_rejects_answers_that_are_not_an_object(
    tmp_path, monkeypatch, capsys
) -> None:
    _collaboration_checkout(tmp_path, monkeypatch)

    code, error = _run_local_api_error(
        monkeypatch, capsys, "collaboration", {"action": "self_assess", "answers": 7}
    )

    assert (code, error) == (2, "answers must be a JSON object")


def test_local_api_review_of_an_imported_naive_lock_answers_409(
    tmp_path, monkeypatch, capsys
) -> None:
    # The audit's probe: a workspace imported with a naive lock_expires_at made the
    # next review raise TypeError (AIA-26), which escaped as a traceback (AIA-21).
    _collaboration_checkout(tmp_path, monkeypatch)
    collaboration = _run_local_api(monkeypatch, capsys, "collaboration")["collaboration"]
    target = collaboration["cells"][0]
    locked = {
        **target,
        "revision": 2,
        "locked_by": "Reviewer A",
        "lock_expires_at": "2999-01-01T00:00:00",
    }
    exported = {**collaboration, "cells": [locked, *collaboration["cells"][1:]]}
    _run_local_api(
        monkeypatch, capsys, "collaboration", {"action": "import", "workspace": exported}
    )

    code, error = _run_local_api_error(
        monkeypatch,
        capsys,
        "collaboration",
        {
            "action": "review",
            "targetId": target["target_id"],
            "expectedRevision": 2,
            "actor": "Reviewer B",
            "reviewerOverride": "human_review_required",
        },
    )

    assert (code, error) == (2, "409 Conflict: review cell is locked by Reviewer A")


def test_local_api_collaboration_recovers_from_a_truncated_store(
    tmp_path, monkeypatch, capsys
) -> None:
    # A half-written store made every cockpit page load fail until the file was
    # deleted by hand (AIA-22).
    _collaboration_checkout(tmp_path, monkeypatch)
    store = Path("runtime-data/collaboration-workspace.json")
    store.parent.mkdir()
    store.write_text('{"schema": "review.collaboration.v1", "cells": [', encoding="utf-8")

    snapshot = _run_local_api(monkeypatch, capsys, "collaboration")

    [recovered] = snapshot["collaboration"]["activity"]
    assert (recovered["event"], recovered["reason"]) == ("recovered", "unreadable")
    assert (store.parent / recovered["archivedAs"]).read_text(encoding="utf-8") == (
        '{"schema": "review.collaboration.v1", "cells": ['
    )
    assert json.loads(store.read_text(encoding="utf-8")) == snapshot["collaboration"]
