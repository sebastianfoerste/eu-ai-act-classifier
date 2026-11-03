"""Structured obligation graph for product and review workflows.

``report.obligations`` and ``report.obligation_graph`` come from the same
:class:`.catalog.Duty` entries. :func:`build_obligations` decides which duties a profile
gets, dates each graph item, sets its review status and lists the same duties, in the
same order, as obligations. The Art. 50 items are the exception: the graph lists them,
and ``report.transparency_obligations`` holds them instead of ``report.obligations``.
"""

from __future__ import annotations

from typing import NamedTuple

from .catalog import (
    ART_50_2,
    AUTHORISED_REPRESENTATIVE,
    DISTRIBUTOR,
    FRIA,
    GPAI_DUTIES,
    GPAI_SYSTEMIC_DUTIES,
    HIGH_RISK_PROVIDER_CHAPTER_IX_DUTIES,
    HIGH_RISK_PROVIDER_DUTIES,
    HIGH_RISK_PROVIDER_SECTION_5_DUTIES,
    IMPORTER,
    PROVIDER_NATIONAL_REGISTRATION,
    VALUE_CHAIN,
    Duty,
    deployer_duty,
    deployer_national_registration_duty,
    derogation_registration_duty,
    eu_database_registration_applies,
    legacy_system_duty,
    national_registration_for_public_authority_deployer,
    provider_registration_duty,
    public_authority_registration_applies,
    public_authority_registration_duty,
    section_b_annex_iii_flag,
    section_b_duty,
    section_b_kept_flag,
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
_TRANSPARENCY_TRIGGER = "Art. 50 transparency trigger in the submitted profile."
_TRANSPARENCY_EVIDENCE = "Transparency notice, label or disclosure record."


class _Entry(NamedTuple):
    """A duty and its graph item: the duty gives the obligation, the item the graph."""

    duty: Duty
    item: ObligationGraphItem


def build_obligations(
    *,
    profile: SystemProfile,
    final_tier: RiskTier,
    is_gpai: bool,
    gpai_systemic: bool,
    fria_required: bool,
    transparency_obligations: list[Obligation],
) -> tuple[list[Obligation], list[ObligationGraphItem]]:
    """``report.obligations`` and ``report.obligation_graph`` from the same duties."""

    entries: list[_Entry] = []

    if final_tier is RiskTier.HIGH and section_b_only(profile):
        # Art. 2(2) AIA: none of the Chapter III duties below, only the listed provisions.
        entries.extend(_section_b_items(profile))
    elif final_tier is RiskTier.HIGH:
        # A high-risk tier always has a route, so the fallback only satisfies the type.
        application_date = chapter_iii_date(profile) or POINT_C_ANNEX_III
        if profile.is_provider:
            entries.extend(_high_risk_provider_graph(application_date, profile))
        if profile.is_deployer:
            public_authority_registration = public_authority_registration_applies(
                profile.annex_iii_area,
                profile.deployer_public_authority,
                profile.public_authority_use,
            )
            # Art. 26(8), second sentence, is a Section 3 duty: the Art. 26 date, not the
            # Art. 49(3) one.
            entries.append(
                _item(
                    deployer_duty(public_authority_registration=public_authority_registration),
                    application_date,
                )
            )
            if fria_required:
                entries.append(_item(FRIA, application_date))
            if public_authority_registration:
                # Like Art. 49(1), Chapter III, Section 5, so the literal date and the
                # point (c)(i) alternative.
                duty = public_authority_registration_duty(
                    profile.annex_iii_area,
                    profile.deployer_public_authority,
                    profile.public_authority_use,
                )
                entries.append(_undeferred_item(duty, _SECTION_5, POINT_C_ANNEX_III))
            elif national_registration_for_public_authority_deployer(
                profile.annex_iii_area,
                profile.deployer_public_authority,
                profile.public_authority_use,
            ):
                duty = deployer_national_registration_duty(profile.deployer_public_authority)
                entries.append(_undeferred_item(duty, _SECTION_5, POINT_C_ANNEX_III))
        if profile.is_importer:
            entries.append(_item(IMPORTER, application_date))
        if profile.is_distributor:
            entries.append(_item(DISTRIBUTOR, application_date))
        if profile.is_authorized_representative or profile.provider_established_outside_eu:
            entries.append(_item(AUTHORISED_REPRESENTATIVE, application_date))
        if profile.substantially_modifies_system or profile.puts_name_or_trademark_on_system:
            entries.append(_item(VALUE_CHAIN, application_date))
        entries = _with_legacy_notes(entries, profile, application_date)
        entries.extend(_art_111_2_items(profile, application_date))
        if section_b_product(profile):
            # Also in an Annex III area: the Annex III duties above stay, flagged here.
            entries.extend(_section_b_items(profile))

    if is_gpai and final_tier is not RiskTier.PROHIBITED:
        entries.extend(_gpai_graph(gpai_systemic, profile))

    obligations = [entry.duty.obligation() for entry in entries]
    graph = [entry.item for entry in entries]
    graph += _transparency_items(profile, final_tier, transparency_obligations)
    return obligations, graph


def _transparency_items(
    profile: SystemProfile, final_tier: RiskTier, transparency_obligations: list[Obligation]
) -> list[ObligationGraphItem]:
    """The Art. 50 items, from the obligations ``rules/transparency.py`` lists."""

    legacy_flag = legacy_transparency_flag(profile) if final_tier is RiskTier.HIGH else None
    items = []
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
        duty = Duty(
            obligation_id=f"transparency.{index}",
            article=obligation.article,
            actor=obligation.applies_to,
            title=obligation.title,
            requirement=obligation.requirement,
            trigger=_TRANSPARENCY_TRIGGER,
            evidence_artifact=_TRANSPARENCY_EVIDENCE,
        )
        # A counsel flag sends the item to review, like every other flagged item.
        items.append(_item(duty, applies_from, review=flagged, note=note).item)
    return items


def _high_risk_provider_graph(application_date: str, profile: SystemProfile) -> list[_Entry]:
    return [
        *(_item(duty, application_date) for duty in HIGH_RISK_PROVIDER_DUTIES),
        # Chapter III, Section 5 (Arts. 40-49) and Chapter IX (Arts. 72-73) are not in
        # the Art. 113, third paragraph, point (c) deferral. Read literally they apply
        # from the general date; whether they follow Sections 1 to 3 is contested, so
        # each item carries the deferred alternative and goes to review.
        *(
            _undeferred_item(duty, _SECTION_5, application_date)
            for duty in HIGH_RISK_PROVIDER_SECTION_5_DUTIES
        ),
        *_registration_items(profile),
        *(
            _undeferred_item(duty, _CHAPTER_IX, application_date)
            for duty in HIGH_RISK_PROVIDER_CHAPTER_IX_DUTIES
        ),
    ]


def _registration_items(profile: SystemProfile) -> list[_Entry]:
    """Art. 49 AIA registration. Every item here needs an Annex III area, so the
    deferred alternative is the point (c)(i) date."""

    annex_iii_area = profile.annex_iii_area
    items: list[_Entry] = []
    if eu_database_registration_applies(annex_iii_area):
        duty = provider_registration_duty(annex_iii_area)
        items.append(_undeferred_item(duty, _SECTION_5, POINT_C_ANNEX_III))
    elif annex_iii_area is AnnexIII.CRITICAL_INFRASTRUCTURE:
        items.append(
            _undeferred_item(PROVIDER_NATIONAL_REGISTRATION, _SECTION_5, POINT_C_ANNEX_III)
        )
    derogation = profile.derogation
    if (
        annex_iii_area is not None
        and derogation.any_condition
        and not derogation.performs_profiling
    ):
        # Art. 49(2) has no point 2 exception: a provider relying on Art. 6(3) registers
        # in the EU database whatever the Annex III point.
        duty = derogation_registration_duty(annex_iii_area)
        items.append(_undeferred_item(duty, _SECTION_5, POINT_C_ANNEX_III))
    return items


def _art_111_2_items(profile: SystemProfile, cut_off: str) -> list[_Entry]:
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
    trigger = f"High-risk AI system {describe_dates(legacy)}, before {cut_off}."
    items = []
    for actor in operator_roles(profile):
        actor_requirement, actor_note, application_date = requirement, note, cut_off
        if deadline and actor in _PROVIDER_OR_DEPLOYER:
            # Also in the note, which the text report and the dossier print.
            actor_requirement, actor_note = f"{requirement} {deadline}", f"{note} {deadline}"
            if profile.public_authority_use and change is not True:
                application_date = ART_111_2_PUBLIC_AUTHORITY_DEADLINE
        duty = legacy_system_duty(actor, trigger, actor_requirement)
        items.append(_item(duty, application_date, note=actor_note))
    return items


def _with_legacy_notes(entries: list[_Entry], profile: SystemProfile, cut_off: str) -> list[_Entry]:
    """Under Art. 111(2) AIA an unchanged legacy system is outside the Regulation (Art. 5
    apart) until its design changes, so its Chapter III dates are conditional; each item
    says so next to any note it already has. The condition rests on the contested
    Chapter III date (the legacy status, or the date from which a change counts), so the
    note carries the flag and the item goes to review."""

    legacy = legacy_dates(profile, cut_off)
    if not legacy or profile.significant_change_after_application_date is True:
        return entries
    # Also for an item dated 2026-08-02 (Section 5, Chapter IX): the duty does not bind
    # the unchanged system from that date either.
    condition = (
        f"Art. 111(2) AIA: the system was {describe_dates(legacy)}, before {cut_off}. "
        "Whatever date this item gives, the duty attaches only once the system's design "
        f"changes significantly as from {cut_off}"
    )
    flag = legacy_note_flag(profile, cut_off)
    out = []
    for duty, item in entries:
        text = condition
        # Art. 111(2), second sentence, binds providers and deployers only.
        if item.actor in _PROVIDER_OR_DEPLOYER:
            text += public_authority_clause(profile)
        text += f". {flag}"
        noted = item.model_copy(
            update={
                "application_date_note": (
                    f"{item.application_date_note} {text}" if item.application_date_note else text
                ),
                "review_status": ReviewStatus.REVIEW_REQUIRED,
            }
        )
        out.append(_Entry(duty, noted))
    return out


def _section_b_items(profile: SystemProfile) -> list[_Entry]:
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
    return [
        _item(section_b_duty(actor, annex_iii=annex_iii), POINT_C_ANNEX_I, note=note)
        for actor in operators(profile, (Role.PROVIDER,))
    ]


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


def _gpai_graph(systemic: bool, profile: SystemProfile) -> list[_Entry]:
    application_date, note, fallback = _gpai_dating(profile)
    duties = GPAI_DUTIES + (GPAI_SYSTEMIC_DUTIES if systemic else ())
    # Every Chapter V item takes the same date and Art. 111(3) AIA note (_art_111_dating).
    # The fallback date is not the model's own: nothing dated by it is determined.
    return [_item(duty, application_date, review=fallback, note=note) for duty in duties]


def _item(
    duty: Duty,
    application_date: str,
    *,
    review: bool = False,
    note: str | None = None,
) -> _Entry:
    """The graph item for ``duty``: review_required where the duty or ``review`` says so."""

    review_status = (
        ReviewStatus.REVIEW_REQUIRED if duty.review_required or review else ReviewStatus.DETERMINED
    )
    item = ObligationGraphItem(
        obligation_id=duty.obligation_id,
        article=duty.article,
        actor=duty.actor,
        trigger=duty.trigger,
        requirement=duty.requirement,
        evidence_artifact=duty.evidence_artifact,
        source_status=SourceStatus.BINDING_LEVEL_1,
        source_url=AI_ACT_URL,
        application_date=application_date,
        review_status=review_status,
        application_date_note=note,
    )
    return _Entry(duty, item)


def _undeferred_item(duty: Duty, location: str, deferred_date: str) -> _Entry:
    """A duty outside the point (c) deferral: the literal general date, the deferred
    alternative in the note, and review."""

    return _item(
        duty,
        GENERAL_APPLICATION_DATE,
        review=True,
        note=_literal_reading_note(location, deferred_date),
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
