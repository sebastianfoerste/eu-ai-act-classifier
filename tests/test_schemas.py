from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from eu_ai_act_classifier import SystemProfile
from eu_ai_act_classifier.cli import main
from eu_ai_act_classifier.schemas import SCHEMAS, schema

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("kind", sorted(SCHEMAS))
def test_committed_schemas_match_models(kind: str) -> None:
    filename, _ = SCHEMAS[kind]
    committed = json.loads((ROOT / "schemas" / filename).read_text(encoding="utf-8"))
    assert committed == schema(kind), "run: python scripts/build_schemas.py"


def test_profile_accepts_and_drops_schema_key() -> None:
    profile = SystemProfile.model_validate(
        {"$schema": "../schemas/system-profile.v1.schema.json", "name": "x"}
    )
    assert profile.name == "x"
    assert "$schema" not in profile.model_dump()


def test_unknown_keys_are_still_rejected() -> None:
    with pytest.raises(ValueError):
        SystemProfile.model_validate({"name": "x", "unexpected": 1})


def test_cli_prints_schema(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--schema", "profile"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["$id"].endswith("system-profile.v1.schema.json")
    assert "name" in printed["properties"]


def test_examples_validate_against_schema_shape() -> None:
    props = set(schema("profile")["properties"])
    for path in (ROOT / "examples").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "name" in data and isinstance(data, dict) and path.name != "classification-packet.json":
            assert set(data) <= props, path.name


def test_profile_schema_carries_the_omnibus_follow_up_fields() -> None:
    profile = schema("profile")
    props = profile["properties"]

    for field in (
        "placing_on_market_date",
        "putting_into_service_date",
        "gpai_model_placing_on_market_date",
    ):
        # "format": "date" alone is not enforced by many validators; the pattern is.
        assert {
            "type": "string",
            "format": "date",
            "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
        } in props[field]["anyOf"], field
    assert profile["$defs"]["AnnexISection"]["enum"] == ["A", "B"]
    assert {"$ref": "#/$defs/AnnexISection"} in props["annex_i_section"]["anyOf"]
    practices = profile["$defs"]["ProhibitedPractice"]["enum"]
    assert practices.index("5.1.ba") == practices.index("5.1.b") + 1
    assert practices.index("5.1.bb") == practices.index("5.1.ba") + 1


@pytest.mark.parametrize("value", ["March 2026", "2026-W09-7", "01.03.2026", "2026-3-1"])
def test_profile_schema_date_pattern_rejects_non_iso_forms(value: str) -> None:
    (date_schema,) = [
        option
        for option in schema("profile")["properties"]["placing_on_market_date"]["anyOf"]
        if option.get("type") == "string"
    ]

    assert re.fullmatch(date_schema["pattern"].strip("^$"), value) is None
    assert re.fullmatch(date_schema["pattern"].strip("^$"), "2026-03-01") is not None


def test_profile_schema_describes_what_null_means_for_the_new_fields() -> None:
    props = schema("profile")["properties"]

    assert "Null: not established" in props["deployer_public_authority"]["description"]
    assert (
        "Null: the model is dated by placing_on_market_date"
        in (props["gpai_model_placing_on_market_date"]["description"])
    )
    assert "Null: treated as Section A" in props["annex_i_section"]["description"]
    change = props["significant_change_after_application_date"]["description"]
    assert "2027-12-02" in change and "2026-08-02" in change
