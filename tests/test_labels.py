"""One label catalog for every surface (src/eu_ai_act_classifier/labels.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eu_ai_act_classifier.catalog import ANNEX_III, PROHIBITED
from eu_ai_act_classifier.labels import label_catalog, option_label
from eu_ai_act_classifier.models import (
    AnnexIII,
    AnnexISection,
    Disposition,
    ExcludedUse,
    ProhibitedPractice,
    ReviewStatus,
    RiskTier,
    Role,
    ScopeStatus,
    SourceStatus,
)

ROOT = Path(__file__).resolve().parents[1]
NAMESPACES = label_catalog()["namespaces"]


def test_every_enum_value_has_a_label() -> None:
    for namespace, enum in (
        ("annex_iii_area", AnnexIII),
        ("prohibited_practices", ProhibitedPractice),
        ("roles", Role),
        ("excluded_use_flags", ExcludedUse),
        ("annex_i_section", AnnexISection),
        ("risk_tier", RiskTier),
        ("disposition", Disposition),
        ("review_status", ReviewStatus),
        ("source_status", SourceStatus),
        ("scope_status", ScopeStatus),
    ):
        assert set(NAMESPACES[namespace]) == {member.value for member in enum}, namespace


def test_annex_iii_and_art_5_labels_name_the_point_the_engine_cites() -> None:
    assert option_label(AnnexIII.CREDITWORTHINESS) == (
        "Annex III(5)(b): Creditworthiness evaluation and credit scoring of natural persons"
    )
    for area, (citation, title) in ANNEX_III.items():
        if area is not AnnexIII.UNSURE:
            assert option_label(area) == f"{citation.ref.removesuffix(' AIA')}: {title}"
    for practice, (citation, title) in PROHIBITED.items():
        assert option_label(practice).startswith(citation.ref.removesuffix(" AIA"))
        assert option_label(practice).endswith(title)


def test_labels_are_never_raw_values_and_have_no_long_dashes() -> None:
    for namespace, labels in NAMESPACES.items():
        for value, label in labels.items():
            assert label and label != value, (namespace, value)
            assert not {chr(0x2013), chr(0x2014)} & set(label), (namespace, value)


def test_web_cockpit_labels_are_current() -> None:
    on_disk = json.loads((ROOT / "web" / "lib" / "labels.json").read_text(encoding="utf-8"))
    assert on_disk == label_catalog(), "web/lib/labels.json is stale: rebuild the playground"


def test_evidence_tracker_labels_cover_its_states_lanes_and_reasons() -> None:
    from eu_ai_act_classifier.evidence_tracker import EVIDENCE_STATES, LANES, STALE_REASONS

    assert tuple(NAMESPACES["evidence_state"]) == EVIDENCE_STATES
    assert tuple(NAMESPACES["evidence_lane"]) == LANES
    assert tuple(NAMESPACES["evidence_stale_reason"]) == STALE_REASONS
    assert NAMESPACES["evidence_state"]["stale"] == "Stale"
    # Lanes are named relative to the assessment date (ADR 0006 D6), not as legal timing.
    assert NAMESPACES["evidence_lane"] == {
        "applies_now": "Applies on the assessment date",
        "upcoming": "Applies after the assessment date",
        "no_assessment_date": "Dated; no assessment date set",
        "contested_or_open": "Contested or open",
    }
    assert NAMESPACES["evidence_stale_reason"]["reviewed_before_source_retrieval"] == (
        "Reviewed before the source was retrieved"
    )


def test_label_catalog_refuses_an_evidence_label_set_that_misses_a_value(monkeypatch) -> None:
    import eu_ai_act_classifier.labels as labels_module

    monkeypatch.setattr(
        labels_module, "EVIDENCE_LANE_LABELS", {"applies_now": "Applies now", "upcoming": "Up"}
    )
    with pytest.raises(ValueError, match="EVIDENCE_LANE_LABELS must cover every value"):
        label_catalog()
