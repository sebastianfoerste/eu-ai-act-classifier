"""Typed domain models for the EU AI Act classifier.

The input (:class:`SystemProfile`) is a structured description of an AI system:
the facts a lawyer establishes. The output (:class:`ClassificationReport`) is
the determined risk tier, the obligations that attach, the documentation a
provider or deployer owes, and an explicit review gate for the calls that turn
on facts the engine cannot settle on its own.

The screening fields are deliberately granular booleans. The legal judgment
sits in *how the facts are characterised* (does this tool "materially
influence" a hiring decision?); the engine only applies rules to characterised
facts. That division, lawyer characterises and engine subsumes, is what keeps
the output deterministic and auditable.
"""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _iso_date_or_none(value: object) -> object:
    """Accept an ISO 8601 calendar date or null; an empty string means null."""
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not _ISO_DATE.match(value):
        raise ValueError("expected an ISO 8601 date (YYYY-MM-DD) or null")
    date.fromisoformat(value)  # rejects impossible dates such as 2026-02-30
    return value


class Role(StrEnum):
    """Operator roles under the AIA. A single company often holds several."""

    PROVIDER = "provider"
    DEPLOYER = "deployer"
    IMPORTER = "importer"
    DISTRIBUTOR = "distributor"
    AUTHORIZED_REPRESENTATIVE = "authorized_representative"
    GPAI_PROVIDER = "gpai_provider"


class RiskTier(StrEnum):
    """The AIA's risk tiers, ordered by severity (see :data:`TIER_ORDER`)."""

    OUT_OF_SCOPE = "outside_scope"
    PROHIBITED = "prohibited"
    HIGH = "high_risk"
    LIMITED = "limited_risk"  # transparency obligations only (Art. 50 AIA)
    MINIMAL = "minimal_risk"


TIER_ORDER: dict[RiskTier, int] = {
    RiskTier.PROHIBITED: 3,
    RiskTier.HIGH: 2,
    RiskTier.LIMITED: 1,
    RiskTier.MINIMAL: 0,
    RiskTier.OUT_OF_SCOPE: -1,
}


class Severity(StrEnum):
    BLOCKER = "blocker"
    HIGH = "high"
    MEDIUM = "medium"
    INFO = "info"


class Disposition(StrEnum):
    """Whether the engine reached a conclusion or handed off to a lawyer."""

    DETERMINED = "determined"
    REQUIRES_REVIEW = "requires_review"


class SourceStatus(StrEnum):
    """Legal status of the source supporting a report element."""

    BINDING_LEVEL_1 = "binding_level_1"
    PROVISIONAL_POLITICAL_AGREEMENT = "provisional_political_agreement"
    NONBINDING_GUIDANCE = "nonbinding_guidance"


class ScopeStatus(StrEnum):
    """Whether the submitted profile is within the AI Act triage perimeter."""

    IN_SCOPE = "in_scope"
    OUTSIDE_SCOPE = "outside_ai_act_scope"
    REQUIRES_REVIEW = "scope_requires_review"


class ReviewStatus(StrEnum):
    """Review posture for obligations and generated work products."""

    DRAFT = "draft"
    REVIEW_REQUIRED = "review_required"
    DETERMINED = "determined"


class ExcludedUse(StrEnum):
    """Common AI Act scope exclusions or carve-outs that need visible review."""

    MILITARY_DEFENCE_NATIONAL_SECURITY = "military_defence_national_security"
    RESEARCH_DEVELOPMENT_TESTING = "research_development_testing"
    PERSONAL_NON_PROFESSIONAL = "personal_non_professional"
    FREE_OPEN_SOURCE = "free_open_source"


