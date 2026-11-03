"""Golden reports: every example profile keeps its locked classification summary.

Each `examples/<name>.json` profile has `tests/goldens/<name>.cli-golden.json`. Paths
resolve from the repository root, so the test passes from any working directory.

A failure means a rule change moved an example. Check each difference against the
change before accepting it, then rewrite the goldens with
`uv run python tests/test_golden_json.py` and review the diff.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eu_ai_act_classifier import SystemProfile, classify

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
GOLDENS = ROOT / "tests" / "goldens"
# Not a SystemProfile: the classification packet the examples README describes.
NOT_A_PROFILE = {"classification-packet.json"}
GOLDEN_SUFFIX = ".cli-golden.json"


def _examples() -> list[str]:
    return sorted(p.stem for p in EXAMPLES.glob("*.json") if p.name not in NOT_A_PROFILE)


def _golden_payload(example: str) -> dict[str, object]:
    profile = SystemProfile.model_validate_json(
        (EXAMPLES / f"{example}.json").read_text(encoding="utf-8")
    )
    report = classify(profile)
    return {
        "system": report.system,
        "risk_tier": report.risk_tier.value,
        "disposition": report.disposition.value,
        "scope_status": report.scope.status.value,
        "finding_citations": [finding.citation for finding in report.findings],
        "obligation_articles": [obligation.article for obligation in report.obligations],
        "timeline_source_statuses": sorted({item.source_status.value for item in report.timeline}),
        "source_manifest_statuses": sorted(
            {source.legal_status.value for source in report.source_manifest}
        ),
    }


def _golden_path(example: str) -> Path:
    return GOLDENS / f"{example}{GOLDEN_SUFFIX}"


def test_every_example_has_a_golden_and_every_golden_an_example() -> None:
    goldens = sorted(p.name.removesuffix(GOLDEN_SUFFIX) for p in GOLDENS.glob(f"*{GOLDEN_SUFFIX}"))

    assert _examples(), f"no example profiles under {EXAMPLES}"
    assert goldens == _examples()


@pytest.mark.parametrize("example", _examples())
def test_example_json_golden(example: str) -> None:
    expected = json.loads(_golden_path(example).read_text(encoding="utf-8"))

    assert _golden_payload(example) == expected


def _write_goldens() -> None:
    for example in _examples():
        text = json.dumps(_golden_payload(example), indent=2, ensure_ascii=False) + "\n"
        _golden_path(example).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    _write_goldens()
