"""Human-readable rendering of a :class:`ClassificationReport`.

The JSON form (``report.model_dump_json()``) is the machine surface; this is
the surface a reviewing lawyer reads. The two never diverge — this function
only formats fields already on the report.
"""

from __future__ import annotations

from .models import ClassificationReport, Disposition, Obligation, RiskTier

_TIER_LABEL = {
    RiskTier.PROHIBITED: "PROHIBITED (Art. 5 AIA)",
    RiskTier.HIGH: "HIGH-RISK (Art. 6 AIA)",
    RiskTier.LIMITED: "LIMITED RISK — transparency only (Art. 50 AIA)",
    RiskTier.MINIMAL: "MINIMAL RISK",
}


def _obligations_block(title: str, obligations: list[Obligation]) -> list[str]:
    if not obligations:
        return []
    lines = [f"{title}:"]
    for ob in obligations:
        flag = "" if ob.citation_verified else "  [noch zu verifizieren]"
        lines.append(f"  - {ob.article}{flag} — {ob.title}: {ob.requirement}")
    lines.append("")
    return lines


def render_report(report: ClassificationReport) -> str:
    lines: list[str] = []
    lines.append("=" * 78)
    lines.append(f"EU AI Act classification — {report.system}")
    lines.append("=" * 78)
    lines.append(f"Risk tier:    {_TIER_LABEL[report.risk_tier]}")
    lines.append(f"Disposition:  {report.disposition.value.upper()}")
    lines.append(f"Roles:        {', '.join(r.value for r in report.roles)}")
    if report.is_gpai:
        gpai = "general-purpose AI model"
        if report.gpai_systemic:
            gpai += " with systemic risk (Art. 51 AIA)"
        lines.append(f"GPAI:         {gpai}")
    lines.append("")

    if report.disposition is Disposition.REQUIRES_REVIEW:
        lines.append("** This classification requires lawyer review before it is relied upon. **")
        lines.append("")

    if report.findings:
        lines.append("Findings:")
        for f in report.findings:
            flag = "" if f.citation_verified else "  [noch zu verifizieren]"
            lines.append(f"  [{f.severity.value}] {f.citation}{flag} — {f.title}")
            if f.detail:
                lines.append(f"      {f.detail}")
        lines.append("")

    lines += _obligations_block("Obligations", report.obligations)
    lines += _obligations_block("Documentation to maintain", report.documentation_required)
    lines += _obligations_block("Transparency obligations", report.transparency_obligations)

    if report.open_questions:
        lines.append("Open questions for review:")
        for q in report.open_questions:
            lines.append(f"  ? {q}")
        lines.append("")

    if report.timeline:
        lines.append("Application timeline (Art. 113 AIA):")
        for t in report.timeline:
            lines.append(f"  {t.applies_from} — {t.provision}")
        lines.append("")

    if report.unverified_citations:
        lines.append("Citations pending verification (noch zu verifizieren):")
        for c in report.unverified_citations:
            lines.append(f"  - {c}")
        lines.append("")

    lines.append("-" * 78)
    lines.append(report.regulation)
    lines.append(report.disclaimer)
    return "\n".join(lines)
