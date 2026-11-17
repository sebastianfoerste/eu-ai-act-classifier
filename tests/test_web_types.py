"""The cockpit's TypeScript types match the pydantic models they mirror.

`web/lib/types.ts` declares by hand the profile the cockpit sends and the report it
receives. `SystemProfile`, `ClassificationReport` and every model nested in them must
have a type of the same name there, with the same fields and field types. The expected
TypeScript type of a field comes from the model's JSON Schema: enums are `string`,
nested models keep their name, arrays are `T[]`, and a nullable value is `T | null`
(`NullableBoolean` for `boolean | null`). A `?` marker on a TypeScript field is not
compared.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from eu_ai_act_classifier.models import ClassificationReport, SystemProfile

TYPES_TS = Path(__file__).resolve().parents[1] / "web" / "lib" / "types.ts"
TS_BLOCK = re.compile(r"^export type (\w+) = \{\n(.*?)\n\};$", re.MULTILINE | re.DOTALL)
TS_FIELD = re.compile(r"^  (\w+)\??: (.+);$")
TS_ALIASES = {"NullableBoolean": "boolean | null"}
JSON_TO_TS = {"string": "string", "number": "number", "integer": "number", "boolean": "boolean"}


def _ts_types() -> dict[str, dict[str, str]]:
    types = {}
    for name, body in TS_BLOCK.findall(TYPES_TS.read_text(encoding="utf-8")):
        fields = {}
        for line in body.splitlines():
            match = TS_FIELD.match(line)
            if match:
                field, ts_type = match.groups()
                fields[field] = TS_ALIASES.get(ts_type, ts_type)
        types[name] = fields
    return types


def _ts_type(node: dict[str, Any], defs: dict[str, Any]) -> str:
    if "$ref" in node:
        name = node["$ref"].rsplit("/", 1)[-1]
        target = defs[name]
        # A nested model keeps its name; an enum travels as its string value.
        return name if "properties" in target else _ts_type(target, defs)
    if "anyOf" in node:
        members = [_ts_type(member, defs) for member in node["anyOf"]]
        return " | ".join(members)
    if node.get("type") == "null":
        return "null"
    if node.get("type") == "array":
        return f"{_ts_type(node['items'], defs)}[]"
    return JSON_TO_TS[node["type"]]


def _python_types() -> dict[str, dict[str, str]]:
    types: dict[str, dict[str, str]] = {}
    for model in (SystemProfile, ClassificationReport):
        schema = model.model_json_schema(mode="serialization")
        defs = schema.get("$defs", {})
        objects = {name: body for name, body in defs.items() if "properties" in body}
        objects[model.__name__] = schema
        for name, body in objects.items():
            types[name] = {
                field: _ts_type(node, defs) for field, node in body["properties"].items()
            }
    return types


MIRRORED = sorted(_python_types())


def test_the_schema_walk_reaches_the_nested_models() -> None:
    assert {"SystemProfile", "Derogation", "ClassificationReport", "Finding"} <= set(MIRRORED)


@pytest.mark.parametrize("name", MIRRORED)
def test_types_ts_matches_the_pydantic_model(name: str) -> None:
    ts_types = _ts_types()

    assert name in ts_types, f"web/lib/types.ts has no `export type {name}`"
    assert ts_types[name] == _python_types()[name]
