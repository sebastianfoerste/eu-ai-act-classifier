"""Gate 2: high-risk classification (Art. 6 + Annex III AIA).

Two routes to high-risk: the Annex I product-safety route (Art. 6(1)) and the
Annex III use-case route (Art. 6(2)). The Annex III route is subject to the
Art. 6(3) derogation, but profiling of natural persons forecloses the
derogation entirely (Art. 6(3) subpara. 2). An asserted-but-unconfirmed
derogation is not silently applied: the system stays high-risk and the call is
handed to review, because Art. 6(3)/(4) require a documented assessment before
a system leaves the high-risk tier.

On the Annex I route the Section matters: for a Section B product Art. 2(2)
limits the AIA to Art. 6(1), Art. 60a and Arts. 102 to 112, so the engine
attaches no Chapter III obligations. The Section is derived from the named
Annex I legislation (Annex I as amended by Art. 1(41) of Regulation (EU)
2026/1744, which moved machinery to Section B).
"""

from __future__ import annotations

from ..catalog import ANNEX_I, ANNEX_III, annex_i_citation
from ..models import AnnexIII, AnnexILegislation, Finding, RiskTier, Severity
from .base import GateOutput

_ROUTE_6_1 = (
    "Safety component of, or itself, a product covered by Annex I harmonisation legislation "
    "requiring third-party conformity assessment."
)


def evaluate(profile) -> GateOutput:
    out = GateOutput()

    # Route 1: Annex I product-safety (Art. 6(1))
    if profile.annex_i_safety_component and profile.annex_i_third_party_assessment:
        out.tier_vote = RiskTier.HIGH
        _annex_i_route(profile.annex_i_legislation, out)

    # Route 2: Annex III use cases (Art. 6(2))
    area = profile.annex_iii_area
    if area is None:
        return out

    citation, label = ANNEX_III[area]

    if area is AnnexIII.UNSURE:
        out.tier_vote = RiskTier.HIGH  # conservative default while the point is pinned
        out.findings.append(
            Finding(
                rule_id="HIGHRISK.III.unsure",
                citation=citation.ref,
                citation_verified=citation.verified,
                title="Potentially high-risk: Annex III area implicated",
                detail="An Annex III use case appears implicated but the point is unsettled.",
                severity=Severity.HIGH,
                tier=RiskTier.HIGH,
            )
        )
        out.open_questions.append(
            "Confirm which Annex III point applies (Art. 6(2) AIA); the system is treated "
            "as high-risk until the point is settled."
        )
        return out

    derog = profile.derogation
    if derog.performs_profiling:
        out.tier_vote = RiskTier.HIGH
        out.findings.append(
            Finding(
                rule_id=f"HIGHRISK.{area.value}",
                citation=citation.ref,
                citation_verified=citation.verified,
                title=f"High-risk: {label}",
                detail=(
                    "Annex III high-risk area. Profiling of natural persons keeps the system "
                    "high-risk despite any derogation (Art. 6(3) subpara. 2 AIA)."
                ),
                severity=Severity.HIGH,
                tier=RiskTier.HIGH,
            )
        )
        return out

    if derog.any_condition:
        out.tier_vote = RiskTier.HIGH  # stays high-risk until the derogation is established
        out.findings.append(
            Finding(
                rule_id=f"HIGHRISK.{area.value}.derogation",
                citation="Art. 6(3) AIA",
                title=f"High-risk pending Art. 6(3) derogation: {label}",
                detail=(
                    f"{label} ({citation.ref}). A derogation condition is asserted and no "
                    "profiling is performed, which may downgrade the system to minimal risk."
                ),
                severity=Severity.MEDIUM,
                tier=RiskTier.HIGH,
            )
        )
        out.open_questions.append(
            f"Art. 6(3) derogation asserted for {citation.ref}: confirm the system does not "
            "pose a significant risk of harm and does not materially influence the outcome "
            "of decision-making. The assessment must be documented (Art. 6(4) AIA). If it "
            "does, the system remains high-risk."
        )
        return out

    out.tier_vote = RiskTier.HIGH
    out.findings.append(
        Finding(
            rule_id=f"HIGHRISK.{area.value}",
            citation=citation.ref,
            citation_verified=citation.verified,
            title=f"High-risk: {label}",
            detail="Annex III high-risk area (Art. 6(2) AIA); no derogation asserted.",
            severity=Severity.HIGH,
            tier=RiskTier.HIGH,
        )
    )
    return out


def _annex_i_route(legislation: AnnexILegislation | None, out: GateOutput) -> None:
    """Art. 6(1) with the Annex I Section that decides what the AIA applies.

    Section A: Chapter III applies (from 2 August 2028 under Art. 113, third
    paragraph, point (c)(ii)). Section B: only Art. 6(1), Art. 60a and Arts. 102
    to 112 apply (Art. 2(2) AIA as replaced by Art. 1(2)(a) of Regulation (EU)
    2026/1744). Machinery moved from Section A to Section B by Art. 1(41).
    """
    if legislation is None:
        out.findings.append(
            Finding(
                rule_id="HIGHRISK.6.1.section_unknown",
                citation="Art. 6(1) AIA; Annex I AIA",
                title="High-risk via the Annex I product-safety route; Annex I Section unknown",
                detail=(
                    f"{_ROUTE_6_1} The Annex I legislation is not named, so whether Section A "
                    "or Section B applies is UNKNOWN. Interpretation: the Chapter III "
                    "obligations of a Section A product are kept until the Section is settled."
                ),
                severity=Severity.HIGH,
                tier=RiskTier.HIGH,
            )
        )
        out.open_questions.append(
            "Art. 6(1) and Art. 2(2) AIA: name the Annex I legislation covering the product "
            "(annex_i_legislation). For a Section B product only Art. 6(1), Art. 60a and "
            "Arts. 102 to 112 apply; machinery under Regulation (EU) 2023/1230 is Section B, "
            "point 21."
        )
        return

    out.annex_i_section = legislation.section
    act = ANNEX_I[legislation]
    if legislation.section == "A":
        out.findings.append(
            Finding(
                rule_id="HIGHRISK.6.1",
                citation=f"Art. 6(1) AIA; {annex_i_citation(legislation)}",
                title="High-risk via the Annex I product-safety route (Section A)",
                detail=f"{_ROUTE_6_1} Legislation: {act}.",
                severity=Severity.HIGH,
                tier=RiskTier.HIGH,
            )
        )
        return

    moved = (
        " Regulation (EU) 2026/1744 deleted Annex I, Section A, point 1 (Directive 2006/42/EC) "
        "and listed machinery in Section B, point 21 (its Art. 1(41))."
        if legislation is AnnexILegislation.MACHINERY
        else ""
    )
    out.findings.append(
        Finding(
            rule_id="HIGHRISK.6.1.section_b",
            citation=f"Art. 6(1) and Art. 2(2) AIA; {annex_i_citation(legislation)}",
            title="High-risk under Art. 6(1), Annex I Section B (Art. 2(2) AIA limits the AIA)",
            detail=(
                f"{_ROUTE_6_1} Legislation: {act}. For an AI system classified as high-risk "
                "under Art. 6(1) related to a Section B product, only Art. 6(1), Art. 60a and "
                "Arts. 102 to 112 AIA apply; Arts. 57 to 59 apply only in so far as the "
                "high-risk requirements have been integrated in that legislation (Art. 2(2) "
                "AIA, as replaced by Regulation (EU) 2026/1744). The Chapter III obligations "
                f"are therefore not attached.{moved}"
            ),
            severity=Severity.HIGH,
            tier=RiskTier.HIGH,
        )
    )
