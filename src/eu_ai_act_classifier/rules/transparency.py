"""Gate 4: transparency obligations (Art. 50 AIA).

These obligations attach on top of any tier: a high-risk system that also acts
as a chatbot owes both its high-risk duties and the Art. 50(1) disclosure. On
their own, with no higher tier, they place the system in the limited-risk tier.

Art. 50 applies from 2 August 2026 (Art. 113, second paragraph AIA). For
generative systems placed on the market before that date, Art. 111(4) AIA,
added by Regulation (EU) 2026/1744, defers Art. 50(2) to 2 December 2026.
"""

from __future__ import annotations

from ..catalog import TRANSPARENCY
from ..citations import ART_50_2_LEGACY_DEADLINE, GENERAL_APPLICATION_DATE
from ..models import Finding, RiskTier, Severity
from .base import GateOutput


def evaluate(profile) -> GateOutput:
    out = GateOutput()

    if profile.interacts_with_natural_persons:
        out.transparency.append(TRANSPARENCY["interaction"])
    if profile.generates_synthetic_content:
        out.transparency.append(TRANSPARENCY["synthetic"])
    if profile.deploys_emotion_or_biometric_categorisation:
        out.transparency.append(TRANSPARENCY["emotion_biometric"])
    if profile.generates_deepfakes:
        out.transparency.append(TRANSPARENCY["deepfake"])

    if out.transparency:
        out.tier_vote = RiskTier.LIMITED
        articles = ", ".join(ob.article for ob in out.transparency)
        out.findings.append(
            Finding(
                rule_id="TRANSPARENCY.50",
                citation=articles,
                title="Transparency obligations apply",
                detail="Art. 50 AIA transparency duties are triggered.",
                severity=Severity.MEDIUM,
                tier=RiskTier.LIMITED,
            )
        )
    if profile.generates_synthetic_content:
        _legacy_generative_deadline(profile.placing_on_market_date, out)
    return out


def _legacy_generative_deadline(placed_on: str | None, out: GateOutput) -> None:
    if placed_on is None:
        out.findings.append(
            Finding(
                rule_id="TRANSPARENCY.50.2.placement_unknown",
                citation="Art. 50(2) and Art. 111(4) AIA",
                title="Art. 50(2): application date unknown",
                detail=(
                    "The system's placing-on-the-market date is not given. Systems placed before "
                    "2 August 2026 comply with Art. 50(2) by 2 December 2026 (Art. 111(4) AIA); "
                    "later systems from 2 August 2026."
                ),
                severity=Severity.MEDIUM,
            )
        )
        out.open_questions.append(
            "Art. 111(4) AIA: give the placing_on_market_date of this system generating "
            "synthetic content. Systems placed before 2 August 2026 comply with Art. 50(2) by "
            "2 December 2026; the Art. 50(2) date is UNKNOWN until then."
        )
        return
    if placed_on < GENERAL_APPLICATION_DATE:
        out.findings.append(
            Finding(
                rule_id="TRANSPARENCY.50.2.legacy",
                citation="Art. 111(4) AIA",
                title="Placed before 2 August 2026: Art. 50(2) applies from 2 December 2026",
                detail=(
                    f"Placed on the market on {placed_on}. Providers of AI systems generating "
                    "synthetic audio, image, video or text content placed on the market before "
                    "2 August 2026 must comply with Art. 50(2) by "
                    f"{ART_50_2_LEGACY_DEADLINE} (Art. 111(4) AIA, added by Regulation (EU) "
                    "2026/1744)."
                ),
                severity=Severity.INFO,
            )
        )
