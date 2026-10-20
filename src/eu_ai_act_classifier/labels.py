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
from .models import (
    AnnexIII,
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


def _short(ref: str) -> str:
    return ref.removesuffix(" AIA")


def annex_iii_label(area: AnnexIII) -> str:
    """``III.5.b`` -> ``Annex III(5)(b): Creditworthiness evaluation and credit scoring``."""

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
    raise KeyError(f"no label for {member!r}")


def _values(labels: dict) -> dict[str, str]:
    return {str(key): value for key, value in labels.items()}


def label_catalog() -> dict:
    """Every label, keyed by namespace and then by the value the JSON carries."""

    if set(DEROGATION_LABELS) != set(Derogation.model_fields):
        raise ValueError("DEROGATION_LABELS must cover every Derogation field")
    if set(ARTIFACT_LABELS) != ARTIFACT_NAMES:
        raise ValueError("ARTIFACT_LABELS must cover every artifact")
    return {
        "locale": LOCALE,
        "namespaces": {
            "annex_iii_area": {area.value: annex_iii_label(area) for area in AnnexIII},
            "prohibited_practices": {p.value: prohibited_label(p) for p in ProhibitedPractice},
            "roles": _values(ROLE_LABELS),
            "excluded_use_flags": _values(EXCLUDED_USE_LABELS),
            "risk_tier": _values(RISK_TIER_LABELS),
            "disposition": _values(DISPOSITION_LABELS),
            "review_status": _values(REVIEW_STATUS_LABELS),
            "source_status": _values(SOURCE_STATUS_LABELS),
            "scope_status": _values(SCOPE_STATUS_LABELS),
            "derogation": dict(DEROGATION_LABELS),
            "artifacts": {name: ARTIFACT_LABELS[name] for name in sorted(ARTIFACT_LABELS)},
        },
    }
