from __future__ import annotations

from eu_ai_act_classifier import Disposition, Role, SystemProfile, classify

# A dated model: an undated one goes to review under Art. 111(3) AIA (C9), which the
# systemic-risk tests below do not exercise.
MODEL_DATE = "2026-01-15"


def test_gpai_below_threshold_not_systemic() -> None:
    profile = SystemProfile(
        name="x",
        is_gpai_model=True,
        training_flops=1e24,
        roles=[Role.GPAI_PROVIDER],
        gpai_model_placing_on_market_date=MODEL_DATE,
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
        gpai_model_placing_on_market_date=MODEL_DATE,
    )
    report = classify(profile)
    assert report.gpai_systemic
    assert report.disposition is Disposition.DETERMINED


def test_undated_model_goes_to_review_unless_the_assessment_date_settles_it() -> None:
    # C9: with no placing date, the Chapter V items apply from 2025-08-02 or, for a model
    # placed before that date, from 2027-08-02 (Art. 111(3) AIA).
    def report(assessment_date: str | None):
        return classify(
            SystemProfile(
                name="x",
                is_gpai_model=True,
                gpai_systemic_risk_designated=True,
                roles=[Role.GPAI_PROVIDER],
                assessment_date=assessment_date,
            )
        )

    for day in (None, "2025-08-02", "2027-08-01"):
        result = report(day)
        assert result.disposition is Disposition.REQUIRES_REVIEW, day
        assert any(q.startswith("Art. 111(3) AIA: neither") for q in result.open_questions)
    for day in ("2025-08-01", "2027-08-02"):
        assert report(day).disposition is Disposition.DETERMINED, day
