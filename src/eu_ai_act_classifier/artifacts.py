"""Draft legal work products generated from a classification report."""

from __future__ import annotations

import re
from pathlib import Path

from .models import ClassificationReport, Disposition, ObligationGraphItem

ARTIFACT_NAMES = {
    "art-6-4-assessment",
    "fria",
    "annex-iv-checklist",
    "post-market-monitoring-plan",
    "serious-incident-register",
    "gpai-model-documentation",
    "training-content-summary",
}

DRAFT_NOTICE = (
    "Draft only. This work product is not legal advice, not a conformity assessment "
    "and not a final regulatory filing. It requires human legal review before use."
)


def selected_artifacts(selection: str) -> list[str]:
    if selection == "all":
        return sorted(ARTIFACT_NAMES)
    if selection not in ARTIFACT_NAMES:
        allowed = ", ".join(sorted(ARTIFACT_NAMES | {"all"}))
        raise ValueError(f"unknown artifact '{selection}'. Allowed values: {allowed}")
    return [selection]


def render_artifact(name: str, report: ClassificationReport) -> str:
    if name == "art-6-4-assessment":
        return _render_artifact(
            "Article 6(4) Non-High-Risk Assessment",
            report,
            [
                "Document the asserted Art. 6(3) condition.",
                "Confirm that the system does not pose a significant risk of harm.",
                "Confirm that the system does not materially influence decision-making outcomes.",
                "Record whether profiling of natural persons is performed.",
                "Record EU database registration steps where the provider relies on Art. 6(3).",
            ],
        )
    if name == "fria":
        return _render_artifact(
            "Article 27 Fundamental Rights Impact Assessment",
            report,
            [
                "Describe deployer processes and intended purpose.",
                "Describe period and frequency of use.",
                "Identify affected natural persons and groups.",
                "Identify specific fundamental-rights risks.",
                "Describe human oversight measures.",
                "Describe governance, mitigation and complaint mechanisms.",
                "Record whether a DPIA covers any overlapping obligation.",
            ],
        )
    if name == "annex-iv-checklist":
        return _render_artifact(
            "Annex IV Technical Documentation Checklist",
            report,
            [
                "System description and intended purpose.",
                "Provider details, versioning and lifecycle information.",
                "Data, training, validation and testing documentation.",
                "Risk management file and residual risk decisions.",
                "Human oversight, accuracy, robustness and cybersecurity controls.",
                "Conformity assessment and EU declaration records.",
            ],
        )
    if name == "post-market-monitoring-plan":
        return _render_artifact(
            "Post-Market Monitoring Plan",
            report,
            [
                "Define monitoring indicators and trigger thresholds.",
                "Assign owners for monitoring, escalation and corrective action.",
                "Track complaints, incidents, drift, misuse and performance changes.",
                "Define review cadence and evidence retention.",
            ],
        )
    if name == "serious-incident-register":
        return _render_artifact(
            "Serious Incident Register",
            report,
            [
                "Incident date and detection date.",
                "System version and deployment context.",
                "Affected persons, harm category and severity.",
                "Immediate mitigation and corrective action.",
                "Authority notification status and deadline.",
            ],
        )
    if name == "gpai-model-documentation":
        return _render_artifact(
            "GPAI Model Documentation Checklist",
            report,
            [
                "Model architecture, parameters and modalities.",
                "Training and testing process.",
                "Evaluation results and limitations.",
                "Information for downstream providers.",
                "Systemic-risk evaluation where applicable.",
            ],
        )
    if name == "training-content-summary":
        return _render_artifact(
            "Training-Content Summary Checklist",
            report,
            [
                "Training data categories and high-level proportions.",
                "Major data sources and collection methods.",
                "Public summary suitable for rightsholder review.",
                "Copyright policy linkage and update cadence.",
            ],
        )
    raise ValueError(f"unknown artifact '{name}'")


def write_artifacts(selection: str, directory: Path, report: ClassificationReport) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for artifact_name in selected_artifacts(selection):
        path = directory / f"{_slug(report.system)}.{artifact_name}.md"
        path.write_text(render_artifact(artifact_name, report), encoding="utf-8")
        written.append(path)
    return written


def _render_artifact(title: str, report: ClassificationReport, checklist: list[str]) -> str:
    lines = [
        f"# {title}",
        "",
        DRAFT_NOTICE,
        "",
        f"System: {report.system}",
        f"Risk tier: {report.risk_tier.value}",
        f"Disposition: {report.disposition.value}",
        f"Scope status: {report.scope.status.value}",
        "",
        "## Review Status",
        "",
        _review_status(report),
        "",
        "## Checklist",
        "",
    ]
    lines.extend(f"- {item}" for item in checklist)
    lines.extend(
        [
            "",
            "## Relevant Obligation Graph Items",
            "",
        ]
    )
    graph = _relevant_graph(report, title)
    if graph:
        lines.extend(_format_graph_item(item) for item in graph)
    else:
        lines.append("- No directly matching graph item. Confirm relevance in review.")
    lines.extend(["", "## Open Questions", ""])
    if report.open_questions:
        lines.extend(f"- {question}" for question in report.open_questions)
    else:
        lines.append("- No open questions recorded by the classifier.")
    lines.extend(["", "## Source Manifest", ""])
    lines.extend(
        (
            f"- {source.citation_label}: {source.legal_status.value}; "
            f"retrieved {source.retrieved_on}; {source.url}"
        )
        for source in report.source_manifest
    )
    return "\n".join(lines) + "\n"


def _review_status(report: ClassificationReport) -> str:
    if report.disposition is Disposition.REQUIRES_REVIEW or report.open_questions:
        return "Review required before this draft is relied upon."
    return "Classifier status is determined, but human legal review is still required."


def _relevant_graph(report: ClassificationReport, title: str) -> list[ObligationGraphItem]:
    title_lower = title.lower()
    if "fria" in title_lower or "fundamental rights" in title_lower:
        return [item for item in report.obligation_graph if item.article.startswith("Art. 27")]
    if "annex iv" in title_lower or "technical documentation" in title_lower:
        return [
            item
            for item in report.obligation_graph
            if item.article in {"Art. 18 AIA", "Art. 53(1)(a) AIA"}
        ]
    if "post-market" in title_lower:
        return [item for item in report.obligation_graph if item.article.startswith("Art. 72")]
    if "serious incident" in title_lower:
        return [
            item
            for item in report.obligation_graph
            if item.article.startswith("Art. 73") or item.article.startswith("Art. 55(1)(c)")
        ]
    if "gpai" in title_lower:
        return [
            item
            for item in report.obligation_graph
            if item.article.startswith("Art. 53") or item.article.startswith("Art. 55")
        ]
    if "training-content" in title_lower:
        return [item for item in report.obligation_graph if item.article == "Art. 53(1)(d) AIA"]
    if "6(4)" in title_lower:
        return [item for item in report.obligation_graph if item.article == "Art. 49 AIA"]
    return []


def _format_graph_item(item: ObligationGraphItem) -> str:
    return (
        f"- {item.article} ({item.actor.value}): {item.requirement} "
        f"Evidence: {item.evidence_artifact}. Review: {item.review_status.value}."
    )


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "ai-system"
