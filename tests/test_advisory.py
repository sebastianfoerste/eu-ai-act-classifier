from __future__ import annotations

from eu_ai_act_classifier import AnnexIII, SourceStatus, SystemProfile, classify


def test_advisory_overlay_is_opt_in() -> None:
    profile = SystemProfile(name="cv", annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION)

    without = classify(profile)
    with_overlay = classify(profile, include_advisory=True)

    assert without.advisory_notes == []
    assert any(
        note.source_id == "draft-high-risk-guidelines-2026" for note in with_overlay.advisory_notes
    )


def test_art_50_sources_are_two_separate_unverified_guidance_instruments() -> None:
    sources = {
        source.source_id: source for source in classify(SystemProfile(name="x")).source_manifest
    }

    assert "transparency-guidance" not in sources
    for source_id in ("art-50-code-of-practice", "art-50-guidelines"):
        source = sources[source_id]
        assert source.legal_status is SourceStatus.NONBINDING_GUIDANCE
        assert source.citation_label.endswith("[noch zu verifizieren]")
        assert "Not primary-verified" in source.implementation_note
        assert "Placeholder" not in source.implementation_note
    assert sources["art-50-code-of-practice"].url != sources["art-50-guidelines"].url


def test_chatbot_gets_the_art_50_guidelines_but_not_the_marking_code() -> None:
    report = classify(
        SystemProfile(name="bot", interacts_with_natural_persons=True), include_advisory=True
    )
    source_ids = {note.source_id for note in report.advisory_notes}

    assert "art-50-guidelines" in source_ids
    assert "art-50-code-of-practice" not in source_ids


def test_synthetic_content_gets_both_art_50_instruments() -> None:
    for facts in ({"generates_synthetic_content": True}, {"generates_deepfakes": True}):
        report = classify(SystemProfile(name="gen", **facts), include_advisory=True)
        source_ids = {note.source_id for note in report.advisory_notes}
        assert {"art-50-guidelines", "art-50-code-of-practice"} <= source_ids
