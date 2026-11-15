"""Every error path of the CLI: readable messages, no documentation links, exit codes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eu_ai_act_classifier.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _write(tmp_path: Path, payload: object) -> str:
    path = tmp_path / "profile.json"
    text = payload if isinstance(payload, str) else json.dumps(payload)
    path.write_text(text, encoding="utf-8")
    return str(path)


def _validation_lines(capsys: pytest.CaptureFixture[str]) -> list[str]:
    err = capsys.readouterr().err
    lines = err.splitlines()
    assert lines[0] == "error: invalid SystemProfile:"
    assert "http" not in err and "errors.pydantic.dev" not in err
    return lines[1:]


def test_missing_profile_argument_prints_help_and_exits_2(capsys) -> None:
    assert main([]) == 2

    out, err = capsys.readouterr()
    assert "the following arguments are required: profile" in err
    assert out.startswith("usage: eu-ai-act-classify")


def test_unreadable_profile_file_exits_2(tmp_path, capsys) -> None:
    assert main([str(tmp_path / "missing.json")]) == 2

    err = capsys.readouterr().err
    assert err.startswith("error: cannot read profile: ")
    assert "missing.json" in err


def test_invalid_json_is_one_readable_line(tmp_path, capsys) -> None:
    assert main([_write(tmp_path, "{not json")]) == 2

    (line,) = _validation_lines(capsys)
    assert line.startswith("  profile: Invalid JSON")


def test_unknown_field_is_named_and_points_at_the_schema(tmp_path, capsys) -> None:
    assert main([_write(tmp_path, {"name": "x", "typo": 1})]) == 2

    (line,) = _validation_lines(capsys)
    assert line == "  typo: unknown field; `eu-ai-act-classify --schema profile` lists the fields"


def test_bad_date_shows_the_validator_message_without_the_pydantic_prefix(tmp_path, capsys) -> None:
    assert main([_write(tmp_path, {"name": "x", "placing_on_market_date": "March 2026"})]) == 2

    (line,) = _validation_lines(capsys)
    assert line == "  placing_on_market_date: must be an ISO date in YYYY-MM-DD form"


def test_enum_error_lists_the_allowed_values(tmp_path, capsys) -> None:
    profile = {"name": "x", "roles": ["bogus"], "annex_iii_area": "III.9"}
    assert main([_write(tmp_path, profile)]) == 2

    roles, area = _validation_lines(capsys)
    assert roles.startswith("  roles.0: allowed values: 'provider', 'deployer', ")
    assert roles.endswith("or 'gpai_provider' (got 'bogus')")
    assert area.startswith("  annex_iii_area: allowed values: 'III.1.a', ")
    assert "'III.unsure' (got 'III.9')" in area


def test_every_error_gets_its_own_line(tmp_path, capsys) -> None:
    profile = {"name": "x", "training_flops": "lots", "eu_nexus": "maybe", "extra": 0}
    assert main([_write(tmp_path, profile)]) == 2

    lines = _validation_lines(capsys)
    assert [line.split(":")[0].strip() for line in lines] == ["eu_nexus", "training_flops", "extra"]


def test_artifact_without_directory_exits_2(capsys) -> None:
    assert main([str(EXAMPLES / "credit_scoring.json"), "--artifact", "fria"]) == 2

    assert capsys.readouterr().err.startswith("error: --artifact requires --artifacts-dir")


def test_artifact_write_error_exits_2(tmp_path, capsys) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("", encoding="utf-8")

    argv = [str(EXAMPLES / "credit_scoring.json"), "--artifact", "fria"]
    assert main([*argv, "--artifacts-dir", str(blocker)]) == 2

    assert capsys.readouterr().err.startswith("error: cannot write artifacts: ")


def test_dossier_write_error_exits_2(tmp_path, capsys) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("", encoding="utf-8")

    assert main([str(EXAMPLES / "credit_scoring.json"), "--dossier-dir", str(blocker)]) == 2

    assert capsys.readouterr().err.startswith("error: cannot write dossier: ")


def test_written_paths_go_to_stderr_when_stdout_carries_json(tmp_path, capsys) -> None:
    argv = [
        str(EXAMPLES / "credit_scoring.json"),
        "--json",
        "--artifact",
        "fria",
        "--artifacts-dir",
        str(tmp_path / "artifacts"),
        "--dossier-dir",
        str(tmp_path / "dossier"),
    ]
    assert main(argv) == 0

    out, err = capsys.readouterr()
    assert json.loads(out)["system"] == "CreditSightScore"
    assert err.count("artifact: ") == 1 and err.count("dossier: ") >= 1


def test_written_paths_go_to_stdout_with_the_text_report(tmp_path, capsys) -> None:
    argv = [
        str(EXAMPLES / "credit_scoring.json"),
        "--artifact",
        "all",
        "--artifacts-dir",
        str(tmp_path / "artifacts"),
    ]
    assert main(argv) == 0

    out, err = capsys.readouterr()
    assert err == ""
    assert out.count("artifact: ") == 7
    assert out.startswith("EU AI Act classification: CreditSightScore")


@pytest.mark.parametrize(
    ("example", "code"),
    [
        pytest.param("social_scoring.json", 1, id="prohibited"),
        pytest.param("ambiguous_use_case.json", 1, id="requires-review"),
        pytest.param("credit_scoring.json", 0, id="determined"),
        pytest.param("spam_filter.json", 0, id="minimal"),
    ],
)
def test_strict_exit_codes(example: str, code: int, capsys) -> None:
    assert main([str(EXAMPLES / example), "--strict"]) == code
    assert main([str(EXAMPLES / example)]) == 0
    capsys.readouterr()


def test_schema_and_sources_flags_print_json(capsys) -> None:
    assert main(["--schema", "report"]) == 0
    report_schema = json.loads(capsys.readouterr().out)
    assert main([str(EXAMPLES / "spam_filter.json"), "--sources"]) == 0
    sources = json.loads(capsys.readouterr().out)

    assert "risk_tier" in report_schema["properties"]
    assert {source["legal_status"] for source in sources} >= {"binding_level_1"}
