from __future__ import annotations

import io
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

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
