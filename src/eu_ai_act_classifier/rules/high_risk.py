"""Gate 2 — high-risk classification (Art. 6 + Annex III AIA).

Two routes to high-risk: the Annex I product-safety route (Art. 6(1)) and the
Annex III use-case route (Art. 6(2)). The Annex III route is subject to the
Art. 6(3) derogation — but profiling of natural persons forecloses the
derogation entirely (Art. 6(3) subpara. 2). An asserted-but-unconfirmed
derogation is not silently applied: the system stays high-risk and the call is
handed to review, because Art. 6(3)/(4) require a documented assessment before
a system leaves the high-risk tier.
"""

from __future__ import annotations

from ..catalog import ANNEX_III
from ..models import AnnexIII, Finding, RiskTier, Severity
from .base import GateOutput


def evaluate(profile) -> GateOutput:
    out = GateOutput()

    # Route 1 — Annex I product-safety (Art. 6(1))
    if profile.annex_i_safety_component and profile.annex_i_third_party_assessment:
        out.tier_vote = RiskTier.HIGH
        out.findings.append(
            Finding(
                rule_id="HIGHRISK.6.1",
                citation="Art. 6(1) AIA",
                title="High-risk via the Annex I product-safety route",
                detail=(
                    "Safety component of, or itself, a product covered by Annex I "
                    "harmonisation legislation requiring third-party conformity assessment."
                ),
                severity=Severity.HIGH,
                tier=RiskTier.HIGH,
            )
        )

    # Route 2 — Annex III use cases (Art. 6(2))
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
