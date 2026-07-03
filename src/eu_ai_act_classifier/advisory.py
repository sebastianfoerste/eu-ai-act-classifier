"""Optional advisory overlay from nonbinding Commission materials."""

from __future__ import annotations

from .citations import (
    AI_SYSTEM_DEFINITION_GUIDELINES_URL,
    GPAI_CODE_URL,
    GPAI_PROVIDER_GUIDELINES_URL,
    HIGH_RISK_GUIDELINES_URL,
    PROHIBITED_GUIDELINES_URL,
    TRANSPARENCY_GUIDANCE_URL,
)
from .models import AdvisoryNote, SystemProfile


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
                title="Transparency guidance tracker",
                detail=(
                    "Track final Art. 50 transparency guidance and marking or labelling "
                    "support tools when published."
                ),
                source_id="transparency-guidance",
                source_url=TRANSPARENCY_GUIDANCE_URL,
            )
        )

    return notes
