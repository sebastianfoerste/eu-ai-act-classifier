"""Local JSON bridge used by the optional web cockpit.

The bridge keeps the Python classifier as the legal source of truth while the
Next.js app provides a local UI and route surface.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pydantic import ValidationError

from .artifacts import ARTIFACT_NAMES, render_artifact, selected_artifacts
from .citations import source_manifest
from .dossier import REVIEW_DOSSIER_SCHEMA, build_review_dossier
from .engine import classify
from .inventory import build_example_inventory
from .models import (
    AnnexIII,
    ExcludedUse,
    ProhibitedPractice,
    Role,
    SystemProfile,
)


def schema_payload() -> dict[str, Any]:
    return {
        "roles": [role.value for role in Role],
        "annex_iii_areas": [area.value for area in AnnexIII],
        "prohibited_practices": [practice.value for practice in ProhibitedPractice],
        "excluded_use_flags": [flag.value for flag in ExcludedUse],
        "artifacts": sorted(ARTIFACT_NAMES),
        "dossier_schema": REVIEW_DOSSIER_SCHEMA,
        "review_posture": "draft_only_human_review_required",
    }


def classify_payload(payload: dict[str, Any]) -> dict[str, Any]:
    profile_data = payload.get("profile", payload)
    include_advisory = bool(payload.get("include_advisory", False))
    report = classify(
        SystemProfile.model_validate(profile_data),
        include_advisory=include_advisory,
    )
    return report.model_dump(mode="json")


def sources_payload() -> list[dict[str, Any]]:
    return [source.model_dump(mode="json") for source in source_manifest()]


def inventory_payload() -> dict[str, Any]:
    return build_example_inventory().model_dump(mode="json", by_alias=True)


def artifacts_payload(payload: dict[str, Any]) -> dict[str, Any]:
    profile_data = payload.get("profile", payload)
    include_advisory = bool(payload.get("include_advisory", False))
    selection = str(payload.get("artifact", "all"))
    report = classify(
        SystemProfile.model_validate(profile_data),
        include_advisory=include_advisory,
    )
    return {
        "system": report.system,
        "review_status": "draft_only_human_review_required",
        "artifacts": [
            {
                "name": artifact_name,
                "filename": f"{report.system}.{artifact_name}.md",
                "content": render_artifact(artifact_name, report),
            }
            for artifact_name in selected_artifacts(selection)
        ],
        "source_manifest": [source.model_dump(mode="json") for source in report.source_manifest],
    }


def dossier_payload(payload: dict[str, Any]) -> dict[str, Any]:
    profile_data = payload.get("profile", payload)
    include_advisory = bool(payload.get("include_advisory", False))
    artifact_selection = str(payload.get("artifact", "all"))
    report = classify(
        SystemProfile.model_validate(profile_data),
        include_advisory=include_advisory,
    )
    return build_review_dossier(
        report,
        artifact_selection=artifact_selection,
    ).model_dump(mode="json", by_alias=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eu-ai-act-local-api")
    parser.add_argument(
        "command",
        choices=["schema", "classify", "sources", "inventory", "artifacts", "dossier"],
    )
    args = parser.parse_args(argv)

    try:
        payload = _read_payload()
        if args.command == "schema":
            result: Any = schema_payload()
        elif args.command == "classify":
            result = classify_payload(payload)
        elif args.command == "sources":
            result = sources_payload()
        elif args.command == "inventory":
            result = inventory_payload()
        elif args.command == "artifacts":
            result = artifacts_payload(payload)
        else:
            result = dossier_payload(payload)
    except (ValidationError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    return 0


def _read_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
