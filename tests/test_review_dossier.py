from __future__ import annotations

import json
from pathlib import Path

from eu_ai_act_classifier import SystemProfile, classify
from eu_ai_act_classifier.cli import main
from eu_ai_act_classifier.dossier import (
    REVIEW_DOSSIER_SCHEMA,
    build_review_dossier,
    render_review_dossier_markdown,
    write_review_dossier,
)


def _credit_report():
    profile = SystemProfile.model_validate_json(
        Path("examples/credit_scoring.json").read_text(encoding="utf-8")
    )
    return classify(profile)


def test_review_dossier_bundles_classification_sources_and_artifacts() -> None:
    dossier = build_review_dossier(_credit_report())

    assert dossier.schema_id == REVIEW_DOSSIER_SCHEMA
    assert dossier.system == "CreditSightScore"
    assert dossier.risk_tier == "high_risk"
    assert dossier.classification_report.system == dossier.system
    assert dossier.obligation_graph
    assert dossier.source_manifest
    assert dossier.source_summary["binding_level_1"] >= 1
    assert {artifact.name for artifact in dossier.artifacts} >= {"fria", "annex-iv-checklist"}
    assert all(artifact.draft_only for artifact in dossier.artifacts)
    assert all("Draft only" in artifact.content for artifact in dossier.artifacts)


def test_review_dossier_markdown_is_review_gated() -> None:
    markdown = render_review_dossier_markdown(build_review_dossier(_credit_report()))

    assert "EU AI Act Review Dossier: CreditSightScore" in markdown
    assert "draft_only_human_review_required" in markdown
    assert "Legal reviewer to approve source status" in markdown
    assert "\u2014" not in markdown
    assert "\u2013" not in markdown


def test_review_dossier_writer_emits_expected_bundle(tmp_path) -> None:
    paths = write_review_dossier(tmp_path, _credit_report())
    names = {path.relative_to(tmp_path).as_posix() for path in paths}

    assert "dossier.md" in names
    assert "dossier.json" in names
    assert "report.json" in names
    assert "source_manifest.json" in names
    assert "open_questions.json" in names
    assert "artifacts/fria.md" in names
    report_json = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report_json["system"] == "CreditSightScore"


def test_cli_dossier_dir_writes_review_bundle(tmp_path) -> None:
    assert main(["examples/credit_scoring.json", "--dossier-dir", str(tmp_path)]) == 0

    assert (tmp_path / "dossier.md").exists()
    assert (tmp_path / "artifacts" / "fria.md").exists()
