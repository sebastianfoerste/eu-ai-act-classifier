"""Gate 1: prohibited practices (Art. 5 AIA).

A prohibited practice is a hard stop: the system may not be placed on the
market or put into service. This gate runs first and, if it fires, dominates
every other tier.
"""

from __future__ import annotations

from ..catalog import (
    ART_5_1A,
    ART_5_1B,
    LATER_PROHIBITIONS,
    PROHIBITED,
    section_b_kept_flag,
)
from ..citations import POINT_A_EXCEPTION_DATE, long_date
from ..models import Finding, ProhibitedPractice, RiskTier, Severity
from ..transitions import section_b_product
from .base import GateOutput

_LATER_FROM = long_date(POINT_A_EXCEPTION_DATE)  # "2 December 2026"
_SECTION_B_FLAG = section_b_kept_flag("Art. 5", "the prohibition")


def evaluate(profile) -> GateOutput:
    out = GateOutput()
    for practice in profile.prohibited_practices:
        citation, label = PROHIBITED[practice]
        title, detail = (
            label,
            (
                "Prohibited practice under Art. 5 AIA. The system may not be "
                "placed on the market, put into service, or used."
            ),
        )
        if practice in LATER_PROHIBITIONS:
            title, detail = _later_prohibition(practice, citation.ref, label)
        if section_b_product(profile):
            # Art. 2(2) AIA does not list Art. 5 for a Section B product.
            detail += f" {_SECTION_B_FLAG}"
        out.findings.append(
            Finding(
                rule_id=f"PROHIBITED.{practice.value}",
                citation=citation.ref,
                citation_verified=citation.verified,
                title=title,
                detail=detail,
                severity=Severity.BLOCKER,
                tier=RiskTier.PROHIBITED,
            )
        )
    if out.findings:
        out.tier_vote = RiskTier.PROHIBITED
        if section_b_product(profile):
            # The dossier and the cockpit list open questions, not finding details.
            out.open_questions.append(f"Art. 2(2) AIA and Art. 5 AIA: {_SECTION_B_FLAG}")
    return out


def _later_prohibition(practice: ProhibitedPractice, ref: str, label: str) -> tuple[str, str]:
    """Art. 5(1)(ba) and (bb) AIA apply from 2 December 2026, not 2 February 2025. The
    sentence does not depend on the run date, so the output stays deterministic."""

    conditions = f'Art. 5(1a): "{ART_5_1A}".'
    if practice is ProhibitedPractice.NON_CONSENSUAL_INTIMATE_IMAGERY:
        conditions += f' Art. 5(1b): "{ART_5_1B}".'
    return (
        f"{label} (prohibited from {_LATER_FROM})",
        (
            f"Prohibited practice under Art. 5 AIA from {_LATER_FROM} ({POINT_A_EXCEPTION_DATE}; "
            "Art. 113, third paragraph, point (a) AIA, as replaced by Regulation (EU) "
            "2026/1744), with no transition for systems already on the market: Art. 111(2) "
            "is without prejudice to Art. 5. "
            f'{ref}: "{LATER_PROHIBITIONS[practice]}". {conditions}'
        ),
    )
