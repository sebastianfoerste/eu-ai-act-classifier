"""The output shown in the sample docs and the case study is real CLI output.

Each fenced output block is paired with the command shown before it (a ``bash`` block, an
inline `eu-ai-act-classify ...` span or an inline `examples/*.json` path). The command is
run in-process and every block line must appear in its output: verbatim, indentation
included, apart from cuts marked with "...". A line that is only "..." marks cut lines;
other block lines must be consecutive in the output, so every cut inside a block is marked.
A block that does not start (end) with a "..." line must start (end) where the output does.
"""

from __future__ import annotations

import io
import re
import shlex
import sys
from pathlib import Path

import pytest

from eu_ai_act_classifier.cli import main

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DOCS = [
    ROOT / "docs" / "sample-output.md",
    ROOT / "docs" / "sample-review-dossier.md",
    ROOT / "CASE_STUDY.md",
]
CLI = "eu-ai-act-classify"
CUT = "..."
EXAMPLE = re.compile(r"examples/[\w-]+\.json")
OUTPUT_FENCES = {"", "text", "json"}


def _output_blocks(path: Path) -> list[tuple[str, str | None, list[str]]]:
    """(block id, command, block lines) for every fenced output block in ``path``."""

    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[tuple[str, str | None, list[str]]] = []
    command: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("```"):
            for span in re.findall(r"`([^`]+)`", line):
                if CLI in span or EXAMPLE.fullmatch(span):
                    command = span
            index += 1
            continue
        info = line[3:].strip()
        end = lines.index("```", index + 1)
        body = lines[index + 1 : end]
        if info == "bash":
            command = next((text for text in body if CLI in text), None)
        elif info in OUTPUT_FENCES:
            blocks.append((f"{path.name}:{index + 1}", command, body))
            command = None
        index = end + 1
    return blocks


BLOCKS = [block for path in SAMPLE_DOCS for block in _output_blocks(path)]


def _run(command: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> str:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    words = list(lexer)
    stdin = ""
    if "|" in words:
        producer, words = words[: words.index("|")], words[words.index("|") + 1 :]
        assert producer[0] == "echo" and len(producer) == 2, command
        stdin = producer[1] + "\n"
    argv = words[words.index(CLI) + 1 :] if CLI in words else words
    assert not {"--artifacts-dir", "--dossier-dir"} & set(argv), command
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    capsys.readouterr()
    assert main(argv) == 0, command
    return capsys.readouterr().out


def _line_matches(excerpt: str, line: str) -> bool:
    """``excerpt`` is ``line`` apart from cuts marked with "..."."""

    if CUT not in excerpt:
        return excerpt == line
    head, *middle, tail = excerpt.split(CUT)
    head, tail = head.rstrip(), tail.strip()
    if not line.startswith(head):
        return False
    position = len(head)
    for fragment in (part.strip() for part in middle):
        found = line.find(fragment, position)
        if found < 0:
            return False
        position = found + len(fragment)
    return not tail or (line.endswith(tail) and len(line) - len(tail) >= position)


def _segments(block: list[str]) -> list[list[str]]:
    """The runs of block lines between "..." lines."""

    segments: list[list[str]] = [[]]
    for line in block:
        if line.strip() == CUT:
            segments.append([])
        else:
            segments[-1].append(line)
    return [segment for segment in segments if segment]


def _find(segment: list[str], output: list[str], start: int) -> int | None:
    for index in range(start, len(output) - len(segment) + 1):
        if all(map(_line_matches, segment, output[index:])):
            return index
    return None


def test_sample_docs_have_output_blocks() -> None:
    for path in SAMPLE_DOCS:
        assert _output_blocks(path), f"no output blocks found in {path.name}"


@pytest.mark.parametrize(("block_id", "command", "block"), BLOCKS, ids=[b[0] for b in BLOCKS])
def test_sample_output_block_is_real_cli_output(
    block_id: str,
    command: str | None,
    block: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert command, f"{block_id}: no command or example file named before the block"
    output = _run(command, monkeypatch, capsys).splitlines()

    position = 0
    for number, segment in enumerate(_segments(block)):
        found = _find(segment, output, position)
        if found is not None and number == 0 and found > 0 and block[0].strip() != CUT:
            pytest.fail(
                f"{block_id} ({command}): output lines before the block; start it with '...'"
            )
        if found is None:
            missing = [line for line in segment if not any(_line_matches(line, o) for o in output)]
            reason = (
                f"not in the output: {missing[0]!r}"
                if missing
                else f"lines from {segment[0]!r} are not consecutive or not in order in the "
                "output; mark each cut with a '...' line"
            )
            pytest.fail(f"{block_id} ({command}): {reason}")
        position = found + len(segment)
    if block and block[-1].strip() != CUT and any(line.strip() for line in output[position:]):
        pytest.fail(f"{block_id} ({command}): output lines after the block; end it with '...'")
