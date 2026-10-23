from __future__ import annotations

import io
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import eu_ai_act_classifier.inventory as inventory_module
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
            return clock[0]

    # inventory._now() stamps generatedAt from this module-level datetime.
    monkeypatch.setattr(inventory_module, "datetime", SteppedClock)

    target = _run_local_api(monkeypatch, capsys, "collaboration")["collaboration"]["cells"][0]
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
    locked_cell = next(
        cell
        for cell in locked["collaboration"]["cells"]
        if cell["target_id"] == target["target_id"]
    )
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

    workspace = commented["collaboration"]
    cell = next(cell for cell in workspace["cells"] if cell["target_id"] == target["target_id"])
    assert (cell["revision"], cell["locked_by"]) == (3, "Local reviewer")
    assert [comment["body"] for comment in cell["comments"]] == [
        "Confirm the factor evidence against approved sources."
    ]
    assert workspace["inventory_digest"] == locked["collaboration"]["inventory_digest"]
    stored = Path("runtime-data/collaboration-workspace.json").read_text(encoding="utf-8")
    assert json.loads(stored) == workspace
