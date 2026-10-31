"""Gate 4: transparency obligations (Art. 50 AIA).

These obligations attach on top of any tier: a high-risk system that also acts
as a chatbot owes both its high-risk duties and the Art. 50(1) disclosure. On
their own, with no higher tier, they place the system in the limited-risk tier.

Each item applies to one role. Where the profile does not hold it, the item stays
listed and an open question names the role, so the result goes to review.
"""

from __future__ import annotations

from ..catalog import TRANSPARENCY, section_b_kept_flag
from ..models import Finding, Obligation, RiskTier, Role, Severity
from ..transitions import section_b_product
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
        detail = "Art. 50 AIA transparency duties are triggered."
        # Art. 2(2) AIA lists Art. 50 for no Section B product, Annex III area or not.
        if section_b_product(profile):
            detail += f" {section_b_kept_flag('Art. 50', 'the Art. 50 duties')}"
        out.findings.append(
            Finding(
                rule_id="TRANSPARENCY.50",
                citation=articles,
                title="Transparency obligations apply",
                detail=detail,
                severity=Severity.MEDIUM,
                tier=RiskTier.LIMITED,
            )
        )
    out.open_questions += _unheld_role_questions(profile, out.transparency)
    return out


def _unheld_role_questions(profile, transparency: list[Obligation]) -> list[str]:
    """One open question for each role an Art. 50 item applies to and the profile does
    not hold."""

    unheld: dict[Role, list[str]] = {}
    for ob in transparency:
        if ob.applies_to not in profile.roles:
            unheld.setdefault(ob.applies_to, []).append(ob.article)
    questions = []
    for role, articles in unheld.items():
        one = len(articles) == 1
        questions.append(
            f"{' and '.join(articles)}: the report lists "
            f"{'this duty' if one else 'these duties'} for the {role.value} role, which the "
            f"profile does not hold. {'It stays' if one else 'They stay'} listed for review. "
            "Confirm the roles the organisation holds for this system (roles)."
        )
    return questions
