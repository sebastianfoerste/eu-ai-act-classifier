"""Display labels for the enum values the profile and report use.

One catalog for every surface: the playground field guide and guided intake,
and the web cockpit, read these labels from files that
``scripts/build_playground.py`` generates. Annex III and Art. 5 labels come
from :mod:`.catalog`, so a label always names the point the engine cites.

Labels are English only. No label adds a citation the catalog does not already
carry.
"""

from __future__ import annotations

from enum import StrEnum

from .artifacts import ARTIFACT_NAMES
from .catalog import ANNEX_III, PROHIBITED
from .evidence_tracker import EVIDENCE_STATES, LANES, STALE_REASONS
from .models import (
    AnnexIII,
    AnnexILegislation,
    AnnexISection,
    Derogation,
    Disposition,
    ExcludedUse,
    ProhibitedPractice,
    ReviewStatus,
    RiskTier,
    Role,
    ScopeStatus,
    SourceStatus,
)

LOCALE = "en"

ROLE_LABELS: dict[Role, str] = {
    Role.PROVIDER: "Provider",
    Role.DEPLOYER: "Deployer",
    Role.IMPORTER: "Importer",
    Role.DISTRIBUTOR: "Distributor",
    Role.AUTHORIZED_REPRESENTATIVE: "Authorised representative",
    Role.GPAI_PROVIDER: "GPAI model provider",
}

# The same wording the cockpit's Annex I section select uses.
ANNEX_I_SECTION_LABELS: dict[AnnexISection, str] = {
    AnnexISection.SECTION_A: "Section A",
    AnnexISection.SECTION_B: "Section B",
}
# Annex I AIA as amended by Regulation (EU) 2026/1744, Art. 1, point (41), read in
# sources/oj/32024R1689.en.xhtml and sources/oj/32026R1744.en.xhtml.
_ANNEX_I_ACTS: dict[AnnexILegislation, str] = {
    AnnexILegislation.TOYS: "Directive 2009/48/EC (toys)",
    AnnexILegislation.RECREATIONAL_CRAFT: (
        "Directive 2013/53/EU (recreational craft and personal watercraft)"
    ),
    AnnexILegislation.LIFTS: "Directive 2014/33/EU (lifts)",
    AnnexILegislation.EXPLOSIVE_ATMOSPHERES_EQUIPMENT: (
        "Directive 2014/34/EU (equipment for potentially explosive atmospheres)"
    ),
    AnnexILegislation.RADIO_EQUIPMENT: "Directive 2014/53/EU (radio equipment)",
    AnnexILegislation.PRESSURE_EQUIPMENT: "Directive 2014/68/EU (pressure equipment)",
    AnnexILegislation.CABLEWAY_INSTALLATIONS: "Regulation (EU) 2016/424 (cableway installations)",
    AnnexILegislation.PERSONAL_PROTECTIVE_EQUIPMENT: (
        "Regulation (EU) 2016/425 (personal protective equipment)"
    ),
    AnnexILegislation.GAS_APPLIANCES: "Regulation (EU) 2016/426 (appliances burning gaseous fuels)",
    AnnexILegislation.MEDICAL_DEVICES: "Regulation (EU) 2017/745 (medical devices)",
    AnnexILegislation.IN_VITRO_DIAGNOSTIC_DEVICES: (
        "Regulation (EU) 2017/746 (in vitro diagnostic medical devices)"
    ),
    AnnexILegislation.CIVIL_AVIATION_SECURITY: (
        "Regulation (EC) No 300/2008 (civil aviation security)"
    ),
    AnnexILegislation.TWO_OR_THREE_WHEEL_VEHICLES: (
        "Regulation (EU) No 168/2013 (two- or three-wheel vehicles and quadricycles)"
    ),
    AnnexILegislation.AGRICULTURAL_AND_FORESTRY_VEHICLES: (
        "Regulation (EU) No 167/2013 (agricultural and forestry vehicles)"
    ),
    AnnexILegislation.MARINE_EQUIPMENT: "Directive 2014/90/EU (marine equipment)",
    AnnexILegislation.RAIL_SYSTEM_INTEROPERABILITY: (
        "Directive (EU) 2016/797 (interoperability of the rail system)"
    ),
    AnnexILegislation.MOTOR_VEHICLES_TYPE_APPROVAL: (
        "Regulation (EU) 2018/858 (motor vehicles and their trailers)"
    ),
    AnnexILegislation.MOTOR_VEHICLES_GENERAL_SAFETY: (
        "Regulation (EU) 2019/2144 (motor vehicle general safety)"
    ),
    AnnexILegislation.UNMANNED_AIRCRAFT: (
        "Regulation (EU) 2018/1139 (civil aviation, as regards unmanned aircraft)"
    ),
    AnnexILegislation.MACHINERY: "Regulation (EU) 2023/1230 (machinery)",
}
ANNEX_I_LEGISLATION_LABELS: dict[AnnexILegislation, str] = {
    act: f"Section {act.section.value}, point {act.value.rsplit('.', 1)[1]}: {title}"
    for act, title in _ANNEX_I_ACTS.items()
}

