"""Single source of truth for EU AI Act citations.

All references are to Regulation (EU) 2024/1689 (Artificial Intelligence Act),
OJ L, 2024/1689, 12.7.2024 ("AIA"). Pinpoint citations follow the German
convention: ``Art. <article> Abs. <paragraph> lit. <letter> AIA``, rendered
here in the shorter ``Art. 5(1)(f) AIA`` form for readability.

A citation carries a ``verified`` flag. ``verified=False`` means the exact
sub-point lettering is pending confirmation against the consolidated EUR-Lex
text. The two Annex III areas (law enforcement, migration) were renumbered
between trilogue drafts, so their sub-point letters are flagged rather than
asserted. The engine propagates this flag into its output so a reviewing
lawyer sees precisely which pinpoints are not yet locked, instead of trusting
a citation that was guessed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import RegulatorySource, SourceStatus

REGULATION = (
    "Regulation (EU) 2024/1689 of the European Parliament and of the Council "
    "of 13 June 2024 (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024"
)
SHORT = "AIA"
AI_ACT_URL = "https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng"
AI_OMNIBUS_COMMISSION_URL = (
    "https://digital-strategy.ec.europa.eu/en/news/"
    "eu-agrees-simplify-ai-rules-boost-innovation-and-ban-nudification-apps-protect-citizens"
)
AI_OMNIBUS_COUNCIL_URL = (
    "https://www.consilium.europa.eu/en/press/press-releases/2026/05/07/"
    "artificial-intelligence-council-and-parliament-agree-to-simplify-and-streamline-rules/pdf/"
)
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


SOURCE_RETRIEVED_ON = "2026-06-17"


def source_manifest() -> list[RegulatorySource]:
    """Versioned source registry used by reports and draft work products."""

    return [
        RegulatorySource(
            source_id="ai-act-2024-1689",
            title="Regulation (EU) 2024/1689, Artificial Intelligence Act",
            legal_status=SourceStatus.BINDING_LEVEL_1,
            url=AI_ACT_URL,
            retrieved_on=SOURCE_RETRIEVED_ON,
            citation_label="Regulation (EU) 2024/1689",
            implementation_note="Binding Level 1 source for classifications and obligations.",
        ),
        RegulatorySource(
            source_id="ai-omnibus-political-agreement-2026",
            title="AI Omnibus provisional political agreement",
            legal_status=SourceStatus.PROVISIONAL_POLITICAL_AGREEMENT,
            url=AI_OMNIBUS_COUNCIL_URL,
            retrieved_on=SOURCE_RETRIEVED_ON,
            citation_label="Council and Parliament provisional agreement, 7 May 2026",
            implementation_note=(
                "Provisional context only until formal adoption and Official Journal publication."
            ),
        ),
        RegulatorySource(
            source_id="ai-act-service-desk",
            title="AI Act Service Desk",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=AI_ACT_SERVICE_DESK_URL,
            retrieved_on=SOURCE_RETRIEVED_ON,
            citation_label="AI Act Service Desk",
            implementation_note="Official explanatory and navigation layer, not legal advice.",
        ),
        RegulatorySource(
            source_id="prohibited-practices-guidelines",
            title="Commission guidelines on prohibited AI practices",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=PROHIBITED_GUIDELINES_URL,
            retrieved_on=SOURCE_RETRIEVED_ON,
            citation_label="Commission prohibited-practices guidelines",
            implementation_note="Nonbinding Commission interpretation and practical examples.",
        ),
        RegulatorySource(
            source_id="ai-system-definition-guidelines",
            title="Commission guidelines on the AI system definition",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=AI_SYSTEM_DEFINITION_GUIDELINES_URL,
            retrieved_on=SOURCE_RETRIEVED_ON,
            citation_label="Commission AI-system-definition guidelines",
            implementation_note="Nonbinding support for scope assessment.",
        ),
        RegulatorySource(
            source_id="draft-high-risk-guidelines-2026",
            title="Draft Commission guidelines on high-risk AI classification",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=HIGH_RISK_GUIDELINES_URL,
            retrieved_on=SOURCE_RETRIEVED_ON,
            citation_label="Draft high-risk classification guidelines",
            implementation_note="Draft guidance used as advisory overlay and eval context.",
        ),
        RegulatorySource(
            source_id="gpai-code-of-practice",
            title="General-Purpose AI Code of Practice",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=GPAI_CODE_URL,
            retrieved_on=SOURCE_RETRIEVED_ON,
            citation_label="GPAI Code of Practice",
            implementation_note="Voluntary tool for GPAI obligations, separate from Level 1 logic.",
        ),
        RegulatorySource(
            source_id="gpai-provider-guidelines",
            title="Guidelines for providers of general-purpose AI models",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=GPAI_PROVIDER_GUIDELINES_URL,
            retrieved_on=SOURCE_RETRIEVED_ON,
            citation_label="GPAI provider guidelines",
            implementation_note="Nonbinding scope and compliance support for GPAI model providers.",
        ),
        RegulatorySource(
            source_id="transparency-guidance",
            title="Transparency guidance status tracker",
            legal_status=SourceStatus.NONBINDING_GUIDANCE,
            url=TRANSPARENCY_GUIDANCE_URL,
            retrieved_on=SOURCE_RETRIEVED_ON,
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
        "Chapters I-II, incl. Art. 5 (prohibited practices)",
        "2025-02-02",
        "Prohibitions apply from 2 February 2025 (Art. 113(a) AIA).",
    ),
    ApplicationDate(
        "Chapter V (general-purpose AI models)",
        "2025-08-02",
        "GPAI obligations apply from 2 August 2025 (Art. 113(b) AIA).",
    ),
    ApplicationDate(
        "General application, incl. Annex III high-risk systems",
        "2026-08-02",
        "Most obligations apply from 2 August 2026 (Art. 113 AIA).",
    ),
    ApplicationDate(
        "Art. 6(1) / Annex I high-risk (product-safety route)",
        "2027-08-02",
        "Annex I high-risk obligations apply from 2 August 2027 (Art. 113(c) AIA).",
    ),
)


PROVISIONAL_APPLICATION_DATES: tuple[ApplicationDate, ...] = (
    ApplicationDate(
        "AI Omnibus: Annex III high-risk systems",
        "2027-12-02",
        (
            "Provisional political agreement points to 2 December 2027 for stand-alone "
            "Annex III high-risk systems. This is not binding until formal adoption and "
            "Official Journal publication."
        ),
        SourceStatus.PROVISIONAL_POLITICAL_AGREEMENT,
        "ai-omnibus-political-agreement-2026",
        AI_OMNIBUS_COUNCIL_URL,
    ),
    ApplicationDate(
        "AI Omnibus: product-embedded high-risk systems",
        "2028-08-02",
        (
            "Provisional political agreement points to 2 August 2028 for high-risk AI "
            "systems embedded in products."
        ),
        SourceStatus.PROVISIONAL_POLITICAL_AGREEMENT,
        "ai-omnibus-political-agreement-2026",
        AI_OMNIBUS_COUNCIL_URL,
    ),
)
