"""Precision notes verified against Regulation (EU) 2026/1744: the recital 39 date rule,
the Art. 75(1a) reporting route, the Art. 72(3) guidance deadline and the amended footer."""

from __future__ import annotations

import re
from pathlib import Path

from eu_ai_act_classifier import AnnexIII, SystemProfile, classify, render_report
from eu_ai_act_classifier.citations import AI_ACT_URL, REGULATION
from eu_ai_act_classifier.intake import QUESTIONS
from eu_ai_act_classifier.schemas import schema

ROOT = Path(__file__).resolve().parents[1]
RECITAL = "recital 39 of Regulation (EU) 2026/1744"


def test_market_date_fields_describe_the_first_unit_rule() -> None:
    props = schema("profile")["properties"]

    for field in ("placing_on_market_date", "putting_into_service_date"):
        description = props[field]["description"]
        assert "YYYY-MM-DD" in description
        assert "first unit of that type and model" in description
        assert RECITAL in description
        assert "Null: not given" in description


def test_intake_dates_question_gives_the_same_hint() -> None:
    (question,) = [q for q in QUESTIONS if q["id"] == "dates"]

    assert "first unit of that type and model" in question["hint"]
    assert RECITAL in question["hint"]
    assert question["article"] == "Art. 111(2) AIA"


def test_art_73_names_both_reporting_routes() -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS))
    (obligation,) = [ob for ob in report.obligations if ob.article == "Art. 73 AIA"]
    (item,) = [i for i in report.obligation_graph if i.article == "Art. 73 AIA"]

    for text in (obligation.requirement, item.requirement):
        assert "market surveillance authorities of the Member States" in text
        assert "Art. 73(1) AIA" in text
        assert "AI Office" in text and "Art. 75(1)" in text
        assert "Art. 75(1a) AIA, inserted by Art. 1, point (31)" in text


def test_art_72_item_dates_the_commission_template() -> None:
    report = classify(SystemProfile(name="x", annex_iii_area=AnnexIII.CREDITWORTHINESS))
    (obligation,) = [ob for ob in report.obligations if ob.article == "Art. 72 AIA"]
    (item,) = [i for i in report.obligation_graph if i.article == "Art. 72 AIA"]

    for text in (obligation.requirement, item.requirement):
        assert "post-market monitoring plan" in text
        assert "Annex IV technical documentation" in text
        assert "2 September 2027" in text
        assert "Art. 72(3) AIA as replaced by Art. 1, point (30)" in text


def test_report_footer_names_the_amendment_and_the_consolidated_version() -> None:
    report = classify(SystemProfile(name="x"))

    assert "as amended by Regulation (EU) 2026/1744" in REGULATION
    assert "consolidated version of 27 July 2026" in REGULATION
    assert report.regulation == REGULATION
    assert render_report(report).splitlines()[-2] == REGULATION


def test_playground_footer_links_the_consolidated_text() -> None:
    html = (ROOT / "docs" / "playground" / "index.html").read_text(encoding="utf-8")
    footer = re.search(r"<footer>.*?</footer>", html, re.S).group(0)
    (href,) = re.findall(r'href="([^"]+)"', footer)

    assert href == AI_ACT_URL
    assert "2026-07-27" in href
