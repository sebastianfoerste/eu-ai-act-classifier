from __future__ import annotations

import asyncio
import json

import pytest

pytest.importorskip("mcp")

from eu_ai_act_classifier.mcp_server import build_server

PROFILE = {"name": "SpamShield"}


def test_server_exposes_both_classification_tools() -> None:
    tools = asyncio.run(build_server().list_tools())

    assert {tool.name for tool in tools} == {"classify_ai_system", "classify_ai_system_text"}


def test_classify_ai_system_returns_report_json() -> None:
    result = asyncio.run(build_server().call_tool("classify_ai_system", {"profile": PROFILE}))
    blocks = result[0] if isinstance(result, tuple) else result
    report = json.loads(blocks[0].text)

    assert report["system"] == "SpamShield"


def test_classify_ai_system_text_returns_report_text() -> None:
    result = asyncio.run(build_server().call_tool("classify_ai_system_text", {"profile": PROFILE}))
    blocks = result[0] if isinstance(result, tuple) else result

    assert "SpamShield" in blocks[0].text


def test_invalid_profile_is_rejected() -> None:
    with pytest.raises(Exception):  # noqa: B017 - FastMCP wraps validation errors
        asyncio.run(build_server().call_tool("classify_ai_system", {"profile": {"roles": "bogus"}}))
