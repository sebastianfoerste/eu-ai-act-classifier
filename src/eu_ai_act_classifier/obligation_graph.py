"""Structured obligation graph for product and review workflows."""

from __future__ import annotations

from datetime import date

from .catalog import ART_49, ART_50_2, eu_database_registration_applies
from .citations import (
    AI_ACT_URL,
    ART_111_3_DEADLINE,
    ART_111_4_DEADLINE,
    GENERAL_APPLICATION_DATE,
    POINT_B_DATE,
    POINT_C_ANNEX_I,
    POINT_C_ANNEX_III,
)
from .models import (
    AnnexIII,
    Obligation,
    ObligationGraphItem,
    ReviewStatus,
    RiskTier,
    Role,
    SourceStatus,
    SystemProfile,
)

_SECTION_5 = "Chapter III, Section 5"
_CHAPTER_IX = "Chapter IX"
_ART_111_3_NOTE = (
    "Art. 111(3) AIA: providers of general-purpose AI models placed on the market before "
    f"{POINT_B_DATE} comply with this Regulation by {ART_111_3_DEADLINE}."
)
_ART_111_4_NOTE = (
    f"Art. 111(4) AIA: providers of systems placed on the market before "
    f"{GENERAL_APPLICATION_DATE} comply with Art. 50(2) by {ART_111_4_DEADLINE}."
)


def build_obligation_graph(
    *,
    profile: SystemProfile,
    final_tier: RiskTier,
    is_gpai: bool,
    gpai_systemic: bool,
    fria_required: bool,
    transparency_obligations: list[Obligation],
) -> list[ObligationGraphItem]:
    items: list[ObligationGraphItem] = []

    if final_tier is RiskTier.HIGH:
        application_date = _high_risk_application_date(profile)
        if profile.is_provider:
            items.extend(_high_risk_provider_graph(application_date, profile.annex_iii_area))
        if profile.is_deployer:
            items.append(
                _item(
                    "high-risk.deployer.26",
                    "Art. 26 AIA",
                    Role.DEPLOYER,
                    "Deployer of a high-risk AI system.",
                    (
                        "Use the system per instructions, assign oversight, monitor operation "
                        "and keep logs."
                    ),
                    "Deployer operating procedure and monitoring log.",
                    application_date,
                )
            )
            if fria_required:
                items.append(
                    _item(
                        "high-risk.deployer.27",
                        "Art. 27 AIA",
                        Role.DEPLOYER,
                        "FRIA trigger under Art. 27(1) AIA.",
                        (
                            "Perform and maintain a fundamental rights impact assessment "
                            "before first use."
                        ),
                        "Draft FRIA and notification record.",
                        application_date,
                        ReviewStatus.REVIEW_REQUIRED,
                    )
                )
        if profile.is_importer:
            items.append(
                _item(
                    "high-risk.importer.23",
                    "Art. 23 AIA",
                    Role.IMPORTER,
                    "Importer of a high-risk AI system.",
                    (
                        "Verify provider conformity, documentation, CE marking and "
                        "instructions before placing on the market."
                    ),
                    "Importer due-diligence checklist.",
                    application_date,
                    ReviewStatus.REVIEW_REQUIRED,
                )
            )
        if profile.is_distributor:
            items.append(
                _item(
                    "high-risk.distributor.24",
                    "Art. 24 AIA",
                    Role.DISTRIBUTOR,
                    "Distributor of a high-risk AI system.",
                    (
                        "Verify CE marking, EU declaration, instructions and provider/importer "
                        "compliance signals."
                    ),
                    "Distributor pre-supply checklist.",
                    application_date,
                    ReviewStatus.REVIEW_REQUIRED,
                )
            )
        if profile.is_authorized_representative or profile.provider_established_outside_eu:
            items.append(
                _item(
                    "high-risk.authorised-representative.22",
                    "Art. 22 AIA",
                    Role.AUTHORIZED_REPRESENTATIVE,
                    (
                        "Provider established outside the EU or authorised representative "
                        "role selected."
                    ),
                    (
                        "Maintain mandate, documentation access and competent-authority "
                        "cooperation process."
                    ),
                    "Authorised representative mandate and document-access file.",
                    application_date,
                    ReviewStatus.REVIEW_REQUIRED,
                )
            )
        if profile.substantially_modifies_system or profile.puts_name_or_trademark_on_system:
            items.append(
                _item(
                    "high-risk.value-chain.25",
                    "Art. 25 AIA",
                    Role.PROVIDER,
                    (
                        "Substantial modification or market placement under own name or "
                        "trademark is asserted."
                    ),
                    "Assess whether provider responsibilities shift along the AI value chain.",
                    "Value-chain responsibility assessment.",
                    application_date,
                    ReviewStatus.REVIEW_REQUIRED,
                )
            )

    if is_gpai and final_tier is not RiskTier.PROHIBITED:
        items.extend(_gpai_graph(gpai_systemic, _art_111_3_note(profile)))

    for index, obligation in enumerate(transparency_obligations, start=1):
        applies_from, note = GENERAL_APPLICATION_DATE, None
        if obligation.article == ART_50_2:
            applies_from, note = _art_50_2_dating(profile)
        items.append(
            _item(
                f"transparency.{index}",
                obligation.article,
                obligation.applies_to,
                "Art. 50 transparency trigger in the submitted profile.",
                obligation.requirement,
                "Transparency notice, label or disclosure record.",
                applies_from,
                application_date_note=note,
            )
        )

    return items


