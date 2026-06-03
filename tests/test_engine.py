from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from eu_ai_act_classifier import (
    AnnexIII,
    RiskTier,
    SystemProfile,
    classify,
    render_report,
)


def test_minimal_is_the_default() -> None:
    assert classify(SystemProfile(name="x")).risk_tier is RiskTier.MINIMAL


def test_report_renders_citations() -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS))
    text = render_report(report)
    assert "HIGH-RISK" in text
    assert "Art. 9 AIA" in text
    assert "Annex III(5)(b) AIA" in text


def test_json_is_machine_readable() -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS))
    data = json.loads(report.model_dump_json())
    assert data["risk_tier"] == "high_risk"
    assert any(ob["article"] == "Art. 11 AIA" for ob in data["obligations"])


def test_extra_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        SystemProfile.model_validate({"name": "x", "unexpected_field": 1})
