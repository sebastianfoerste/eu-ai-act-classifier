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
# Art. 111(2), second sentence, in its own words: what providers and deployers of
# high-risk systems intended to be used by public authorities do "in any case".
PUBLIC_AUTHORITY_DUTY = (
    "take the necessary steps to comply with the requirements and obligations laid down in "
    f"this Regulation by {DEADLINE_2030}"
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
    """The operator roles the profile holds (a GPAI model provider is not an operator of
    the system)."""

    return [role for role in profile.roles if role is not Role.GPAI_PROVIDER]


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


def cut_off_contested(profile: SystemProfile, cut_off: str) -> bool:
    """Whether the Art. 111(2) result turns on which Chapter III date is meant.

    Art. 113 AIA gives Chapter III no single date. Read as the point (c) date the
    system is a legacy system; read as the general date (when Section 5 applies
    on the literal reading) it is not, if its earliest date falls in between.
    """

    earliest = min((value for _label, value in market_dates(profile)), default=None)
    if earliest is None:
        return False
    return not before(earliest, GENERAL_APPLICATION_DATE) and before(earliest, cut_off)


def legacy_note_flag(cut_off: str) -> str:
    """The short form of ``cut_off_flag`` for a note that rests on the contested cut-off."""

    return (
        f"Literal reading, confirm with counsel: this uses {cut_off} as the Art. 111(2) AIA "
        f"cut-off. If the general date of {GENERAL_APPLICATION_DATE} is meant, the system is "
        "not a legacy system and the condition does not apply (see the Art. 111(2) item)."
    )


def cut_off_flag(cut_off: str) -> str:
    return (
        'Literal reading, confirm with counsel: Art. 111(2) AIA refers to "the date of '
        'application of Chapter III referred to in Article 113", and Art. 113 gives '
        "Chapter III no single date (Section 4, from 2 August 2025, concerns notifying "
        f"authorities and notified bodies). This uses {cut_off}, when Chapter III, Sections 1 to "
        f"3 apply to this system (Art. 113, third paragraph, {chapter_iii_point(cut_off)}). "
        f"If the general date of {GENERAL_APPLICATION_DATE} is meant, a system first placed "
        "on the market or put into service on or after that date is not a legacy system."
    )