def _high_risk_provider_graph(
    application_date: str, annex_iii_area: AnnexIII | None
) -> list[ObligationGraphItem]:
    return [
        _item(
            "high-risk.provider.16",
            "Art. 16 AIA",
            Role.PROVIDER,
            "Provider of a high-risk AI system.",
            "Ensure the high-risk system complies with Chapter III requirements.",
            "Provider compliance responsibility matrix.",
            application_date,
        ),
        _item(
            "high-risk.provider.17",
            "Art. 17 AIA",
            Role.PROVIDER,
            "Provider of a high-risk AI system.",
            "Maintain a quality management system.",
            "Quality management system file.",
            application_date,
        ),
        _item(
            "high-risk.provider.18",
            "Art. 18 AIA",
            Role.PROVIDER,
            "Provider of a high-risk AI system.",
            "Keep technical documentation, logs and conformity documentation.",
            "Document retention register.",
            application_date,
        ),
        _item(
            "high-risk.provider.19",
            "Art. 19 AIA",
            Role.PROVIDER,
            "Provider of a high-risk AI system.",
            "Keep automatically generated logs where under provider control.",
            "Logging retention policy.",
            application_date,
        ),
        _item(
            "high-risk.provider.20",
            "Art. 20 AIA",
            Role.PROVIDER,
            "Risk or nonconformity after placing on the market.",
            "Take corrective action and inform relevant parties where required.",
            "Corrective-action and notification log.",
            application_date,
            ReviewStatus.REVIEW_REQUIRED,
        ),
        _item(
            "high-risk.provider.21",
            "Art. 21 AIA",
            Role.PROVIDER,
            "Competent-authority request.",
            "Cooperate with competent authorities and provide requested information.",
            "Authority cooperation protocol.",
            application_date,
            ReviewStatus.REVIEW_REQUIRED,
        ),
        # Chapter III, Section 5 (Arts. 40-49) and Chapter IX (Arts. 72-73) are not in
        # the Art. 113, third paragraph, point (c) deferral. Read literally they apply
        # from the general date; whether they follow Sections 1 to 3 is contested, so
        # each item carries the deferred alternative and goes to review.
        _undeferred_item(
            "high-risk.provider.40",
            "Art. 40 AIA",
            "High-risk requirements where harmonised standards are available.",
            "Track applicable harmonised standards and standardisation deliverables.",
            "Standards applicability matrix.",
            _SECTION_5,
            application_date,
        ),
        _undeferred_item(
            "high-risk.provider.41",
            "Art. 41 AIA",
            "Common specifications become applicable.",
            (
                "Assess common specifications where harmonised standards are unavailable "
                "or insufficient."
            ),
            "Common specifications assessment.",
            _SECTION_5,
            application_date,
        ),
        _undeferred_item(
            "high-risk.provider.42",
            "Art. 42 AIA",
            "Use of standards or specifications for presumption of conformity.",
            "Map implemented controls to standards, specifications or alternative evidence.",
            "Presumption of conformity mapping.",
            _SECTION_5,
            application_date,
        ),
        _undeferred_item(
            "high-risk.provider.43",
            "Art. 43 AIA",
            "Before placing high-risk AI system on the market or putting into service.",
            "Complete the applicable conformity assessment.",
            "Conformity assessment file.",
            _SECTION_5,
            application_date,
        ),
        _undeferred_item(
            "high-risk.provider.44",
            "Art. 44 AIA",
            "Certificate issued by notified body where applicable.",
            "Track certificate validity, changes and renewal obligations.",
            "Certificate register.",
            _SECTION_5,
            application_date,
        ),
        _undeferred_item(
            "high-risk.provider.47",
            "Art. 47 AIA",
            "Conformity established.",
            "Draw up and keep the EU declaration of conformity.",
            "EU declaration of conformity.",
            _SECTION_5,
            application_date,
        ),
        _undeferred_item(
            "high-risk.provider.48",
            "Art. 48 AIA",
            "Conformity established for a high-risk AI system.",
            "Affix CE marking where required.",
            "CE marking record.",
            _SECTION_5,
            application_date,
        ),
        *_registration_items(annex_iii_area),
        _undeferred_item(
            "high-risk.provider.72",
            "Art. 72 AIA",
            "High-risk AI system lifecycle.",
            "Operate a post-market monitoring system and plan.",
            "Post-market monitoring plan.",
            _CHAPTER_IX,
            application_date,
        ),
        _undeferred_item(
            "high-risk.provider.73",
            "Art. 73 AIA",
            "Serious incident identified.",
            "Report serious incidents to the market surveillance authority.",
            "Serious incident register.",
            _CHAPTER_IX,
            application_date,
        ),
    ]


