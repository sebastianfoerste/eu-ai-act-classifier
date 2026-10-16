from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from eu_ai_act_classifier import AnnexIII, Disposition, RiskTier, SystemProfile, classify
from eu_ai_act_classifier.catalog import ANNEX_III

ROOT = Path(__file__).resolve().parent.parent


def _builder():
    spec = importlib.util.spec_from_file_location(
        "build_coverage", ROOT / "scripts" / "build_coverage.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_coverage_doc_is_up_to_date() -> None:
    expected = _builder().build()
    actual = (ROOT / "docs" / "coverage.md").read_text(encoding="utf-8")
    assert actual == expected, "run: python scripts/build_coverage.py"


def test_catalog_covers_every_annex_iii_point() -> None:
    assert set(ANNEX_III) == set(AnnexIII)


@pytest.mark.parametrize("area", list(AnnexIII), ids=lambda a: a.value)
def test_every_annex_iii_point_is_high_risk_on_a_minimal_profile(area: AnnexIII) -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=area))
    assert report.risk_tier is RiskTier.HIGH
    expected = Disposition.REQUIRES_REVIEW if area is AnnexIII.UNSURE else Disposition.DETERMINED
    assert report.disposition is expected
