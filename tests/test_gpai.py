from __future__ import annotations

from eu_ai_act_classifier import Disposition, Role, SystemProfile, classify


def test_gpai_below_threshold_not_systemic() -> None:
    profile = SystemProfile(
        name="x", is_gpai_model=True, training_flops=1e24, roles=[Role.GPAI_PROVIDER]
    )
    report = classify(profile)
    assert report.is_gpai and not report.gpai_systemic
    assert report.disposition is Disposition.DETERMINED
    articles = {ob.article for ob in report.obligations}
    assert "Art. 53(1)(a) AIA" in articles
    assert not any(a.startswith("Art. 55") for a in articles)


def test_gpai_above_threshold_is_systemic() -> None:
    profile = SystemProfile(
        name="x", is_gpai_model=True, training_flops=2e25, roles=[Role.GPAI_PROVIDER]
    )
    report = classify(profile)
    assert report.gpai_systemic
    assert any(ob.article.startswith("Art. 55") for ob in report.obligations)


def test_gpai_unknown_compute_requires_review() -> None:
    profile = SystemProfile(name="x", is_gpai_model=True, roles=[Role.GPAI_PROVIDER])
    assert classify(profile).disposition is Disposition.REQUIRES_REVIEW


def test_gpai_commission_designation_is_systemic() -> None:
    profile = SystemProfile(
        name="x",
        is_gpai_model=True,
        gpai_systemic_risk_designated=True,
        roles=[Role.GPAI_PROVIDER],
    )
    report = classify(profile)
    assert report.gpai_systemic
    assert report.disposition is Disposition.DETERMINED