EXCLUDED_USE_LABELS: dict[ExcludedUse, str] = {
    ExcludedUse.MILITARY_DEFENCE_NATIONAL_SECURITY: "Military, defence or national security",
    ExcludedUse.RESEARCH_DEVELOPMENT_TESTING: "Research, development or testing",
    ExcludedUse.PERSONAL_NON_PROFESSIONAL: "Personal, non-professional use",
    ExcludedUse.FREE_OPEN_SOURCE: "Free and open-source licence",
}

RISK_TIER_LABELS: dict[RiskTier, str] = {
    RiskTier.PROHIBITED: "Prohibited",
    RiskTier.HIGH: "High-risk",
    RiskTier.LIMITED: "Limited risk",
    RiskTier.MINIMAL: "Minimal risk",
    RiskTier.OUT_OF_SCOPE: "Outside AI Act scope",
}

DISPOSITION_LABELS: dict[Disposition, str] = {
    Disposition.DETERMINED: "Determined",
    Disposition.REQUIRES_REVIEW: "Requires review",
}

REVIEW_STATUS_LABELS: dict[ReviewStatus, str] = {
    ReviewStatus.DRAFT: "Draft",
    ReviewStatus.REVIEW_REQUIRED: "Review required",
    ReviewStatus.DETERMINED: "Determined",
}

SOURCE_STATUS_LABELS: dict[SourceStatus, str] = {
    SourceStatus.BINDING_LEVEL_1: "Binding",
    SourceStatus.PROVISIONAL_POLITICAL_AGREEMENT: "Provisional",
    SourceStatus.NONBINDING_GUIDANCE: "Nonbinding guidance",
}

SCOPE_STATUS_LABELS: dict[ScopeStatus, str] = {
    ScopeStatus.IN_SCOPE: "In scope",
    ScopeStatus.OUTSIDE_SCOPE: "Outside AI Act scope",
    ScopeStatus.REQUIRES_REVIEW: "Scope requires review",
}

DEROGATION_LABELS: dict[str, str] = {
    "narrow_procedural_task": "Performs a narrow procedural task",
    "improves_prior_human_activity": "Improves the result of a completed human activity",
    "detects_patterns_without_replacing_human": (
        "Detects decision patterns without replacing human assessment"
    ),
    "preparatory_task": "Performs a preparatory task to an assessment",
    "performs_profiling": "Performs profiling of natural persons",
}

ARTIFACT_LABELS: dict[str, str] = {
    "art-6-4-assessment": "Art. 6(4) non-high-risk assessment",
    "fria": "Fundamental rights impact assessment (Art. 27)",
    "annex-iv-checklist": "Annex IV technical documentation checklist",
    "post-market-monitoring-plan": "Post-market monitoring plan",
    "serious-incident-register": "Serious-incident register",
    "gpai-model-documentation": "GPAI model documentation checklist",
    "training-content-summary": "Training-content summary checklist",
}

# The cockpit's obligation tracker (ADR 0006): evidence states, lanes and the reasons a
# saved record has gone stale.
EVIDENCE_STATE_LABELS: dict[str, str] = {
    "not_started": "Not started",
    "in_progress": "In progress",
    "evidence_attached": "Evidence attached",
    "reviewed": "Reviewed",
    "stale": "Stale",
}

