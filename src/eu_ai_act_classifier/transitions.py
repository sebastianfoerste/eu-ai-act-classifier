"""Art. 111(2) AIA: the Chapter III date a high-risk system is compared with.

The scope gate's transitional status and the obligation graph both read these
helpers, so the text and the graph items cannot disagree about which date a
system was placed on the market or put into service before.
"""

from __future__ import annotations

from datetime import date

from .citations import (
    ART_111_2_PUBLIC_AUTHORITY_DEADLINE,
    GENERAL_APPLICATION_DATE,
    POINT_C_ANNEX_I,
    POINT_C_ANNEX_III,
    long_date,
)
from .models import AnnexISection, Role, SystemProfile

DEADLINE_2030 = long_date(ART_111_2_PUBLIC_AUTHORITY_DEADLINE)  # "2 August 2030"
# Art. 111(2), second sentence: what providers and deployers of high-risk systems intended
# to be used by public authorities do "in any case", whatever their design changes.
PUBLIC_AUTHORITY_DUTY = (
    "in any case take the necessary steps to comply with the requirements and obligations "
    f"laid down in this Regulation by {DEADLINE_2030}"
)
# Art. 111(1) AIA, the carve-out Art. 111(2) excludes.
ANNEX_X_CARVE_OUT = (
    "components of the Annex X large-scale IT systems placed on the market or put into "
    "service before 2 August 2027, which are brought into compliance by 31 December 2030 "
    "(Art. 111(1) AIA)"
)


def annex_i_route(profile: SystemProfile) -> bool:
    """Art. 6(1) AIA: an Annex I product or safety component that needs third-party
    conformity assessment."""

    return profile.annex_i_safety_component and profile.annex_i_third_party_assessment


def section_b_product(profile: SystemProfile) -> bool:
    """An Art. 6(1) high-risk system for a product listed in Annex I, Section B."""

    return annex_i_route(profile) and profile.annex_i_section is AnnexISection.SECTION_B


def section_b_only(profile: SystemProfile) -> bool:
    """A Section B product with no Annex III area: Art. 2(2) AIA leaves only Art. 6(1),
    Art. 60a and Arts. 102 to 112, so no Chapter III duty attaches."""

    return section_b_product(profile) and profile.annex_iii_area is None


def operator_roles(profile: SystemProfile) -> list[Role]:
    """The operator roles the profile holds, each once (a GPAI model provider is not an
    operator of the system). Graph item ids are built from them, so a repeated role must
    not repeat an id."""

    return list(dict.fromkeys(role for role in profile.roles if role is not Role.GPAI_PROVIDER))


def operators(profile: SystemProfile, preferred: tuple[Role, ...]) -> list[Role]:
    """The ``preferred`` roles the profile holds, else its first other operator role;
    empty when it holds none."""

    held = operator_roles(profile)
    return [role for role in held if role in preferred] or held[:1]


def derogation_asserted(profile: SystemProfile) -> bool:
    """An Art. 6(3) AIA derogation condition is asserted for an Annex III area and no
    profiling is performed, so the Annex III route may fall away on review."""

    derogation = profile.derogation
    return (
        profile.annex_iii_area is not None
        and derogation.any_condition
        and not derogation.performs_profiling
    )


def chapter_iii_date(profile: SystemProfile) -> str | None:
    """Art. 113, third paragraph, point (c) AIA date for Chapter III, Sections 1 to 3, or
    None where no high-risk route is screened or only Art. 2(2) applies."""

    if profile.annex_iii_area is not None:
        # Point (c)(i), also for a system that is an Annex I product too: it is still
        # "classified as high-risk pursuant to Article 6(2) and Annex III".
        return POINT_C_ANNEX_III
    if annex_i_route(profile) and not section_b_only(profile):
        return POINT_C_ANNEX_I  # point (c)(ii): Art. 6(1) and Annex I only
    return None


def derogation_chapter_iii_date(profile: SystemProfile) -> str | None:
    """The point (c)(ii) date for an Annex I (not Section B) product also in an Annex III
    area with an asserted Art. 6(3) derogation: if the derogation is established, only
    Art. 6(1) and Annex I classify it. None where that cannot happen."""

    if derogation_asserted(profile) and annex_i_route(profile) and not section_b_product(profile):
        return POINT_C_ANNEX_I
    return None


def chapter_iii_point(cut_off: str) -> str:
    return "point (c)(i)" if cut_off == POINT_C_ANNEX_III else "point (c)(ii)"


def market_dates(profile: SystemProfile) -> list[tuple[str, str]]:
    """The AI system's given dates as (verb phrase, ISO date) pairs."""

    dates = [
        ("placed on the market", profile.placing_on_market_date),
        ("put into service", profile.putting_into_service_date),
    ]
    return [(label, value) for label, value in dates if value is not None]


