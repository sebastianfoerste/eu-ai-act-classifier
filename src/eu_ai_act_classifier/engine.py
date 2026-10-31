"""The engine: run the gates, resolve the tier, assemble the report."""

from __future__ import annotations

from .advisory import build_advisory_notes
from .catalog import (
    ANNEX_III,
    ai_literacy_obligations,
    eu_database_registration_applies,
    gpai_obligations,
    high_risk_authorized_representative_obligations,
    high_risk_deployer_obligations,
    high_risk_distributor_obligations,
    high_risk_documentation,
    high_risk_importer_obligations,
    high_risk_provider_obligations,
    high_risk_value_chain_obligations,
    public_authority_registration_applies,
    public_authority_users,
    section_b_annex_iii_flag,
    section_b_kept_flag,
    section_b_obligations,
)
from .citations import AMENDING_APPLICATION_DATES, APPLICATION_DATES, REGULATION, source_manifest
from .models import (
    TIER_ORDER,
    AnnexIII,
    ClassificationReport,
    Disposition,
    Obligation,
    RiskTier,
    Role,
    ScopeStatus,
    SystemProfile,
    TimelineItem,
)
from .obligation_graph import build_obligation_graph
from .rules import gpai, high_risk, prohibited, scope, transparency
from .transitions import (
    before,
    chapter_iii_date,
    derogation_asserted,
    derogation_note,
    describe_dates,
    gpai_model_date,
    legacy_dates,
    legacy_note_flag,
    legacy_transparency_flag,
    market_dates,
    operators,
    public_authority_sentence,
    section_b_only,
    section_b_product,
)

_FRIA_AREAS = {AnnexIII.CREDITWORTHINESS, AnnexIII.INSURANCE_LIFE_HEALTH}
_FRIA_EXCLUDED_AREAS = {AnnexIII.CRITICAL_INFRASTRUCTURE}
# Art. 2(2) AIA lists Art. 4 for no Section B product; the report keeps the duty, flagged,
# as it keeps Art. 5 and Art. 50. The graph item carries the same flag.
SECTION_B_LITERACY_FLAG = section_b_kept_flag("Art. 4", "the Art. 4 duty")


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

    if final_tier is RiskTier.HIGH and section_b_only(profile):
        # Art. 2(2) AIA: none of the Chapter III duties below, only the listed provisions.
        for role in operators(profile, (Role.PROVIDER,)):
            obligations += section_b_obligations(role)
    elif final_tier is RiskTier.HIGH:
        if profile.is_provider:
            obligations += high_risk_provider_obligations(
                eu_database_registration=eu_database_registration_applies(profile.annex_iii_area),
                annex_iii_area=profile.annex_iii_area,
            )
            documentation += high_risk_documentation()
        if profile.is_deployer:
            fria_required = _fria_required(profile)
            public_authority_registration = public_authority_registration_applies(
                profile.annex_iii_area,
                profile.deployer_public_authority,
                profile.public_authority_use,
            )
            obligations += high_risk_deployer_obligations(
                fria_required=fria_required,
                public_authority_registration=public_authority_registration,
                annex_iii_area=profile.annex_iii_area,
                deployer_public_authority=profile.deployer_public_authority,
            )
            open_questions += _art_49_3_questions(profile, public_authority_registration)
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
        if section_b_product(profile):
            # Also in an Annex III area: the Annex III duties above stay, flagged here.
            flag = section_b_annex_iii_flag(derogation_asserted(profile))
            for role in operators(profile, (Role.PROVIDER,)):
                obligations += section_b_obligations(role, flag)
        open_questions += _art_111_2_questions(profile)
        if legacy_flag := legacy_transparency_flag(profile):
            # The Art. 50 graph items carry the same flag.
            findings = [
                finding.model_copy(update={"detail": f"{finding.detail} {legacy_flag}"})
                if finding.rule_id == "TRANSPARENCY.50"
                else finding
                for finding in findings
            ]

    if is_gpai and final_tier is not RiskTier.PROHIBITED:
        obligations += gpai_obligations(systemic_risk=gpai_systemic)
        open_questions += _gpai_date_questions(profile)

    if ai_literacy_applies(final_tier):
        # Art. 4 AIA (Chapter I) binds every provider and deployer of an AI system within
        # the Regulation's scope, whatever the tier, so it heads the list.
        literacy_flag = SECTION_B_LITERACY_FLAG if section_b_product(profile) else ""
        obligations = ai_literacy_obligations(profile.roles, literacy_flag) + obligations

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
        for a in sorted(APPLICATION_DATES + AMENDING_APPLICATION_DATES, key=lambda d: d.date)
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


