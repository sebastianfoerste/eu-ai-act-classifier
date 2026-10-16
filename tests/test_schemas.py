from __future__ import annotations

import json
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
