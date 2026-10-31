"""Single source of truth for EU AI Act citations.

All references are to Regulation (EU) 2024/1689 (Artificial Intelligence Act),
OJ L, 2024/1689, 12.7.2024 ("AIA"). Pinpoint citations follow the German
convention: ``Art. <article> Abs. <paragraph> lit. <letter> AIA``, rendered
here in the shorter ``Art. 5(1)(f) AIA`` form for readability.

A citation carries a ``verified`` flag. ``verified=False`` means the exact
sub-point lettering is pending confirmation against the consolidated EUR-Lex
text. All asserted Annex III sub-point letters (areas 1-8, including law
enforcement and migration) and the Art. 5(1) prohibited-practice letters
(a)-(h) were checked against the consolidated EUR-Lex text on 2026-06-23, and
points (ba) and (bb), inserted by Regulation (EU) 2026/1744, against the
consolidated text of 27 July 2026 on 2026-10-18;
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
    "of 13 June 2024 (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024, as amended by "
    "Regulation (EU) 2026/1744 (consolidated version of 27 July 2026)"
)
SHORT = "AIA"
AI_ACT_URL = "https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng"
AI_ACT_AMENDMENT_URL = "https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng"
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
GPAI_PROVIDER_GUIDELINES_URL = (
    "https://digital-strategy.ec.europa.eu/en/library/"
    "guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act"
)
# Commission guidelines on the transparency obligations under Art. 50 AIA, published
# 20 July 2026, and the final Code of Practice on marking and labelling of AI-generated
# content (Art. 50(2) and (4)), published 10 June 2026. Both nonbinding.
TRANSPARENCY_GUIDELINES_URL = (
    "https://digital-strategy.ec.europa.eu/en/library/"
    "guidelines-transparency-obligations-providers-and-deployers-ai-systems"
)
AI_CONTENT_CODE_URL = (
    "https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content"
)


BINDING_SOURCE_RETRIEVED_ON = "2026-10-18"
ADVISORY_SOURCE_RETRIEVED_ON = "2026-06-18"
# The Art. 50 sources were read later than the other advisory sources, so they carry
# their own date. `verify_sources --update` moves all three dates together.
TRANSPARENCY_SOURCE_RETRIEVED_ON = "2026-10-31"


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
            title=(
                "Guidelines on the scope of obligations for providers of general-purpose AI models"
            ),
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=GPAI_PROVIDER_GUIDELINES_URL,
            retrieved_on=ADVISORY_SOURCE_RETRIEVED_ON,
            citation_label="GPAI provider guidelines",
            implementation_note="Nonbinding scope and compliance support for GPAI model providers.",
        ),
        RegulatorySource(
            source_id="transparency-guidelines-2026",
            title="Commission guidelines on the transparency obligations under Art. 50 AIA",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=TRANSPARENCY_GUIDELINES_URL,
            retrieved_on=TRANSPARENCY_SOURCE_RETRIEVED_ON,
            citation_label="Art. 50 transparency guidelines",
            implementation_note=(
                "Nonbinding Commission guidance on Art. 50(1) to (4), published 20 July 2026; "
                "advisory overlay only."
            ),
        ),
        RegulatorySource(
            source_id="ai-content-code-of-practice",
            title="Code of Practice on marking and labelling of AI-generated content",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=AI_CONTENT_CODE_URL,
            retrieved_on=TRANSPARENCY_SOURCE_RETRIEVED_ON,
            citation_label="Code of Practice on AI-generated content",
            implementation_note=(
                "Voluntary code, final text published 10 June 2026, on the Art. 50(2) marking "
                "and detection and Art. 50(4) labelling duties. The Commission's page states "
                "that the Commission and the Board confirmed it as an adequate voluntary tool."
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
# Entry into force 1.8.2024; staggered application thereafter. Checked on
# 2026-10-18 against Art. 113 and Art. 111 in the consolidated text of
# 27 July 2026 (CELEX 02024R1689-20260727) and against Art. 1, points (39) and
# (40) of Regulation (EU) 2026/1744 (OJ L, 2026/1744, 24.7.2026; in force
# 27.7.2026 under its Art. 4). The engine sorts the entries by date.
#
# Each date is written out once here; the timeline below and the obligation
# graph both read these constants, so they cannot drift apart.
POINT_A_DATE = "2025-02-02"  # Art. 113, third paragraph, point (a)
POINT_A_EXCEPTION_DATE = "2026-12-02"  # point (a): Art. 5(1)(ba), (bb), 5(1a), (1b)
POINT_B_DATE = "2025-08-02"  # point (b), incl. Chapter V (GPAI models)
POINT_D_DATE = "2026-07-27"  # point (d): Arts. 102 to 110
GENERAL_APPLICATION_DATE = "2026-08-02"  # Art. 113, second paragraph
POINT_C_ANNEX_III = "2027-12-02"  # point (c)(i): Chapter III, Sections 1 to 3, Annex III
POINT_C_ANNEX_I = "2028-08-02"  # point (c)(ii): Chapter III, Sections 1 to 3, Annex I
# Art. 111(3): GPAI models placed on the market before POINT_B_DATE.
ART_111_3_DEADLINE = "2027-08-02"
# Art. 111(4): Art. 50(2) for systems placed on the market before GENERAL_APPLICATION_DATE.
ART_111_4_DEADLINE = "2026-12-02"
# Art. 111(2), second sentence: high-risk systems intended to be used by public authorities.
ART_111_2_PUBLIC_AUTHORITY_DEADLINE = "2030-08-02"


_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def long_date(iso: str) -> str:
    """ "2026-12-02" -> "2 December 2026", whatever the process locale."""

    year, month, day = (int(part) for part in iso.split("-"))
    return f"{day} {_MONTHS[month - 1]} {year}"


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
        "Chapters I-II, incl. Art. 5 (prohibited practices)",
        POINT_A_DATE,
        (
            "Art. 113, third paragraph, point (a) AIA. Art. 5(1), first subparagraph, "
            "points (ba) and (bb), and Art. 5(1a) and (1b) apply from 2 December 2026."
        ),
    ),
    ApplicationDate(
        "Chapter V (general-purpose AI models)",
        POINT_B_DATE,
        "GPAI obligations apply from 2 August 2025 (Art. 113, third paragraph, point (b) AIA).",
    ),
    ApplicationDate(
        "Chapter III Section 4, Chapter VII, Chapter XII (except Art. 101) and Art. 78",
        POINT_B_DATE,
        (
            "Notifying authorities and notified bodies, governance, penalties and "
            "confidentiality apply from 2 August 2025 (Art. 113, third paragraph, point (b) "
            "AIA). Art. 101 applies from the general date."
        ),
    ),
    ApplicationDate(
        "General application for provisions without a later specific date",
        GENERAL_APPLICATION_DATE,
        (
            "Art. 113, second paragraph AIA. Literal reading, confirm with counsel: this "
            "includes the high-risk duties in Chapter III, Section 5 (Arts. 40-49) and "
            "Chapter IX (e.g. Arts. 72 and 73), which point (c) does not defer. If they are "
            "read as following the Sections 1 to 3 deferral, 2 December 2027 (Annex III, "
            "also for a system that is an Annex I product too) or 2 August 2028 (Annex I "
            "only) applies."
        ),
    ),
    ApplicationDate(
        "Art. 111(3) AIA: general-purpose AI models already on the market before 2 August 2025",
        ART_111_3_DEADLINE,
        (
            "Providers of general-purpose AI models placed on the market before 2 August 2025 "
            "take the necessary steps to comply with the obligations of this Regulation by "
            "2 August 2027 (Art. 111(3) AIA, original text, not amended by Regulation (EU) "
            "2026/1744)."
        ),
    ),
)


AMENDING_APPLICATION_DATES: tuple[ApplicationDate, ...] = (
    ApplicationDate(
        "Regulation (EU) 2026/1744: Arts. 102-110 AIA (amendments to other Union acts)",
        POINT_D_DATE,
        (
            "Art. 113, third paragraph, point (d) AIA, added by Art. 1, point (40) of "
            "Regulation (EU) 2026/1744."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Regulation (EU) 2026/1744: Art. 5(1)(ba) and (bb), Art. 5(1a) and (1b) AIA",
        POINT_A_EXCEPTION_DATE,
        (
            "Prohibitions on non-consensual realistic intimate material and child sexual "
            "abuse material apply from 2 December 2026 (Art. 113, third paragraph, point (a) AIA "
            "as replaced by Art. 1, point (40) of Regulation (EU) 2026/1744)."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Regulation (EU) 2026/1744: Art. 50(2) AIA for generative systems already on the market",
        ART_111_4_DEADLINE,
        (
            "Providers of AI systems generating synthetic audio, image, video or text "
            "content placed on the market before 2 August 2026 take the necessary steps to "
            "comply with Art. 50(2) by "
            "2 December 2026 (Art. 111(4) AIA, added by Art. 1, point (39) of Regulation "
            "(EU) 2026/1744)."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Regulation (EU) 2026/1744: Chapter III Sections 1-3, Annex III high-risk systems",
        POINT_C_ANNEX_III,
        (
            "Chapter III, Sections 1, 2 and 3 (except Art. 6(5)) apply from 2 December 2027 "
            "for systems classified high-risk under Art. 6(2) and Annex III (Art. 113, third "
            "paragraph, point (c)(i) AIA as replaced by Regulation (EU) 2026/1744)."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Regulation (EU) 2026/1744: Chapter III Sections 1-3, product-embedded high-risk systems",
        POINT_C_ANNEX_I,
        (
            "Chapter III, Sections 1, 2 and 3 (except Art. 6(5)) apply from 2 August 2028 "
            "for systems classified high-risk under Art. 6(1) and Annex I (Art. 113, third "
            "paragraph, point (c)(ii) AIA as replaced by Regulation (EU) 2026/1744)."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
    ApplicationDate(
        "Regulation (EU) 2026/1744: Art. 111(2) AIA, high-risk systems for public authorities",
        ART_111_2_PUBLIC_AUTHORITY_DEADLINE,
        (
            "Apart from Art. 5, high-risk systems placed on the market or put into service "
            "before the date of application of Chapter III are covered only if, as from that "
            "date, their designs change significantly, but providers and deployers of "
            "high-risk systems intended to be used by public authorities take the necessary "
            "steps to comply with the requirements and obligations laid down in the Regulation "
            "by 2 August 2030 in any case (Art. 111(2) AIA as replaced by Art. 1, point (39)(a) "
            "of Regulation (EU) 2026/1744). Components of the Annex X large-scale IT systems "
            "placed on the market or put into service before 2 August 2027 follow Art. 111(1) "
            "instead."
        ),
        SourceStatus.BINDING_LEVEL_1,
        "ai-act-amendment-2026-1744",
        AI_ACT_AMENDMENT_URL,
    ),
)
