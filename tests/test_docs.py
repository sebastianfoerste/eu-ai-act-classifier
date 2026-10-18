from __future__ import annotations

import re
from pathlib import Path

from eu_ai_act_classifier import SystemProfile, classify, render_report
from eu_ai_act_classifier.artifacts import render_artifact

EXAMPLES = Path("examples")
README = Path("README.md")
EXAMPLES_README = EXAMPLES / "README.md"
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


def test_readme_and_moved_sections_have_working_relative_links() -> None:
    for path in [README, *README_CONTENT_DOCS]:
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
        assert f"]({target})" in readme


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
