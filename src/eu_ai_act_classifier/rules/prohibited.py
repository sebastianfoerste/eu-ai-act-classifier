"""Gate 1: prohibited practices (Art. 5 AIA).

A prohibited practice is a hard stop: the system may not be placed on the
market or put into service. This gate runs first and, if it fires, dominates
every other tier.
"""

from __future__ import annotations

from ..catalog import PROHIBITED
from ..models import Finding, RiskTier, Severity
from .base import GateOutput


def evaluate(profile) -> GateOutput:
    out = GateOutput()
    for practice in profile.prohibited_practices:
        citation, label = PROHIBITED[practice]
        out.findings.append(
            Finding(
                rule_id=f"PROHIBITED.{practice.value}",
                citation=citation.ref,
                citation_verified=citation.verified,
                title=label,
                detail=(
                    "Prohibited practice under Art. 5 AIA. The system may not be "
                    "placed on the market, put into service, or used."
                ),
                severity=Severity.BLOCKER,
                tier=RiskTier.PROHIBITED,
            )
        )
    if out.findings:
        out.tier_vote = RiskTier.PROHIBITED
    return out