class AnnexIII(StrEnum):
    """Annex III high-risk areas (Art. 6(2) AIA).

    Values double as short locators (``III.4.a`` = Annex III point 4(a)).
    ``UNSURE`` is the residual case: an Annex III area is implicated but the
    specific point is unsettled. The engine treats it conservatively as
    high-risk and routes it to review.
    """

    BIOMETRICS_REMOTE_ID = "III.1.a"
    BIOMETRICS_CATEGORISATION = "III.1.b"
    BIOMETRICS_EMOTION = "III.1.c"
    CRITICAL_INFRASTRUCTURE = "III.2"
    EDUCATION_ACCESS = "III.3.a"
    EDUCATION_EVALUATION = "III.3.b"
    EDUCATION_ASSESSMENT_LEVEL = "III.3.c"
    EDUCATION_PROCTORING = "III.3.d"
    EMPLOYMENT_SELECTION = "III.4.a"
    EMPLOYMENT_MANAGEMENT = "III.4.b"
    ESSENTIAL_PUBLIC_BENEFITS = "III.5.a"
    CREDITWORTHINESS = "III.5.b"
    INSURANCE_LIFE_HEALTH = "III.5.c"
    EMERGENCY_DISPATCH = "III.5.d"
    LAW_ENFORCEMENT_VICTIM_RISK = "III.6.a"
    LAW_ENFORCEMENT_POLYGRAPH = "III.6.b"
    LAW_ENFORCEMENT_EVIDENCE_RELIABILITY = "III.6.c"
    LAW_ENFORCEMENT_REOFFENDING_RISK = "III.6.d"
    LAW_ENFORCEMENT_PROFILING = "III.6.e"
    MIGRATION_POLYGRAPH = "III.7.a"
    MIGRATION_RISK_ASSESSMENT = "III.7.b"
    MIGRATION_APPLICATION_EXAMINATION = "III.7.c"
    MIGRATION_IDENTIFICATION = "III.7.d"
    JUSTICE = "III.8.a"
    DEMOCRATIC_PROCESSES = "III.8.b"
    UNSURE = "III.unsure"  # an Annex III area is implicated but the point is unclear


class AnnexILegislation(StrEnum):
    """Union harmonisation legislation listed in Annex I AIA, as amended.

    Values are locators: ``I.A.2`` is Annex I, Section A, point 2. Regulation
    (EU) 2026/1744 deleted Section A, point 1 (Directive 2006/42/EC, machinery)
    and added Section B, point 21 (Regulation (EU) 2023/1230, machinery) by its
    Art. 1(41), so machinery is a Section B act and ``I.A.1`` does not exist.
    The engine derives the Section from the point; the reviewer only names the
    legislation that covers the product.
    """

    TOYS = "I.A.2"
    RECREATIONAL_CRAFT = "I.A.3"
    LIFTS = "I.A.4"
    EXPLOSIVE_ATMOSPHERES_EQUIPMENT = "I.A.5"
    RADIO_EQUIPMENT = "I.A.6"
    PRESSURE_EQUIPMENT = "I.A.7"
    CABLEWAY_INSTALLATIONS = "I.A.8"
    PERSONAL_PROTECTIVE_EQUIPMENT = "I.A.9"
    GAS_APPLIANCES = "I.A.10"
    MEDICAL_DEVICES = "I.A.11"
    IN_VITRO_DIAGNOSTIC_DEVICES = "I.A.12"
    CIVIL_AVIATION_SECURITY = "I.B.13"
    TWO_OR_THREE_WHEEL_VEHICLES = "I.B.14"
    AGRICULTURAL_AND_FORESTRY_VEHICLES = "I.B.15"
    MARINE_EQUIPMENT = "I.B.16"
    RAIL_SYSTEM_INTEROPERABILITY = "I.B.17"
    MOTOR_VEHICLES_TYPE_APPROVAL = "I.B.18"
    MOTOR_VEHICLES_GENERAL_SAFETY = "I.B.19"
    UNMANNED_AIRCRAFT = "I.B.20"
    MACHINERY = "I.B.21"

    @property
    def section(self) -> str:
        """``"A"`` or ``"B"``."""
        return self.value.split(".")[1]

    @property
    def point(self) -> int:
        return int(self.value.split(".")[2])