def _registration_items(annex_iii_area: AnnexIII | None) -> list[ObligationGraphItem]:
    """Art. 49 AIA registration. Only Annex III systems register under Art. 49(1) and
    (5), so the deferred alternative is the point (c)(i) date even for a system that
    is also an Annex I product."""

    if eu_database_registration_applies(annex_iii_area):
        return [
            _undeferred_item(
                "high-risk.provider.49",
                ART_49,
                (
                    "Before placing an Annex III high-risk AI system on the market or putting "
                    "it into service."
                ),
                "Register the provider and system in the EU database where required.",
                "EU database registration record.",
                _SECTION_5,
                POINT_C_ANNEX_III,
            )
        ]
    if annex_iii_area is AnnexIII.CRITICAL_INFRASTRUCTURE:
        return [
            _undeferred_item(
                "high-risk.provider.49.5",
                "Art. 49(5) AIA",
                "Annex III point 2 high-risk AI system (critical infrastructure).",
                (
                    "Have the system registered at national level, not in the EU database; "
                    "confirm the national procedure and who registers."
                ),
                "National registration record.",
                _SECTION_5,
                POINT_C_ANNEX_III,
            )
        ]
    return []


def _gpai_graph(systemic: bool, note: str | None) -> list[ObligationGraphItem]:
    # Every Chapter V item carries the Art. 111(3) AIA transition unless the model was
    # placed on the market on or after the point (b) date.
    items = [
        _item(
            "gpai.provider.53.a",
            "Art. 53(1)(a) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Keep model technical documentation per Annex XI.",
            "GPAI model documentation checklist.",
            POINT_B_DATE,
            ReviewStatus.DETERMINED,
            note,
        ),
        _item(
            "gpai.provider.53.b",
            "Art. 53(1)(b) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Provide downstream providers with information per Annex XII.",
            "Downstream provider information pack.",
            POINT_B_DATE,
            ReviewStatus.DETERMINED,
            note,
        ),
        _item(
            "gpai.provider.53.c",
            "Art. 53(1)(c) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Maintain a policy to comply with Union copyright law.",
            "Copyright compliance policy.",
            POINT_B_DATE,
            ReviewStatus.REVIEW_REQUIRED,
            note,
        ),
        _item(
            "gpai.provider.53.d",
            "Art. 53(1)(d) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Publish a sufficiently detailed summary of training content.",
            "Training-content summary.",
            POINT_B_DATE,
            ReviewStatus.REVIEW_REQUIRED,
            note,
        ),
        _item(
            "gpai.provider.56",
            "Art. 56 AIA",
            Role.GPAI_PROVIDER,
            "Provider choosing a Code of Practice route or alternative compliance evidence.",
            "Track Code of Practice adherence or alternative means of compliance.",
            "GPAI Code of Practice adherence record.",
            POINT_B_DATE,
            ReviewStatus.REVIEW_REQUIRED,
            note,
        ),
    ]
    if systemic:
        items.extend(
            [
                _item(
                    "gpai.provider.55.a",
                    "Art. 55(1)(a) AIA",
                    Role.GPAI_PROVIDER,
                    "GPAI model with systemic risk.",
                    "Perform model evaluation, including adversarial testing.",
                    "Systemic model evaluation file.",
                    POINT_B_DATE,
                    ReviewStatus.REVIEW_REQUIRED,
                    note,
                ),
                _item(
                    "gpai.provider.55.b",
                    "Art. 55(1)(b) AIA",
                    Role.GPAI_PROVIDER,
                    "GPAI model with systemic risk.",
                    "Assess and mitigate systemic risks at Union level.",
                    "Systemic risk assessment and mitigation plan.",
                    POINT_B_DATE,
                    ReviewStatus.REVIEW_REQUIRED,
                    note,
                ),
                _item(
                    "gpai.provider.55.c",
                    "Art. 55(1)(c) AIA",
                    Role.GPAI_PROVIDER,
                    "GPAI model with systemic risk.",
                    "Track, document and report serious incidents.",
                    "GPAI serious incident register.",
                    POINT_B_DATE,
                    ReviewStatus.REVIEW_REQUIRED,
                    note,
                ),
                _item(
                    "gpai.provider.55.d",
                    "Art. 55(1)(d) AIA",
                    Role.GPAI_PROVIDER,
                    "GPAI model with systemic risk.",
                    "Ensure an adequate level of cybersecurity protection.",
                    "Cybersecurity control file.",
                    POINT_B_DATE,
                    ReviewStatus.REVIEW_REQUIRED,
                    note,
                ),
            ]
        )
    return items


