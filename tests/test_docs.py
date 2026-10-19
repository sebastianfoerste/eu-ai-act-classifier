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
SAMPLE_OUTPUT = Path("docs/sample-output.md")
PYPROJECT = Path("pyproject.toml")
# Docs that hold sections moved out of the README.
README_CONTENT_DOCS = [
    Path("docs/README.md"),
    Path("docs/overview.md"),
    Path("docs/FEATURES.md"),
    Path("docs/SETUP.md"),
    Path("docs/sample-output.md"),
    Path("docs/surfaces.md"),
]
PUBLIC_MARKDOWN = [
    README,
    EXAMPLES_README,
    Path("docs/DESIGN.md"),
    Path("docs/launch-readiness.md"),
    Path("docs/methodology.md"),
    Path("docs/reviewer-notes.md"),
    *README_CONTENT_DOCS,
]
EM_DASH = "\u2014"
EN_DASH = "\u2013"
README_MAX_WORDS = 350
# The README is the PyPI long description, so it links into the repository by absolute URL.
GITHUB_REPO = "https://github.com/sebastianfoerste/eu-ai-act-classifier"
RAW_REPO = "https://raw.githubusercontent.com/sebastianfoerste/eu-ai-act-classifier"
REPO_LINK_PREFIXES = (f"{GITHUB_REPO}/blob/", f"{GITHUB_REPO}/tree/", f"{RAW_REPO}/")
REPO_MAIN_LINK = re.compile(
    rf"(?:{re.escape(GITHUB_REPO)}/(?P<kind>blob|tree)|{re.escape(RAW_REPO)})/main"
    r"(?:/(?P<path>[^#]*))?(?:#(?P<anchor>.*))?"
)
URL_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
DAY_MONTH_YEAR = re.compile(
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?"
    r"|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b\.?,?\s+\d{4}\b",
    re.IGNORECASE,
)


def _github_slug(heading: str) -> str:
    # Slug the rendered text: images render no text and links render only their label.
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", heading)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


def _heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    fence = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        marker = re.match(r" {0,3}(`{3,}|~{3,})", line)
        if fence:
            if marker and marker.group(1).startswith(fence) and not line[marker.end() :].strip():
                fence = ""
            continue
        if marker:
            fence = marker.group(1)
            continue
        heading = re.match(r" {0,3}#{1,6}(?:\s+(.*?))?(?:\s+#+)?\s*$", line)
        if not heading:
            continue
        slug = _github_slug(heading.group(1) or "")
        anchor, suffix = slug, 0
        while anchor in anchors:
            suffix += 1
            anchor = f"{slug}-{suffix}"
        anchors.add(anchor)
    return anchors


def _link_targets(text: str) -> list[str]:
    # Inline links and images, reference definitions, and HTML href or src attributes.
    return [
        *re.findall(r"\]\(\s*<?([^)\s>]+)", text),
        *re.findall(r"^ {0,3}\[[^\]]+\]:\s*<?([^\s>]+)", text, re.M),
        *re.findall(r"\b(?:href|src)\s*=\s*[\"']([^\"']+)", text),
    ]


def test_examples_readme_lists_every_json_example() -> None:
    example_docs = EXAMPLES_README.read_text(encoding="utf-8")

    for path in sorted(EXAMPLES.glob("*.json")):
        if path.name == "classification-packet.json":
            continue
        assert f"`{path.name}`" in example_docs


def test_readme_has_no_relative_links() -> None:
    readme = README.read_text(encoding="utf-8")
    relative = [target for target in _link_targets(readme) if not URL_SCHEME.match(target)]
    assert not relative, f"README is the PyPI description, use absolute links: {relative}"


def test_readme_repository_links_resolve_locally() -> None:
    for target in _link_targets(README.read_text(encoding="utf-8")):
        if not target.startswith(REPO_LINK_PREFIXES):
            continue
        link = REPO_MAIN_LINK.fullmatch(target)
        assert link, f"README repository link does not point at main: {target}"
        resolved, anchor = Path(link["path"] or "."), link["anchor"]
        expected = "directory" if link["kind"] == "tree" else "file"
        found = resolved.is_dir() if expected == "directory" else resolved.is_file()
        assert found, f"README link target is not a {expected}: {target}"
        if anchor and resolved.suffix == ".md":
            assert anchor in _heading_anchors(resolved), f"README anchor not found: {target}"


def test_moved_sections_have_working_relative_links() -> None:
    for path in README_CONTENT_DOCS:
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if target.startswith(("http://", "https://")):
                continue
            file_part, _, anchor = target.partition("#")
            resolved = path.parent / file_part if file_part else path
            assert resolved.exists(), f"{path} link target does not exist: {target}"
            if anchor and resolved.suffix == ".md":
                assert anchor in _heading_anchors(resolved), f"{path} anchor not found: {target}"


def test_readme_stays_within_word_budget() -> None:
    words = len(README.read_text(encoding="utf-8").split())
    assert words <= README_MAX_WORDS, f"README has {words} words, budget is {README_MAX_WORDS}"


def test_readme_states_no_dates() -> None:
    readme = README.read_text(encoding="utf-8")
    iso_dates = ISO_DATE.findall(readme)
    assert not iso_dates, f"ISO date in README: {iso_dates}"
    dates = DAY_MONTH_YEAR.findall(readme)
    assert not dates, f"day month year date in README: {dates}"


def test_readme_links_docs_index_overview_and_claim_ledger() -> None:
    readme = README.read_text(encoding="utf-8")
    for target in ("docs/README.md", "docs/overview.md", "docs/REGULATORY_CLAIM_LEDGER.md"):
        assert f"]({GITHUB_REPO}/blob/main/{target})" in readme


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


def test_demo_image_caption_states_the_real_line_count_of_the_demo_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    line_count = len(_cli_output(capsys, str(CREDIT_SCORING)).splitlines())
    sample_output = SAMPLE_OUTPUT.read_text(encoding="utf-8")
    caption = re.search(r"\]\(demo\.png\)\n\n\*(.*?)\*\n", sample_output, re.S)
    assert caption, f"{SAMPLE_OUTPUT} no longer captions demo.png"
    assert f"of {line_count} lines" in caption.group(1)


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
