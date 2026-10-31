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

from datetime import date
from enum import StrEnum
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, Field, WithJsonSchema, model_validator


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


class ProhibitedPractice(StrEnum):
    """Prohibited practices (Art. 5(1) AIA), keyed to their letters."""

    SUBLIMINAL_MANIPULATION = "5.1.a"
    EXPLOITS_VULNERABILITIES = "5.1.b"
    # Points (ba) and (bb), inserted by Regulation (EU) 2026/1744, apply from 2 December 2026.
    NON_CONSENSUAL_INTIMATE_IMAGERY = "5.1.ba"
    CHILD_SEXUAL_ABUSE_MATERIAL = "5.1.bb"
    SOCIAL_SCORING = "5.1.c"
    PREDICTIVE_POLICING_INDIVIDUAL = "5.1.d"
    FACIAL_SCRAPING = "5.1.e"
    EMOTION_RECOGNITION_WORK_EDUCATION = "5.1.f"
    BIOMETRIC_CATEGORISATION_SENSITIVE = "5.1.g"
    REALTIME_REMOTE_BIOMETRIC_ID = "5.1.h"


class AnnexISection(StrEnum):
    """Annex I sections for the Art. 6(1) AIA product route.

    For a Section B product only Art. 6(1), Art. 60a and Arts. 102 to 112 apply,
    and Arts. 57 to 59 only in so far as the high-risk requirements have been
    integrated in the sectoral legislation (Art. 2(2) AIA). Regulation (EU)
    2026/1744 moved machinery to Section B:
    Section A, point 1 is deleted and Regulation (EU) 2023/1230 is Section B,
    point 21.
    """

    SECTION_A = "A"
    SECTION_B = "B"


class Derogation(BaseModel):
    """Art. 6(3) AIA derogation facts for an Annex III system.

    An Annex III system is *not* high-risk if it does not pose a significant
    risk of harm, but only where one of the four conditions holds AND the
    system does not perform profiling of natural persons. Profiling always
    keeps the system high-risk (Art. 6(3), third subparagraph, AIA; the
    conditions are in the second subparagraph).
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


def _iso_date(value: str) -> str:
    # The Art. 111 AIA transitions compare these dates with fixed cut-off dates, so
    # only a calendar date in YYYY-MM-DD form is accepted ("2026-03-01", not
    # "March 2026" or "01.03.2026").
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        parsed = None
    if parsed is None or parsed.isoformat() != value:
        raise ValueError("must be an ISO date in YYYY-MM-DD form")
    return value


# "format": "date" alone is an annotation many validators skip, so the pattern keeps
# "March 2026" and "2026-W09-7" out at the schema level too.
IsoDate = Annotated[
    str,
    AfterValidator(_iso_date),
    WithJsonSchema({"type": "string", "format": "date", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}),
]


class SystemProfile(BaseModel):
    """Structured description of an AI system with characterised facts."""

    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    @classmethod
    def _drop_schema_reference(cls, data: Any) -> Any:
        # Profiles may point editors at schemas/system-profile.v1.schema.json
        # via "$schema"; that key is metadata, not a fact about the system.
        if isinstance(data, dict) and "$schema" in data:
            data = {key: value for key, value in data.items() if key != "$schema"}
        return data

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
    # The AI system's dates: Art. 111(2) and, for placing on the market, Art. 111(4) AIA.
    placing_on_market_date: IsoDate | None = Field(
        default=None,
        description=(
            "ISO date (YYYY-MM-DD) on which the AI system was placed on the Union market. "
            "Drives Art. 111(2) and (4) AIA. For Art. 111(2) the date on which the first unit "
            "of that type and model was placed on the market or put into service decides "
            "(recital 39 of Regulation (EU) 2026/1744), not the date of a later unit. Null: "
            "not given."
        ),
    )
    putting_into_service_date: IsoDate | None = Field(
        default=None,
        description=(
            "ISO date (YYYY-MM-DD) on which the AI system was put into service. Drives "
            "Art. 111(2) AIA, for which the first unit of that type and model placed on the "
            "market or put into service decides (recital 39 of Regulation (EU) 2026/1744). "
            "Null: not given."
        ),
    )
    significant_change_after_application_date: bool | None = Field(
        default=None,
        description=(
            "Art. 111(2) AIA: whether the design of a system placed on the market or put into "
            "service before its Chapter III date has changed significantly as from that date. "
            "That date is contested: the report uses the Art. 113, third paragraph, point (c) "
            "date for the route (2027-12-02 for Annex III, 2028-08-02 for Annex I), but the "
            "general date of 2026-08-02 may be meant. Null: not established."
        ),
    )
    # A system intended to be used by public authorities (Art. 111(2) AIA).
    public_authority_use: bool = False
    # The deployer is a public authority, Union institution, body, office or agency, or
    # acts on behalf of one (Art. 49(3) AIA). None: not established.
    deployer_public_authority: bool | None = Field(
        default=None,
        description=(
            "Art. 49(3) AIA: the deployer is a public authority, Union institution, body, office "
            "or agency, or acts on behalf of one. Null: not established, so the registration of "
            "use is inferred, for review, where the system is intended to be used by public "
            "authorities or its Annex III point (5(a), 6 or 7) describes such use."
        ),
    )
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
    # The model's own date for Art. 111(3) AIA, apart from the AI system's placing_on_market_date.
    gpai_model_placing_on_market_date: IsoDate | None = Field(
        default=None,
        description=(
            "Art. 111(3) AIA: the date the general-purpose AI model itself was placed on the "
            "market. Null: the model is dated by placing_on_market_date, for review."
        ),
    )

    # Prohibited-practice screens (Art. 5(1) AIA)
    prohibited_practices: list[ProhibitedPractice] = Field(default_factory=list)

    # High-risk screens
    annex_i_safety_component: bool = False  # Art. 6(1)(a): product / safety component
    annex_i_third_party_assessment: bool = False  # Art. 6(1)(b): third-party conformity assessment
    annex_i_section: AnnexISection | None = Field(
        default=None,
        description=(
            "Annex I section of the Art. 6(1) AIA product. For Section B only the Art. 2(2) "
            "provisions apply. Null: treated as Section A."
        ),
    )
    annex_iii_area: AnnexIII | None = None  # Art. 6(2) + Annex III
    derogation: Derogation = Field(default_factory=Derogation)

    # Transparency screens (Art. 50 AIA)
    interacts_with_natural_persons: bool = False  # 50(1)
    generates_synthetic_content: bool = False  # 50(2)
    deploys_emotion_or_biometric_categorisation: bool = False  # 50(3)
    generates_deepfakes: bool = False  # 50(4)

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
    application_date: str
    review_status: ReviewStatus
    # Qualifies the application date: a contestable reading of Art. 113 AIA or a
    # transitional rule in Art. 111 AIA.
    application_date_note: str | None = None


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