def describe_dates(dates: list[tuple[str, str]]) -> str:
    return " and ".join(f"{label} on {value}" for label, value in dates)


def before(value: str, cut_off: str) -> bool:
    """Whether ``value`` is before ``cut_off``; "before" excludes the cut-off date."""

    return date.fromisoformat(value) < date.fromisoformat(cut_off)


def legacy_dates(profile: SystemProfile, cut_off: str) -> list[tuple[str, str]]:
    """Given dates before ``cut_off``. Art. 111(2) AIA covers a system "placed on the
    market or put into service before" the Chapter III date, so either date counts."""

    return [(label, value) for label, value in market_dates(profile) if before(value, cut_off)]


def change_used(profile: SystemProfile) -> bool:
    """Whether ``significant_change_after_application_date`` can change the result: only
    for a high-risk system, with no prohibited practice screened, placed on the market or
    put into service before its Chapter III date (Art. 111(2) AIA)."""

    cut_off = chapter_iii_date(profile)
    return (
        not profile.prohibited_practices
        and cut_off is not None
        and bool(legacy_dates(profile, cut_off))
    )


def gpai_model_date(profile: SystemProfile) -> tuple[str | None, bool]:
    """The date Art. 111(3) AIA dates a general-purpose AI model by, and whether it is the
    AI system's placing_on_market_date standing in for the model's own date."""

    if profile.gpai_model_placing_on_market_date is not None:
        return profile.gpai_model_placing_on_market_date, False
    return profile.placing_on_market_date, profile.placing_on_market_date is not None


def cut_off_contested(profile: SystemProfile, cut_off: str) -> bool:
    """Whether the system's legacy status turns on which Chapter III date is meant.

    Art. 113 AIA gives Chapter III no single date. Read as the point (c) date the
    system is a legacy system; read as the general date (when Section 5 applies
    on the literal reading) it is not, if its earliest date falls in between.
    """

    earliest = min(
        (value for _label, value in market_dates(profile)), key=date.fromisoformat, default=None
    )
    if earliest is None:
        return False
    return not before(earliest, GENERAL_APPLICATION_DATE) and before(earliest, cut_off)


def public_authority_status_used(profile: SystemProfile) -> bool:
    """Whether ``deployer_public_authority`` can change the result. It describes the
    profile's own deployer role, so only where the profile holds that role for a high-risk
    system with no prohibited practice screened (Art. 49(3) and Art. 111(2) AIA)."""

    return (
        profile.is_deployer
        and not profile.prohibited_practices
        and (profile.annex_iii_area is not None or annex_i_route(profile))
    )


def public_authority_deployer(profile: SystemProfile) -> bool:
    """A public-authority deployer is asserted for the profile's own deployer role. For
    an operator that is not the deployer, whether the system is intended to be used by
    public authorities is its public_authority_use answer alone."""

    return profile.is_deployer and profile.deployer_public_authority is True


def public_authority_sentence(profile: SystemProfile) -> str:
    """Art. 111(2), second sentence, which applies "in any case", so also after an
    asserted change. It turns on intended use; a public-authority deployer is evidence
    of that use, for the reviewer to confirm. Starts with a space where not empty."""

    if profile.public_authority_use:
        return (
            " As the system is intended to be used by public authorities, its providers and "
            f"deployers {PUBLIC_AUTHORITY_DUTY}."
        )
    if public_authority_deployer(profile):
        return (
            " A public-authority deployer is asserted: confirm whether the system is intended "
            "to be used by public authorities. If it is, its providers and deployers "
            f"{PUBLIC_AUTHORITY_DUTY}."
        )
    return ""


def undated_public_authority_sentence(profile: SystemProfile) -> str:
    """``public_authority_sentence`` for a system with no given date: the second sentence
    of Art. 111(2) binds only a system placed on the market or put into service before
    its Chapter III date ("that date"), which the profile does not show."""

    before_that_date = "placed on the market or put into service before that date"
    if profile.public_authority_use:
        return (
            " As the system is intended to be used by public authorities, if it was "
            f"{before_that_date}, its providers and deployers {PUBLIC_AUTHORITY_DUTY}."
        )
    if public_authority_deployer(profile):
        return (
            " A public-authority deployer is asserted: confirm whether the system is intended "
            f"to be used by public authorities. If it is and was {before_that_date}, its "
            f"providers and deployers {PUBLIC_AUTHORITY_DUTY}."
        )
    return ""


def public_authority_clause(profile: SystemProfile) -> str:
    """The same deadline as a clause after "attaches only once its design changes
    significantly", for an item of a provider or deployer."""

    if profile.public_authority_use:
        return (
            f", and by {DEADLINE_2030} in any case, as the system is intended to be used by "
            "public authorities"
        )
    if public_authority_deployer(profile):
        return (
            f", and by {DEADLINE_2030} in any case if, as the public-authority deployer "
            "suggests, the system is intended to be used by public authorities"
        )
    return ""


