from __future__ import annotations

from pathlib import Path

import pytest

from eu_ai_act_classifier import Disposition, RiskTier, SourceStatus, SystemProfile, classify

EXAMPLES = Path("examples")


def _report(filename: str):
    profile = SystemProfile.model_validate_json((EXAMPLES / filename).read_text(encoding="utf-8"))
    return classify(profile, include_advisory=True)


@pytest.mark.parametrize(
    ("filename", "tier", "disposition"),
    [
        ("social_scoring.json", RiskTier.PROHIBITED, Disposition.DETERMINED),
        ("credit_scoring.json", RiskTier.HIGH, Disposition.DETERMINED),
        ("foundation_model_systemic.json", RiskTier.MINIMAL, Disposition.DETERMINED),
        ("deepfake_generator.json", RiskTier.LIMITED, Disposition.DETERMINED),
        ("ambiguous_use_case.json", RiskTier.HIGH, Disposition.REQUIRES_REVIEW),
    ],
)
def test_required_representative_dispositions(
    filename: str, tier: RiskTier, disposition: Disposition
) -> None:
    report = _report(filename)

    assert report.risk_tier is tier
    assert report.disposition is disposition


def test_every_report_separates_binding_provisional_and_nonbinding_sources() -> None:
    report = _report("credit_scoring.json")
    timeline_statuses = {item.source_status for item in report.timeline}
    manifest_statuses = {source.legal_status for source in report.source_manifest}
    advisory_statuses = {note.source_status for note in report.advisory_notes}

    assert SourceStatus.BINDING_LEVEL_1 in timeline_statuses
    assert SourceStatus.PROVISIONAL_POLITICAL_AGREEMENT in timeline_statuses
    assert SourceStatus.NONBINDING_GUIDANCE in manifest_statuses
    assert advisory_statuses == {SourceStatus.NONBINDING_GUIDANCE}
