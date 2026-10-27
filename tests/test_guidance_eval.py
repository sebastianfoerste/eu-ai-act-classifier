from __future__ import annotations

from eu_ai_act_classifier import SystemProfile, classify
from eu_ai_act_classifier.guidance_eval import (
    build_comparison_report,
    evaluate_guidance_examples,
    load_guidance_examples,
)


def test_guidance_examples_match_expected_results() -> None:
    results = evaluate_guidance_examples()

    assert results
    assert all(result["matches"] for result in results)


def test_compliance_checker_comparison_is_nonbinding_review_evidence() -> None:
    report = build_comparison_report()

    assert report["compliance_checker_comparison"]
    assert "nonbinding" in report["notice"]
    assert all(
        item["checker_status"] == "nonbinding_beta" and item["manual_review_note"]
        for item in report["compliance_checker_comparison"]
    )


def test_machinery_example_is_a_section_b_product() -> None:
    # Regulation (EU) 2026/1744 moved machinery (Regulation (EU) 2023/1230) to Annex I,
    # Section B, so only the Art. 2(2) provisions apply to the safe-stop system.
    (example,) = [
        example
        for example in load_guidance_examples()
        if example["id"] == "draft-guidance-machinery-safety-stop"
    ]
    report = classify(SystemProfile.model_validate(example["profile"]))

    assert report.risk_tier.value == example["expected"]["risk_tier"]
    assert [ob.article for ob in report.obligations] == ["Art. 2(2) AIA"]
