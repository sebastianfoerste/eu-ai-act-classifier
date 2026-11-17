"""The engine: run the gates, resolve the tier, assemble the report."""

from __future__ import annotations

from .advisory import build_advisory_notes
from .catalog import (
    ANNEX_III,
    ART_50_2,
    eu_database_registration_applies,
    high_risk_documentation,
    public_authority_registration_applies,
    public_authority_users,
)
from .citations import (
    AMENDING_APPLICATION_DATES,
    APPLICATION_DATES,
    ART_111_1,
    ART_111_3_DEADLINE,
    ART_111_4_DEADLINE,
    GENERAL_APPLICATION_DATE,
    POINT_B_DATE,
    REGULATION,
    source_manifest,
)
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
from .obligation_graph import build_obligation_graph, listed_obligations
from .rules import gpai, high_risk, prohibited, scope, transparency
from .transitions import (
    ANNEX_X_CARVE_OUT,
    PUBLIC_AUTHORITY_DUTY,
    before,
    chapter_iii_date,
    cut_off_contested,
    derogation_note,
    describe_dates,
    gpai_model_date,
    legacy_dates,
    legacy_note_flag,
    legacy_transparency_flag,
    market_dates,
    operator_roles,
    public_authority_sentence,
    public_authority_status_used,
    section_b_only,
    start_date_open,
)

