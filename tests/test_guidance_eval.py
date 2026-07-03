from __future__ import annotations

from eu_ai_act_classifier.guidance_eval import build_comparison_report, evaluate_guidance_examples


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