class ProhibitedPractice(StrEnum):
    """Prohibited practices (Art. 5(1) AIA), keyed to their letters.

    Points (ba) and (bb), inserted by Regulation (EU) 2026/1744, are not listed
    here: they turn on facts the engine subsumes itself (see
    :class:`IntimateImageryScreen` and :class:`ChildSexualAbuseMaterialScreen`)
    and on the date they apply from.
    """

    SUBLIMINAL_MANIPULATION = "5.1.a"
    EXPLOITS_VULNERABILITIES = "5.1.b"
    SOCIAL_SCORING = "5.1.c"
    PREDICTIVE_POLICING_INDIVIDUAL = "5.1.d"
    FACIAL_SCRAPING = "5.1.e"
    EMOTION_RECOGNITION_WORK_EDUCATION = "5.1.f"
    BIOMETRIC_CATEGORISATION_SENSITIVE = "5.1.g"
    REALTIME_REMOTE_BIOMETRIC_ID = "5.1.h"


class Derogation(BaseModel):
    """Art. 6(3) AIA derogation facts for an Annex III system.

    An Annex III system is *not* high-risk if it does not pose a significant
    risk of harm, but only where one of the four conditions holds AND the
    system does not perform profiling of natural persons. Profiling always
    keeps the system high-risk (Art. 6(3) subpara. 2 AIA).
    """

    narrow_procedural_task: bool = False
    improves_prior_human_activity: bool = False
    detects_patterns_without_replacing_human: bool = False
    preparatory_task: bool = False
    performs_profiling: bool = False

    @property
    def any_condition(self) -> bool:
        return (
            self.narrow_procedural_task
            or self.improves_prior_human_activity
            or self.detects_patterns_without_replacing_human
            or self.preparatory_task
        )


class Article5aFacts(BaseModel):
    """Facts for Art. 5(1a) AIA, shared by Art. 5(1)(ba) and (bb).

    Every fact is three-valued: ``true``, ``false`` or ``null`` (not
    established). A ``null`` that could change the result keeps the result
    UNKNOWN and routes it to review; it is never read as ``false``.
    """

    model_config = {"extra": "forbid"}

    intended_purpose: bool | None = Field(
        default=None,
        description=(
            "The generation or manipulation is the intended purpose of the AI system "
            "(Art. 5(1a)(a)(i) AIA)."
        ),
    )
    foreseeable_and_reproducible: bool | None = Field(
        default=None,
        description=(
            "The system's design, training, architecture, capabilities or user-facing "
            "functionalities make the generation or manipulation a reasonably foreseeable and "
            "reproducible outcome, without requiring significant technical modification "
            "(Art. 5(1a)(a)(ii) AIA)."
        ),
    )
    adequate_safeguards: bool | None = Field(
        default=None,
        description=(
            "The system has reasonable and adequate technical safety measures and other "
            "safeguards to reliably prevent the generation or manipulation, taking into account "
            "reasonably foreseeable misuse, and to correct observed or reported misuse "
            "(Art. 5(1a)(a)(ii) AIA)."
        ),
    )
    deployer_uses_for_that_purpose: bool | None = Field(
        default=None,
        description=(
            "The deployer uses the system for the purpose of generating or manipulating the "
            "material or performance (Art. 5(1a)(b) AIA)."
        ),
    )


class IntimateImageryScreen(Article5aFacts):
    """Facts for Art. 5(1), first subparagraph, point (ba) AIA, with Art. 5(1a) and (1b).

    Applies from 2 December 2026 (Art. 113, third paragraph, point (a) AIA, as
    amended by Regulation (EU) 2026/1744).
    """

    generates_material: bool | None = Field(
        default=None,
        description=(
            "The system generates realistic images, videos, audio or similar material of an "
            "identifiable natural person's intimate parts, or of an identifiable natural person "
            "engaged in sexually explicit activities."
        ),
    )
    manipulates_material_increasing_exposure: bool | None = Field(
        default=None,
        description=(
            "The system manipulates such material in a way that increases the exposure of any "
            "depicted intimate parts or alters the nature of any depicted sexually explicit "
            "activities. Other manipulation is not manipulation (Art. 5(1b) AIA)."
        ),
    )
    consent_ensured: bool | None = Field(
        default=None,
        description=(
            "The generation or manipulation takes place only with the depicted person's "
            "freely-given, specific, informed, unambiguous and explicit consent."
        ),
    )


