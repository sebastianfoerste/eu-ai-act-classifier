"""Review dossier assembly for supervised EU AI Act triage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .artifacts import DRAFT_NOTICE, render_artifact, selected_artifacts
from .models import ClassificationReport, RegulatorySource

REVIEW_DOSSIER_SCHEMA = "eu-ai-act.review-dossier.v1"
REVIEW_STATUS = "draft_only_human_review_required"


class DossierArtifact(BaseModel):
    name: str
    filename: str
    content: str
    draft_only: bool = True


class ReviewDossier(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_id: Literal["eu-ai-act.review-dossier.v1"] = Field(
        default=REVIEW_DOSSIER_SCHEMA,
        alias="schema",
    )
    system: str
    risk_tier: str
    disposition: str
    scope_status: str
    review_status: Literal["draft_only_human_review_required"] = REVIEW_STATUS
    draft_notice: str = DRAFT_NOTICE
    next_actions: list[str] = Field(default_factory=list)
    classification_report: ClassificationReport
    obligation_graph: list[dict[str, object]]
    open_questions: list[str] = Field(default_factory=list)
    source_manifest: list[RegulatorySource] = Field(default_factory=list)
    source_summary: dict[str, int] = Field(default_factory=dict)
    artifacts: list[DossierArtifact] = Field(default_factory=list)


def build_review_dossier(
    report: ClassificationReport,
    *,
    artifact_selection: str = "all",
) -> ReviewDossier:
    artifacts = [
        DossierArtifact(
            name=artifact_name,
            filename=f"artifacts/{artifact_name}.md",
            content=render_artifact(artifact_name, report),
        )
        for artifact_name in selected_artifacts(artifact_selection)
    ]

    return ReviewDossier(
        system=report.system,
        risk_tier=report.risk_tier.value,
        disposition=report.disposition.value,
        scope_status=report.scope.status.value,
        next_actions=_next_actions(report),
        classification_report=report,
        obligation_graph=[item.model_dump(mode="json") for item in report.obligation_graph],
        open_questions=report.open_questions,
        source_manifest=report.source_manifest,
        source_summary=_source_summary(report.source_manifest),
        artifacts=artifacts,
    )


def render_review_dossier_markdown(dossier: ReviewDossier) -> str:
    lines = [
        f"# EU AI Act Review Dossier: {dossier.system}",
        "",
        dossier.draft_notice,
        "",
        "## Classification",
        "",
        f"- Risk tier: {dossier.risk_tier}",
        f"- Disposition: {dossier.disposition}",
        f"- Scope status: {dossier.scope_status}",
        f"- Review status: {dossier.review_status}",
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- {action}" for action in dossier.next_actions)
    lines.extend(["", "## Open Questions", ""])
    if dossier.open_questions:
        lines.extend(f"- {question}" for question in dossier.open_questions)
    else:
        lines.append("- No open questions recorded by the classifier.")
    lines.extend(["", "## Obligation Graph", ""])
    if dossier.obligation_graph:
        for item in dossier.obligation_graph:
            lines.append(
                "- "
                f"{item['obligation_id']}: {item['article']} ({item['actor']}), "
                f"evidence: {item['evidence_artifact']}, review: {item['review_status']}"
            )
    else:
        lines.append("- No obligation graph items generated for the submitted facts.")
    lines.extend(["", "## Source Manifest", ""])
    lines.extend(
        (
            f"- {source.citation_label}: {source.legal_status.value}; "
            f"retrieved {source.retrieved_on}; {source.url}"
        )
        for source in dossier.source_manifest
    )
    lines.extend(["", "## Draft Artifacts", ""])
    lines.extend(f"- {artifact.filename}" for artifact in dossier.artifacts)
    return "\n".join(lines) + "\n"


def write_review_dossier(
    directory: Path,
    report: ClassificationReport,
    *,
    artifact_selection: str = "all",
) -> list[Path]:
    dossier = build_review_dossier(report, artifact_selection=artifact_selection)
    directory.mkdir(parents=True, exist_ok=True)
    artifacts_dir = directory / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    paths = [
        directory / "dossier.json",
        directory / "report.json",
        directory / "source_manifest.json",
        directory / "open_questions.json",
        directory / "dossier.md",
    ]
    paths[0].write_text(dossier.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    paths[1].write_text(report.model_dump_json(indent=2), encoding="utf-8")
    paths[2].write_text(
        json.dumps(
            [source.model_dump(mode="json") for source in dossier.source_manifest],
            indent=2,
        ),
        encoding="utf-8",
    )
    paths[3].write_text(json.dumps(dossier.open_questions, indent=2), encoding="utf-8")
    paths[4].write_text(render_review_dossier_markdown(dossier), encoding="utf-8")

    for artifact in dossier.artifacts:
        path = directory / artifact.filename
        path.write_text(artifact.content, encoding="utf-8")
        paths.append(path)

    return paths


def _next_actions(report: ClassificationReport) -> list[str]:
    actions: list[str] = []
    if report.open_questions:
        actions.append("Resolve open factual or legal questions before relying on the report.")
    if any(item.review_status.value == "review_required" for item in report.obligation_graph):
        actions.append("Review obligation graph items marked review_required.")
    if report.unverified_citations:
        actions.append("Verify citations flagged by the classifier before external use.")
    actions.append("Legal reviewer to approve source status, classification and draft artifacts.")
    return actions


def _source_summary(sources: list[RegulatorySource]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for source in sources:
        status = source.legal_status.value
        summary[status] = summary.get(status, 0) + 1
    return summary


__all__ = [
    "REVIEW_DOSSIER_SCHEMA",
    "REVIEW_STATUS",
    "DossierArtifact",
    "ReviewDossier",
    "build_review_dossier",
    "render_review_dossier_markdown",
    "write_review_dossier",
]
