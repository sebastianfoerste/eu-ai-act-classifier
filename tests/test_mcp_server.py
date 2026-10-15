from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from eu_ai_act_classifier import mcp_server

PIN = "mcp>=1.2,<2"
EU_REG_MCP_COMMAND = (
    "uvx --from 'eu-reg-mcp[lint,classify] @ git+https://github.com/sebastianfoerste/eu-reg-mcp'"
    " eu-reg-mcp"
)
LOCAL_SERVER_COMMAND = "uv run --extra mcp python -m eu_ai_act_classifier.mcp_server"
PIP_EXTRA_COMMAND = "pip install 'eu-ai-act-classifier[mcp]'"
UVX_SERVER_COMMAND = (
    "uvx --from 'eu-ai-act-classifier[mcp] @ git+https://github.com/sebastianfoerste/eu-ai-act-classifier'"
    " eu-ai-act-classifier-mcp"
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
    assert LOCAL_SERVER_COMMAND in message
    assert "uv sync --extra mcp" in message
    assert PIP_EXTRA_COMMAND in message
    assert UVX_SERVER_COMMAND in message
    assert "uv pip install" not in message
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


@pytest.mark.parametrize("installed_version", ["1.2.0", "1.30.0"])
def test_mcp_that_meets_the_pin_reports_the_import_error_without_reinstall_advice(
    monkeypatch: pytest.MonkeyPatch, installed_version: str
) -> None:
    message = _exit_message(monkeypatch, installed_version)

    assert message.startswith(f"mcp {installed_version} is installed and meets {PIN}")
    assert "could not be imported" in message
    assert LOCAL_SERVER_COMMAND not in message
    assert "pip install" not in message
    assert EU_REG_MCP_COMMAND in message


@pytest.mark.parametrize(
    ("version", "release"),
    [("1.30.0", (1, 30, 0)), ("1.2", (1, 2)), ("1.2.0rc1", None), ("1.30.0+local", None)],
)
def test_release_reads_only_final_versions(version: str, release: tuple[int, ...] | None) -> None:
    assert mcp_server._release(version) == release


def test_pin_and_commands_match_pyproject_and_docs() -> None:
    assert mcp_server.MCP_REQUIREMENT == PIN
    assert mcp_server.EU_REG_MCP_COMMAND == EU_REG_MCP_COMMAND
    assert mcp_server.LOCAL_SERVER_COMMAND == LOCAL_SERVER_COMMAND
    assert mcp_server.PIP_EXTRA_COMMAND == PIP_EXTRA_COMMAND
    assert mcp_server.UVX_SERVER_COMMAND == UVX_SERVER_COMMAND
    scripts = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'eu-ai-act-classifier-mcp = "eu_ai_act_classifier.mcp_server:main"' in scripts
    assert f'mcp = ["{PIN}"]' in Path("pyproject.toml").read_text(encoding="utf-8")
    for doc in (
        Path("README.md"),
        Path("docs/mcp-configuration-guide.md"),
        Path("docs/surfaces.md"),
    ):
        assert EU_REG_MCP_COMMAND in doc.read_text(encoding="utf-8"), doc
    for doc in (Path("README.md"), Path("docs/surfaces.md")):
        assert LOCAL_SERVER_COMMAND in doc.read_text(encoding="utf-8"), doc


def test_server_lists_both_tools_when_a_compatible_mcp_is_installed() -> None:
    # Skipped in the default dev environment; runs with `uv run --extra dev --extra mcp pytest`.
    pytest.importorskip("mcp.server.fastmcp")

    tools = asyncio.run(mcp_server.build_server().list_tools())

    assert {tool.name for tool in tools} == {"classify_ai_system", "classify_ai_system_text"}
