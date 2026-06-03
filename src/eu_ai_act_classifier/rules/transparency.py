"""Gate 4 — transparency obligations (Art. 50 AIA).

These obligations attach on top of any tier: a high-risk system that also acts
as a chatbot owes both its high-risk duties and the Art. 50(1) disclosure. On
their own, with no higher tier, they place the system in the limited-risk tier.
"""

from __future__ import annotations

from ..catalog import TRANSPARENCY
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
    return out