def _item(
    obligation_id: str,
    article: str,
    actor: Role,
    trigger: str,
    requirement: str,
    evidence_artifact: str,
    application_date: str,
    review_status: ReviewStatus = ReviewStatus.DETERMINED,
    application_date_note: str | None = None,
) -> ObligationGraphItem:
    return ObligationGraphItem(
        obligation_id=obligation_id,
        article=article,
        actor=actor,
        trigger=trigger,
        requirement=requirement,
        evidence_artifact=evidence_artifact,
        source_status=SourceStatus.BINDING_LEVEL_1,
        source_url=AI_ACT_URL,
        application_date=application_date,
        review_status=review_status,
        application_date_note=application_date_note,
    )


def _undeferred_item(
    obligation_id: str,
    article: str,
    trigger: str,
    requirement: str,
    evidence_artifact: str,
    location: str,
    deferred_date: str,
) -> ObligationGraphItem:
    """A provider duty outside the point (c) deferral: the literal general date, the
    deferred alternative in the note, and review."""

    return _item(
        obligation_id,
        article,
        Role.PROVIDER,
        trigger,
        requirement,
        evidence_artifact,
        GENERAL_APPLICATION_DATE,
        ReviewStatus.REVIEW_REQUIRED,
        _literal_reading_note(location, deferred_date),
    )


def _placed_before(profile: SystemProfile, cut_off: str) -> bool | None:
    """Whether the system was placed on the market before ``cut_off``, as Art. 111(3)
    and (4) AIA require; None when the profile gives no placing-on-market date."""

    if profile.placing_on_market_date is None:
        return None
    return date.fromisoformat(profile.placing_on_market_date) < date.fromisoformat(cut_off)


def _art_111_3_note(profile: SystemProfile) -> str | None:
    if _placed_before(profile, POINT_B_DATE) is False:
        return None
    return _ART_111_3_NOTE


def _art_50_2_dating(profile: SystemProfile) -> tuple[str, str | None]:
    """Application date and note for the Art. 50(2) item under Art. 111(4) AIA."""

    placed_before = _placed_before(profile, GENERAL_APPLICATION_DATE)
    if placed_before is None:
        # Placing date unknown: the general date, with the transition as a condition.
        return GENERAL_APPLICATION_DATE, _ART_111_4_NOTE
    if placed_before:
        return ART_111_4_DEADLINE, _ART_111_4_NOTE
    return GENERAL_APPLICATION_DATE, None


def _literal_reading_note(location: str, deferred_date: str) -> str:
    return (
        "Literal reading, confirm with counsel: Art. 113, third paragraph, point (c) AIA "
        f"defers only Chapter III, Sections 1, 2 and 3, so this {location} duty applies "
        f"from {GENERAL_APPLICATION_DATE} (Art. 113, second paragraph). If it is read as "
        f"following that deferral, {deferred_date} applies."
    )


def _high_risk_application_date(profile: SystemProfile) -> str:
    """Art. 113, third paragraph, point (c) AIA date for Chapter III, Sections 1 to 3."""

    if profile.annex_i_safety_component and profile.annex_i_third_party_assessment:
        return POINT_C_ANNEX_I  # point (c)(ii): Art. 6(1) and Annex I
    # Point (c)(i): every other high-risk route here runs through Art. 6(2) and
    # Annex III, including III.unsure.
    return POINT_C_ANNEX_III
