from __future__ import annotations

import asyncio
import sys
import tomllib
import types
from pathlib import Path

import pytest

from eu_ai_act_classifier import mcp_server

ROOT = Path(__file__).resolve().parents[1]
PIP_COMMAND = "pip install 'eu-ai-act-classifier[mcp]'"
UVX_COMMAND = "uvx --from 'eu-ai-act-classifier[mcp]' eu-ai-act-classifier-mcp"
CLONE_COMMAND = "uv run --extra mcp eu-ai-act-classifier-mcp"


def _exit_message(
    monkeypatch: pytest.MonkeyPatch, fastmcp: types.ModuleType | None, installed_mcp: str | None
) -> str:
    # None in sys.modules makes the import raise ModuleNotFoundError, as it does without mcp
    # and under mcp 2.x; a module without FastMCP raises a plain ImportError instead.
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp)
    monkeypatch.setattr(mcp_server, "_installed_mcp_version", lambda: installed_mcp)
    with pytest.raises(SystemExit) as excinfo:
        mcp_server.build_server()
    message = excinfo.value.code
    assert isinstance(message, str)
    return message


@pytest.mark.parametrize("installed_mcp", [None, "2.3.0"])
def test_hint_gives_the_pypi_and_clone_commands(
    monkeypatch: pytest.MonkeyPatch, installed_mcp: str | None
) -> None:
    message = _exit_message(monkeypatch, None, installed_mcp)

    assert f"needs {mcp_server.MCP_REQUIREMENT}" in message
    for command in (PIP_COMMAND, UVX_COMMAND, CLONE_COMMAND):
        assert f"  {command}" in message.splitlines()
    assert "pip install -e" not in message


def test_hint_says_the_extra_is_missing_when_mcp_is_not_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = _exit_message(monkeypatch, None, None)

    assert message.startswith("The MCP extra is not installed.\n")


def test_hint_names_an_incompatible_mcp_instead_of_a_missing_extra(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = _exit_message(monkeypatch, None, "2.3.0")

    assert message.startswith("mcp 2.3.0 is installed, but mcp.server.fastmcp could not be")
    assert "not installed" not in message


def test_hint_covers_import_errors_other_than_a_missing_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = _exit_message(monkeypatch, types.ModuleType("mcp.server.fastmcp"), "1.30.0")

    assert message.startswith("mcp 1.30.0 is installed")
    assert "cannot import name 'FastMCP'" in message
    assert PIP_COMMAND in message


def test_requirement_in_the_hint_matches_the_mcp_extra() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["optional-dependencies"]["mcp"] == [mcp_server.MCP_REQUIREMENT]
    assert "eu-ai-act-classifier-mcp" in pyproject["project"]["scripts"]


def test_server_lists_both_tools_when_a_compatible_mcp_is_installed() -> None:
    # Skipped without the extra; run it with `uv run --extra dev --extra mcp pytest`.
    pytest.importorskip("mcp.server.fastmcp")

    tools = asyncio.run(mcp_server.build_server().list_tools())

    assert {tool.name for tool in tools} == {"classify_ai_system", "classify_ai_system_text"}
