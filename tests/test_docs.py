from __future__ import annotations

import re
from pathlib import Path

import pytest

from eu_ai_act_classifier import SystemProfile, classify, render_report
from eu_ai_act_classifier.artifacts import render_artifact
from eu_ai_act_classifier.cli import main

EXAMPLES = Path("examples")
README = Path("README.md")
EXAMPLES_README = EXAMPLES / "README.md"
CASE_STUDY = Path("CASE_STUDY.md")
CREDIT_SCORING = EXAMPLES / "credit_scoring.json"
CV_SCREENING = EXAMPLES / "cv_screening.json"
PACKET_MD = EXAMPLES / "classification-packet.md"
PACKET_JSON = EXAMPLES / "classification-packet.json"
PYPROJECT = Path("pyproject.toml")
PUBLIC_MARKDOWN = [
    README,
    EXAMPLES_README,
    Path("docs/DESIGN.md"),
    Path("docs/launch-readiness.md"),
    Path("docs/methodology.md"),
    Path("docs/reviewer-notes.md"),
    Path("docs/sample-output.md"),
]
EM_DASH = "\u2014"
EN_DASH = "\u2013"


def test_examples_readme_lists_every_json_example() -> None:
    example_docs = EXAMPLES_README.read_text(encoding="utf-8")

    for path in sorted(EXAMPLES.glob("*.json")):
        if path.name == "classification-packet.json":
            continue
        assert f"`{path.name}`" in example_docs


def test_readme_local_markdown_links_exist() -> None:
    readme = README.read_text(encoding="utf-8")
    markdown_links = re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", readme)

    for link in markdown_links:
        assert Path(link).exists(), f"README link target does not exist: {link}"


def test_launch_readiness_is_discoverable_from_readme() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "docs/launch-readiness.md" in readme


def test_python_version_is_consistent_in_public_metadata() -> None:
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    assert 'requires-python = ">=3.13"' in pyproject
    assert "Programming Language :: Python :: 3.13" in pyproject
    assert "Python 3.13+" in readme
    assert "Python 3." + "12+" not in readme


def test_public_markdown_avoids_em_and_en_dashes() -> None:
    for path in PUBLIC_MARKDOWN:
        text = path.read_text(encoding="utf-8")
        assert EM_DASH not in text, f"em dash found in {path}"
        assert EN_DASH not in text, f"en dash found in {path}"


def test_generated_public_text_avoids_em_and_en_dashes() -> None:
    report = classify(SystemProfile(name="x"))
    rendered = render_report(report)
    artifact = render_artifact("fria", report)

    for text in (rendered, artifact):
        assert EM_DASH not in text
        assert EN_DASH not in text


def test_mcp_guide_lists_the_tools_the_server_exposes() -> None:
    server = Path("src/eu_ai_act_classifier/mcp_server.py").read_text(encoding="utf-8")
    exposed = set(re.findall(r"@server\.tool\(\)\s+def (\w+)\(", server))
    guide = Path("docs/mcp-configuration-guide.md").read_text(encoding="utf-8")
    verification = guide[guide.index("## Verification") :]
    listed = set(re.findall(r"^\d+\. `(\w+)`", verification, re.M))
    assert exposed and listed == exposed
    assert "/Users/" not in guide


def _cli_output(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    assert main(list(argv)) == 0
    return capsys.readouterr().out


def test_committed_packet_markdown_matches_real_cli_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = _cli_output(capsys, str(CREDIT_SCORING))
    assert output == PACKET_MD.read_text(encoding="utf-8"), (
        f"{PACKET_MD} is stale; regenerate it with "
        f"`uv run eu-ai-act-classify {CREDIT_SCORING} > {PACKET_MD}`"
    )


def test_committed_packet_json_matches_real_cli_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = _cli_output(capsys, str(CREDIT_SCORING), "--json")
    assert output == PACKET_JSON.read_text(encoding="utf-8"), (
        f"{PACKET_JSON} is stale; regenerate it with "
        f"`uv run eu-ai-act-classify {CREDIT_SCORING} --json > {PACKET_JSON}`"
    )


def test_readme_states_the_real_line_count_of_the_demo_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    line_count = len(_cli_output(capsys, str(CREDIT_SCORING)).splitlines())
    readme = README.read_text(encoding="utf-8")
    assert f"of {line_count} lines" in readme


def test_case_study_quotes_a_prefix_of_the_real_cv_screening_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_study = CASE_STUDY.read_text(encoding="utf-8")
    match = re.search(
        rf"`uv run eu-ai-act-classify {re.escape(str(CV_SCREENING))}` are:\n\n"
        r"```text\n(.*?)```",
        case_study,
        re.S,
    )
    assert match, "CASE_STUDY.md no longer quotes the cv_screening output block"
    quoted = match.group(1)
    assert _cli_output(capsys, str(CV_SCREENING)).startswith(quoted)
