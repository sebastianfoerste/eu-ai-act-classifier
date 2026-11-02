from __future__ import annotations

import ast
import asyncio
import importlib.util
import json
import re
import struct
from pathlib import Path
from types import ModuleType

import pytest

from eu_ai_act_classifier import (
    ClassificationReport,
    Disposition,
    ReviewStatus,
    Role,
    SystemProfile,
    classify,
    render_report,
)
from eu_ai_act_classifier.artifacts import render_artifact
from eu_ai_act_classifier.cli import main
from eu_ai_act_classifier.mcp_server import build_server

EXAMPLES = Path("examples")
README = Path("README.md")
EXAMPLES_README = EXAMPLES / "README.md"
CASE_STUDY = Path("CASE_STUDY.md")
CREDIT_SCORING = EXAMPLES / "credit_scoring.json"
CV_SCREENING = EXAMPLES / "cv_screening.json"
SAMPLE_OUTPUT = Path("docs/sample-output.md")
DEMO_PNG = Path("docs/demo.png")
PYPROJECT = Path("pyproject.toml")
CLAIM_LEDGER = Path("docs/REGULATORY_CLAIM_LEDGER.md")
SOURCE = Path("src/eu_ai_act_classifier")
# How the code and the claim ledger cite the amending points of Regulation (EU) 2026/1744.
AMENDING_POINT = re.compile(r"Art\. 1, point \((\d+)\)")
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
    Path("docs/mcp-configuration-guide.md"),
    Path("docs/worked-examples/bank-credit-scoring.md"),
    Path("docs/worked-examples/life-insurer-pricing.md"),
    *README_CONTENT_DOCS,
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


def test_claim_ledger_names_every_amending_point_the_code_cites() -> None:
    # The README, docs/overview.md and docs/surfaces.md send readers to the claim ledger
    # for what the classifier encodes from Regulation (EU) 2026/1744, so the ledger names
    # every point of that regulation's Art. 1 that the code cites.
    cited = {
        point
        for path in SOURCE.rglob("*.py")
        for point in AMENDING_POINT.findall(path.read_text(encoding="utf-8"))
    }
    named = set(AMENDING_POINT.findall(CLAIM_LEDGER.read_text(encoding="utf-8")))
    assert cited, f"no 'Art. 1, point (n)' citation found under {SOURCE}"
    missing = sorted(cited - named, key=int)
    assert not missing, f"{CLAIM_LEDGER} names no Art. 1, point {missing} cited in {SOURCE}"


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


MCP_SERVER = Path("src/eu_ai_act_classifier/mcp_server.py")
TOOL_DECORATORS = """
@server.tool()
def bare(): ...


@server.tool(title="Titled", annotations=read_only)
def titled(): ...


@server.tool(
    title="Wrapped (over lines)",
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def wrapped(): ...


@other.tool()
def other_object(): ...


# @server.tool()
def commented_out(): ...
"""


def _server_tools(source: str) -> list[str]:
    # Functions decorated with @server.tool(...), whether or not the decorator takes arguments.
    return [
        node.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and any(
            isinstance(decorator, ast.Call) and ast.unparse(decorator.func) == "server.tool"
            for decorator in node.decorator_list
        )
    ]


def test_tool_lookup_reads_decorators_with_and_without_arguments() -> None:
    assert _server_tools(TOOL_DECORATORS) == ["bare", "titled", "wrapped"]


def test_tool_lookup_finds_every_tool_the_server_registers() -> None:
    pytest.importorskip("mcp.server.fastmcp")
    source = MCP_SERVER.read_text(encoding="utf-8")
    registered = [tool.name for tool in asyncio.run(build_server().list_tools())]
    found = _server_tools(source)

    assert len(found) == len(registered)
    assert sorted(found) == sorted(registered)
    # The lookup _server_tools replaced matched only `@server.tool()` without arguments.
    assert set(re.findall(r"@server\.tool\(\)\s+def (\w+)\(", source)) <= set(found)


def test_mcp_guide_lists_the_tools_the_server_exposes() -> None:
    server = MCP_SERVER.read_text(encoding="utf-8")
    exposed = set(_server_tools(server))
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