class ChildSexualAbuseMaterialScreen(Article5aFacts):
    """Facts for Art. 5(1), first subparagraph, point (bb) AIA, with Art. 5(1a).

    Applies from 2 December 2026 (Art. 113, third paragraph, point (a) AIA, as
    amended by Regulation (EU) 2026/1744).
    """

    generates_or_manipulates: bool | None = Field(
        default=None,
        description=(
            "The system generates or manipulates material or performance within the meaning "
            "of Art. 2, points (c) and (e), of Directive 2011/93/EU."
        ),
    )
    without_right_defence_applies: bool | None = Field(
        default=None,
        description='A "without right" defence applies under national law.',
    )


class SystemProfile(BaseModel):
    """Structured description of an AI system with characterised facts."""

    model_config = {"extra": "forbid"}

    name: str
    description: str = ""
    roles: list[Role] = Field(default_factory=lambda: [Role.PROVIDER])
    purpose: str = ""
    sector: str = ""

    # Scope and intake screens. Defaults preserve the alpha examples: a submitted
    # profile is treated as an in-scope AI system unless the caller says otherwise.
    is_ai_system: bool | None = True
    intended_purpose_source: str = ""
    eu_nexus: bool | None = True
    excluded_use_flags: list[ExcludedUse] = Field(default_factory=list)
    assessment_date: str | None = Field(
        default=None,
        description=(
            "ISO date of the placing on the market, putting into service or use under "
            "assessment. Selects the rules in force; null leaves date-dependent results UNKNOWN."
        ),
    )
    placing_on_market_date: str | None = None
    putting_into_service_date: str | None = None
    significant_change_after_application_date: bool | None = None
    public_authority_use: bool = False
    deployer_public_law_body: bool | None = None
    deployer_private_public_service: bool | None = None
    provider_established_outside_eu: bool = False
    has_authorised_representative: bool | None = None
    substantially_modifies_system: bool = False
    puts_name_or_trademark_on_system: bool = False

    # General-purpose AI model (Chapter V AIA)
    is_gpai_model: bool = False
    training_flops: float | None = Field(
        default=None,
        description=(
            "Cumulative training compute in FLOP; drives the Art. 51(2) systemic-risk presumption."
        ),
    )
    gpai_systemic_risk_designated: bool = False  # Commission designation under Art. 51(1)(b)

    # Prohibited-practice screens (Art. 5(1) AIA)
    prohibited_practices: list[ProhibitedPractice] = Field(default_factory=list)
    # Art. 5(1)(ba) and (bb), from 2 December 2026. null means the screen was not
    # completed; for a system that generates synthetic content or deep fakes that
    # goes to review.
    intimate_imagery: IntimateImageryScreen | None = None
    child_sexual_abuse_material: ChildSexualAbuseMaterialScreen | None = None

    # High-risk screens
    annex_i_safety_component: bool = False  # Art. 6(1)(a): product / safety component
    annex_i_third_party_assessment: bool = False  # Art. 6(1)(b): third-party conformity assessment
    annex_i_legislation: AnnexILegislation | None = None  # Annex I point; decides Section A or B
    annex_iii_area: AnnexIII | None = None  # Art. 6(2) + Annex III
    derogation: Derogation = Field(default_factory=Derogation)

    # Transparency screens (Art. 50 AIA)
    interacts_with_natural_persons: bool = False  # 50(1)
    generates_synthetic_content: bool = False  # 50(2)
    deploys_emotion_or_biometric_categorisation: bool = False  # 50(3)
    generates_deepfakes: bool = False  # 50(4)

    @field_validator(
        "assessment_date", "placing_on_market_date", "putting_into_service_date", mode="before"
    )
    @classmethod
    def _iso_dates(cls, value: object) -> object:
        return _iso_date_or_none(value)

    @property
    def is_provider(self) -> bool:
        return Role.PROVIDER in self.roles

    @property
    def is_deployer(self) -> bool:
        return Role.DEPLOYER in self.roles

    @property
    def is_importer(self) -> bool:
        return Role.IMPORTER in self.roles

    @property
    def is_distributor(self) -> bool:
        return Role.DISTRIBUTOR in self.roles

    @property
    def is_authorized_representative(self) -> bool:
        return Role.AUTHORIZED_REPRESENTATIVE in self.roles


