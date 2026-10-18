"""Gate 2: high-risk classification (Art. 6 + Annex III AIA).

Two routes to high-risk: the Annex I product-safety route (Art. 6(1)) and the
Annex III use-case route (Art. 6(2)). The Annex III route is subject to the
Art. 6(3) derogation, but profiling of natural persons forecloses the
derogation entirely (Art. 6(3) subpara. 2). An asserted-but-unconfirmed
derogation is not silently applied: the system stays high-risk and the call is
handed to review, because Art. 6(3)/(4) require a documented assessment before
a system leaves the high-risk tier.
"""

from __future__ import annotations

from ..catalog import ANNEX_III, SECTION_B_PROVISIONS, section_b_annex_iii_flag
from ..models import AnnexIII, AnnexISection, Finding, RiskTier, Severity
from ..transitions import annex_i_route, derogation_asserted, section_b_product
from .base import GateOutput

# Art. 6(1c) AIA, inserted by Regulation (EU) 2026/1744, Art. 1, point (8).
_ART_6_1C = (
    "A third-party conformity assessment required solely for risks other than risks to "
    "health and safety, such as radio spectrum or electromagnetic interference, does not "
    "meet Art. 6(1)(b) (Art. 6(1c) AIA)."
)
# Art. 2(2) AIA limits a Section B product; Regulation (EU) 2026/1744, Art. 1, point (41)
# moved machinery there (Section A, point 1 deleted; Section B, point 21 added). Art. 2(13),
# added by its Art. 1, point (3), lets delegated acts limit some duties for Section A.
_ANNEX_I_SECTION_NOTE: dict[AnnexISection | None, str] = {
    AnnexISection.SECTION_A: (
        "Annex I, Section A: the Chapter III duties apply. Delegated acts under Art. 2(13) "
        "AIA, due by 2 August 2027, may limit Arts. 9 to 15 and 17 to 25 where the Section A "
        "legislation gives an equivalent or higher level of protection."
    ),
    AnnexISection.SECTION_B: (
        f"Annex I, Section B: {SECTION_B_PROVISIONS} (Art. 2(2) AIA), so no Chapter III "
        "duty attaches through this route."
    ),
    None: (
        "Annex I section not given, so treated as Section A. For a Section B product, "
        "including machinery under Regulation (EU) 2023/1230 since Regulation (EU) "
        f"2026/1744, {SECTION_B_PROVISIONS} (Art. 2(2) AIA)."
    ),
}


def evaluate(profile) -> GateOutput:
    out = GateOutput()

    # Route 1: Annex I product-safety (Art. 6(1))
    if annex_i_route(profile):
        out.tier_vote = RiskTier.HIGH
        detail = (
            "Safety component of, or itself, a product covered by Annex I harmonisation "
            f"legislation requiring third-party conformity assessment. {_ART_6_1C} "
            f"{_ANNEX_I_SECTION_NOTE[profile.annex_i_section]}"
        )
        if section_b_product(profile) and profile.annex_iii_area is not None:
            detail += f" {section_b_annex_iii_flag(derogation_asserted(profile))}"
        out.findings.append(
            Finding(
                rule_id="HIGHRISK.6.1",
                citation="Art. 6(1) AIA",
                title="High-risk via the Annex I product-safety route",
                detail=detail,
                severity=Severity.HIGH,
                tier=RiskTier.HIGH,
            )
        )

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
        if section_b_product(profile):
            effect = (
                "which may take the system out of the Annex III route. It stays high-risk "
                "under Art. 6(1), and if the derogation is established only the Art. 2(2) "
                "AIA provisions apply to it."
            )
        elif annex_i_route(profile):
            effect = (
                "which may take the system out of the Annex III route. It stays high-risk "
                "under Art. 6(1)."
            )
        else:
            effect = "which may downgrade the system to minimal risk."
        out.findings.append(
            Finding(
                rule_id=f"HIGHRISK.{area.value}.derogation",
                citation="Art. 6(3) AIA",
                title=f"High-risk pending Art. 6(3) derogation: {label}",
                detail=(
                    f"{label} ({citation.ref}). A derogation condition is asserted and no "
                    f"profiling is performed, {effect}"
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
