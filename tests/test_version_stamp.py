"""Every report names the classifier version that produced it (AIA-30).

`eu-ai-act-classify --version` prints the version, and `classifier_version` carries it in
the JSON report, in the local API's report and dossier, and in the dossier files. The
expected value is the version in `pyproject.toml`, the one the wheel and PyPI carry.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from eu_ai_act_classifier import SystemProfile, __version__, classify
from eu_ai_act_classifier.cli import main
from eu_ai_act_classifier.dossier import write_review_dossier
from eu_ai_act_classifier.local_api import classify_payload, dossier_payload
from eu_ai_act_classifier.schemas import schema

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "credit_scoring.json"
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
VERSION = PYPROJECT["project"]["version"]


def _example_report():
    return classify(SystemProfile.model_validate_json(EXAMPLE.read_text(encoding="utf-8")))


def test_package_version_is_the_distribution_version() -> None:
    assert __version__ == VERSION


def test_version_flag_prints_the_distribution_name_and_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exited:
        main(["--version"])

    assert exited.value.code == 0
    assert capsys.readouterr().out == f"{PYPROJECT['project']['name']} {VERSION}\n"


def test_report_names_the_classifier_version() -> None:
    assert classify(SystemProfile(name="x")).classifier_version == VERSION
    assert _example_report().classifier_version == VERSION


def test_cli_json_report_names_the_classifier_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([str(EXAMPLE), "--json"]) == 0

    assert json.loads(capsys.readouterr().out)["classifier_version"] == VERSION


def test_local_api_report_and_dossier_name_the_classifier_version() -> None:
    assert classify_payload({"profile": {"name": "x"}})["classifier_version"] == VERSION

    dossier = dossier_payload({"profile": {"name": "x"}})
    assert dossier["classification_report"]["classifier_version"] == VERSION


def test_dossier_files_name_the_classifier_version(tmp_path: Path) -> None:
    write_review_dossier(tmp_path, _example_report())

    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    dossier = json.loads((tmp_path / "dossier.json").read_text(encoding="utf-8"))
    assert report["classifier_version"] == VERSION
    assert dossier["classification_report"]["classifier_version"] == VERSION


def test_report_schema_requires_the_classifier_version() -> None:
    report_schema = schema("report")

    assert "classifier_version" in report_schema["required"]
    assert report_schema["properties"]["classifier_version"]["type"] == "string"
