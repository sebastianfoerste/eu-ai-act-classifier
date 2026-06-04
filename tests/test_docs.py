from __future__ import annotations

import re
from pathlib import Path

EXAMPLES = Path("examples")
README = Path("README.md")
EXAMPLES_README = EXAMPLES / "README.md"


def test_examples_readme_lists_every_json_example() -> None:
    example_docs = EXAMPLES_README.read_text(encoding="utf-8")

    for path in sorted(EXAMPLES.glob("*.json")):
        assert f"`{path.name}`" in example_docs


def test_readme_local_markdown_links_exist() -> None:
    readme = README.read_text(encoding="utf-8")
    markdown_links = re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", readme)

    for link in markdown_links:
        assert Path(link).exists(), f"README link target does not exist: {link}"


def test_launch_readiness_is_discoverable_from_readme() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "docs/launch-readiness.md" in readme
