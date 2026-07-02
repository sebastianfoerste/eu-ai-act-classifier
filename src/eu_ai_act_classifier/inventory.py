"""AI systems inventory projection built from the deterministic classifier."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .artifacts import ARTIFACT_NAMES
from .engine import classify
from .models import ClassificationReport, Disposition, RegulatorySource, RiskTier, SystemProfile

INVENTORY_SCHEMA = "eu-ai-act-classifier.system-inventory.v1"
SYSTEM_REVIEW_TABLE_SCHEMA = "eu-ai-act-classifier.system-review-table.v1"
SYSTEM_REVIEW_PROFILE_SCHEMA = "eu-ai-act-classifier.system-review-profile.v1"


class AISystemInventoryRow(BaseModel):
    system_id: str
    name: str
    role: str
    risk_tier: str
    disposition: str
    source_manifest_status: Literal["complete", "review_required", "missing"]
    open_facts: list[str]
    obligations: list[str]
    draft_artifacts: list[str]
    review_status: Literal["determined", "review_required", "blocked"]
    next_action: str


class AISystemPinpointCitation(BaseModel):
    source_id: str
    source_class: Literal[
        "binding_law",
        "official_guidance",
        "provisional_context",
        "advisory_source",
    ]
    citation_label: str
    url: str
    verified: bool
    legal_status_class: str
    source_status: str
    support_ref: str
    quote: str | None = None
    offset_start: int | None = None
    offset_end: int | None = None
    derived_from: Literal["classifier_finding", "obligation_graph", "source_manifest"]


class AISystemReviewTableRow(BaseModel):
    row_id: str
    system_id: str
    system_name: str
    factor_id: str
    factor_label: str
    classifier_value: str
    source_status: Literal["complete", "review_required", "missing"]
    obligation_refs: list[str]
    draft_artifacts: list[str]
    pinpoint_citations: list[AISystemPinpointCitation]
    reviewer_notes: list[str]
    cell_status: Literal["complete", "review_required", "blocked"]
    review_status: Literal["determined", "review_required", "blocked"]
    next_action: str


class AISystemReviewControlRoute(BaseModel):
    key: str
    label: str
    route: Literal["deterministic_classifier", "draft_artifact_builder", "external_action"]
    status: Literal["determined", "review_required", "blocked"]
    gate: str


class AISystemReviewSourceConnector(BaseModel):
    key: str
    label: str
    status: Literal["enabled", "review_required", "blocked"]
    scope: str
    gate: str


class AISystemReviewControlProfile(BaseModel):
    schema_id: str = Field("eu-ai-act-classifier.review-control-profile.v1", alias="schema")
    externalActionAllowed: bool = False
    routeSummary: str
    contextWindowStrategy: str
    workflowRoutes: list[AISystemReviewControlRoute]
    sourceConnectors: list[AISystemReviewSourceConnector]


class AISystemGuidedInput(BaseModel):
    key: str
    label: str
    prompt: str
    required: bool = True


class AISystemPromptBrief(BaseModel):
    schema_id: str = Field("eu-ai-act-classifier.system-prompt-brief.v1", alias="schema")
    objective: str
    actor: str
    jurisdiction: str
    sourceHierarchy: list[str]
    requiredInputs: list[str]
    guidedInputs: list[AISystemGuidedInput]
    outputFormat: list[str]
    reviewGate: str
    failureConditions: list[str]
    suggestedPrompt: str


class AISystemReviewTableScale(BaseModel):
    schema_id: str = Field("eu-ai-act-classifier.system-review-table-scale.v1", alias="schema")
    rowCount: int
    columnCount: int
    estimatedCellTasks: int
    maxVaultDocuments: int
    resetStrategy: str
    needleInHaystackStrategy: str


class AISystemReviewLayer(BaseModel):
    key: Literal[
        "large_language_models",
        "agentic_harness",
        "data_integrations",
        "context_knowledge",
        "legal_capabilities",
        "products_interfaces",
        "security_governance",
    ]
    label: str
    status: Literal["implemented", "metadata_only", "blocked"]
    evidence: str
    gate: str


class AISystemReviewSkill(BaseModel):
    id: str
    label: str
    objective: str
    outputSchema: list[str]
    reviewGate: str
    externalActionAllowed: bool = False


class AISystemReviewProfile(BaseModel):
    schema_id: str = Field(SYSTEM_REVIEW_PROFILE_SCHEMA, alias="schema")
    reviewLayers: list[AISystemReviewLayer]
    agentPlan: dict[Literal["plan", "execute", "review", "deliver"], str]
    skills: list[AISystemReviewSkill]
    tabularReview: dict[str, object]
    trustedSources: dict[str, object]
    editorDraft: dict[str, object]
    wordExportPackage: dict[str, object]
    portalRoom: dict[str, object]
    monitors: dict[str, object]
    lists: dict[str, object]
    securityGovernance: dict[str, object]
    vendorIntegration: Literal["none"] = "none"
    externalActionAllowed: bool = False
    reviewNotice: str


class AISystemReviewTable(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_id: str = Field(SYSTEM_REVIEW_TABLE_SCHEMA, alias="schema")
    generatedAt: str
    summary: dict[str, int]
    rows: list[AISystemReviewTableRow]
    controlProfile: AISystemReviewControlProfile
    reviewTableScale: AISystemReviewTableScale
    promptBrief: AISystemPromptBrief
    reviewProfile: AISystemReviewProfile
    reviewNotice: str


class AISystemInventory(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_id: str = Field(INVENTORY_SCHEMA, alias="schema")
    sourceMode: Literal["example_profiles", "runtime_projection"] = "example_profiles"
    generatedAt: str
    subjectId: str
    module: Literal["eu-ai-act-classifier"]
    sourceRefs: list[str]
    evidenceArtifacts: list[str]
    reviewStatus: Literal["determined", "review_required", "blocked"]
    blockers: list[str]
    warnings: list[str]
    exportAllowed: bool
    externalActionAllowed: bool
    nextAction: str
    systems: list[AISystemInventoryRow]
    reviewTable: AISystemReviewTable


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _public_label(value: str) -> str:
    text = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "[redacted-email]", value, flags=re.I)
    text = re.sub(
        r"\b(?:client|candidate|matter|account)\s*[:#]\s*[A-Za-z0-9._-]+",
        "[redacted-reference]",
        text,
        flags=re.I,
    )
    return text[:160]


def load_example_profiles(examples_dir: Path | str = Path("examples")) -> list[SystemProfile]:
    root = Path(examples_dir)
    profiles: list[SystemProfile] = []
    for path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            profiles.append(SystemProfile.model_validate(payload))
        except (OSError, json.JSONDecodeError, ValidationError):
            continue
    return profiles


def _source_manifest_status(
    report: ClassificationReport,
) -> Literal["complete", "review_required", "missing"]:
    if not report.source_manifest:
        return "missing"
    if report.unverified_citations:
        return "review_required"
    return "complete"


def _review_status(
    report: ClassificationReport,
) -> Literal["determined", "review_required", "blocked"]:
    if report.risk_tier is RiskTier.PROHIBITED:
        return "blocked"
    if report.disposition is Disposition.REQUIRES_REVIEW:
        return "review_required"
    return "determined"


def _next_action(report: ClassificationReport) -> str:
    if report.risk_tier is RiskTier.PROHIBITED:
        return "Stop or redesign the use case before deployment."
    if report.open_questions:
        return "Resolve open facts and rerun the deterministic classifier."
    if report.obligations or report.documentation_required or report.transparency_obligations:
        return "Prepare draft artifacts for reviewer sign-off."
    return "Record the determination and monitor source updates."


def _inventory_row(profile: SystemProfile, report: ClassificationReport) -> AISystemInventoryRow:
    obligations = [
        *[f"{item.article}: {item.title}" for item in report.obligations],
        *[f"{item.article}: {item.title}" for item in report.documentation_required],
        *[f"{item.article}: {item.title}" for item in report.transparency_obligations],
    ]
    return AISystemInventoryRow(
        system_id=_public_label(profile.name.lower().replace(" ", "-")),
        name=_public_label(profile.name),
        role=", ".join(role.value for role in profile.roles),
        risk_tier=report.risk_tier.value,
        disposition=report.disposition.value,
        source_manifest_status=_source_manifest_status(report),
        open_facts=[_public_label(item) for item in report.open_questions],
        obligations=obligations[:12],
        draft_artifacts=sorted(ARTIFACT_NAMES),
        review_status=_review_status(report),
        next_action=_next_action(report),
    )


def _reviewer_notes(report: ClassificationReport) -> list[str]:
    notes: list[str] = []
    if report.open_questions:
        notes.extend(f"Open fact: {_public_label(item)}" for item in report.open_questions[:3])
    if report.unverified_citations:
        notes.append("One or more citations require source verification.")
    if report.risk_tier is RiskTier.PROHIBITED:
        notes.append("Prohibited-practice screen blocks deployment pending redesign.")
    if report.disposition is Disposition.REQUIRES_REVIEW:
        notes.append("Classifier disposition routes this system to lawyer review.")
    return notes


def _source_index(report: ClassificationReport) -> dict[str, RegulatorySource]:
    return {source.source_id: source for source in report.source_manifest}


def _source_by_url(
    report: ClassificationReport,
    source_url: str,
) -> RegulatorySource | None:
    return next(
        (source for source in report.source_manifest if source.url == source_url),
        None,
    )


def _binding_source(report: ClassificationReport) -> RegulatorySource | None:
    sources = _source_index(report)
    return sources.get("ai-act-2024-1689") or next(iter(report.source_manifest), None)


def _source_class(
    source: RegulatorySource,
) -> Literal["binding_law", "official_guidance", "provisional_context", "advisory_source"]:
    status = source.legal_status.value
    if status == "binding_level_1":
        return "binding_law"
    if status == "provisional_political_agreement":
        return "provisional_context"
    if "guidance" in status:
        return "official_guidance"
    return "advisory_source"


def _pinpoint(
    source: RegulatorySource,
    *,
    support_ref: str,
    verified: bool,
    derived_from: Literal["classifier_finding", "obligation_graph", "source_manifest"],
) -> AISystemPinpointCitation:
    quote = f"{source.citation_label}: {support_ref}"
    return AISystemPinpointCitation(
        source_id=source.source_id,
        source_class=_source_class(source),
        citation_label=source.citation_label,
        url=source.url,
        verified=verified,
        legal_status_class=source.legal_status.value,
        source_status=source.legal_status.value,
        support_ref=support_ref,
        quote=quote,
        offset_start=0,
        offset_end=len(quote),
        derived_from=derived_from,
    )


def _fallback_source_projection(report: ClassificationReport) -> list[AISystemPinpointCitation]:
    source = _binding_source(report)
    if source is None:
        return []
    return [
        _pinpoint(
            source,
            support_ref=source.citation_label,
            verified=True,
            derived_from="source_manifest",
        )
    ]


def _risk_citation_projection(report: ClassificationReport) -> list[AISystemPinpointCitation]:
    source = _binding_source(report)
    if source is None:
        return []
    seen: set[tuple[str, str]] = set()
    citations: list[AISystemPinpointCitation] = []
    for finding in report.findings:
        key = (source.source_id, finding.citation)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            _pinpoint(
                source,
                support_ref=finding.citation,
                verified=finding.citation_verified,
                derived_from="classifier_finding",
            )
        )
    return citations or _fallback_source_projection(report)


def _obligation_citation_projection(report: ClassificationReport) -> list[AISystemPinpointCitation]:
    seen: set[tuple[str, str]] = set()
    citations: list[AISystemPinpointCitation] = []
    for item in report.obligation_graph:
        source = _source_by_url(report, item.source_url) or _binding_source(report)
        if source is None:
            continue
        key = (source.source_id, item.article)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            _pinpoint(
                source,
                support_ref=item.article,
                verified=True,
                derived_from="obligation_graph",
            )
        )
    return citations or _fallback_source_projection(report)


def _source_projection_for_factor(
    factor_id: str,
    report: ClassificationReport,
) -> list[AISystemPinpointCitation]:
    if factor_id == "risk_classification":
        return _risk_citation_projection(report)
    if factor_id in {"operator_role", "artifact_pack"}:
        return _obligation_citation_projection(report)
    return _fallback_source_projection(report)


def _cell_status(
    *,
    source_status: Literal["complete", "review_required", "missing"],
    review_status: Literal["determined", "review_required", "blocked"],
    citations: list[AISystemPinpointCitation],
) -> Literal["complete", "review_required", "blocked"]:
    if review_status == "blocked":
        return "blocked"
    if source_status != "complete":
        return "review_required"
    if any(not citation.verified for citation in citations):
        return "review_required"
    return "complete"


def _review_table_rows(
    profile: SystemProfile,
    report: ClassificationReport,
    inventory_row: AISystemInventoryRow,
) -> list[AISystemReviewTableRow]:
    source_status = _source_manifest_status(report)
    obligations = [item.obligation_id for item in report.obligation_graph]
    draft_artifacts = sorted(ARTIFACT_NAMES)
    reviewer_notes = _reviewer_notes(report)
    base = {
        "system_id": inventory_row.system_id,
        "system_name": inventory_row.name,
        "source_status": source_status,
        "draft_artifacts": draft_artifacts,
        "reviewer_notes": reviewer_notes,
        "review_status": inventory_row.review_status,
    }
    role_value = ", ".join(role.value for role in profile.roles)
    factor_rows = [
        (
            "scope",
            "Scope assessment",
            report.scope.status.value,
            [],
            "Resolve scope facts before relying on downstream duties."
            if report.scope.notes
            else "Scope facts are recorded for reviewer confirmation.",
        ),
        (
            "risk_classification",
            "Risk classification",
            report.risk_tier.value,
            obligations,
            inventory_row.next_action,
        ),
        (
            "operator_role",
            "Operator role",
            role_value,
            obligations,
            "Confirm provider, deployer and value-chain roles before sign-off.",
        ),
        (
            "artifact_pack",
            "Draft artifact pack",
            f"{len(draft_artifacts)} draft artifacts",
            obligations,
            "Prepare only draft artifacts for qualified reviewer sign-off.",
        ),
    ]

    rows: list[AISystemReviewTableRow] = []
    for factor_id, factor_label, classifier_value, obligation_refs, next_action in factor_rows:
        citations = _source_projection_for_factor(factor_id, report)[:12]
        rows.append(
            AISystemReviewTableRow(
                row_id=f"{inventory_row.system_id}:{factor_id}",
                factor_id=factor_id,
                factor_label=factor_label,
                classifier_value=classifier_value,
                obligation_refs=obligation_refs[:12],
                next_action=next_action,
                pinpoint_citations=citations,
                cell_status=_cell_status(
                    source_status=source_status,
                    review_status=inventory_row.review_status,
                    citations=citations,
                ),
                **base,
            )
        )
    return rows


def _build_review_table(
    profile_reports: list[tuple[SystemProfile, ClassificationReport, AISystemInventoryRow]],
    *,
    generated_at: str,
) -> AISystemReviewTable:
    rows = [
        row
        for profile, report, inventory_row in profile_reports
        for row in _review_table_rows(profile, report, inventory_row)
    ]
    summary = {
        "rows": len(rows),
        "blocked": sum(row.review_status == "blocked" for row in rows),
        "review_required": sum(row.review_status == "review_required" for row in rows),
        "determined": sum(row.review_status == "determined" for row in rows),
    }
    control_profile = _review_control_profile(rows, summary)
    review_table_scale = _review_table_scale(rows)
    prompt_brief = _prompt_brief(rows, summary)
    return AISystemReviewTable(
        generatedAt=generated_at,
        summary=summary,
        rows=rows,
        controlProfile=control_profile,
        reviewTableScale=review_table_scale,
        promptBrief=prompt_brief,
        reviewProfile=_system_review_profile(
            rows=rows,
            summary=summary,
            control_profile=control_profile,
            review_table_scale=review_table_scale,
            prompt_brief=prompt_brief,
        ),
        reviewNotice=(
            "System review table rows restate deterministic classifier output. "
            "They remain draft-only until facts, sources and legal characterisation are reviewed."
        ),
    )


def _review_table_scale(rows: list[AISystemReviewTableRow]) -> AISystemReviewTableScale:
    column_count = 10
    return AISystemReviewTableScale(
        rowCount=len(rows),
        columnCount=column_count,
        estimatedCellTasks=len(rows) * column_count,
        maxVaultDocuments=100_000,
        resetStrategy=(
            "Each AI-system factor and generated review column is evaluated as an "
            "isolated review cell."
        ),
        needleInHaystackStrategy=(
            "Needle-in-haystack questions use selected source-manifest and obligation "
            "chunks. Comprehensive review runs factor-by-factor through the review table."
        ),
    )


def _prompt_brief(
    rows: list[AISystemReviewTableRow],
    summary: dict[str, int],
) -> AISystemPromptBrief:
    blocked_systems = sorted({row.system_name for row in rows if row.review_status == "blocked"})
    review_required = sorted(
        {row.system_name for row in rows if row.review_status == "review_required"}
    )
    failure_conditions = [
        "Do not state a categorical legal conclusion beyond the deterministic classifier result.",
        "Do not omit open facts, source status or the reviewer gate.",
        "Do not generate regulator, customer or public communications.",
    ]
    if blocked_systems:
        failure_conditions.append(
            "Blocked systems must be described as deployment-blocked pending redesign or review."
        )
    return AISystemPromptBrief(
        objective="Prepare a supervised review note for one AI system classification factor.",
        actor="EU AI Act reviewer",
        jurisdiction="EU AI Act classification and obligation mapping",
        sourceHierarchy=[
            "system profile facts",
            "deterministic classifier result",
            "source manifest",
            "obligation graph",
            "draft artifact inventory",
        ],
        requiredInputs=[
            "system name and operator role",
            "factor id and classifier value",
            "source status and open facts",
            "obligation references and draft artifacts",
            "review status and next action",
        ],
        guidedInputs=[
            AISystemGuidedInput(
                key="system_factor",
                label="System factor",
                prompt="Select one system profile and classification factor for review.",
            ),
            AISystemGuidedInput(
                key="source_status",
                label="Source status",
                prompt="Attach source-manifest status, unverified citations and open facts.",
            ),
            AISystemGuidedInput(
                key="obligation_graph",
                label="Obligation graph",
                prompt=(
                    "Provide obligation references and draft artifact inventory for this factor."
                ),
            ),
            AISystemGuidedInput(
                key="review_decision",
                label="Review decision",
                prompt=(
                    "Record reviewer notes, next action and whether the classifier "
                    "result is accepted."
                ),
            ),
            AISystemGuidedInput(
                key="external_use_gate",
                label="External use gate",
                prompt="Confirm that no regulator, customer or public output will be sent.",
            ),
        ],
        outputFormat=[
            "classification factor",
            "source status",
            "obligation impact",
            "open facts",
            "reviewer next action",
        ],
        reviewGate=(
            "Draft-only. Qualified review is required before deployment or external reliance."
        ),
        failureConditions=failure_conditions,
        suggestedPrompt="\n".join(
            [
                "Role: EU AI Act reviewer.",
                "Objective: prepare a source-aware review note for one system factor.",
                f"Inventory state: {summary['determined']} determined row(s), "
                f"{summary['review_required']} review-required row(s), "
                f"{summary['blocked']} blocked row(s).",
                f"Blocked systems: {', '.join(blocked_systems) if blocked_systems else 'none'}.",
                "Review-required systems: "
                f"{', '.join(review_required) if review_required else 'none'}.",
                (
                    "Output: factor, classifier value, source status, obligations, "
                    "open facts and next action."
                ),
                (
                    "Review gate: draft only. Do not create external legal, "
                    "customer or regulator output."
                ),
            ]
        ),
    )


def _review_control_profile(
    rows: list[AISystemReviewTableRow],
    summary: dict[str, int],
) -> AISystemReviewControlProfile:
    complete_sources = sum(row.source_status == "complete" for row in rows)
    unique_systems = sorted({row.system_id for row in rows})
    return AISystemReviewControlProfile(
        routeSummary=(
            f"{summary['determined']} determined row(s), "
            f"{summary['review_required']} review-required row(s), "
            f"{summary['blocked']} blocked row(s)."
        ),
        contextWindowStrategy=(
            f"{len(rows)} factor row(s) evaluated one system and factor at a time."
        ),
        workflowRoutes=[
            AISystemReviewControlRoute(
                key="scope-screen",
                label="Scope screen",
                route="deterministic_classifier",
                status="blocked" if summary["blocked"] else "determined",
                gate="Scope result must be reviewed before downstream obligations are relied on.",
            ),
            AISystemReviewControlRoute(
                key="risk-classification",
                label="Risk classification",
                route="deterministic_classifier",
                status="blocked" if summary["blocked"] else "determined",
                gate="No categorical conclusion beyond the classifier result is added.",
            ),
            AISystemReviewControlRoute(
                key="artifact-pack",
                label="Draft artifact pack",
                route="draft_artifact_builder",
                status="review_required" if summary["review_required"] else "determined",
                gate="FRIA, dossier and transparency artifacts remain draft-only.",
            ),
            AISystemReviewControlRoute(
                key="external-action",
                label="External action",
                route="external_action",
                status="blocked",
                gate="No regulator, customer or public communication is sent by the classifier.",
            ),
        ],
        sourceConnectors=[
            AISystemReviewSourceConnector(
                key="example-profile-inventory",
                label="Example profiles",
                status="enabled",
                scope=f"{len(unique_systems)} system profile(s) in this projection.",
                gate="Synthetic examples only unless a user-provided profile is explicitly loaded.",
            ),
            AISystemReviewSourceConnector(
                key="legal-source-manifest",
                label="Legal source manifest",
                status="enabled" if complete_sources == len(rows) and rows else "review_required",
                scope=f"{complete_sources}/{len(rows)} row(s) have complete source status.",
                gate="Current legal source status must be verified before reliance.",
            ),
            AISystemReviewSourceConnector(
                key="obligation-graph",
                label="Obligation graph",
                status="enabled",
                scope=(
                    f"{sum(bool(row.obligation_refs) for row in rows)} "
                    "row(s) reference obligations."
                ),
                gate="Obligation graph items are draft compliance work, not legal sign-off.",
            ),
            AISystemReviewSourceConnector(
                key="external-delivery",
                label="External delivery",
                status="blocked",
                scope="External legal, customer or regulator communications are not implemented.",
                gate="Human review is mandatory before any external use.",
            ),
        ],
    )


def _system_review_profile(
    *,
    rows: list[AISystemReviewTableRow],
    summary: dict[str, int],
    control_profile: AISystemReviewControlProfile,
    review_table_scale: AISystemReviewTableScale,
    prompt_brief: AISystemPromptBrief,
) -> AISystemReviewProfile:
    complete_sources = sum(row.source_status == "complete" for row in rows)
    verified_citations = sum(
        citation.verified for row in rows for citation in row.pinpoint_citations
    )
    total_citations = sum(len(row.pinpoint_citations) for row in rows)
    obligation_rows = sum(bool(row.obligation_refs) for row in rows)
    return AISystemReviewProfile(
        schema=SYSTEM_REVIEW_PROFILE_SCHEMA,
        reviewLayers=[
            AISystemReviewLayer(
                key="large_language_models",
                label="Large language model routing",
                status="blocked",
                evidence="Inventory projection uses the deterministic Python classifier.",
                gate="No LLM route or external output is used for classification.",
            ),
            AISystemReviewLayer(
                key="agentic_harness",
                label="Agentic harness",
                status="metadata_only",
                evidence="Prompt brief can seed draft-only review notes.",
                gate="No autonomous legal conclusion is added beyond classifier output.",
            ),
            AISystemReviewLayer(
                key="data_integrations",
                label="Data and integrations",
                status="implemented",
                evidence="Example profiles, source manifest and obligation graph are linked.",
                gate="Synthetic examples only unless a user explicitly loads a profile.",
            ),
            AISystemReviewLayer(
                key="context_knowledge",
                label="Context and knowledge",
                status="implemented",
                evidence=f"{complete_sources}/{len(rows)} row(s) have complete source status.",
                gate="Source-manifest status remains visible in every review row.",
            ),
            AISystemReviewLayer(
                key="legal_capabilities",
                label="Legal capabilities",
                status="implemented",
                evidence=(
                    f"{summary['determined']} determined, "
                    f"{summary['review_required']} review-required, "
                    f"{summary['blocked']} blocked row(s)."
                ),
                gate="Qualified review is required before deployment or external reliance.",
            ),
            AISystemReviewLayer(
                key="products_interfaces",
                label="Products and interfaces",
                status="implemented",
                evidence="Inventory, review table, prompt brief and draft artifacts are exposed.",
                gate="Artifacts remain draft-only.",
            ),
            AISystemReviewLayer(
                key="security_governance",
                label="Security and governance",
                status="implemented",
                evidence="External action is false and sensitive labels are redacted.",
                gate="No regulator, customer or public communication is sent.",
            ),
        ],
        agentPlan={
            "plan": "Select system profile, factor row, source manifest and obligation graph.",
            "execute": "Run the deterministic classifier and draft artifact inventory.",
            "review": "Check source status, obligation refs, open facts and reviewer notes.",
            "deliver": (
                "Record a local review table or draft artifact pack after reviewer sign-off."
            ),
        },
        skills=[
            AISystemReviewSkill(
                id="system-factor-review",
                label="System factor review",
                objective=prompt_brief.objective,
                outputSchema=prompt_brief.outputFormat,
                reviewGate=prompt_brief.reviewGate,
            ),
            AISystemReviewSkill(
                id="obligation-graph-review",
                label="Obligation graph review",
                objective="Review obligation graph references and draft artifact coverage.",
                outputSchema=["obligation refs", "draft artifacts", "source status", "next action"],
                reviewGate="Obligation graph output remains draft compliance work.",
            ),
            AISystemReviewSkill(
                id="source-manifest-check",
                label="Source manifest check",
                objective="Verify source id, citation label, URL and legal-status class per row.",
                outputSchema=["source id", "citation label", "verified flag", "legal-status class"],
                reviewGate="Current source status must be verified before reliance.",
            ),
        ],
        tabularReview={
            "schema": review_table_scale.schema_id,
            "rowCount": review_table_scale.rowCount,
            "columnCount": review_table_scale.columnCount,
            "estimatedCellTasks": review_table_scale.estimatedCellTasks,
            "reviewMode": "review_gated",
            "externalActionAllowed": False,
        },
        trustedSources={
            "sourceMode": "source_manifest_and_obligation_graph",
            "verifiedCitations": verified_citations,
            "totalCitations": total_citations,
            "completeSourceRows": complete_sources,
            "externalActionAllowed": False,
        },
        editorDraft={
            "status": "draft_only",
            "sourceTraceability": "required",
            "approvalRequired": True,
        },
        wordExportPackage={
            "status": "review_gated",
            "formats": ["json", "markdown", "draft-artifacts"],
            "externalActionAllowed": False,
        },
        portalRoom={
            "accessMode": "local_cockpit",
            "roleBasedAccess": False,
            "auditTrailRequired": True,
            "externalGuestAccessAllowed": False,
        },
        monitors={
            "status": "metadata_only",
            "perimeter": [
                "system profiles",
                "source manifest",
                "obligation graph",
                "draft artifacts",
            ],
            "deliveryStatus": "blocked_without_review",
        },
        lists={
            "status": "implemented",
            "items": [
                {
                    "key": "source-manifest-review",
                    "label": "Verify source manifest and citation coverage",
                    "owner": "EU AI Act reviewer",
                    "signOffRequired": True,
                },
                {
                    "key": "obligation-graph-review",
                    "label": f"Review obligation refs across {obligation_rows} row(s)",
                    "owner": "EU AI Act reviewer",
                    "signOffRequired": True,
                },
                {
                    "key": "external-use-gate",
                    "label": "Confirm no external legal or customer output is sent",
                    "owner": "Responsible reviewer",
                    "signOffRequired": True,
                },
            ],
        },
        securityGovernance={
            "zeroTrust": True,
            "noFoundationModelTraining": True,
            "dataRetention": "local_runtime_projection",
            "auditTrail": "review_table_digest",
            "approvalGate": "required_for_deployment_or_external_reliance",
        },
        vendorIntegration="none",
        externalActionAllowed=False,
        reviewNotice=(
            "Review-profile metadata generated from local system-inventory evidence. "
            "The deterministic classifier remains the boundary for legal characterisation."
        ),
    )


def build_system_inventory(
    profiles: list[SystemProfile],
    *,
    generated_at: str | None = None,
    subject_id: str = "example-profile-inventory",
) -> AISystemInventory:
    generated_at_value = generated_at or _now()
    classified = [(profile, classify(profile, include_advisory=True)) for profile in profiles]
    profile_reports = [
        (profile, report, _inventory_row(profile, report)) for profile, report in classified
    ]
    rows = [inventory_row for _, _, inventory_row in profile_reports]
    blockers = [f"{row.system_id}: prohibited" for row in rows if row.review_status == "blocked"]
    warnings = [
        f"{row.system_id}: open facts" for row in rows if row.review_status == "review_required"
    ]
    review_status: Literal["determined", "review_required", "blocked"]
    if blockers:
        review_status = "blocked"
    elif warnings:
        review_status = "review_required"
    else:
        review_status = "determined"
    source_refs = sorted(
        {source.source_id for _, report in classified for source in report.source_manifest}
    )

    return AISystemInventory(
        generatedAt=generated_at_value,
        subjectId=subject_id,
        module="eu-ai-act-classifier",
        sourceRefs=source_refs,
        evidenceArtifacts=["classification-report", "review-dossier", *sorted(ARTIFACT_NAMES)],
        reviewStatus=review_status,
        blockers=blockers,
        warnings=warnings,
        exportAllowed=not blockers,
        externalActionAllowed=False,
        nextAction=(
            blockers[0]
            if blockers
            else warnings[0]
            if warnings
            else "Record current determinations and monitor source updates."
        ),
        systems=rows,
        reviewTable=_build_review_table(profile_reports, generated_at=generated_at_value),
    )


def build_example_inventory(
    examples_dir: Path | str = Path("examples"),
    *,
    generated_at: str | None = None,
) -> AISystemInventory:
    return build_system_inventory(
        load_example_profiles(examples_dir),
        generated_at=generated_at,
    )
