"""JSON Schemas for the classifier's input and output, generated from the models."""

from __future__ import annotations

from typing import Any

from .models import ClassificationReport, SystemProfile

BASE_URL = "https://raw.githubusercontent.com/sebastianfoerste/eu-ai-act-classifier/main/schemas"

SCHEMAS: dict[str, tuple[str, type]] = {
    "profile": ("system-profile.v1.schema.json", SystemProfile),
    "report": ("classification-report.v1.schema.json", ClassificationReport),
}


def schema(kind: str) -> dict[str, Any]:
    filename, model = SCHEMAS[kind]
    body = model.model_json_schema()
    if kind == "profile":
        # Profiles may carry "$schema" for editor autocomplete; the model drops it.
        body.setdefault("properties", {})["$schema"] = {"type": "string"}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{BASE_URL}/{filename}",
        **body,
    }