# The example output that the README quoted until main's README trim (#27) moved it here.
# tests/test_sample_output.py checks each output block on the page against the CLI; this
# test checks the sentence that introduces the high-risk excerpt.
SAMPLE_OUTPUT = Path("docs/sample-output.md")
HIGH_RISK_SUMMARY = re.compile(
    r"A high-risk case \(`(examples/\w+\.json)`\) returns `([^`]+)`, the finding `([^`]+)`, "
    r"and (\d+) cited obligations, for example:\n\n```text\n(.*?)\n```",
    re.S,
)
CUT = "..."


def _cli_lines(example: str) -> list[str]:
    profile = SystemProfile.model_validate_json(Path(example).read_text(encoding="utf-8"))
    return render_report(classify(profile)).split("\n")


def test_sample_output_high_risk_summary_matches_the_cli() -> None:
    match = HIGH_RISK_SUMMARY.search(SAMPLE_OUTPUT.read_text(encoding="utf-8"))
    assert match, f"{SAMPLE_OUTPUT} no longer summarises the high-risk case"
    example, tier, finding, count, quoted = match.groups()
    profile = SystemProfile.model_validate_json(Path(example).read_text(encoding="utf-8"))
    report = classify(profile)
    actual = _cli_lines(example)
    assert tier in actual
    assert any(line.strip().endswith(finding) for line in actual), finding
    assert int(count) == len(report.obligations)
    for line in quoted.split("\n"):
        assert line.strip() == CUT or line in actual, line


# tests/test_sample_output.py checks each dossier block against the CLI. This test checks
# that the summary table and the blocks name the same profiles in the same order, so a
# block cannot go missing, and that the table's scope, roles and obligation counts match.
SAMPLE_DOSSIER = Path("docs/sample-review-dossier.md")
DOSSIER_SOURCE = re.compile(r"^\*\*Source File:\*\* `(examples/\w+\.json)`$", re.M)
DOSSIER_ROW = re.compile(r"^\| \*\*([^*|]+)\*\* \| [^|]+ \| (\w+) \| ([^|]+) \| (\d+) \|", re.M)


def test_sample_review_dossier_table_and_blocks_cover_the_same_profiles() -> None:
    text = SAMPLE_DOSSIER.read_text(encoding="utf-8")
    reports = [
        classify(SystemProfile.model_validate_json(Path(example).read_text(encoding="utf-8")))
        for example in DOSSIER_SOURCE.findall(text)
    ]
    rows = DOSSIER_ROW.findall(text)
    assert rows, f"{SAMPLE_DOSSIER} has no summary table rows"
    assert [name for name, *_ in rows] == [report.system for report in reports]
    for (name, scope, roles, count), report in zip(rows, reports, strict=True):
        assert scope == report.scope.status.value, name
        assert roles.strip() == ", ".join(role.value for role in report.roles), name
        assert int(count) == len(report.obligations), name


