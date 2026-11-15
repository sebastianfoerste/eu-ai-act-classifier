from __future__ import annotations

import json
from pathlib import Path

from eu_ai_act_classifier import AnnexIII, SourceStatus, SystemProfile, classify, render_report
from eu_ai_act_classifier.citations import (
    ADVISORY_SOURCE_RETRIEVED_ON,
    ART_50_CODE_OF_PRACTICE_URL,
    ART_50_GUIDELINES_URL,
    ART_50_SOURCES_RETRIEVED_ON,
    GPAI_PROVIDER_GUIDELINES_URL,
    source_manifest,
)
from eu_ai_act_classifier.models import ProhibitedPractice
from eu_ai_act_classifier.verify_sources import URLS

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
STALE = ("placeholder", "when published", "tracker")
# Wording the two Art. 50 sources carried until their pages and documents were read.
UNREAD = ("noch zu verifizieren", "primary-verified", "reported as", "search results")


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


def test_art_50_sources_are_two_separate_guidance_instruments_with_their_own_date() -> None:
    sources = {source.source_id: source for source in source_manifest()}
    guidelines = sources["art-50-guidelines"]
    code = sources["art-50-code-of-practice"]

    assert "transparency-guidance" not in sources
    for source in (guidelines, code):
        assert source.legal_status is SourceStatus.NONBINDING_GUIDANCE
        assert source.retrieved_on == ART_50_SOURCES_RETRIEVED_ON == "2026-11-14"
        assert source.retrieved_on != ADVISORY_SOURCE_RETRIEVED_ON
        text = f"{source.title} {source.citation_label} {source.implementation_note}".lower()
        for unread in UNREAD:
            assert unread not in text, (source.source_id, unread)
    assert guidelines.url == ART_50_GUIDELINES_URL
    assert code.url == ART_50_CODE_OF_PRACTICE_URL
    assert guidelines.url != code.url
    # The guidelines state their legal basis and, in points (146) and (147), call the code
    # one assessed as adequate pursuant to Art. 50(7); the code itself does not cite it.
    assert "Art. 96(1)(d)" in guidelines.implementation_note
    assert "C(2026) 7702 final" in guidelines.title
    assert "10 June 2026" in code.implementation_note
    assert "Art. 50(2)" in code.implementation_note and "Art. 50(4)" in code.implementation_note
    assert "does not cite" in code.implementation_note
    assert "points (146) and (147)" in code.implementation_note
    assert "classifier reads" not in code.implementation_note
    assert sources["gpai-provider-guidelines"].url == GPAI_PROVIDER_GUIDELINES_URL
    assert "printable" not in GPAI_PROVIDER_GUIDELINES_URL
    checked = set(URLS.values())
    for url in (ART_50_GUIDELINES_URL, ART_50_CODE_OF_PRACTICE_URL, GPAI_PROVIDER_GUIDELINES_URL):
        assert url in checked


def test_no_placeholder_wording_remains_for_art_50() -> None:
    report = classify(_example("deepfake_generator.json"), include_advisory=True)
    text = render_report(report) + json.dumps(report.model_dump(mode="json"))

    for stale in STALE:
        assert stale not in text.lower(), stale


def test_chatbot_gets_the_art_50_guidelines_but_not_the_marking_code() -> None:
    report = classify(
        SystemProfile(name="bot", interacts_with_natural_persons=True), include_advisory=True
    )
    source_ids = {note.source_id for note in report.advisory_notes}

    assert "art-50-guidelines" in source_ids
    assert "art-50-code-of-practice" not in source_ids


def test_emotion_or_biometric_use_gets_the_art_50_guidelines_but_not_the_marking_code() -> None:
    # The code of practice concerns the marking and labelling duties in Art. 50(2) and (4)
    # (Art. 50(7) AIA), not the Art. 50(3) duty to inform the persons exposed.
    report = classify(
        SystemProfile(name="emotion", deploys_emotion_or_biometric_categorisation=True),
        include_advisory=True,
    )
    source_ids = {note.source_id for note in report.advisory_notes}

    assert "art-50-guidelines" in source_ids
    assert "art-50-code-of-practice" not in source_ids


def test_synthetic_content_gets_both_art_50_instruments() -> None:
    for facts in ({"generates_synthetic_content": True}, {"generates_deepfakes": True}):
        report = classify(SystemProfile(name="gen", **facts), include_advisory=True)
        source_ids = {note.source_id for note in report.advisory_notes}
        assert {"art-50-guidelines", "art-50-code-of-practice"} <= source_ids


def test_art_50_notes_name_their_source_and_stay_nonbinding() -> None:
    report = classify(_example("deepfake_generator.json"), include_advisory=True)
    notes = {note.note_id: note for note in report.advisory_notes}
    guidelines = notes["guidance.transparency-guidelines"]
    code = notes["guidance.transparency-code-of-practice"]

    assert guidelines.source_id == "art-50-guidelines"
    assert guidelines.source_url == ART_50_GUIDELINES_URL
    assert "Art. 96(1)(d)" in guidelines.detail
    assert code.source_id == "art-50-code-of-practice"
    assert code.source_url == ART_50_CODE_OF_PRACTICE_URL
    assert "Art. 50(2)" in code.detail and "(4)" in code.detail
    for note in (guidelines, code):
        for unread in UNREAD:
            assert unread not in note.detail.lower(), (note.note_id, unread)
    assert all(
        note.source_status is SourceStatus.NONBINDING_GUIDANCE for note in report.advisory_notes
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
