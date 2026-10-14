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
    Finding,
    Obligation,
    RiskTier,
    ScopeStatus,
    Severity,
    SystemProfile,
    TimelineItem,
)
from .obligation_graph import build_obligation_graph
from .rules import gpai, high_risk, prohibited, scope, transparency
from .rules.base import GateOutput, on_or_after

_FRIA_AREAS = {AnnexIII.CREDITWORTHINESS, AnnexIII.INSURANCE_LIFE_HEALTH}
_FRIA_EXCLUDED_AREAS = {AnnexIII.CRITICAL_INFRASTRUCTURE}


def classify(profile: SystemProfile, *, include_advisory: bool = False) -> ClassificationReport:
    scope_assessment, scope_findings, scope_open_questions = scope.evaluate(profile)

    outputs = []
    section_b_only = False
    if scope_assessment.status is not ScopeStatus.OUTSIDE_SCOPE:
        prohibited_out = prohibited.evaluate(profile)
        high_risk_out = high_risk.evaluate(profile)
        transparency_out = transparency.evaluate(profile)
        section_b_only = _apply_article_2_2(
            profile, prohibited_out, high_risk_out, transparency_out
        )
        outputs = [prohibited_out, high_risk_out, gpai.evaluate(profile), transparency_out]

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

    if final_tier is RiskTier.HIGH and not section_b_only:
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
        for a in sorted(APPLICATION_DATES + AMENDING_APPLICATION_DATES, key=lambda a: a.date)
    ]

    obligation_graph = build_obligation_graph(
        profile=profile,
        final_tier=final_tier,
        is_gpai=is_gpai,
        gpai_systemic=gpai_systemic,
        fria_required=fria_required,
        transparency_obligations=transparency_obligations,
        chapter_iii_applies=not section_b_only,
    )
    for item in obligation_graph:
        item.applies_on_assessment_date = (
            None
            if item.application_date is None
            else on_or_after(profile.assessment_date, item.application_date)
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


def _apply_article_2_2(
    profile: SystemProfile,
    prohibited_out: GateOutput,
    high_risk_out: GateOutput,
    transparency_out: GateOutput,
) -> bool:
    """Apply Art. 2(2) AIA to an Art. 6(1) system related to an Annex I Section B product.

    Only Art. 6(1), Art. 60a and Arts. 102 to 112 apply to such a system (Art. 2(2)
    as replaced by Art. 1(2)(a) of Regulation (EU) 2026/1744). Interpretation: the
    literal reading removes the Chapter III and Art. 50 obligations; an Art. 5
    finding or an Annex III listing is not set aside on that reading but goes to
    review. Returns whether the Chapter III obligations are to be left out.
    """
    if high_risk_out.annex_i_section != "B":
        return False
    if prohibited_out.tier_vote is RiskTier.PROHIBITED:
        prohibited_out.open_questions.append(
            "Art. 2(2) AIA: for an Art. 6(1) system related to an Annex I, Section B product "
            "only Art. 6(1), Art. 60a and Arts. 102 to 112 apply. Confirm whether the Art. 5 "
            "finding stands; interpretation: the engine keeps it."
        )
        return False
    if profile.annex_iii_area is not None:
        high_risk_out.open_questions.append(
            "Art. 2(2) AIA: the system is an Art. 6(1) system related to an Annex I, Section B "
            "product and is also listed in Annex III. Confirm whether Art. 2(2) limits the AIA "
            "for this system; interpretation: the Annex III obligations are kept."
        )
        return False
    if transparency_out.transparency:
        articles = ", ".join(ob.article for ob in transparency_out.transparency)
        transparency_out.transparency = []
        transparency_out.tier_vote = None
        transparency_out.open_questions = []
        transparency_out.findings = [
            Finding(
                rule_id="TRANSPARENCY.50.art_2_2",
                citation="Art. 2(2) AIA",
                title="Art. 50 obligations not attached: Annex I, Section B product",
                detail=(
                    f"The profile triggers {articles}, but Art. 2(2) AIA applies only Art. 6(1), "
                    "Art. 60a and Arts. 102 to 112 to this system. Interpretation: literal "
                    "reading of Art. 2(2)."
                ),
                severity=Severity.INFO,
            )
        ]
    return True


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
