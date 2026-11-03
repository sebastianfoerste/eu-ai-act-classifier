"""The CLI exit codes that make `--strict` a CI gate.

`--strict` exits 1 for a prohibited report and for a `requires_review` report, and 0
otherwise. Without the flag every classified profile exits 0. The parametrisation is
the one #58 adds to `tests/test_cli.py`, which reaches main only with draft PR #55.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eu_ai_act_classifier import Disposition, RiskTier, SystemProfile, classify
from eu_ai_act_classifier.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize(
    ("example", "code"),
    [
        pytest.param("social_scoring.json", 1, id="prohibited"),
        pytest.param("ambiguous_use_case.json", 1, id="requires-review"),
        pytest.param("credit_scoring.json", 0, id="determined"),
        pytest.param("spam_filter.json", 0, id="minimal"),
    ],
)
def test_strict_exit_codes(example: str, code: int, capsys) -> None:
    assert main([str(EXAMPLES / example), "--strict"]) == code
    assert main([str(EXAMPLES / example)]) == 0
    capsys.readouterr()


@pytest.mark.parametrize(
    ("example", "tier", "disposition"),
    [
        ("social_scoring.json", RiskTier.PROHIBITED, Disposition.DETERMINED),
        ("ambiguous_use_case.json", RiskTier.HIGH, Disposition.REQUIRES_REVIEW),
    ],
)
def test_each_strict_exit_1_case_meets_one_condition_only(
    example: str, tier: RiskTier, disposition: Disposition
) -> None:
    # The prohibited case is determined and the review case is not prohibited, so each
    # half of the --strict condition gets its own exit 1.
    profile = SystemProfile.model_validate_json((EXAMPLES / example).read_text(encoding="utf-8"))
    report = classify(profile)

    assert (report.risk_tier, report.disposition) == (tier, disposition)
