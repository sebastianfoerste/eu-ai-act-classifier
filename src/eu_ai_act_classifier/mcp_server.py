"""MCP server exposing the classifier as an agent-callable tool.

An agent, for example a product-intake agent on an AI platform, can call
``classify_ai_system`` with a system profile and get back a cited, tiered,
review-gated classification. The ``mcp`` dependency is optional and imported
lazily, so the core engine never depends on it.

Run::

    pip install 'eu-ai-act-classifier[mcp]'
    eu-ai-act-classifier-mcp

or let uv fetch the package and start the server::

    uvx --from 'eu-ai-act-classifier[mcp]' eu-ai-act-classifier-mcp

The server is built on ``mcp.server.fastmcp`` from the 1.x SDK, which mcp 2.0
renamed, so the ``[mcp]`` extra pins ``mcp>=1.2,<2``.
"""

from __future__ import annotations

from importlib import metadata
from typing import Any

from .engine import classify
from .models import SystemProfile
from .report import render_report

# The [mcp] extra in pyproject.toml; tests/test_mcp_server.py keeps the two in step.
MCP_REQUIREMENT = "mcp>=1.2,<2"


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
            "  uvx --from 'eu-ai-act-classifier[mcp]' eu-ai-act-classifier-mcp",
            "In a clone of the repository:",
            "  uv run --extra mcp eu-ai-act-classifier-mcp",
        ]
    )


def build_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit(_missing_extra_message(_installed_mcp_version(), exc)) from exc

    server = FastMCP("eu-ai-act-classifier")

    @server.tool()
    def classify_ai_system(
        profile: dict[str, Any], include_advisory: bool = False
    ) -> dict[str, Any]:
        """Classify an AI system under the EU AI Act (Reg (EU) 2024/1689).

        `profile` is a SystemProfile object (name, roles, annex_iii_area,
        prohibited_practices, is_gpai_model, training_flops, transparency
        screens, …; dates YYYY-MM-DD, e.g. placing_on_market_date
        "2026-03-01"). Returns a ClassificationReport: risk tier, disposition,
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
