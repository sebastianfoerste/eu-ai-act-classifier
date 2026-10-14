from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from eu_ai_act_classifier import mcp_server

PIN = "mcp>=1.2,<2"
EU_REG_MCP_COMMAND = (
    "uvx --from 'eu-reg-mcp[classify,lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp'"
    " eu-reg-mcp"
)


def _exit_message(monkeypatch: pytest.MonkeyPatch, installed_version: str | None) -> str:
    # A None entry in sys.modules makes the import raise ModuleNotFoundError, which is what
    # happens without mcp and under mcp 2.x, where mcp.server.fastmcp no longer exists.
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", None)
    monkeypatch.setattr(mcp_server, "_installed_mcp_version", lambda: installed_version)
    with pytest.raises(SystemExit) as excinfo:
        mcp_server.build_server()
    message = excinfo.value.code
    assert isinstance(message, str)
    return message


@pytest.mark.parametrize("installed_version", [None, "2.0.0", "2.3.0", "1.1.0"])
def test_exit_message_names_the_pin_and_eu_reg_mcp(
    monkeypatch: pytest.MonkeyPatch, installed_version: str | None
) -> None:
    message = _exit_message(monkeypatch, installed_version)

    assert PIN in message
    assert "uv pip install -e '.[mcp]'" in message
    assert "eu-reg-mcp" in message
    assert EU_REG_MCP_COMMAND in message


def test_missing_mcp_is_reported_as_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    message = _exit_message(monkeypatch, None)

    assert message.startswith("The optional mcp package is not installed.")


@pytest.mark.parametrize("installed_version", ["2.0.0", "2.3.0"])
def test_mcp_2_is_reported_as_installed_but_incompatible(
    monkeypatch: pytest.MonkeyPatch, installed_version: str
) -> None:
    message = _exit_message(monkeypatch, installed_version)

    assert message.startswith(f"mcp {installed_version} is installed")
    assert "mcp 2.0 removed mcp.server.fastmcp" in message
    assert "not installed" not in message


def test_older_mcp_reports_the_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    message = _exit_message(monkeypatch, "1.1.0")

    assert message.startswith("mcp 1.1.0 is installed")
    assert "could not be imported" in message
    assert "mcp.server.fastmcp" in message


def test_pin_and_command_match_pyproject_and_docs() -> None:
    assert mcp_server.MCP_REQUIREMENT == PIN
    assert mcp_server.EU_REG_MCP_COMMAND == EU_REG_MCP_COMMAND
    assert f'mcp = ["{PIN}"]' in Path("pyproject.toml").read_text(encoding="utf-8")
    for doc in (Path("README.md"), Path("docs/mcp-configuration-guide.md")):
        assert EU_REG_MCP_COMMAND in doc.read_text(encoding="utf-8"), doc


def test_server_lists_both_tools_when_a_compatible_mcp_is_installed() -> None:
    # Skipped in the default dev environment; runs with `uv run --extra dev --extra mcp pytest`.
    pytest.importorskip("mcp.server.fastmcp")

    tools = asyncio.run(mcp_server.build_server().list_tools())

    assert {tool.name for tool in tools} == {"classify_ai_system", "classify_ai_system_text"}