EVIDENCE_LANE_LABELS: dict[str, str] = {
    "applies_now": "Applies on the assessment date",
    "upcoming": "Applies after the assessment date",
    "no_assessment_date": "Dated; no assessment date set",
    "contested_or_open": "Contested or open",
}

EVIDENCE_STALE_REASON_LABELS: dict[str, str] = {
    "report_changed": "Report changed since saved",
    "item_changed": "This obligation changed since saved",
    "reviewed_before_source_retrieval": "Reviewed before the source was retrieved",
}


def _short(ref: str) -> str:
    return ref.removesuffix(" AIA")


def annex_iii_label(area: AnnexIII) -> str:
    """``III.5.b`` -> ``Annex III(5)(b): Creditworthiness evaluation and credit scoring
    of natural persons``."""

    citation, title = ANNEX_III[area]
    if area is AnnexIII.UNSURE:
        return f"Annex III, point unsettled: {title}"
    return f"{_short(citation.ref)}: {title}"


def prohibited_label(practice: ProhibitedPractice) -> str:
    """``5.1.c`` -> ``Art. 5(1)(c): Social scoring ...``."""

    citation, title = PROHIBITED[practice]
    return f"{_short(citation.ref)}: {title}"


def option_label(member: StrEnum) -> str:
    """The display label for any enum value a profile field accepts."""

    if isinstance(member, AnnexIII):
        return annex_iii_label(member)
    if isinstance(member, ProhibitedPractice):
        return prohibited_label(member)
    if isinstance(member, Role):
        return ROLE_LABELS[member]
    if isinstance(member, ExcludedUse):
        return EXCLUDED_USE_LABELS[member]
    if isinstance(member, AnnexISection):
        return ANNEX_I_SECTION_LABELS[member]
    if isinstance(member, AnnexILegislation):
        return ANNEX_I_LEGISLATION_LABELS[member]
    raise KeyError(f"no label for {member!r}")


def _values(labels: dict) -> dict[str, str]:
    return {str(key): value for key, value in labels.items()}


def label_catalog() -> dict:
    """Every label, keyed by namespace and then by the value the JSON carries."""

    if set(DEROGATION_LABELS) != set(Derogation.model_fields):
        raise ValueError("DEROGATION_LABELS must cover every Derogation field")
    if set(ARTIFACT_LABELS) != ARTIFACT_NAMES:
        raise ValueError("ARTIFACT_LABELS must cover every artifact")
    for labels, values, name in (
        (EVIDENCE_STATE_LABELS, EVIDENCE_STATES, "EVIDENCE_STATE_LABELS"),
        (EVIDENCE_LANE_LABELS, LANES, "EVIDENCE_LANE_LABELS"),
        (EVIDENCE_STALE_REASON_LABELS, STALE_REASONS, "EVIDENCE_STALE_REASON_LABELS"),
    ):
        if tuple(labels) != values:
            raise ValueError(f"{name} must cover every value, in order")
    return {
        "locale": LOCALE,
        "namespaces": {
            "annex_iii_area": {area.value: annex_iii_label(area) for area in AnnexIII},
            "prohibited_practices": {p.value: prohibited_label(p) for p in ProhibitedPractice},
            "roles": _values(ROLE_LABELS),
            "excluded_use_flags": _values(EXCLUDED_USE_LABELS),
            "annex_i_legislation": _values(ANNEX_I_LEGISLATION_LABELS),
            "annex_i_section": _values(ANNEX_I_SECTION_LABELS),
            "risk_tier": _values(RISK_TIER_LABELS),
            "disposition": _values(DISPOSITION_LABELS),
            "review_status": _values(REVIEW_STATUS_LABELS),
            "source_status": _values(SOURCE_STATUS_LABELS),
            "scope_status": _values(SCOPE_STATUS_LABELS),
            "derogation": dict(DEROGATION_LABELS),
            "artifacts": {name: ARTIFACT_LABELS[name] for name in sorted(ARTIFACT_LABELS)},
            "evidence_state": dict(EVIDENCE_STATE_LABELS),
            "evidence_lane": dict(EVIDENCE_LANE_LABELS),
            "evidence_stale_reason": dict(EVIDENCE_STALE_REASON_LABELS),
        },
    }
