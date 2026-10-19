from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

from eu_ai_act_classifier import (
    ClassificationReport,
    ReviewStatus,
    Role,
    SystemProfile,
    classify,
    render_report,
)
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
DEMO_PNG = Path("docs/demo.png")
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


def _load_script(name: str) -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_image_shows_the_real_cli_output_and_its_caption_counts_the_lines(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # scripts/render_demo_png.py records the exact text it draws in the PNG, so the
    # cut marker in the image can be checked without a browser or OCR.
    render_demo = _load_script("render_demo_png")
    output = _cli_output(capsys, str(CREDIT_SCORING))
    total = len(output.splitlines())
    shown = render_demo.SHOWN_LINES
    drawn = render_demo.drawn_text(DEMO_PNG.read_bytes())
    assert drawn == render_demo.terminal_text(output), (
        f"{DEMO_PNG} is stale; re-render it with `uv run python scripts/render_demo_png.py`"
    )
    assert drawn.splitlines()[-1] == f"[\u2026 {total - shown} more lines not shown]"

    sample_output = SAMPLE_OUTPUT.read_text(encoding="utf-8")
    caption = re.search(r"\]\(demo\.png\)\n\n\*(.*?)\*\n", sample_output, re.S)
    assert caption, f"{SAMPLE_OUTPUT} no longer captions demo.png"
    assert f"`{render_demo.COMMAND}`" in caption.group(1)
    assert f"first {shown} of {total} lines" in caption.group(1)


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


# The docs spell out numbers below ten ("five documentation items").
NUMBER_WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
DATE = rf"({ISO_DATE.pattern})"


def _report(path: Path) -> ClassificationReport:
    return classify(SystemProfile.model_validate_json(path.read_text(encoding="utf-8")))


def _evaluation() -> str:
    case_study = CASE_STUDY.read_text(encoding="utf-8")
    section = case_study[case_study.index("## Evaluation") : case_study.index("## Limitations")]
    return " ".join(section.split())


def _count(token: str) -> int:
    return int(token) if token.isdigit() else NUMBER_WORDS.index(token.lower())


def _article_list(span: str) -> list[int]:
    """Expand prose such as '9 to 15, 17, 43 and 73' into article numbers."""
    numbers: list[int] = []
    for part in re.split(r", | and ", span):
        low, _, high = part.partition(" to ")
        numbers.extend(range(int(low), int(high or low) + 1))
    return numbers


def _article_numbers(articles: list[str]) -> list[int]:
    return sorted(int(re.fullmatch(r"Art\. (\d+) AIA", article).group(1)) for article in articles)


def _search(pattern: str, text: str) -> re.Match[str]:
    match = re.search(pattern, text)
    assert match, f"CASE_STUDY.md Evaluation no longer matches {pattern!r}"
    return match


def test_case_study_evaluation_counts_match_the_real_cv_screening_report() -> None:
    report = _report(CV_SCREENING)
    evaluation = _evaluation()

    obligations = _search(r"lists (\w+) provider obligations \(Art\. ([^)]+) AIA\)", evaluation)
    assert _count(obligations.group(1)) == len(report.obligations)
    assert {obligation.applies_to for obligation in report.obligations} == {Role.PROVIDER}
    assert _article_list(obligations.group(2)) == _article_numbers(
        [obligation.article for obligation in report.obligations]
    )

    documentation = _search(r"and (\w+) documentation items", evaluation)
    assert _count(documentation.group(1)) == len(report.documentation_required)

    graph = _search(
        r"marks (\d+) of (\d+) items `review: review_required` \(Art\. ([^)]+) AIA\)",
        evaluation,
    )
    flagged = [
        item
        for item in report.obligation_graph
        if item.review_status is ReviewStatus.REVIEW_REQUIRED
    ]
    assert int(graph.group(1)) == len(flagged)
    assert int(graph.group(2)) == len(report.obligation_graph)
    assert _article_list(graph.group(3)) == _article_numbers([item.article for item in flagged])

    notes = _search(
        r"Each of the Art\. (.+?) items carries a note: on a literal reading, confirm with "
        rf"counsel, it applies from {DATE}, or from {DATE} if it follows",
        evaluation,
    )
    noted = [item for item in report.obligation_graph if item.application_date_note]
    assert _article_list(notes.group(1)) == _article_numbers([item.article for item in noted])
    assert all(item.review_status is ReviewStatus.REVIEW_REQUIRED for item in noted)
    assert all(
        item.application_date_note.startswith("Literal reading, confirm with counsel")
        for item in noted
    )
    assert {item.application_date for item in noted} == {notes.group(2)}
    deferred = {
        re.search(rf"following that deferral, {DATE} applies", item.application_date_note).group(1)
        for item in noted
    }
    assert deferred == {notes.group(3)}


def test_case_study_packet_sentence_matches_the_real_credit_scoring_report() -> None:
    credit, cv = _report(CREDIT_SCORING), _report(CV_SCREENING)
    sentence = _search(
        r"CreditSightScore, classified high-risk under (Annex III\(\d+\)\(\w\)), "
        r"with the same (\w+) provider obligations and the same dating notes",
        _evaluation(),
    )
    assert any(finding.citation == sentence.group(1) + " AIA" for finding in credit.findings)
    assert _count(sentence.group(2)) == len(credit.obligations)
    assert [o.article for o in credit.obligations] == [o.article for o in cv.obligations]

    def dating(report: ClassificationReport) -> list[tuple[str, str, str]]:
        return [
            (item.article, item.application_date, item.application_date_note)
            for item in report.obligation_graph
            if item.application_date_note
        ]

    assert dating(credit) and dating(credit) == dating(cv)
