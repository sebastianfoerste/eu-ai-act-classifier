"""Single source of truth for EU AI Act citations.

All references are to Regulation (EU) 2024/1689 (Artificial Intelligence Act),
OJ L, 2024/1689, 12.7.2024 ("AIA"). Pinpoint citations follow the German
convention: ``Art. <article> Abs. <paragraph> lit. <letter> AIA``, rendered
here in the shorter ``Art. 5(1)(f) AIA`` form for readability.

A citation carries a ``verified`` flag. ``verified=False`` means the exact
sub-point lettering is pending confirmation against the consolidated EUR-Lex
text. All asserted Annex III sub-point letters (areas 1-8, including law
enforcement and migration) and the Art. 5(1) prohibited-practice letters
(a)-(h) were checked against the consolidated EUR-Lex text on 2026-06-23;
only the residual ``UNSURE`` bucket — an Annex III area is implicated but the
specific point is unsettled on the facts — carries the ``noch zu verifizieren``
flag. The engine propagates this flag into its output so a reviewing lawyer
sees precisely which pinpoints are not yet locked, instead of trusting a
citation that was guessed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import RegulatorySource, SourceStatus

REGULATION = (
    "Regulation (EU) 2024/1689 of the European Parliament and of the Council "
    "of 13 June 2024 (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024"
)
SHORT = "AIA"
AI_ACT_URL = "https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng"
AI_ACT_AMENDMENT_URL = "https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng"
CSA_DIRECTIVE_URL = "https://publications.europa.eu/resource/celex/32011L0093"
AI_ACT_SERVICE_DESK_URL = "https://ai-act-service-desk.ec.europa.eu/en/ai-act-explorer"
HIGH_RISK_GUIDELINES_URL = (
    "https://digital-strategy.ec.europa.eu/en/library/"
    "draft-commission-guidelines-classification-high-risk-ai-systems"
)
PROHIBITED_GUIDELINES_URL = (
    "https://digital-strategy.ec.europa.eu/en/library/"
    "commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act"
)
AI_SYSTEM_DEFINITION_GUIDELINES_URL = (
    "https://digital-strategy.ec.europa.eu/en/library/"
    "commission-publishes-guidelines-ai-system-definition-facilitate-first-ai-acts-rules-application"
)
GPAI_CODE_URL = "https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai"
GPAI_PROVIDER_GUIDELINES_URL = "https://digital-strategy.ec.europa.eu/en/node/13982/printable/pdf"
TRANSPARENCY_GUIDANCE_URL = (
    "https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai"
)


BINDING_SOURCE_RETRIEVED_ON = "2026-08-26"
ADVISORY_SOURCE_RETRIEVED_ON = "2026-06-18"
# Read from the Official Journal snapshot in sources/oj/32011L0093.en.xhtml.
CSA_DIRECTIVE_RETRIEVED_ON = "2026-10-14"

# --- Dates the rules turn on -----------------------------------------------
# Each comes from the snapshotted Official Journal text named beside it.
# Art. 113, third paragraph, point (a) AIA, as replaced by Art. 1(40)(a) of
# Regulation (EU) 2026/1744: Art. 5(1)(ba), (bb), (1a) and (1b) apply from here.
NEW_PROHIBITIONS_APPLY_FROM = "2026-12-02"
# Art. 113, third paragraph, point (b) AIA: Chapter V applies from this date.
CHAPTER_V_APPLIES_FROM = "2025-08-02"
# Art. 111(3) AIA (original text, not amended): GPAI models placed on the market
# before CHAPTER_V_APPLIES_FROM comply by this date.
GPAI_LEGACY_DEADLINE = "2027-08-02"
# Art. 113, second paragraph AIA: the general date of application, which Art. 50
# follows.
GENERAL_APPLICATION_DATE = "2026-08-02"
# Art. 111(4) AIA, added by Art. 1(39)(b) of Regulation (EU) 2026/1744: generative
# systems placed on the market before GENERAL_APPLICATION_DATE comply with
# Art. 50(2) by this date.
ART_50_2_LEGACY_DEADLINE = "2026-12-02"


def source_manifest() -> list[RegulatorySource]:
    """Versioned source registry used by reports and draft work products."""

    return [
        RegulatorySource(
            source_id="ai-act-2024-1689",
            title="Regulation (EU) 2024/1689, Artificial Intelligence Act",
            legal_status=SourceStatus.BINDING_LEVEL_1,
            url=AI_ACT_URL,
            retrieved_on=BINDING_SOURCE_RETRIEVED_ON,
            citation_label="Regulation (EU) 2024/1689",
            implementation_note="Binding Level 1 source for classifications and obligations.",
        ),
        RegulatorySource(
            source_id="ai-act-amendment-2026-1744",
            title="Regulation (EU) 2026/1744 amending the Artificial Intelligence Act",
            legal_status=SourceStatus.BINDING_LEVEL_1,
            url=AI_ACT_AMENDMENT_URL,
            retrieved_on=BINDING_SOURCE_RETRIEVED_ON,
            citation_label="Regulation (EU) 2026/1744",
            implementation_note=(
                "Binding amendment adopted on 8 July 2026 and published in the Official "
                "Journal on 24 July 2026."
            ),
        ),
        RegulatorySource(
            source_id="csa-directive-2011-93",
            title=(
                "Directive 2011/93/EU on combating the sexual abuse and sexual exploitation "
                "of children and child pornography"
            ),
            legal_status=SourceStatus.BINDING_LEVEL_1,
            url=CSA_DIRECTIVE_URL,
            retrieved_on=CSA_DIRECTIVE_RETRIEVED_ON,
            citation_label="Directive 2011/93/EU",
            implementation_note=(
                "Art. 2, points (c) and (e), define the material and performance referred to "
                "in Art. 5(1), first subparagraph, point (bb) AIA."
            ),
        ),
        RegulatorySource(
            source_id="ai-act-service-desk",
            title="AI Act Service Desk",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=AI_ACT_SERVICE_DESK_URL,
            retrieved_on=ADVISORY_SOURCE_RETRIEVED_ON,
            citation_label="AI Act Service Desk",
            implementation_note="Official explanatory and navigation layer, not legal advice.",
        ),
        RegulatorySource(
            source_id="prohibited-practices-guidelines",
            title="Commission guidelines on prohibited AI practices",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=PROHIBITED_GUIDELINES_URL,
            retrieved_on=ADVISORY_SOURCE_RETRIEVED_ON,
            citation_label="Commission prohibited-practices guidelines",
            implementation_note="Nonbinding Commission interpretation and practical examples.",
        ),
        RegulatorySource(
            source_id="ai-system-definition-guidelines",
            title="Commission guidelines on the AI system definition",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=AI_SYSTEM_DEFINITION_GUIDELINES_URL,
            retrieved_on=ADVISORY_SOURCE_RETRIEVED_ON,
            citation_label="Commission AI-system-definition guidelines",
            implementation_note="Nonbinding support for scope assessment.",
        ),
        RegulatorySource(
            source_id="draft-high-risk-guidelines-2026",
            title="Draft Commission guidelines on high-risk AI classification",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=HIGH_RISK_GUIDELINES_URL,
            retrieved_on=ADVISORY_SOURCE_RETRIEVED_ON,
            citation_label="Draft high-risk classification guidelines",
            implementation_note="Draft guidance used as advisory overlay and eval context.",
        ),
        RegulatorySource(
            source_id="gpai-code-of-practice",
            title="General-Purpose AI Code of Practice",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=GPAI_CODE_URL,
            retrieved_on=ADVISORY_SOURCE_RETRIEVED_ON,
            citation_label="GPAI Code of Practice",
            implementation_note="Voluntary tool for GPAI obligations, separate from Level 1 logic.",
        ),
        RegulatorySource(
            source_id="gpai-provider-guidelines",
            title="Guidelines for providers of general-purpose AI models",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=GPAI_PROVIDER_GUIDELINES_URL,
            retrieved_on=ADVISORY_SOURCE_RETRIEVED_ON,
            citation_label="GPAI provider guidelines",
            implementation_note="Nonbinding scope and compliance support for GPAI model providers.",
        ),
        RegulatorySource(
            source_id="transparency-guidance",
            title="Transparency guidance status tracker",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=TRANSPARENCY_GUIDANCE_URL,
            retrieved_on=ADVISORY_SOURCE_RETRIEVED_ON,
            citation_label="Transparency guidance tracker",
            implementation_note=(
                "Placeholder advisory source until final Art. 50 guidance is published."
            ),
        ),
    ]


@dataclass(frozen=True, slots=True)
class Citation:
    """A pinpoint reference into the AIA.

    ``verified`` is False where the sub-point lettering is not yet confirmed
    against the official text. ``noch zu verifizieren`` is preserved verbatim
    in rendered output for any unverified citation.
    """

    ref: str
    verified: bool = True

    def render(self) -> str:
        suffix = "" if self.verified else "  [noch zu verifizieren]"
        return f"{self.ref}{suffix}"


def cite(ref: str, *, verified: bool = True) -> Citation:
    return Citation(ref=ref, verified=verified)


# --- Application timeline (Art. 113 AIA) -----------------------------------
# Entry into force 1.8.2024; staggered application thereafter.
@dataclass(frozen=True, slots=True)
class ApplicationDate:
    provision: str
    date: str
    note: str
    source_status: SourceStatus = SourceStatus.BINDING_LEVEL_1
    source_id: str = "ai-act-2024-1689"
    source_url: str = AI_ACT_URL


APPLICATION_DATES: tuple[ApplicationDate, ...] = (
    ApplicationDate(
        "Chapters I-II, incl. Art. 5 (prohibited practices), with 2026/1744 exceptions",
        "2025-02-02",
        (
            "Chapters I and II apply from 2 February 2025, except Art. 5(1), first "
            "subparagraph, points (ba) and (bb), and Art. 5(1a) and (1b) (Art. 113, third "
            "paragraph, point (a) AIA, as amended by Regulation (EU) 2026/1744)."
        ),
    ),
    ApplicationDate(
        "Chapter V (general-purpose AI models)",
        "2025-08-02",
        "GPAI obligations apply from 2 August 2025 (Art. 113(b) AIA).",
    ),
    ApplicationDate(
        "Art. 111(3): GPAI models placed on the market before 2025-08-02",
        GPAI_LEGACY_DEADLINE,
        (
            "Providers of general-purpose AI models placed on the market before 2 August 2025 "
            "must comply by 2 August 2027 (Art. 111(3) AIA; not amended by Regulation (EU) "
            "2026/1744)."
        ),
    ),
    ApplicationDate(
        "General application for provisions without a later specific date",
        "2026-08-02",
        (
            "The general application date remains 2 August 2026, subject to the later "
            "dates introduced by Regulation (EU) 2026/1744."
        ),
    ),
)


AMENDING_APPLICATION_DATES: tuple[ApplicationDate, ...] = (
    ApplicationDate(
        "Art. 2(2) and Annex I as amended: machinery moved to Annex I, Section B",
        "2026-07-27",
        (
            "Regulation (EU) 2026/1744 entered into force on 27 July 2026 (its Art. 4) and "
            "sets no later date for these amendments. Annex I, Section A, point 1 is deleted "
            "and Section B, point 21 (Regulation (EU) 2023/1230, machinery) is added "
            "(Art. 1(41)). For AI systems classified as high-risk under Art. 6(1) related to "
            "Section B products, only Art. 6(1), Art. 60a and Arts. 102 to 112 apply "
            "(Art. 2(2) AIA, as replaced by Art. 1(2)(a))."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Arts. 102 to 110 (amendments to other Union acts)",
        "2026-07-27",
        (
            "Articles 102 to 110 apply from 27 July 2026 (Art. 113, third paragraph, "
            "point (d) AIA, as added by Regulation (EU) 2026/1744)."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Art. 5(1)(ba), (bb), (1a), (1b) (prohibitions added by Reg. (EU) 2026/1744)",
        "2026-12-02",
        (
            "Art. 5(1), first subparagraph, points (ba) and (bb), and Art. 5(1a) and (1b) "
            "apply from 2 December 2026 (Art. 113, third paragraph, point (a) AIA, as "
            "amended by Regulation (EU) 2026/1744). The prohibited-practices gate tests "
            "them against the profile's assessment_date."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Art. 50(2) for generative AI systems placed on the market before 2026-08-02",
        "2026-12-02",
        (
            "Providers of AI systems generating synthetic audio, image, video or text "
            "content placed on the market before 2 August 2026 must comply with Art. 50(2) "
            "by 2 December 2026 (Art. 111(4) AIA, as added by Regulation (EU) 2026/1744)."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Chapter III, Sections 1 to 3: Art. 6(2) and Annex III high-risk systems",
        "2027-12-02",
        (
            "Chapter III, Sections 1 to 3, except Art. 6(5), apply from 2 December 2027 to "
            "AI systems classified as high-risk under Art. 6(2) and Annex III (Art. 113, "
            "third paragraph, point (c)(i) AIA, as amended by Regulation (EU) 2026/1744)."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Chapter III, Sections 1 to 3: Art. 6(1) and Annex I high-risk systems",
        "2028-08-02",
        (
            "Chapter III, Sections 1 to 3, except Art. 6(5), apply from 2 August 2028 to "
            "AI systems classified as high-risk under Art. 6(1) and Annex I (Art. 113, "
            "third paragraph, point (c)(ii) AIA, as amended by Regulation (EU) 2026/1744)."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
)