class Finding(BaseModel):
    """One classification result with its citation and severity."""

    rule_id: str
    citation: str
    citation_verified: bool = True
    title: str
    detail: str = ""
    severity: Severity = Severity.INFO
    tier: RiskTier | None = None


class Obligation(BaseModel):
    """A duty that attaches once a tier/role is determined."""

    article: str
    citation_verified: bool = True
    title: str
    applies_to: Role
    requirement: str


class TimelineItem(BaseModel):
    provision: str
    applies_from: str
    note: str
    source_status: SourceStatus = SourceStatus.BINDING_LEVEL_1
    source_id: str = "ai-act-2024-1689"
    source_url: str = ""


class RegulatorySource(BaseModel):
    source_id: str
    title: str
    legal_status: SourceStatus
    url: str
    retrieved_on: str
    citation_label: str
    implementation_note: str


class ScopeAssessment(BaseModel):
    status: ScopeStatus = ScopeStatus.IN_SCOPE
    is_ai_system: bool | None = True
    intended_purpose_source: str = ""
    eu_nexus: bool | None = True
    excluded_use_flags: list[ExcludedUse] = Field(default_factory=list)
    assessment_date: str | None = None
    transitional_status: str = "No transitional limitation identified from the submitted facts."
    notes: list[str] = Field(default_factory=list)


class ObligationGraphItem(BaseModel):
    obligation_id: str
    article: str
    actor: Role
    trigger: str
    requirement: str
    evidence_artifact: str
    source_status: SourceStatus
    source_url: str
    application_date: str | None  # null: turns on a fact not given (see open_questions)
    review_status: ReviewStatus
    # Whether the obligation applies on the profile's assessment_date; null when
    # either date is unknown.
    applies_on_assessment_date: bool | None = None


class AdvisoryNote(BaseModel):
    note_id: str
    title: str
    detail: str
    source_id: str
    source_status: SourceStatus = SourceStatus.NONBINDING_GUIDANCE
    source_url: str
    review_status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED


class ClassificationReport(BaseModel):
    """The engine's output: tier, obligations, documentation, and review gate."""

    system: str
    regulation: str
    risk_tier: RiskTier
    disposition: Disposition
    scope: ScopeAssessment = Field(default_factory=ScopeAssessment)
    roles: list[Role]
    is_gpai: bool = False
    gpai_systemic: bool = False
    findings: list[Finding] = Field(default_factory=list)
    obligations: list[Obligation] = Field(default_factory=list)
    documentation_required: list[Obligation] = Field(default_factory=list)
    transparency_obligations: list[Obligation] = Field(default_factory=list)
    obligation_graph: list[ObligationGraphItem] = Field(default_factory=list)
    timeline: list[TimelineItem] = Field(default_factory=list)
    source_manifest: list[RegulatorySource] = Field(default_factory=list)
    advisory_notes: list[AdvisoryNote] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    unverified_citations: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "This is a screening tool, not legal advice. It does not produce a "
        "conformity assessment and it does not replace review by a qualified "
        "lawyer. Determinations marked 'requires_review' turn on facts the "
        "engine cannot settle."
    )