def _see_item(profile: SystemProfile) -> str:
    # One Art. 111(2) item per operator role: point to it only where there is one.
    return " (see the Art. 111(2) item)" if operator_roles(profile) else ""


def legacy_note_flag(profile: SystemProfile, cut_off: str) -> str:
    """The short form of ``cut_off_flag`` for a note or question that rests on the
    contested date: the system's legacy status or, for an earlier system, the date from
    which a significant change in design counts."""

    if cut_off_contested(profile, cut_off):
        effect = "the system is not a legacy system and the condition does not apply"
    else:
        effect = "a significant change in design made on or after that date already counts"
    return (
        f"Literal reading, confirm with counsel: this uses {cut_off} as the Art. 111(2) AIA "
        f"cut-off. If the general date of {GENERAL_APPLICATION_DATE} is meant, {effect}"
        f"{_see_item(profile)}."
    )


def cut_off_flag(profile: SystemProfile, cut_off: str) -> str:
    """Art. 111(2) AIA uses one date twice: the system must have been placed on the market
    or put into service "before" it, and a significant change counts "as from" it. Which
    date is meant is contested, so every legacy result and every undated check is
    flagged."""

    not_legacy = (
        "a system first placed on the market or put into service on or after that date is "
        "not a legacy system"
    )
    window = "a significant change in design made on or after that date already counts"
    if not market_dates(profile):
        effect = f"{not_legacy}, and for an earlier system {window}"
    elif cut_off_contested(profile, cut_off):
        effect = not_legacy
    else:
        effect = window
    if profile.significant_change_after_application_date is True and change_used(profile):
        # The asserted change is not dated: say which changes count on each reading.
        effect += (
            f". On the date used here, the asserted change counts only if it was made on or "
            f"after {cut_off}"
        )
    return (
        'Literal reading, confirm with counsel: Art. 111(2) AIA refers to "the date of '
        'application of Chapter III referred to in Article 113", and Art. 113 gives '
        "Chapter III no single date (Section 4, from 2 August 2025, concerns notifying "
        f"authorities and notified bodies). This uses {cut_off}, when Chapter III, Sections 1 to "
        f"3 apply to this system (Art. 113, third paragraph, {chapter_iii_point(cut_off)}), "
        "both as the date the system must precede and as the date from which a significant "
        f'change in design counts ("as from that date"). If the general date of '
        f"{GENERAL_APPLICATION_DATE} is meant, {effect}."
    )


def legacy_transparency_flag(profile: SystemProfile) -> str | None:
    """Art. 111(2) AIA applies "this Regulation", not only Chapter III, to a legacy
    high-risk system only after a significant change in design, so on its wording that
    reaches Art. 50 too. The report keeps the Art. 50 dating as the conservative reading.
    For a high-risk system only; the caller checks the tier."""

    if section_b_only(profile) or profile.significant_change_after_application_date is True:
        return None
    cut_off = chapter_iii_date(profile)
    legacy = legacy_dates(profile, cut_off) if cut_off else []
    if not legacy:
        return None
    return (
        "Literal reading, confirm with counsel: Art. 111(2) AIA applies this Regulation to a "
        f"high-risk system {describe_dates(legacy)}, before {cut_off}, only if its design "
        "changes significantly as from that date, so on its wording Art. 50 would apply to it "
        "only then. This report keeps the Art. 50 dating as the conservative reading."
        f"{public_authority_sentence(profile)} Which date Art. 111(2) means is itself "
        f"contested{_see_item(profile)}."
    )


def derogation_note(profile: SystemProfile, cut_off: str) -> str:
    """For a legacy check that an asserted Art. 6(3) derogation would change: with the
    derogation established the point (c)(ii) date applies instead. Empty otherwise."""

    alternative = derogation_chapter_iii_date(profile)
    alternative_legacy = legacy_dates(profile, alternative) if alternative else []
    if not alternative_legacy:
        return ""
    lead = (
        "If the asserted Art. 6(3) derogation is established, only Art. 6(1) and Annex I "
        f"classify the system, so its Chapter III date is {alternative} (Art. 113, third "
        f"paragraph, {chapter_iii_point(alternative)} AIA)"
    )
    if legacy_dates(profile, cut_off):
        return f"{lead} instead."
    # Only the later point (c)(ii) date makes it a legacy system; on the general date it
    # is none on either route.
    return (
        f"{lead}: it was {describe_dates(alternative_legacy)}, before that date, so the "
        "Art. 111(2) transition would apply to it. Literal reading, confirm with counsel: "
        f"this uses {alternative} as the Art. 111(2) AIA cut-off. If the general date of "
        f"{GENERAL_APPLICATION_DATE} is meant, the system is not a legacy system on either "
        "route."
    )
