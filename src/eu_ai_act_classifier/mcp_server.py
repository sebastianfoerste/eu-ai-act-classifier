"""MCP server exposing the classifier as an agent-callable tool.

An agent — for example a product-intake agent on an AI platform — can call
``classify_ai_system`` with a system profile and get back a cited, tiered,
review-gated classification. The ``mcp`` dependency is optional and imported
lazily, so the core engine never depends on it.

Run::

    pip install -e ".[mcp]"
    python -m eu_ai_act_classifier.mcp_server
"""

from __future__ import annotations

from typing import Any

from .engine import classify
from .models import SystemProfile
from .report import render_report


def build_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised only without the extra
        raise SystemExit('The MCP extra is not installed. Run: pip install -e ".[mcp]"') from exc

    server = FastMCP("eu-ai-act-classifier")

    @server.tool()
    def classify_ai_system(profile: dict[str, Any]) -> dict[str, Any]:
        """Classify an AI system under the EU AI Act (Reg (EU) 2024/1689).

        `profile` is a SystemProfile object (name, roles, annex_iii_area,
        prohibited_practices, is_gpai_model, training_flops, transparency
        screens, …). Returns a ClassificationReport: risk tier, disposition,
        obligations with article citations, required documentation, open
        questions for review, and any citations pending verification.
        """
        report = classify(SystemProfile.model_validate(profile))
        return report.model_dump(mode="json")

    @server.tool()
    def classify_ai_system_text(profile: dict[str, Any]) -> str:
        """As classify_ai_system, but returns the human-readable report text."""
        return render_report(classify(SystemProfile.model_validate(profile)))

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
