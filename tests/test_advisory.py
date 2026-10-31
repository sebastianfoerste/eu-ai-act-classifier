from __future__ import annotations

import json
from pathlib import Path

from eu_ai_act_classifier import AnnexIII, SourceStatus, SystemProfile, classify, render_report
from eu_ai_act_classifier.citations import (
    ADVISORY_SOURCE_RETRIEVED_ON,
    AI_CONTENT_CODE_URL,
    GPAI_PROVIDER_GUIDELINES_URL,
    TRANSPARENCY_GUIDELINES_URL,
    TRANSPARENCY_SOURCE_RETRIEVED_ON,
    source_manifest,
)
from eu_ai_act_classifier.models import ProhibitedPractice
from eu_ai_act_classifier.verify_sources import URLS

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
STALE = ("placeholder", "when published", "tracker")


def test_advisory_overlay_is_opt_in() -> None:
    profile = SystemProfile(name="cv", annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION)

    without = classify(profile)
    with_overlay = classify(profile, include_advisory=True)

    assert without.advisory_notes == []
    assert any(
        note.source_id == "draft-high-risk-guidelines-2026" for note in with_overlay.advisory_notes
    )


def _example(name: str) -> SystemProfile:
    return SystemProfile.model_validate_json((EXAMPLES / name).read_text(encoding="utf-8"))


def test_manifest_lists_the_final_art_50_guidelines_and_the_code_with_their_own_date() -> None:
    sources = {source.source_id: source for source in source_manifest()}
    guidelines = sources["transparency-guidelines-2026"]
    code = sources["ai-content-code-of-practice"]

    assert "transparency-guidance" not in sources
    for source in (guidelines, code):
        assert source.legal_status is SourceStatus.NONBINDING_GUIDANCE
        assert source.retrieved_on == TRANSPARENCY_SOURCE_RETRIEVED_ON == "2026-10-31"
        assert source.retrieved_on != ADVISORY_SOURCE_RETRIEVED_ON
    assert guidelines.url == TRANSPARENCY_GUIDELINES_URL
    assert "20 July 2026" in guidelines.implementation_note
    assert code.url == AI_CONTENT_CODE_URL
    assert "10 June 2026" in code.implementation_note
    assert "Art. 50(2)" in code.implementation_note and "Art. 50(4)" in code.implementation_note
    assert sources["gpai-provider-guidelines"].url == GPAI_PROVIDER_GUIDELINES_URL
    assert "printable" not in GPAI_PROVIDER_GUIDELINES_URL
    assert {TRANSPARENCY_GUIDELINES_URL, AI_CONTENT_CODE_URL, GPAI_PROVIDER_GUIDELINES_URL} <= set(
        URLS.values()
    )


def test_no_placeholder_wording_remains_for_art_50() -> None:
    report = classify(_example("deepfake_generator.json"), include_advisory=True)
    text = render_report(report) + json.dumps(report.model_dump(mode="json"))

    for stale in STALE:
        assert stale not in text.lower(), stale


def test_art_50_triggers_add_the_guidelines_and_synthetic_content_adds_the_code() -> None:
    deepfake = classify(_example("deepfake_generator.json"), include_advisory=True)
    chatbot = classify(_example("support_chatbot.json"), include_advisory=True)

    deepfake_ids = [note.note_id for note in deepfake.advisory_notes]
    chatbot_ids = [note.note_id for note in chatbot.advisory_notes]
    assert "guidance.transparency" in deepfake_ids and "guidance.ai-content-code" in deepfake_ids
    assert "guidance.transparency" in chatbot_ids and "guidance.ai-content-code" not in chatbot_ids
    guidelines = next(n for n in deepfake.advisory_notes if n.note_id == "guidance.transparency")
    code = next(n for n in deepfake.advisory_notes if n.note_id == "guidance.ai-content-code")
    assert guidelines.source_id == "transparency-guidelines-2026"
    assert guidelines.source_url == TRANSPARENCY_GUIDELINES_URL
    assert "20 July 2026" in guidelines.detail
    assert code.source_id == "ai-content-code-of-practice"
    assert code.source_url == AI_CONTENT_CODE_URL
    assert "Art. 50(2)" in code.detail and "Art. 50(4)" in code.detail
    assert all(
        note.source_status is SourceStatus.NONBINDING_GUIDANCE for note in deepfake.advisory_notes
    )


def test_prohibited_practices_note_still_dates_the_guidance_before_the_new_bans() -> None:
    report = classify(
        SystemProfile(
            name="x", prohibited_practices=[ProhibitedPractice.NON_CONSENSUAL_INTIMATE_IMAGERY]
        ),
        include_advisory=True,
    )
    (note,) = [n for n in report.advisory_notes if n.note_id == "guidance.prohibited-practices"]

    assert ADVISORY_SOURCE_RETRIEVED_ON == "2026-06-18"
    assert f"retrieved on {ADVISORY_SOURCE_RETRIEVED_ON}, predates" in note.detail
