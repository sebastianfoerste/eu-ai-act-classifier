from __future__ import annotations

from eu_ai_act_classifier.local_api import (
    artifacts_payload,
    classify_payload,
    dossier_payload,
    schema_payload,
    sources_payload,
)


def test_local_api_schema_exposes_cockpit_contract() -> None:
    schema = schema_payload()

    assert "provider" in schema["roles"]
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