def test_feature_matrix_capability_cells_use_the_allowed_values() -> None:
    import csv

    with Path("docs/research/feature-matrix.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    header = rows[0]
    first, last = header.index("c01_intake"), header.index("c14_ui_shell")
    evidence = header.index("evidence")
    for row in rows[1:]:
        assert len(row) == len(header), row[0]
        assert row[evidence] in {"Observed", "Claimed", "Inferred"}, row[0]
        for cell in row[first : last + 1]:
            assert re.match(r"(yes|partial|no|unknown)(:|$)", cell), (row[0], cell)


def _cli_output(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    assert main(list(argv)) == 0
    return capsys.readouterr().out


def _load_script(name: str) -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_image_fits_the_real_cli_output_and_its_caption_counts_the_lines(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # scripts/render_demo.py sizes the screenshot from the number of wrapped output
    # lines, so the image size shows, without a browser, whether demo.png was
    # rendered from output of the current length. It cannot see a change within a line.
    render_demo = _load_script("render_demo")
    command, *argv = render_demo.COMMAND
    output = _cli_output(capsys, *argv)
    png = DEMO_PNG.read_bytes()
    assert png[12:16] == b"IHDR", f"{DEMO_PNG} is not a PNG file"
    assert struct.unpack(">II", png[16:24]) == render_demo.window_size(
        render_demo.terminal_lines(output)
    ), f"{DEMO_PNG} is stale; re-render it with `uv run python scripts/render_demo.py`"

    sample_output = SAMPLE_OUTPUT.read_text(encoding="utf-8")
    caption = re.search(r"\]\(demo\.png\)\n\n\*(.*?)\*\n", sample_output, re.S)
    assert caption, f"{SAMPLE_OUTPUT} no longer captions demo.png"
    text = " ".join(caption.group(1).split())
    assert f"All {len(output.splitlines())} lines of `{command} {' '.join(argv)}`" in text
    assert f"hard-wrapped at {render_demo.COLUMNS} columns" in text
    assert "(../scripts/render_demo.py)" in text


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


def _article_key(reference: str) -> tuple[int, str]:
    number, _, paragraph = reference.partition("(")
    return int(number), paragraph


def _article_list(span: str) -> list[str]:
    """Expand prose such as '9 to 15, 17, 43(2) and 73' into article references."""
    references: list[str] = []
    for part in re.split(r", | and ", span):
        low, _, high = part.partition(" to ")
        if high:
            references.extend(str(n) for n in range(int(low), int(high) + 1))
        else:
            references.append(low)
    return references


def _article_numbers(articles: list[str]) -> list[str]:
    """'Art. 43(2) AIA' -> '43(2)', in article order; a paragraph sorts after its article."""
    references = (re.fullmatch(r"Art\. (\d+(?:\(\d+\))?) AIA", a).group(1) for a in articles)
    return sorted(references, key=_article_key)


def _search(pattern: str, text: str) -> re.Match[str]:
    match = re.search(pattern, text)
    assert match, f"CASE_STUDY.md Evaluation no longer matches {pattern!r}"
    return match


def test_case_study_evaluation_counts_match_the_real_cv_screening_report() -> None:
    report = _report(CV_SCREENING)
    evaluation = _evaluation()

    obligations = _search(
        r"lists (\w+) provider obligations \(Art\. ((?:[^()]|\(\d+\))+) AIA\)", evaluation
    )
    assert _count(obligations.group(1)) == len(report.obligations)
    assert {obligation.applies_to for obligation in report.obligations} == {Role.PROVIDER}
    assert _article_list(obligations.group(2)) == _article_numbers(
        [obligation.article for obligation in report.obligations]
    )

    documentation = _search(r"and (\w+) documentation items", evaluation)
    assert _count(documentation.group(1)) == len(report.documentation_required)

    graph = _search(
        r"marks (\d+) of (\d+) items `review: review_required` \(Art\. ((?:[^()]|\(\d+\))+) AIA\)",
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
        r"Each of the Art\. (.+?) items carries a note flagged \"Literal reading, confirm "
        rf"with counsel\": it applies from {DATE}, or from {DATE} if it follows",
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


def test_case_study_example_counts_match_the_bundled_examples() -> None:
    case_study = " ".join(CASE_STUDY.read_text(encoding="utf-8").split())
    examples = sorted(p for p in EXAMPLES.glob("*.json") if p.name != "classification-packet.json")
    review = [p.name for p in examples if _report(p).disposition is Disposition.REQUIRES_REVIEW]

    path = _search(
        r"(\w+) of the (\d+) bundled examples take that path: "
        r"((?:`[\w-]+\.json`(?:, | and )?)+)\.",
        case_study,
    )
    assert _count(path.group(1)) == len(review)
    assert int(path.group(2)) == len(examples)
    assert re.findall(r"`([\w-]+\.json)`", path.group(3)) == review

    asserted = _search(
        r"all (\d+) bundled examples are asserted in `tests/test_examples\.py`", case_study
    )
    assert int(asserted.group(1)) == len(examples)


def test_overview_example_count_matches_the_bundled_examples() -> None:
    overview = " ".join(Path("docs/overview.md").read_text(encoding="utf-8").split())
    examples = [p for p in EXAMPLES.glob("*.json") if p.name != "classification-packet.json"]

    count = re.search(r"pick one of the (\d+) synthetic examples", overview)
    assert count, "docs/overview.md no longer says how many synthetic examples there are"
    assert int(count.group(1)) == len(examples)
