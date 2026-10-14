"""MCP server exposing the classifier as an agent-callable tool.

An agent, for example a product-intake agent on an AI platform, can call
``classify_ai_system`` with a system profile and get back a cited, tiered,
review-gated classification. The ``mcp`` dependency is optional and imported
lazily, so the core engine never depends on it.

The server is built on ``mcp.server.fastmcp``, which mcp 2.0 removed, so the
``[mcp]`` extra pins ``mcp>=1.2,<2``. For Claude Code and Claude Desktop, the
supported integration is eu-reg-mcp, which serves this classifier as a tool.

Run::

    uv run --extra mcp python -m eu_ai_act_classifier.mcp_server
"""

from __future__ import annotations

import re
from importlib import metadata
from typing import Any

from .engine import classify
from .models import SystemProfile
from .report import render_report

# Keep in step with the `mcp` extra in pyproject.toml; tests/test_mcp_server.py checks both.
MCP_REQUIREMENT = "mcp>=1.2,<2"
EU_REG_MCP_COMMAND = (
    "uvx --from 'eu-reg-mcp[classify,lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp'"
    " eu-reg-mcp"
)


def _installed_mcp_version() -> str | None:
    try:
        return metadata.version("mcp")
    except metadata.PackageNotFoundError:
        return None


def mcp_unavailable_message(installed_version: str | None, error: ImportError) -> str:
    """Say why ``mcp.server.fastmcp`` could not be imported and what to run instead."""
    if installed_version is None:
        problem = "The optional mcp package is not installed."
    else:
        major = re.match(r"\d+", installed_version)
        if major and int(major.group()) >= 2:
            problem = (
                f"mcp {installed_version} is installed, but mcp 2.0 removed "
                "mcp.server.fastmcp, which this server is built on."
            )
        else:
            problem = (
                f"mcp {installed_version} is installed, but mcp.server.fastmcp "
                f"could not be imported from it: {error}"
            )
    return "\n".join(
        [
            problem,
            f"This server needs {MCP_REQUIREMENT}, which the [mcp] extra pins. Install it with",
            "  uv pip install -e '.[mcp]'   (from a clone of this repository), or",
            f"  uv pip install '{MCP_REQUIREMENT}'",
            "For Claude Code or Claude Desktop, use eu-reg-mcp instead. It is the supported",
            "Claude integration and serves this classifier as an MCP tool:",
            f"  {EU_REG_MCP_COMMAND}",
        ]
    )


def build_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit(mcp_unavailable_message(_installed_mcp_version(), exc)) from exc

    server = FastMCP("eu-ai-act-classifier")

    @server.tool()
    def classify_ai_system(
        profile: dict[str, Any], include_advisory: bool = False
    ) -> dict[str, Any]:
        """Classify an AI system under the EU AI Act (Reg (EU) 2024/1689).

        `profile` is a SystemProfile object (name, roles, annex_iii_area,
        prohibited_practices, is_gpai_model, training_flops, transparency
        screens, …). Returns a ClassificationReport: risk tier, disposition,
        obligations with article citations, required documentation, open
        questions for review, and any citations pending verification.
        """
        report = classify(SystemProfile.model_validate(profile), include_advisory=include_advisory)
        return report.model_dump(mode="json")

    @server.tool()
    def classify_ai_system_text(profile: dict[str, Any], include_advisory: bool = False) -> str:
        """As classify_ai_system, but returns the human-readable report text."""
        return render_report(
            classify(SystemProfile.model_validate(profile), include_advisory=include_advisory)
        )

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
