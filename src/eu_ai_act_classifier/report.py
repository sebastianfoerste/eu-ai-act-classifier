"""Human-readable rendering of a :class:`ClassificationReport`."""

from __future__ import annotations

from .models import ClassificationReport, Disposition, Obligation, RiskTier, SourceStatus

_TIER_LABEL = {
    RiskTier.OUT_OF_SCOPE: "OUTSIDE AI ACT SCOPE",
    RiskTier.PROHIBITED: "PROHIBITED (Art. 5 AIA)",
    RiskTier.HIGH: "HIGH-RISK (Art. 6 AIA)",
    RiskTier.LIMITED: "LIMITED RISK, transparency only (Art. 50 AIA)",
    RiskTier.MINIMAL: "MINIMAL RISK",
}


def _obligations_block(title: str, obligations: list[Obligation]) -> list[str]:
    if not obligations:
        return []
    lines = [f"{title}:"]
    for ob in obligations:
        flag = "" if ob.citation_verified else " [noch zu verifizieren]"
        lines.append(f"  - {ob.article}{flag}: {ob.title}. {ob.requirement}")
    lines.append("")
    return lines


def render_report(report: ClassificationReport) -> str:
    lines: list[str] = []
    lines.append(f"EU AI Act classification: {report.system}")
    lines.append(f"Risk tier: {_TIER_LABEL[report.risk_tier]}")
    lines.append(f"Disposition: {report.disposition.value.upper()}")
    lines.append(f"Scope status: {report.scope.status.value}")
    lines.append(f"Roles: {', '.join(r.value for r in report.roles)}")
    if report.is_gpai:
        gpai = "general-purpose AI model"
        if report.gpai_systemic:
            gpai += " with systemic risk (Art. 51 AIA)"
        lines.append(f"GPAI: {gpai}")
    lines.append("")

    if report.disposition is Disposition.REQUIRES_REVIEW:
        lines.append("This classification requires lawyer review before it is relied upon.")
        lines.append("")

    lines.append("Scope and intake:")
    lines.append(f"  AI system: {report.scope.is_ai_system}")
    lines.append(f"  EU nexus: {report.scope.eu_nexus}")
    if report.scope.intended_purpose_source:
        lines.append(f"  Intended-purpose source: {report.scope.intended_purpose_source}")
    if report.scope.excluded_use_flags:
        flags = ", ".join(flag.value for flag in report.scope.excluded_use_flags)
        lines.append(f"  Excluded-use flags: {flags}")
    lines.append(f"  Transitional status: {report.scope.transitional_status}")
    lines.append("")

    if report.findings:
        lines.append("Findings:")
        for f in report.findings:
            flag = "" if f.citation_verified else " [noch zu verifizieren]"
            lines.append(f"  [{f.severity.value}] {f.citation}{flag}: {f.title}")
            if f.detail:
                lines.append(f"      {f.detail}")
        lines.append("")

    lines += _obligations_block("Obligations", report.obligations)
    lines += _obligations_block("Documentation to maintain", report.documentation_required)
    lines += _obligations_block("Transparency obligations", report.transparency_obligations)

    if report.obligation_graph:
        lines.append("Obligation graph:")
        for item in report.obligation_graph:
            lines.append(
                "  - "
                f"{item.obligation_id}: {item.article} ({item.actor.value}), "
                f"evidence: {item.evidence_artifact}, review: {item.review_status.value}"
            )
        lines.append("")

    if report.open_questions:
        lines.append("Open questions for review:")
        for q in report.open_questions:
            lines.append(f"  ? {q}")
        lines.append("")

    _append_timeline(lines, report)

    if report.advisory_notes:
        lines.append("Advisory overlay:")
        for note in report.advisory_notes:
            lines.append(f"  - {note.title}: {note.detail}")
            lines.append(f"    Source: {note.source_url}")
        lines.append("")

    if report.unverified_citations:
        lines.append("Citations pending verification (noch zu verifizieren):")
        for c in report.unverified_citations:
            lines.append(f"  - {c}")
        lines.append("")

    if report.source_manifest:
        lines.append("Source manifest:")
        for source in report.source_manifest:
            lines.append(
                f"  - {source.citation_label}: {source.legal_status.value}, "
                f"retrieved {source.retrieved_on}"
            )
        lines.append("")

    lines.append(report.regulation)
    lines.append(report.disclaimer)
    return "\n".join(lines)


def _append_timeline(lines: list[str], report: ClassificationReport) -> None:
    binding = [t for t in report.timeline if t.source_status is SourceStatus.BINDING_LEVEL_1]
    provisional = [
        t
        for t in report.timeline
        if t.source_status is SourceStatus.PROVISIONAL_POLITICAL_AGREEMENT
    ]
    if binding:
        lines.append("Binding application timeline:")
        for t in binding:
            lines.append(f"  {t.applies_from}: {t.provision}")
        lines.append("")
    if provisional:
        lines.append("Provisional political-agreement timeline:")
        for t in provisional:
            lines.append(f"  {t.applies_from}: {t.provision}")
            lines.append(f"      {t.note}")
        lines.append("")
