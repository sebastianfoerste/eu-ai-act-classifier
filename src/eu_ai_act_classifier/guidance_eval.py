"""Guidance-example evaluation harness.

The corpus is nonbinding evidence. It checks whether Commission-derived examples
still line up with the deterministic classifier and highlights manual-review
differences.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .engine import classify
from .models import SystemProfile

REPO = Path(__file__).resolve().parents[2]
GUIDANCE_EXAMPLES = REPO / "examples" / "guidance" / "commission_guidance_examples.json"
CHECKER_COMPARISON = REPO / "examples" / "guidance" / "compliance_checker_comparison.json"


def load_guidance_examples(path: Path = GUIDANCE_EXAMPLES) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_checker_comparison(path: Path = CHECKER_COMPARISON) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_guidance_examples() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for example in load_guidance_examples():
        report = classify(SystemProfile.model_validate(example["profile"]))
        expected = example["expected"]
        results.append(
            {
                "id": example["id"],
                "source_status": example["source_status"],
                "authority_status": example["authority_status"],
                "expected_risk_tier": expected["risk_tier"],
                "actual_risk_tier": report.risk_tier.value,
                "expected_disposition": expected["disposition"],
                "actual_disposition": report.disposition.value,
                "matches": (
                    expected["risk_tier"] == report.risk_tier.value
                    and expected["disposition"] == report.disposition.value
                ),
            }
        )
    return results


def build_comparison_report() -> dict[str, Any]:
    return {
        "guidance_results": evaluate_guidance_examples(),
        "compliance_checker_comparison": load_checker_comparison(),
        "notice": (
            "Commission-derived examples and beta checker comparisons are nonbinding "
            "evidence for review. They do not override Regulation (EU) 2024/1689."
        ),
    }


def main() -> int:
    print(json.dumps(build_comparison_report(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
