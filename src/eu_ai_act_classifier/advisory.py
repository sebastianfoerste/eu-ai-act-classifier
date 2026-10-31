"""Optional advisory overlay from nonbinding Commission materials."""

from __future__ import annotations

from datetime import date

from .catalog import LATER_PROHIBITIONS
from .citations import (
    ADVISORY_SOURCE_RETRIEVED_ON,
    AI_CONTENT_CODE_URL,
    AI_SYSTEM_DEFINITION_GUIDELINES_URL,
    GPAI_CODE_URL,
    GPAI_PROVIDER_GUIDELINES_URL,
    HIGH_RISK_GUIDELINES_URL,
    PROHIBITED_GUIDELINES_URL,
    TRANSPARENCY_GUIDELINES_URL,
)
from .models import AdvisoryNote, SystemProfile

# Regulation (EU) 2026/1744, which inserted Art. 5(1)(ba) and (bb), was published in the
# Official Journal on 24 July 2026 (OJ L, 2026/1744, 24.7.2026).
_AMENDMENT_PUBLISHED_ON = "2026-07-24"


def _later_prohibitions_sentence() -> str:
    """Whether the guidance predates the new bans follows from its retrieval date, which
    `verify_sources --update` may move, so the sentence is worked out from it."""

    if date.fromisoformat(ADVISORY_SOURCE_RETRIEVED_ON) < date.fromisoformat(
        _AMENDMENT_PUBLISHED_ON
    ):
        return (
            f" The linked guidance, retrieved on {ADVISORY_SOURCE_RETRIEVED_ON}, predates "
            "Art. 5(1)(ba) and (bb), inserted by Regulation (EU) 2026/1744, so confirm whether "
            "a later version covers them."
        )
    return (
        f" Confirm whether the linked guidance, retrieved on {ADVISORY_SOURCE_RETRIEVED_ON}, "
        "covers Art. 5(1)(ba) and (bb), inserted by Regulation (EU) 2026/1744."
    )


def build_advisory_notes(profile: SystemProfile) -> list[AdvisoryNote]:
    notes = [
        AdvisoryNote(
            note_id="guidance.ai-system-definition",
            title="AI-system-definition guidance",
            detail=(
                "Use the Commission AI-system-definition guidelines to support the scope "
                "analysis. This advisory note does not determine legal scope."
            ),
            source_id="ai-system-definition-guidelines",
            source_url=AI_SYSTEM_DEFINITION_GUIDELINES_URL,
        )
    ]

    if profile.prohibited_practices:
        notes.append(
            AdvisoryNote(
                note_id="guidance.prohibited-practices",
                title="Prohibited-practices guidance",
                detail=(
                    "Commission prohibited-practices guidance may help review the asserted "
                    "Art. 5 trigger and examples."
                    + (
                        _later_prohibitions_sentence()
                        if set(profile.prohibited_practices) & set(LATER_PROHIBITIONS)
                        else ""
                    )
                ),
                source_id="prohibited-practices-guidelines",
                source_url=PROHIBITED_GUIDELINES_URL,
            )
        )

    if profile.annex_i_safety_component or profile.annex_iii_area is not None:
        notes.append(
            AdvisoryNote(
                note_id="guidance.high-risk-classification",
                title="Draft high-risk classification guidance",
                detail=(
                    "Draft high-risk classification guidance can support the intended-purpose, "
                    "Annex I, Annex III and Art. 6(3) review."
                ),
                source_id="draft-high-risk-guidelines-2026",
                source_url=HIGH_RISK_GUIDELINES_URL,
            )
        )

    if profile.is_gpai_model:
        notes.extend(
            [
                AdvisoryNote(
                    note_id="guidance.gpai-code",
                    title="GPAI Code of Practice",
                    detail=(
                        "The GPAI Code of Practice is a voluntary tool for transparency, "
                        "copyright, safety and security obligations."
                    ),
                    source_id="gpai-code-of-practice",
                    source_url=GPAI_CODE_URL,
                ),
                AdvisoryNote(
                    note_id="guidance.gpai-provider",
                    title="GPAI provider guidelines",
                    detail=(
                        "GPAI provider guidelines support scope and compliance analysis for "
                        "general-purpose AI model providers."
                    ),
                    source_id="gpai-provider-guidelines",
                    source_url=GPAI_PROVIDER_GUIDELINES_URL,
                ),
            ]
        )

    if (
        profile.interacts_with_natural_persons
        or profile.generates_synthetic_content
        or profile.deploys_emotion_or_biometric_categorisation
        or profile.generates_deepfakes
    ):
        notes.append(
            AdvisoryNote(
                note_id="guidance.transparency",
                title="Art. 50 transparency guidelines",
                detail=(
                    "The Commission guidelines on the transparency obligations under Art. 50 "
                    "AIA (published 20 July 2026) are a nonbinding aid for the Art. 50(1) to "
                    "(4) review. They change no obligation."
                ),
                source_id="transparency-guidelines-2026",
                source_url=TRANSPARENCY_GUIDELINES_URL,
            )
        )

    if profile.generates_synthetic_content or profile.generates_deepfakes:
        # The Code covers the Art. 50(2) marking and detection and the Art. 50(4)
        # labelling duties, not Art. 50(1) and (3).
        notes.append(
            AdvisoryNote(
                note_id="guidance.ai-content-code",
                title="Code of Practice on AI-generated content",
                detail=(
                    "The final Code of Practice on marking and labelling of AI-generated "
                    "content (published 10 June 2026) is a voluntary, nonbinding aid for the "
                    "Art. 50(2) marking and detection and Art. 50(4) deepfake disclosure "
                    "duties. The Commission's page states that the Commission and the Board "
                    "confirmed it as an adequate voluntary tool."
                ),
                source_id="ai-content-code-of-practice",
                source_url=AI_CONTENT_CODE_URL,
            )
        )

    return notes
