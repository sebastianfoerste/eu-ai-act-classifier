"""Structured obligation graph for product and review workflows."""

from __future__ import annotations

from .catalog import (
    ANNEX_III,
    ART_2_2,
    ART_26_8,
    ART_49,
    ART_49_2,
    ART_49_3,
    ART_50_2,
    ART_111_2,
    eu_database_registration_applies,
    national_registration_for_public_authority_deployer,
    public_authority_registration_applies,
    public_authority_registration_requirement,
    public_authority_users,
    section_b_annex_iii_flag,
    section_b_kept_flag,
    section_b_requirement,
    secure_section_note,
)
from .citations import (
    AI_ACT_URL,
    ART_111_2_PUBLIC_AUTHORITY_DEADLINE,
    ART_111_3_DEADLINE,
    ART_111_4_DEADLINE,
    GENERAL_APPLICATION_DATE,
    POINT_B_DATE,
    POINT_C_ANNEX_I,
    POINT_C_ANNEX_III,
    POINT_D_DATE,
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
from .transitions import (
    ANNEX_X_CARVE_OUT,
    before,
    chapter_iii_date,
    cut_off_flag,
    derogation_asserted,
    derogation_note,
    describe_dates,
    gpai_model_date,
    legacy_dates,
    legacy_note_flag,
    legacy_transparency_flag,
    operator_roles,
    operators,
    public_authority_clause,
    public_authority_sentence,
    section_b_only,
    section_b_product,
)

_SECTION_5 = "Chapter III, Section 5"
_CHAPTER_IX = "Chapter IX"
_ART_111_3_NOTE = (
    "Art. 111(3) AIA: providers of general-purpose AI models placed on the market before "
    f"{POINT_B_DATE} take the necessary steps to comply with the obligations laid down in "
    f"this Regulation by {ART_111_3_DEADLINE}."
)
_ART_111_4_NOTE = (
    f"Art. 111(4) AIA: providers of systems placed on the market before "
    f"{GENERAL_APPLICATION_DATE} take the necessary steps to comply with Art. 50(2) by "
    f"{ART_111_4_DEADLINE}."
)
# Backwards compatibility: a GPAI profile without the model's own date is dated by the
# AI system's placing_on_market_date, as before, says so and goes to review.
_GPAI_DATE_FALLBACK = (
    "no gpai_model_placing_on_market_date is given, the model is dated by "
    "placing_on_market_date, the AI system's date. Review it and give the model's own date."
)
# Art. 2(2) AIA lists neither Art. 5 nor Art. 50 for a Section B product. The report keeps
# the Art. 50 duties (and, in rules/prohibited.py, Art. 5) as the conservative reading.
_SECTION_B_TRANSPARENCY_FLAG = section_b_kept_flag("Art. 50", "the Art. 50 duties")
_PROVIDER_OR_DEPLOYER = (Role.PROVIDER, Role.DEPLOYER)


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

    if final_tier is RiskTier.HIGH and section_b_only(profile):
        items.extend(_section_b_items(profile))
    elif final_tier is RiskTier.HIGH:
        # A high-risk tier always has a route, so the fallback only satisfies the type.
        application_date = chapter_iii_date(profile) or POINT_C_ANNEX_III
        if profile.is_provider:
            items.extend(_high_risk_provider_graph(application_date, profile))
        if profile.is_deployer:
            public_authority_registration = public_authority_registration_applies(
                profile.annex_iii_area,
                profile.deployer_public_authority,
                profile.public_authority_use,
            )
            # Art. 26(8), second sentence, is a Section 3 duty: the Art. 26 date, not the
            # Art. 49(3) one.
            art_26_8 = f" {ART_26_8}" if public_authority_registration else ""
            items.append(
                _item(
                    "high-risk.deployer.26",
                    "Art. 26 AIA",
                    Role.DEPLOYER,
                    "Deployer of a high-risk AI system.",
                    (
                        "Use the system per instructions, assign oversight, monitor operation "
                        f"and keep logs.{art_26_8}"
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
            if public_authority_registration:
                items.append(_public_authority_registration_item(profile))
            elif national_registration_for_public_authority_deployer(
                profile.annex_iii_area,
                profile.deployer_public_authority,
                profile.public_authority_use,
            ):
                system = "an Annex III point 2 high-risk AI system (critical infrastructure)"
                trigger = (
                    "Deployer that is, or acts on behalf of, a public authority or Union "
                    f"institution, body, office or agency, using {system}."
                    if profile.deployer_public_authority
                    else f"{system[0].upper()}{system[1:]}, intended to be used by public "
                    "authorities; the deployer's own status is not given."
                )
                items.append(
                    _undeferred_item(
                        "high-risk.deployer.49.5",
                        "Art. 49(5) AIA",
                        trigger,
                        (
                            "Art. 49(3) AIA excepts point 2, so there is no registration of use "
                            "in the EU database; the system is registered at national level. "
                            "Confirm what the national procedure asks of the deployer."
                        ),
                        "National registration record.",
                        _SECTION_5,
                        POINT_C_ANNEX_III,
                        actor=Role.DEPLOYER,
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
        items = _with_legacy_notes(items, profile, application_date)
        items.extend(_art_111_2_items(profile, application_date))
        if section_b_product(profile):
            items.extend(_section_b_items(profile))

    if is_gpai and final_tier is not RiskTier.PROHIBITED:
        items.extend(_gpai_graph(gpai_systemic, profile))

    legacy_flag = legacy_transparency_flag(profile) if final_tier is RiskTier.HIGH else None
    for index, obligation in enumerate(transparency_obligations, start=1):
        applies_from, note = GENERAL_APPLICATION_DATE, None
        if obligation.article == ART_50_2:
            applies_from, note = _art_111_dating(
                profile.placing_on_market_date,
                GENERAL_APPLICATION_DATE,
                ART_111_4_DEADLINE,
                _ART_111_4_NOTE,
            )
        # Art. 2(2) lists Art. 50 for no Section B product, Annex III area or not.
        section_b_flag = _SECTION_B_TRANSPARENCY_FLAG if section_b_product(profile) else None
        flagged = bool(section_b_flag or legacy_flag)
        note = " ".join(part for part in (section_b_flag, note, legacy_flag) if part) or None
        items.append(
            _item(
                f"transparency.{index}",
                obligation.article,
                obligation.applies_to,
                "Art. 50 transparency trigger in the submitted profile.",
                obligation.requirement,
                "Transparency notice, label or disclosure record.",
                applies_from,
                # A counsel flag sends the item to review, like every other flagged item.
                ReviewStatus.REVIEW_REQUIRED if flagged else ReviewStatus.DETERMINED,
                note,
            )
        )

    return items


def _high_risk_provider_graph(
    application_date: str, profile: SystemProfile
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
        _conformity_route_item(
            application_date, internal_control_route=_internal_control_route(profile)
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
        *_registration_items(profile),
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


def _conformity_route_item(
    application_date: str, *, internal_control_route: bool
) -> ObligationGraphItem:
    """The Art. 43(2) internal-control item for Annex III points 2 to 8, else the Art. 44
    certificate item. Both are Chapter III, Section 5 duties, dated like the other
    Section 5 items (_undeferred_item)."""

    if internal_control_route:
        return _undeferred_item(
            "high-risk.provider.43.2",
            "Art. 43(2) AIA",
            "High-risk AI system referred to in points 2 to 8 of Annex III.",
            (
                "Follow the conformity assessment procedure based on internal control "
                "(Annex VI), which does not involve a notified body."
            ),
            "Annex VI internal-control assessment record.",
            _SECTION_5,
            application_date,
        )
    return _undeferred_item(
        "high-risk.provider.44",
        "Art. 44 AIA",
        "Certificate issued by notified body where applicable.",
        "Track certificate validity, changes and renewal obligations.",
        "Certificate register.",
        _SECTION_5,
        application_date,
    )


def _registration_items(profile: SystemProfile) -> list[ObligationGraphItem]:
    """Art. 49 AIA registration. Every item here needs an Annex III area, so the
    deferred alternative is the point (c)(i) date."""

    annex_iii_area = profile.annex_iii_area
    items: list[ObligationGraphItem] = []
    if eu_database_registration_applies(annex_iii_area):
        items.append(
            _undeferred_item(
                "high-risk.provider.49",
                ART_49,
                (
                    "Before placing an Annex III high-risk AI system on the market or putting "
                    "it into service."
                ),
                (
                    "Register the provider and system in the EU database where required."
                    f"{secure_section_note(annex_iii_area)}"
                ),
                "EU database registration record.",
                _SECTION_5,
                POINT_C_ANNEX_III,
            )
        )
    elif annex_iii_area is AnnexIII.CRITICAL_INFRASTRUCTURE:
        items.append(
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
        )
    derogation = profile.derogation
    if (
        annex_iii_area is not None
        and derogation.any_condition
        and not derogation.performs_profiling
    ):
        # Art. 49(2) has no point 2 exception: a provider relying on Art. 6(3) registers
        # in the EU database whatever the Annex III point.
        items.append(
            _undeferred_item(
                "high-risk.provider.49.2",
                ART_49_2,
                "Art. 6(3) derogation asserted for an Annex III AI system.",
                (
                    "If the provider concludes under Art. 6(3) that the system is not "
                    "high-risk, register the provider and system in the EU database before "
                    "placing it on the market or putting it into service."
                    f"{secure_section_note(annex_iii_area)}"
                ),
                "Art. 6(4) assessment and EU database registration record.",
                _SECTION_5,
                POINT_C_ANNEX_III,
            )
        )
    return items


def _public_authority_registration_item(profile: SystemProfile) -> ObligationGraphItem:
    """Art. 49(3) AIA: public-authority deployers of Annex III systems other than point 2.
    Like Art. 49(1), Chapter III, Section 5, so the literal date and the point (c)(i)
    alternative."""

    if profile.annex_iii_area is AnnexIII.UNSURE:
        system = (
            "an Annex III high-risk AI system whose point is not settled (if it is point 2, "
            "national registration under Art. 49(5) AIA applies instead)"
        )
    else:
        system = "an Annex III high-risk AI system (not point 2)"
    if profile.deployer_public_authority:
        trigger = (
            "Deployer that is, or acts on behalf of, a public authority or Union institution, "
            f"body, office or agency, using {system}."
        )
    else:
        use = "intended to be used by public authorities"
        if not profile.public_authority_use and (
            users := public_authority_users(profile.annex_iii_area)
        ):
            # Annex III, points 5(a), 6 and 7 describe use by the deployers Art. 49(3) names.
            use = f"which {ANNEX_III[profile.annex_iii_area][0].ref} describes as used {users}"
        trigger = (
            f"{system[0].upper()}{system[1:]}, {use}. Confirm that the deployer is, or acts on "
            "behalf of, a public authority or Union institution, body, office or agency."
        )
    return _undeferred_item(
        "high-risk.deployer.49.3",
        ART_49_3,
        trigger,
        public_authority_registration_requirement(
            profile.annex_iii_area, profile.deployer_public_authority
        ),
        "EU database registration-of-use record.",
        _SECTION_5,
        POINT_C_ANNEX_III,
        actor=Role.DEPLOYER,
    )


def _art_111_2_items(profile: SystemProfile, cut_off: str) -> list[ObligationGraphItem]:
    """Art. 111(2) AIA for a high-risk system placed on the market or put into service
    before ``cut_off``, the Chapter III date for its route. It applies to "operators", so
    one item per operator role held; only providers and deployers carry the
    public-authority deadline of the second sentence."""

    legacy = legacy_dates(profile, cut_off)
    if not legacy:
        return []
    change = profile.significant_change_after_application_date
    if change is True:
        # Which date the change must follow is the contested point the note flags, so the
        # requirement does not restate it.
        requirement = (
            "A significant change in design is asserted: the Regulation applies to the "
            "changed system. Keep the design-change log with the date of the change."
        )
    elif change is False:
        requirement = (
            "No significant change in design is asserted: apart from Art. 5, the Regulation "
            f"applies only if the design changes significantly as from {cut_off}. Keep a "
            "design-change log."
        )
    else:
        requirement = (
            "Apart from Art. 5, the Regulation applies only if the design changes "
            f"significantly as from {cut_off}. Confirm whether it has and keep a "
            "design-change log."
        )
    note = (
        f"{cut_off_flag(profile, cut_off)} Art. 111(2) AIA: covers high-risk systems placed on "
        f"the market or put into service before {cut_off}, other than {ANNEX_X_CARVE_OUT}. "
        "The date the first unit of the type and model was lawfully placed on the market or "
        "put into service decides (Regulation (EU) 2026/1744, recital 39)."
    )
    if derogation := derogation_note(profile, cut_off):
        note = f"{note} {derogation}"
    deadline = public_authority_sentence(profile).lstrip()
    items = []
    for actor in operator_roles(profile):
        actor_requirement, actor_note, application_date = requirement, note, cut_off
        if deadline and actor in _PROVIDER_OR_DEPLOYER:
            # Also in the note, which the text report and the dossier print.
            actor_requirement, actor_note = f"{requirement} {deadline}", f"{note} {deadline}"
            if profile.public_authority_use and change is not True:
                application_date = ART_111_2_PUBLIC_AUTHORITY_DEADLINE
        items.append(
            _item(
                f"high-risk.{_actor_slug(actor)}.111.2",
                ART_111_2,
                actor,
                f"High-risk AI system {describe_dates(legacy)}, before {cut_off}.",
                actor_requirement,
                "First placing-on-market or putting-into-service record and design-change log.",
                application_date,
                ReviewStatus.REVIEW_REQUIRED,
                actor_note,
            )
        )
    return items


def _with_legacy_notes(
    items: list[ObligationGraphItem], profile: SystemProfile, cut_off: str
) -> list[ObligationGraphItem]:
    """Under Art. 111(2) AIA an unchanged legacy system is outside the Regulation (Art. 5
    apart) until its design changes, so its Chapter III dates are conditional; each item
    says so next to any note it already has. The condition rests on the contested
    Chapter III date (the legacy status, or the date from which a change counts), so the
    note carries the flag and the item goes to review."""

    legacy = legacy_dates(profile, cut_off)
    if not legacy or profile.significant_change_after_application_date is True:
        return items
    # Also for an item dated 2026-08-02 (Section 5, Chapter IX): the duty does not bind
    # the unchanged system from that date either.
    condition = (
        f"Art. 111(2) AIA: the system was {describe_dates(legacy)}, before {cut_off}. "
        "Whatever date this item gives, the duty attaches only once the system's design "
        f"changes significantly as from {cut_off}"
    )
    flag = legacy_note_flag(profile, cut_off)
    out = []
    for item in items:
        text = condition
        # Art. 111(2), second sentence, binds providers and deployers only.
        if item.actor in _PROVIDER_OR_DEPLOYER:
            text += public_authority_clause(profile)
        text += f". {flag}"
        out.append(
            item.model_copy(
                update={
                    "application_date_note": (
                        f"{item.application_date_note} {text}"
                        if item.application_date_note
                        else text
                    ),
                    "review_status": ReviewStatus.REVIEW_REQUIRED,
                }
            )
        )
    return out


def _section_b_items(profile: SystemProfile) -> list[ObligationGraphItem]:
    """Art. 2(2) AIA for an Art. 6(1) high-risk system of an Annex I, Section B product.
    With no Annex III area this item replaces the Chapter III duties."""

    note = (
        "Dated by Art. 6(1), which classifies Annex I products as high-risk from "
        f"{POINT_C_ANNEX_I} (Art. 113, third paragraph, point (c)(ii) AIA). The other listed "
        f"provisions apply earlier: Arts. 102 to 110 from {POINT_D_DATE} (point (d)); "
        f"Art. 60a, Arts. 111 and 112 and, where they apply, Arts. 57 to 59 from "
        f"{GENERAL_APPLICATION_DATE} (Art. 113, second paragraph)."
    )
    annex_iii = profile.annex_iii_area is not None
    if annex_iii:
        note = f"{section_b_annex_iii_flag(derogation_asserted(profile))} {note}"
    requirement = section_b_requirement(annex_iii=annex_iii)
    return [
        _item(
            "high-risk.section-b.2.2",
            ART_2_2,
            actor,
            "Art. 6(1) high-risk AI system for a product in Annex I, Section B.",
            requirement,
            "Sectoral legislation mapping for the Annex I, Section B product.",
            POINT_C_ANNEX_I,
            ReviewStatus.REVIEW_REQUIRED,
            note,
        )
        for actor in operators(profile, (Role.PROVIDER,))
    ]


def _actor_slug(actor: Role) -> str:
    if actor is Role.AUTHORIZED_REPRESENTATIVE:
        return "authorised-representative"
    return actor.value.replace("_", "-")


def _gpai_dating(profile: SystemProfile) -> tuple[str, str | None, bool]:
    """Art. 111(3) AIA dating from the model's own date, or from the AI system's
    placing_on_market_date when only that is given, with a note, and whether it is that
    fallback, which sends every item to review."""

    model_date, fallback = gpai_model_date(profile)
    applies_from, note = _art_111_dating(
        model_date, POINT_B_DATE, ART_111_3_DEADLINE, _ART_111_3_NOTE
    )
    if fallback:
        # One "Art. 111(3) AIA:" lead, whether or not the transition note is there.
        note = (
            f"{note} As {_GPAI_DATE_FALLBACK}"
            if note
            else f"Art. 111(3) AIA: as {_GPAI_DATE_FALLBACK}"
        )
    return applies_from, note, fallback


def _gpai_graph(systemic: bool, profile: SystemProfile) -> list[ObligationGraphItem]:
    application_date, note, fallback = _gpai_dating(profile)
    # The fallback date is not the model's own: nothing dated by it is determined.
    status = ReviewStatus.REVIEW_REQUIRED if fallback else ReviewStatus.DETERMINED
    # Every Chapter V item takes the same date and Art. 111(3) AIA note (_art_111_dating).
    items = [
        _item(
            "gpai.provider.53.a",
            "Art. 53(1)(a) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Keep model technical documentation per Annex XI.",
            "GPAI model documentation checklist.",
            application_date,
            status,
            note,
        ),
        _item(
            "gpai.provider.53.b",
            "Art. 53(1)(b) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Provide downstream providers with information per Annex XII.",
            "Downstream provider information pack.",
            application_date,
            status,
            note,
        ),
        _item(
            "gpai.provider.53.c",
            "Art. 53(1)(c) AIA",
            Role.GPAI_PROVIDER,
            "Provider of a general-purpose AI model.",
            "Maintain a policy to comply with Union copyright law.",
            "Copyright compliance policy.",
            application_date,
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
            application_date,
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
            application_date,
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
                    application_date,
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
                    application_date,
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
                    application_date,
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
                    application_date,
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
    *,
    actor: Role = Role.PROVIDER,
) -> ObligationGraphItem:
    """A duty outside the point (c) deferral: the literal general date, the deferred
    alternative in the note, and review."""

    return _item(
        obligation_id,
        article,
        actor,
        trigger,
        requirement,
        evidence_artifact,
        GENERAL_APPLICATION_DATE,
        ReviewStatus.REVIEW_REQUIRED,
        _literal_reading_note(location, deferred_date),
    )


def _art_111_dating(
    placed_on: str | None, cut_off: str, deadline: str, note: str
) -> tuple[str, str | None]:
    """Application date and note under Art. 111(3) or (4) AIA. The duty applies from
    ``cut_off``; what was placed on the market before that date has until ``deadline``."""

    if placed_on is None:
        # Placing date unknown: the cut-off date, with the transition as a condition.
        return cut_off, note
    if before(placed_on, cut_off):
        return deadline, note
    return cut_off, None


def _literal_reading_note(location: str, deferred_date: str) -> str:
    return (
        "Literal reading, confirm with counsel: Art. 113, third paragraph, point (c) AIA "
        f"defers only Chapter III, Sections 1, 2 and 3, so this {location} duty applies "
        f"from {GENERAL_APPLICATION_DATE} (Art. 113, second paragraph). If it is read as "
        f"following that deferral, {deferred_date} applies."
    )


_ANNEX_III_POINT_1 = {
    AnnexIII.BIOMETRICS_REMOTE_ID,
    AnnexIII.BIOMETRICS_CATEGORISATION,
    AnnexIII.BIOMETRICS_EMOTION,
}


def _internal_control_route(profile: SystemProfile) -> bool:
    """Whether Art. 43(2) AIA fixes internal control (Annex VI) as the route.

    Art. 43(2) covers Annex III points 2 to 8. Point 1 (biometrics) can involve a
    notified body under Art. 43(1), an unsettled Annex III point could be point 1,
    and an Annex III system that is also an Annex I product follows the Annex I
    procedure (Art. 43(3), last subparagraph), whether or not that procedure
    involves a third party. Those cases keep the review_required Art. 44 item.
    """
    area = profile.annex_iii_area
    if area is None or area is AnnexIII.UNSURE or area in _ANNEX_III_POINT_1:
        return False
    return not profile.annex_i_safety_component
