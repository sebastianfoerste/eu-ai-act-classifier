from __future__ import annotations

import json
from pathlib import Path

from eu_ai_act_classifier import SystemProfile, classify


def _golden_payload() -> dict[str, object]:
    profile = SystemProfile.model_validate_json(
        Path("examples/credit_scoring.json").read_text(encoding="utf-8")
    )
    report = classify(profile)
    return {
        "system": report.system,
        "risk_tier": report.risk_tier.value,
        "disposition": report.disposition.value,
        "scope_status": report.scope.status.value,
        "finding_citations": [finding.citation for finding in report.findings],
        "obligation_articles": [obligation.article for obligation in report.obligations],
        "timeline_source_statuses": sorted(
            {item.source_status.value for item in report.timeline}
        ),
        "source_manifest_statuses": sorted(
            {source.legal_status.value for source in report.source_manifest}
        ),
    }


def test_credit_scoring_json_golden() -> None:
    expected = json.loads(
        Path("tests/goldens/credit_scoring.cli-golden.json").read_text(encoding="utf-8")
    )

    assert _golden_payload() == expected
