from __future__ import annotations

import pytest

from eu_ai_act_classifier import Disposition, ExcludedUse, Role, SystemProfile, classify


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


# AIA-07: the improvement prompt expects an Art. 54 representative item (or an open
# question) for a GPAI provider established outside the EU, an Art. 52(1) notification
# item where systemic risk rests on the compute presumption, and an open question or
# note citing the Chapter V carve-outs for free and open-source models (Art. 53(2) and
# Art. 54(6)) with their systemic-risk exception. The change is blocked until those
# provisions are read on EUR-Lex and recorded in docs/REGULATORY_CLAIM_LEDGER.md. The
# tests encode the outcome the prompt states, not a reading of the provisions. The
# designation case (no notification after a Commission designation) waits for the
# reading and has no test here. Remove this marker with the engine change.
GPAI_NOTIFICATION_AND_REPRESENTATIVE = pytest.mark.xfail(
    strict=True,
    reason="AIA-07 is blocked on the EUR-Lex reading of Arts. 52(1), 53(2), 54(1) and 54(6) AIA",
)


def _gpai_provider(**facts: object) -> SystemProfile:
    return SystemProfile(name="x", is_gpai_model=True, roles=[Role.GPAI_PROVIDER], **facts)


def _texts(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _texts(item)]
    if isinstance(value, list):
        return [text for item in value for text in _texts(item)]
    return []


@GPAI_NOTIFICATION_AND_REPRESENTATIVE
@pytest.mark.parametrize("has_representative", [None, False, True])
def test_gpai_provider_outside_the_eu_lists_the_representative_duty(
    has_representative: bool | None,
) -> None:
    report = classify(
        _gpai_provider(
            training_flops=2e25,
            provider_established_outside_eu=True,
            has_authorised_representative=has_representative,
        )
    )

    listed = any(
        ob.article.startswith("Art. 54") and ob.applies_to is Role.GPAI_PROVIDER
        for ob in report.obligations
    )
    asked = any("Art. 54" in question for question in report.open_questions)
    assert listed or asked


def test_gpai_provider_in_the_eu_gets_no_representative_item() -> None:
    report = classify(_gpai_provider(training_flops=1e24))

    assert not any(ob.article.startswith("Art. 54") for ob in report.obligations)
    assert not any("Art. 54" in question for question in report.open_questions)


@GPAI_NOTIFICATION_AND_REPRESENTATIVE
def test_compute_presumption_lists_the_notification_duty() -> None:
    report = classify(_gpai_provider(training_flops=2e25))

    assert report.gpai_systemic
    assert any(
        ob.article.startswith("Art. 52(1)") and ob.applies_to is Role.GPAI_PROVIDER
        for ob in report.obligations
    )


@GPAI_NOTIFICATION_AND_REPRESENTATIVE
def test_open_source_gpai_model_cites_the_chapter_v_carve_outs() -> None:
    report = classify(
        _gpai_provider(training_flops=1e24, excluded_use_flags=[ExcludedUse.FREE_OPEN_SOURCE])
    )

    cited = [
        text
        for text in _texts(report.model_dump(mode="json"))
        if "Art. 53(2)" in text and "Art. 54(6)" in text
    ]
    assert cited
    assert all("systemic" in text for text in cited)
