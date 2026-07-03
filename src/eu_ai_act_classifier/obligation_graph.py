"""Structured obligation graph for product and review workflows."""

from __future__ import annotations

from .citations import AI_ACT_URL
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
            items.extend(_high_risk_provider_graph(application_date))
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
        items.extend(_gpai_graph(gpai_systemic))

    for index, obligation in enumerate(transparency_obligations, start=1):
        items.append(
            _item(
                f"transparency.{index}",
                obligation.article,
                obligation.applies_to,
                "Art. 50 transparency trigger in the submitted profile.",
                obligation.requirement,
                "Transparency notice, label or disclosure record.",
                "2026-08-02",
            )
        )

    return items


def _high_risk_provider_graph(application_date: str) -> list[ObligationGraphItem]:
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
        _item(
            "high-risk.provider.40",
            "Art. 40 AIA",
            Role.PROVIDER,
            "High-risk requirements where harmonised standards are available.",
            "Track applicable harmonised standards and standardisation deliverables.",
            "Standards applicability matrix.",
            application_date,
            ReviewStatus.REVIEW_REQUIRED,
        ),
        _item(
            "high-risk.provider.41",
            "Art. 41 AIA",
            Role.PROVIDER,
            "Common specifications become applicable.",
            (
                "Assess common specifications where harmonised standards are unavailable "
                "or insufficient."
            ),
            "Common specifications assessment.",
            application_date,
            ReviewStatus.REVIEW_REQUIRED,
        ),
        _item(
            "high-risk.provider.42",
            "Art. 42 AIA",
            Role.PROVIDER,
            "Use of standards or specifications for presumption of conformity.",
            "Map implemented controls to standards, specifications or alternative evidence.",
            "Presumption of conformity mapping.",
            application_date,
            ReviewStatus.REVIEW_REQUIRED,
        ),
        _item(
            "high-risk.provider.43",
            "Art. 43 AIA",
            Role.PROVIDER,
            "Before placing high-risk AI system on the market or putting into service.",
            "Complete the applicable conformity assessment.",
            "Conformity assessment file.",
            application_date,
            ReviewStatus.REVIEW_REQUIRED,
        ),
        _item(
            "high-risk.provider.44",
            "Art. 44 AIA",
            Role.PROVIDER,
            "Certificate issued by notified body where applicable.",
            "Track certificate validity, changes and renewal obligations.",
            "Certificate register.",
            application_date,
            ReviewStatus.REVIEW_REQUIRED,
        ),
        _item(
            "high-risk.provider.47",
            "Art. 47 AIA",
            Role.PROVIDER,
            "Conformity established.",
            "Draw up and keep the EU declaration of conformity.",
            "EU declaration of conformity.",
            application_date,
        ),
        _item(
            "high-risk.provider.48",
            "Art. 48 AIA",
            Role.PROVIDER,
            "Conformity established for a high-risk AI system.",
            "Affix CE marking where required.",
            "CE marking record.",
            application_date,
        ),
        _item(
            "high-risk.provider.49",
            "Art. 49 AIA",
            Role.PROVIDER,
            (
                "Before placing an Annex III high-risk AI system on the market or putting "
                "it into service."
            ),
            "Register the provider and system in the EU database where required.",
            "EU database registration record.",
            application_date,
            ReviewStatus.REVIEW_REQUIRED,
        ),
        _item(
            "high-risk.provider.72",
            "Art. 72 AIA",
            Role.PROVIDER,
            "High-risk AI system lifecycle.",
            "Operate a post-market monitoring system and plan.",
            "Post-market monitoring plan.",
            application_date,
        ),
        _item(
            "high-risk.provider.73",
            "Art. 73 AIA",
            Role.PROVIDER,
            "Serious incident identified.",
            "Report serious incidents to the market surveillance authority.",
            "Serious incident register.",
            application_date,
            ReviewStatus.REVIEW_REQUIRED,
        ),
    ]


def _gpai_graph(systemic: bool) -> list[ObligationGraphItem]:
    items = [
        _item(
            "gpai.provider.53.a",
            "Art. 53(1)(a) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Keep model technical documentation per Annex XI.",
            "GPAI model documentation checklist.",
            "2025-08-02",
        ),
        _item(
            "gpai.provider.53.b",
            "Art. 53(1)(b) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Provide downstream providers with information per Annex XII.",
            "Downstream provider information pack.",
            "2025-08-02",
        ),
        _item(
            "gpai.provider.53.c",
            "Art. 53(1)(c) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Maintain a policy to comply with Union copyright law.",
            "Copyright compliance policy.",
            "2025-08-02",
            ReviewStatus.REVIEW_REQUIRED,
        ),
        _item(
            "gpai.provider.53.d",
            "Art. 53(1)(d) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Publish a sufficiently detailed summary of training content.",
            "Training-content summary.",
            "2025-08-02",
            ReviewStatus.REVIEW_REQUIRED,
        ),
        _item(
            "gpai.provider.56",
            "Art. 56 AIA",
            Role.GPAI_PROVIDER,
            "Provider choosing a Code of Practice route or alternative compliance evidence.",
            "Track Code of Practice adherence or alternative means of compliance.",
            "GPAI Code of Practice adherence record.",
            "2025-08-02",
            ReviewStatus.REVIEW_REQUIRED,
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
                    "2025-08-02",
                    ReviewStatus.REVIEW_REQUIRED,
                ),
                _item(
                    "gpai.provider.55.b",
                    "Art. 55(1)(b) AIA",
                    Role.GPAI_PROVIDER,
                    "GPAI model with systemic risk.",
                    "Assess and mitigate systemic risks at Union level.",
                    "Systemic risk assessment and mitigation plan.",
                    "2025-08-02",
                    ReviewStatus.REVIEW_REQUIRED,
                ),
                _item(
                    "gpai.provider.55.c",
                    "Art. 55(1)(c) AIA",
                    Role.GPAI_PROVIDER,
                    "GPAI model with systemic risk.",
                    "Track, document and report serious incidents.",
                    "GPAI serious incident register.",
                    "2025-08-02",
                    ReviewStatus.REVIEW_REQUIRED,
                ),
                _item(
                    "gpai.provider.55.d",
                    "Art. 55(1)(d) AIA",
                    Role.GPAI_PROVIDER,
                    "GPAI model with systemic risk.",
                    "Ensure an adequate level of cybersecurity protection.",
                    "Cybersecurity control file.",
                    "2025-08-02",
                    ReviewStatus.REVIEW_REQUIRED,
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
    )


def _high_risk_application_date(profile: SystemProfile) -> str:
    if profile.annex_i_safety_component and profile.annex_i_third_party_assessment:
        return "2027-08-02"
    if profile.annex_iii_area is AnnexIII.UNSURE or profile.annex_iii_area is not None:
        return "2026-08-02"
    return "2026-08-02"
