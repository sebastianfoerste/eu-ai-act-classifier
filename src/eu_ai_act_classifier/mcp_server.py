"""MCP server exposing the classifier as an agent-callable tool.

An agent, for example a product-intake agent on an AI platform, can call
``classify_ai_system`` with a system profile and get back a cited, tiered,
review-gated classification. The ``mcp`` dependency is optional and imported
lazily, so the core engine never depends on it.

Run::

    pip install 'eu-ai-act-classifier[mcp]'
    eu-ai-act-classifier-mcp

or let uv fetch the package and start the server::

    uvx --python 3.13 --from 'eu-ai-act-classifier[mcp]' eu-ai-act-classifier-mcp

The server is built on ``mcp.server.fastmcp`` from the 1.x SDK, which mcp 2.0
renamed (``mcp.server.mcpserver.MCPServer``). mcp releases before 1.21.1 fail
to import it under pydantic 2.14 or later, so the ``[mcp]`` extra pins
``mcp>=1.21.1,<2``. Both tools take the ``SystemProfile`` model as their
``profile`` parameter and carry read-only tool annotations; both the typed
schema and ``ToolAnnotations`` exist at the 1.21.1 floor.

For Claude Code and Claude Desktop, the recommended integration is eu-reg-mcp,
which serves this classifier as a tool next to its MiCAR tools.
"""

from __future__ import annotations

from importlib import metadata
from typing import Any

from .engine import classify
from .models import SystemProfile
from .report import render_report

# The [mcp] extra in pyproject.toml; tests/test_mcp_server.py keeps the two in step.
MCP_REQUIREMENT = "mcp>=1.21.1,<2"
# The recommended Claude integration; README.md and the docs give the same command.
EU_REG_MCP_COMMAND = "uvx --python 3.13 --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp"


def _installed_mcp_version() -> str | None:
    try:
        return metadata.version("mcp")
    except metadata.PackageNotFoundError:
        return None


def _missing_extra_message(installed_mcp: str | None, error: ImportError) -> str:
    """Say why the MCP SDK did not import and how to install the [mcp] extra."""
    if installed_mcp is None:
        reason = "The MCP extra is not installed."
    else:
        reason = (
            f"mcp {installed_mcp} is installed, but mcp.server.fastmcp could not be imported: "
            f"{error}"
        )
    return "\n".join(
        [
            reason,
            f"The server needs {MCP_REQUIREMENT}, which the [mcp] extra installs:",
            "  pip install 'eu-ai-act-classifier[mcp]'",
            "or let uv fetch the package and start the server:",
            "  uvx --python 3.13 --from 'eu-ai-act-classifier[mcp]' eu-ai-act-classifier-mcp",
            "In a clone of the repository:",
            "  uv run --extra mcp eu-ai-act-classifier-mcp",
            "For Claude Code or Claude Desktop, use eu-reg-mcp instead. It is the recommended",
            "Claude integration and serves this classifier as an MCP tool:",
            f"  {EU_REG_MCP_COMMAND}",
        ]
    )


def build_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
        from mcp.types import ToolAnnotations
    except ImportError as exc:
        raise SystemExit(_missing_extra_message(_installed_mcp_version(), exc)) from exc

    server = FastMCP("eu-ai-act-classifier")
    # Both tools read the profile and compute a report: nothing is written or fetched,
    # and the same profile always gives the same report.
    read_only = ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
    )

    # The parameter is typed as the SystemProfile model, so the tool's input schema is
    # the profile's JSON Schema (field names, enums such as prohibited_practices codes,
    # date patterns), and the SDK validates the argument before the tool runs.
    @server.tool(annotations=read_only)
    def classify_ai_system(
        profile: SystemProfile, include_advisory: bool = False
    ) -> dict[str, Any]:
        """Classify an AI system under the EU AI Act (Reg (EU) 2024/1689 as amended by
        Reg (EU) 2026/1744).

        `profile` is a SystemProfile object; its JSON Schema is this tool's input
        schema (name, roles, annex_iii_area, annex_i_section, prohibited_practices,
        is_gpai_model, training_flops, transparency screens, …; dates YYYY-MM-DD,
        e.g. placing_on_market_date "2026-03-01" for the AI system and
        gpai_model_placing_on_market_date for the model). Returns a
        ClassificationReport: risk tier, disposition, obligations with article
        citations, required documentation, open questions for review, and any
        citations pending verification.
        """
        return classify(profile, include_advisory=include_advisory).model_dump(mode="json")

    @server.tool(annotations=read_only)
    def classify_ai_system_text(profile: SystemProfile, include_advisory: bool = False) -> str:
        """As classify_ai_system, but returns the human-readable report text."""
        return render_report(classify(profile, include_advisory=include_advisory))

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
