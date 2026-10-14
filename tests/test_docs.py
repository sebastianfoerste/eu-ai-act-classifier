from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from eu_ai_act_classifier import SystemProfile, classify, render_report
from eu_ai_act_classifier.artifacts import render_artifact

EXAMPLES = Path("examples")
README = Path("README.md")
EXAMPLES_README = EXAMPLES / "README.md"
PYPROJECT = Path("pyproject.toml")
PUBLIC_MARKDOWN = [
    README,
    EXAMPLES_README,
    Path("docs/DESIGN.md"),
    Path("docs/launch-readiness.md"),
    Path("docs/methodology.md"),
    Path("docs/reviewer-notes.md"),
    Path("docs/sample-output.md"),
    Path("docs/worked-examples/bank-credit-scoring.md"),
    Path("docs/worked-examples/life-insurer-pricing.md"),
]
WORKED_EXAMPLES = {
    Path("docs/worked-examples/bank-credit-scoring.md"): Path(
        "examples/credit_scoring_deployer.json"
    ),
    Path("docs/worked-examples/life-insurer-pricing.md"): Path(
        "examples/life_insurer_pricing.json"
    ),
}
OMITTED = re.compile(r"^\[\.\.\. (\d+) lines omitted\]$")
SAMPLE_DOSSIER = Path("docs/sample-review-dossier.md")
DOSSIER_BLOCK = re.compile(r"\*\*Source File:\*\* `(examples/\w+\.json)`\n```\n(.*?)\n```", re.S)
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


def _fenced(text: str, language: str) -> list[str]:
    return re.findall(rf"```{language}\n(.*?)\n```", text, re.S)


@pytest.mark.parametrize(("doc", "example"), WORKED_EXAMPLES.items())
def test_worked_example_quotes_the_real_profile_and_cli_output(doc: Path, example: Path) -> None:
    text = doc.read_text(encoding="utf-8")
    profile_text = example.read_text(encoding="utf-8")
    assert f"uv run eu-ai-act-classify {example.as_posix()}" in text
    assert json.loads(_fenced(text, "json")[0]) == json.loads(profile_text)

    actual = render_report(classify(SystemProfile.model_validate_json(profile_text))).split("\n")
    assert f"Output ({len(actual)} lines" in text
    position = 0
    for line in _fenced(text, "text")[0].split("\n"):
        omitted = OMITTED.match(line)
        if omitted:
            position += int(omitted.group(1))
            continue
        assert position < len(actual) and actual[position] == line, (
            f"{doc} no longer matches the CLI output at line {position + 1}: rerun the command"
        )
        position += 1
    assert position == len(actual), f"{doc} does not quote the CLI output to its end"


def test_sample_review_dossier_quotes_the_current_cli_output() -> None:
    blocks = DOSSIER_BLOCK.findall(SAMPLE_DOSSIER.read_text(encoding="utf-8"))
    assert len(blocks) == 4
    for example, quoted in blocks:
        profile = SystemProfile.model_validate_json(Path(example).read_text(encoding="utf-8"))
        assert quoted == render_report(classify(profile)), (
            f"{SAMPLE_DOSSIER} no longer matches the CLI output for {example}: "
            f"rerun uv run eu-ai-act-classify {example}"
        )
