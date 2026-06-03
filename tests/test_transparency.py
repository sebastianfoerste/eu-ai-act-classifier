from __future__ import annotations

from eu_ai_act_classifier import AnnexIII, RiskTier, SystemProfile, classify


def test_chatbot_is_limited_risk() -> None:
    report = classify(SystemProfile(name="x", interacts_with_natural_persons=True))
    assert report.risk_tier is RiskTier.LIMITED
    assert any(ob.article == "Art. 50(1) AIA" for ob in report.transparency_obligations)


def test_transparency_stacks_on_high_risk() -> None:
    profile = SystemProfile(
        name="x",
        annex_iii_area=AnnexIII.CREDITWORTHINESS,
        interacts_with_natural_persons=True,
    )
    report = classify(profile)
    assert report.risk_tier is RiskTier.HIGH  # high-risk dominates the tier
    assert any(ob.article == "Art. 50(1) AIA" for ob in report.transparency_obligations)