def ai_literacy_applies(final_tier: RiskTier) -> bool:
    """Art. 4 AIA attaches to every system within the Regulation's scope, whatever its
    tier, except a prohibited one: as for the GPAI duties, a system that may not be placed
    on the market, put into service or used (Art. 5 AIA) has no staff to operate it."""

    return final_tier not in (RiskTier.OUT_OF_SCOPE, RiskTier.PROHIBITED)


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


def _art_111_2_questions(profile: SystemProfile) -> list[str]:
    """Art. 111(2) AIA: whether the Regulation applies to a legacy high-risk system at all
    turns on a significant change in design, so an unknown answer is an open question."""

    cut_off = chapter_iii_date(profile)
    if cut_off is None:
        return []
    legacy = legacy_dates(profile, cut_off)
    questions = []
    if legacy and profile.significant_change_after_application_date is None:
        # The second sentence of Art. 111(2) binds "in any case", whatever the answer.
        questions.append(
            f"Art. 111(2) AIA: the system was {describe_dates(legacy)}, before {cut_off}. "
            "Confirm whether its design changes significantly as from that date, and the date "
            "of any such change (significant_change_after_application_date); apart from "
            f"Art. 5, the Regulation applies to it only then.{public_authority_sentence(profile)} "
            f"{legacy_note_flag(profile, cut_off)}"
        )
    if not legacy and (derogation := derogation_note(profile, cut_off)):
        questions.append(
            f"Art. 111(2) AIA: the system was {describe_dates(market_dates(profile))}, not "
            f"before {cut_off}, so the transition does not apply to it as classified. "
            f"{derogation} Confirm the derogation (Art. 6(4) AIA)."
        )
    return questions


def _art_49_3_questions(profile: SystemProfile, registration: bool) -> list[str]:
    """Art. 49(3) AIA turns on the deployer's own status. Where it is not given, ask for
    it when the registration item is inferred, or when other facts point to it."""

    if profile.deployer_public_authority is not None:
        return []
    confirm = (
        "Confirm whether the deployer is, or acts on behalf of, a public authority or Union "
        "institution, body, office or agency (deployer_public_authority)."
    )
    if registration:
        if profile.public_authority_use:
            reason = "the system is intended to be used by public authorities"
        else:
            # The same words as the item's trigger.
            users = public_authority_users(profile.annex_iii_area)
            reason = f"{ANNEX_III[profile.annex_iii_area][0].ref} describes use {users}"
        return [f"Art. 49(3) AIA: {reason}, but the deployer's status is not given. {confirm}"]
    if profile.annex_iii_area is AnnexIII.JUSTICE:
        # Point 8(a) also covers alternative dispute resolution, which may be private.
        return [
            "Art. 49(3) AIA: Annex III(8)(a) AIA covers use by or on behalf of a judicial "
            "authority, or in a similar way in alternative dispute resolution. If the deployer "
            "is, or acts on behalf of, a public authority or Union institution, body, office "
            f"or agency, it registers its use in the EU database. {confirm}"
        ]
    if profile.deployer_public_law_body and eu_database_registration_applies(
        profile.annex_iii_area
    ):
        return [
            "Art. 49(3) AIA: the deployer is a body governed by public law (Art. 27 AIA), "
            "which may be a public authority. If it is, or acts on behalf of one, it registers "
            f"its use in the EU database. {confirm}"
        ]
    return []


def _gpai_date_questions(profile: SystemProfile) -> list[str]:
    """Art. 111(3) AIA dates a general-purpose AI model by its own placing on the market."""

    model_date, fallback = gpai_model_date(profile)
    if fallback:
        return [
            "Art. 111(3) AIA: no gpai_model_placing_on_market_date is given, so the model is "
            f"dated by the AI system's placing_on_market_date ({model_date}). Confirm the "
            "model's own date (gpai_model_placing_on_market_date)."
        ]
    system_date = profile.placing_on_market_date
    if model_date and system_date and before(system_date, model_date):
        return [
            f"Art. 111(3) AIA: the model's date ({model_date}) is later than the AI system's "
            f"placing_on_market_date ({system_date}). Confirm both dates."
        ]
    return []
