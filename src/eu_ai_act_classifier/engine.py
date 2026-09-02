"""The engine: run the gates, resolve the tier, assemble the report."""

from __future__ import annotations

from .advisory import build_advisory_notes
from .catalog import (
    gpai_obligations,
    high_risk_authorized_representative_obligations,
    high_risk_deployer_obligations,
    high_risk_distributor_obligations,
    high_risk_documentation,
    high_risk_importer_obligations,
    high_risk_provider_obligations,
    high_risk_value_chain_obligations,
)
from .citations import AMENDING_APPLICATION_DATES, APPLICATION_DATES, REGULATION, source_manifest
from .models import (
    TIER_ORDER,
    AnnexIII,
    ClassificationReport,
    Disposition,
    Obligation,
    RiskTier,
    ScopeStatus,
    SystemProfile,
    TimelineItem,
)
from .obligation_graph import build_obligation_graph
from .rules import gpai, high_risk, prohibited, scope, transparency

_FRIA_AREAS = {AnnexIII.CREDITWORTHINESS, AnnexIII.INSURANCE_LIFE_HEALTH}
_FRIA_EXCLUDED_AREAS = {AnnexIII.CRITICAL_INFRASTRUCTURE}


def classify(profile: SystemProfile, *, include_advisory: bool = False) -> ClassificationReport:
    scope_assessment, scope_findings, scope_open_questions = scope.evaluate(profile)

    outputs = []
    if scope_assessment.status is not ScopeStatus.OUTSIDE_SCOPE:
        outputs = [
            prohibited.evaluate(profile),
            high_risk.evaluate(profile),
            gpai.evaluate(profile),
            transparency.evaluate(profile),
        ]

    findings = scope_findings + [f for o in outputs for f in o.findings]
    open_questions = scope_open_questions + [q for o in outputs for q in o.open_questions]
    transparency_obligations = [t for o in outputs for t in o.transparency]
    is_gpai = any(o.is_gpai for o in outputs)
    gpai_systemic = any(o.gpai_systemic for o in outputs)

    votes = [o.tier_vote for o in outputs if o.tier_vote is not None]
    final_tier = (
        RiskTier.OUT_OF_SCOPE
        if scope_assessment.status is ScopeStatus.OUTSIDE_SCOPE
        else max(votes, key=lambda t: TIER_ORDER[t])
        if votes
        else RiskTier.MINIMAL
    )

    obligations: list[Obligation] = []
    documentation: list[Obligation] = []
    fria_required = False

    if final_tier is RiskTier.HIGH:
        if profile.is_provider:
            obligations += high_risk_provider_obligations()
            documentation += high_risk_documentation()
        if profile.is_deployer:
            fria_required = _fria_required(profile)
            obligations += high_risk_deployer_obligations(fria_required=fria_required)
            if _fria_needs_review(profile, fria_required):
                open_questions.append(
                    "Art. 27 AIA: a fundamental rights impact assessment is also required "
                    "where the deployer is a body governed by public law or a private "
                    "operator providing a public service. Confirm deployer status."
                )
        if profile.is_importer:
            obligations += high_risk_importer_obligations()
        if profile.is_distributor:
            obligations += high_risk_distributor_obligations()
        if profile.is_authorized_representative or profile.provider_established_outside_eu:
            obligations += high_risk_authorized_representative_obligations()
        if (
            profile.provider_established_outside_eu
            and profile.has_authorised_representative is False
        ):
            open_questions.append(
                "Art. 22 AIA: provider is established outside the EU and no authorised "
                "representative is confirmed. Confirm representative arrangements."
            )
        if profile.substantially_modifies_system or profile.puts_name_or_trademark_on_system:
            obligations += high_risk_value_chain_obligations()

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
        TimelineItem(
            provision=a.provision,
            applies_from=a.date,
            note=a.note,
            source_status=a.source_status,
            source_id=a.source_id,
            source_url=a.source_url,
        )
        for a in APPLICATION_DATES + AMENDING_APPLICATION_DATES
    ]

    obligation_graph = build_obligation_graph(
        profile=profile,
        final_tier=final_tier,
        is_gpai=is_gpai,
        gpai_systemic=gpai_systemic,
        fria_required=fria_required,
        transparency_obligations=transparency_obligations,
    )

    return ClassificationReport(
        system=profile.name,
        regulation=REGULATION,
        risk_tier=final_tier,
        disposition=disposition,
        scope=scope_assessment,
        roles=profile.roles,
        is_gpai=is_gpai,
        gpai_systemic=gpai_systemic,
        findings=findings,
        obligations=obligations,
        documentation_required=documentation,
        transparency_obligations=transparency_obligations,
        obligation_graph=obligation_graph,
        timeline=timeline,
        source_manifest=source_manifest(),
        advisory_notes=build_advisory_notes(profile) if include_advisory else [],
        open_questions=open_questions,
        unverified_citations=unverified,
    )


def _fria_required(profile: SystemProfile) -> bool:
    if profile.annex_iii_area in _FRIA_EXCLUDED_AREAS:
        return False
    if profile.annex_iii_area in _FRIA_AREAS:
        return True
    return bool(profile.deployer_public_law_body or profile.deployer_private_public_service)


def _fria_needs_review(profile: SystemProfile, fria_required: bool) -> bool:
    if fria_required or profile.annex_iii_area in _FRIA_EXCLUDED_AREAS:
        return False
    return (
        profile.is_deployer
        and profile.annex_iii_area is not None
        and (
            profile.deployer_public_law_body is None
            or profile.deployer_private_public_service is None
        )
    )
