from __future__ import annotations

from eu_ai_act_classifier import AnnexIII, SystemProfile, classify


def test_advisory_overlay_is_opt_in() -> None:
    profile = SystemProfile(name="cv", annex_iii_area=AnnexIII.EMPLOYMENT_SELECTION)

    without = classify(profile)
    with_overlay = classify(profile, include_advisory=True)

    assert without.advisory_notes == []
    assert any(
        note.source_id == "draft-high-risk-guidelines-2026" for note in with_overlay.advisory_notes
    )
