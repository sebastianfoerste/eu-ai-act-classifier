from __future__ import annotations

import asyncio
import json
import sys
import tomllib
import types
from pathlib import Path
from typing import Any

import pydantic
import pytest

from eu_ai_act_classifier import SystemProfile, classify, mcp_server, render_report

ROOT = Path(__file__).resolve().parents[1]
PIP_COMMAND = "pip install 'eu-ai-act-classifier[mcp]'"
UVX_COMMAND = "uvx --from 'eu-ai-act-classifier[mcp]' eu-ai-act-classifier-mcp"
CLONE_COMMAND = "uv run --extra mcp eu-ai-act-classifier-mcp"
PROFILE = {"name": "SpamShield"}


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


def _server() -> Any:
    # The hint tests run without mcp; the server tests skip unless a compatible mcp is
    # installed. Run them all with `uv run --extra dev --extra mcp pytest`.
    pytest.importorskip("mcp.server.fastmcp")
    return mcp_server.build_server()


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


def test_server_exposes_both_classification_tools() -> None:
    tools = asyncio.run(_server().list_tools())

    assert {tool.name for tool in tools} == {"classify_ai_system", "classify_ai_system_text"}


def test_classify_tool_description_names_the_date_and_section_fields() -> None:
    tools = {tool.name: tool for tool in asyncio.run(_server().list_tools())}
    description = tools["classify_ai_system"].description

    for field in ("annex_i_section", "placing_on_market_date", "gpai_model_placing_on_market_date"):
        assert field in description


def _example(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "examples" / f"{name}.json").read_text(encoding="utf-8"))


# One profile per outcome; the expected report always comes from the engine.
TOOL_PROFILES = [
    pytest.param(PROFILE, id="minimal"),
    pytest.param(_example("social_scoring"), id="social_scoring"),
    pytest.param(_example("cv_screening"), id="cv_screening"),
    pytest.param(_example("ambiguous_use_case"), id="ambiguous_use_case"),
    pytest.param(_example("support_chatbot"), id="support_chatbot"),
    pytest.param(_example("spam_filter"), id="spam_filter"),
]


def _call(tool: str, arguments: dict[str, Any]) -> tuple[Any, Any]:
    # mcp 1.30 returns (content blocks, structured output); earlier 1.x the blocks alone.
    result = asyncio.run(_server().call_tool(tool, arguments))
    return result if isinstance(result, tuple) else (result, None)


@pytest.mark.parametrize("include_advisory", [False, True])
@pytest.mark.parametrize("profile", TOOL_PROFILES)
def test_classify_ai_system_returns_the_engine_report(
    profile: dict[str, Any], include_advisory: bool
) -> None:
    expected = classify(
        SystemProfile.model_validate(profile), include_advisory=include_advisory
    ).model_dump(mode="json")

    blocks, structured = _call(
        "classify_ai_system", {"profile": profile, "include_advisory": include_advisory}
    )

    assert expected["system"] == profile["name"]
    assert json.loads(blocks[0].text) == expected
    if structured is not None:
        assert structured == expected


@pytest.mark.parametrize("profile", TOOL_PROFILES)
def test_classify_ai_system_text_returns_the_rendered_report(profile: dict[str, Any]) -> None:
    expected = render_report(classify(SystemProfile.model_validate(profile)))

    blocks, _structured = _call("classify_ai_system_text", {"profile": profile})

    assert profile["name"] in expected
    assert blocks[0].text == expected


@pytest.mark.parametrize("tool", ["classify_ai_system", "classify_ai_system_text"])
def test_invalid_profile_is_rejected_with_a_tool_error_naming_the_field(tool: str) -> None:
    server = _server()
    from mcp.server.fastmcp.exceptions import ToolError

    with pytest.raises(ToolError, match=f"^Error executing tool {tool}: ") as excinfo:
        asyncio.run(server.call_tool(tool, {"profile": {**PROFILE, "roles": "bogus"}}))

    # pydantic puts each failing field on its own line of the message.
    assert "roles" in str(excinfo.value).splitlines()
    cause = excinfo.value.__cause__
    assert isinstance(cause, pydantic.ValidationError)
    assert [error["loc"] for error in cause.errors()] == [("roles",)]
