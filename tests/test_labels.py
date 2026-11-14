"""One label catalog for every surface (src/eu_ai_act_classifier/labels.py)."""

from __future__ import annotations

import json
from pathlib import Path

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
