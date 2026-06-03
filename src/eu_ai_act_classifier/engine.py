"""The engine: run the gates, resolve the tier, assemble the obligations.

The engine is generic. It knows how to order gate votes and attach the right
obligation sets to a determined tier and role; it knows nothing about any
specific provision. All substance lives in :mod:`.catalog` and :mod:`.rules`.
"""

from __future__ import annotations

from .catalog import (
    gpai_obligations,
    high_risk_deployer_obligations,
    high_risk_documentation,
    high_risk_provider_obligations,
)
from .citations import APPLICATION_DATES, REGULATION
from .models import (
    TIER_ORDER,
    AnnexIII,
    ClassificationReport,
    Disposition,
    Obligation,
    RiskTier,
    SystemProfile,
    TimelineItem,
)
from .rules import gpai, high_risk, prohibited, transparency

# Annex III points whose deployers are expressly named for a FRIA (Art. 27(1)(b) AIA).
_FRIA_AREAS = {AnnexIII.CREDITWORTHINESS, AnnexIII.INSURANCE_LIFE_HEALTH}


def classify(profile: SystemProfile) -> ClassificationReport:
    outputs = [
        prohibited.evaluate(profile),
        high_risk.evaluate(profile),
        gpai.evaluate(profile),
        transparency.evaluate(profile),
    ]

    findings = [f for o in outputs for f in o.findings]
    open_questions = [q for o in outputs for q in o.open_questions]
    transparency_obligations = [t for o in outputs for t in o.transparency]
    is_gpai = any(o.is_gpai for o in outputs)
    gpai_systemic = any(o.gpai_systemic for o in outputs)

    votes = [o.tier_vote for o in outputs if o.tier_vote is not None]
    final_tier = max(votes, key=lambda t: TIER_ORDER[t]) if votes else RiskTier.MINIMAL

    obligations: list[Obligation] = []
    documentation: list[Obligation] = []

    if final_tier is RiskTier.HIGH:
        if profile.is_provider:
            obligations += high_risk_provider_obligations()
            documentation += high_risk_documentation()
        if profile.is_deployer:
            fria_required = profile.annex_iii_area in _FRIA_AREAS
            obligations += high_risk_deployer_obligations(fria_required=fria_required)
            if not fria_required:
                open_questions.append(
                    "Art. 27 AIA: a fundamental rights impact assessment is also required "
                    "where the deployer is a body governed by public law or a private "
                    "operator providing a public service — confirm deployer status."
                )

    # Chapter V duties attach regardless of the system tier, but a prohibited
    # practice has no compliance pathway, so nothing is listed under it.
    if is_gpai and final_tier is not RiskTier.PROHIBITED:
        obligations += gpai_obligations(systemic_risk=gpai_systemic)

    disposition = Disposition.REQUIRES_REVIEW if open_questions else Disposition.DETERMINED

    unverified = sorted(
        {f.citation for f in findings if not f.citation_verified}
        | {
            ob.article
            for ob in (obligations + documentation + transparency_obligations)
            if not ob.citation_verified
        }
    )

    timeline = [
        TimelineItem(provision=a.provision, applies_from=a.date, note=a.note)
        for a in APPLICATION_DATES
    ]

    return ClassificationReport(
        system=profile.name,
        regulation=REGULATION,
        risk_tier=final_tier,
        disposition=disposition,
        roles=profile.roles,
        is_gpai=is_gpai,
        gpai_systemic=gpai_systemic,
        findings=findings,
        obligations=obligations,
        documentation_required=documentation,
        transparency_obligations=transparency_obligations,
        timeline=timeline,
        open_questions=open_questions,
        unverified_citations=unverified,
    )