_FRIA_AREAS = {AnnexIII.CREDITWORTHINESS, AnnexIII.INSURANCE_LIFE_HEALTH}
_FRIA_EXCLUDED_AREAS = {AnnexIII.CRITICAL_INFRASTRUCTURE}
_OPERATOR_ROLES = [role.value for role in Role if role is not Role.GPAI_PROVIDER]


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

    # The duties themselves are graph items (obligation_graph.py); this block keeps the
    # documentation list and the open questions.
    documentation: list[Obligation] = []
    fria_required = False

    if final_tier is RiskTier.HIGH and not section_b_only(profile):
        if profile.is_provider:
            documentation += high_risk_documentation()
        if profile.is_deployer:
            fria_required = _fria_required(profile)
            public_authority_registration = public_authority_registration_applies(
                profile.annex_iii_area,
                profile.deployer_public_authority,
                profile.public_authority_use,
            )
            open_questions += _art_49_3_questions(profile, public_authority_registration)
            if _fria_needs_review(profile, fria_required):
                open_questions.append(
                    "Art. 27 AIA: a fundamental rights impact assessment is also required "
                    "where the deployer is a body governed by public law or a private "
                    "operator providing a public service. Confirm deployer status."
                )
        if (
            profile.provider_established_outside_eu
            and profile.has_authorised_representative is False
        ):
            open_questions.append(
                "Art. 22 AIA: provider is established outside the EU and no authorised "
                "representative is confirmed. Confirm representative arrangements."
            )
        open_questions += _art_111_2_questions(profile)
        if legacy_flag := legacy_transparency_flag(profile):
            # The Art. 50 graph items carry the same flag.
            findings = [
                finding.model_copy(update={"detail": f"{finding.detail} {legacy_flag}"})
                if finding.rule_id == "TRANSPARENCY.50"
                else finding
                for finding in findings
            ]

    if scope_assessment.status is not ScopeStatus.OUTSIDE_SCOPE:
        open_questions += _role_questions(profile, final_tier)

    if is_gpai and final_tier is not RiskTier.PROHIBITED:
        open_questions += _gpai_date_questions(profile)

    if final_tier is not RiskTier.PROHIBITED:
        open_questions += _art_111_4_questions(profile, transparency_obligations)

    disposition = Disposition.REQUIRES_REVIEW if open_questions else Disposition.DETERMINED

    obligation_graph = build_obligation_graph(
        profile=profile,
        final_tier=final_tier,
        is_gpai=is_gpai,
        gpai_systemic=gpai_systemic,
        fria_required=fria_required,
        transparency_obligations=transparency_obligations,
    )
    # One source for both lists: every obligation is a graph item (Art. 4 AIA first).
    obligations = listed_obligations(obligation_graph)

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

    # The Art. 111(1) carve-out is stated in prose, not as a finding or an obligation, so
    # while its citation is unverified the engine lists it wherever the report states it.
    stated = [scope_assessment.transitional_status]
    stated += [item.application_date_note or "" for item in obligation_graph]
    if not ART_111_1.verified and any(ANNEX_X_CARVE_OUT in text for text in stated):
        unverified = sorted({*unverified, ART_111_1.ref})

    # Imported here because the package's __init__ imports this module before it sets
    # __version__.
    from . import __version__

    return ClassificationReport(
        system=profile.name,
        regulation=REGULATION,
        classifier_version=__version__,
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


def _role_questions(profile: SystemProfile, final_tier: RiskTier) -> list[str]:
    """Duties attach per role. Where the roles do not match the facts the profile screens,
    the result goes to review instead of resolving silently; the items stay listed.
    ``rules/transparency.py`` does the same for the Art. 50 items."""

    questions = []
    if final_tier is RiskTier.HIGH and not operator_roles(profile):
        roles = f"{', '.join(_OPERATOR_ROLES[:-1])} or {_OPERATOR_ROLES[-1]}"
        questions.append(
            f"High-risk AI system: the profile holds no operator role for the system ({roles}), "
            "and the high-risk duties attach per operator role. Confirm the roles the "
            "organisation holds for this system (roles)."
        )
    gpai_role = Role.GPAI_PROVIDER in profile.roles
    if profile.is_gpai_model and not gpai_role:
        # classify() lists no Chapter V item on a prohibited report.
        listed = (
            "The report lists no Chapter V item, as the system is prohibited. "
            if final_tier is RiskTier.PROHIBITED
            else "Any Chapter V item stays listed for review. "
        )
        questions.append(
            "GPAI model: the profile describes a general-purpose AI model (is_gpai_model) but "
            f"does not hold the gpai_provider role. {listed}"
            "Confirm whether the organisation is the model's provider (roles)."
        )
    if gpai_role and not profile.is_gpai_model:
        questions.append(
            "GPAI model: the profile holds the gpai_provider role but does not describe a "
            "general-purpose AI model (is_gpai_model), so the report lists no Chapter V item. "
            "Confirm is_gpai_model and the roles (roles)."
        )
    return questions


def _fria_required(profile: SystemProfile) -> bool:
    # Art. 27(1) AIA reaches "a high-risk AI system referred to in Article 6(2)":
    # a system that is high-risk only through Annex I carries no FRIA.
    if profile.annex_iii_area is None:
        return False
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


_STATUS_CONFIRM = (
    "Confirm whether the deployer is, or acts on behalf of, a public authority or Union "
    "institution, body, office or agency (deployer_public_authority)."
)


def _art_111_2_questions(profile: SystemProfile) -> list[str]:
    """Art. 111(2) AIA: whether the Regulation applies to a legacy high-risk system at all
    turns on a significant change in design, so an unknown answer is an open question.
    So is an unknown deployer status where the 2030 date may turn on it; that question
    is asked after an asserted change too, where the status changes only the wording."""

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
    # On an Annex I route without an Annex III area no Art. 49 question asks for the
    # deployer's status, yet the 2030 date of the second sentence may turn on it.
    if (
        profile.annex_iii_area is None
        and profile.deployer_public_authority is None
        and public_authority_status_used(profile)
    ):
        when = (
            f"the system was {describe_dates(legacy)}, before {cut_off}"
            if legacy
            else "no placing-on-market or putting-into-service date is given to compare "
            f"with {cut_off}"
        )
        # public_authority_use is a plain flag, so "not recorded" covers an answer of no too.
        placed_before = (
            "" if legacy else f" and was placed on the market or put into service before {cut_off}"
        )
        # Which date the cut-off is, is contested: say so where the answer rests on it.
        literal = f"Literal reading, confirm with counsel: this uses {cut_off} as the "
        general = f"Art. 111(2) AIA cut-off. If the general date of {GENERAL_APPLICATION_DATE} "
        if not legacy:
            flag = (
                " Give the date the system was placed on the market or put into service "
                f"(placing_on_market_date, putting_into_service_date). {literal}{general}"
                "is meant, only a system placed on the market or put into service before "
                "that date is a legacy system."
            )
        elif cut_off_contested(profile, cut_off):
            flag = (
                f" {literal}{general}is meant, the system is not a legacy system and the "
                "2 August 2030 date does not apply to it."
            )
        else:
            flag = ""
        questions.append(
            f"Art. 111(2) AIA: {when}; the profile records no intended use by public "
            "authorities, and the deployer's status is not given. If the system is intended "
            f"to be used by public authorities{placed_before}, its providers and deployers "
            f"{PUBLIC_AUTHORITY_DUTY}; a "
            "public-authority deployer may indicate that use. Confirm whether the system is "
            "intended to be used by public authorities (public_authority_use). "
            f"{_STATUS_CONFIRM}{flag}"
        )
    if not legacy and (derogation := derogation_note(profile, cut_off)):
        questions.append(
            f"Art. 111(2) AIA: the system was {describe_dates(market_dates(profile))}, not "
            f"before {cut_off}, so the transition does not apply to it as classified. "
            f"{derogation} Confirm the derogation (Art. 6(4) AIA)."
        )
    return questions


def _art_49_3_questions(profile: SystemProfile, registration: bool) -> list[str]:
    """Art. 49(3) AIA turns on the deployer's own status, and so does the Art. 49(5)
    pointer for Annex III point 2. Where the status is not given, ask for it on every
    Annex III point, naming what points to it where something does: a missing status
    would otherwise read like "no"."""

    if profile.deployer_public_authority is not None:
        return []
    confirm = _STATUS_CONFIRM
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
    if eu_database_registration_applies(profile.annex_iii_area):
        # Any other point but 2; III.unsure too, as for Art. 49(1).
        point_2 = (
            " If the Annex III point is 2, Art. 49(5) AIA registers the system at national "
            "level instead."
            if profile.annex_iii_area is AnnexIII.UNSURE
            else ""
        )
        return [
            "Art. 49(3) AIA: the deployer's status is not given. A deployer that is, or acts "
            "on behalf of, a public authority or Union institution, body, office or agency "
            f"registers its use of the system in the EU database.{point_2} {confirm}"
        ]
    if profile.annex_iii_area is AnnexIII.CRITICAL_INFRASTRUCTURE:
        use = (
            "the system is intended to be used by public authorities, but "
            if profile.public_authority_use
            else ""
        )
        return [
            f"Art. 49(5) AIA: {use}the deployer's status is not given. Art. 49(3) AIA "
            "excepts Annex III point 2, which is registered at national level; a deployer "
            "that is, or acts on behalf of, a public authority or Union institution, body, "
            f"office or agency should check what the national procedure asks of it. {confirm}"
        ]
    return []


def _art_111_4_questions(
    profile: SystemProfile, transparency_obligations: list[Obligation]
) -> list[str]:
    """C9: Art. 111(4) AIA dates Art. 50(2) by the system's placing on the market, so an
    unknown placing date is asked until the assessment date falls on or after both dates."""

    if profile.placing_on_market_date is not None or not any(
        ob.article == ART_50_2 for ob in transparency_obligations
    ):
        return []
    if not start_date_open(profile.assessment_date, ART_111_4_DEADLINE):
        return []
    return [
        "Art. 111(4) AIA: placing_on_market_date is not given. A system generating synthetic "
        f"content placed on the market before {GENERAL_APPLICATION_DATE} complies with "
        f"Art. 50(2) by {ART_111_4_DEADLINE}; a later one is bound from "
        f"{GENERAL_APPLICATION_DATE}. Give the date the system was placed on the market "
        "(placing_on_market_date)."
    ]


def _gpai_date_questions(profile: SystemProfile) -> list[str]:
    """Art. 111(3) AIA dates a general-purpose AI model by its own placing on the market."""

    model_date, fallback = gpai_model_date(profile)
    if model_date is None:
        if not start_date_open(profile.assessment_date, ART_111_3_DEADLINE):
            return []
        # C9: the Art. 111(3) date turns on the model's placing date, so it is asked.
        return [
            "Art. 111(3) AIA: neither gpai_model_placing_on_market_date nor "
            "placing_on_market_date is given. A model placed on the market before "
            f"{POINT_B_DATE} complies by {ART_111_3_DEADLINE}; a later one is bound from "
            f"{POINT_B_DATE}. Give the model's own date (gpai_model_placing_on_market_date)."
        ]
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
