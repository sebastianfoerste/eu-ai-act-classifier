"""Rebuild the static browser playground in docs/playground/.

    uv run python scripts/build_playground.py

Writes samples.json and fields.json from the canonical examples and the
SystemProfile model, then rebuilds the classifier wheel the page installs.
tests/test_playground.py fails if any of the three drifts from the source.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from enum import StrEnum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYGROUND = ROOT / "docs" / "playground"
sys.path.insert(0, str(ROOT / "src"))

from pydantic import BaseModel  # noqa: E402

from eu_ai_act_classifier import Derogation, SystemProfile, __version__  # noqa: E402
from eu_ai_act_classifier.models import (  # noqa: E402
    AnnexIII,
    AnnexILegislation,
    ChildSexualAbuseMaterialScreen,
    ExcludedUse,
    IntimateImageryScreen,
    ProhibitedPractice,
    Role,
)

# The 17 base examples, grouped by the outcome tests/test_examples.py asserts.
SAMPLE_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "Prohibited",
        [
            ("social_scoring", "Social scoring"),
            ("emotion_hiring", "Emotion recognition in hiring"),
        ],
    ),
    (
        "High-risk",
        [
            ("credit_scoring", "Credit scoring, provider"),
            ("credit_scoring_deployer", "Credit scoring, deployer"),
            ("cv_screening", "CV screening"),
            ("proctoring_education", "Exam proctoring"),
            ("law_enforcement", "Reoffending risk"),
        ],
    ),
    (
        "Requires review",
        [
            ("ambiguous_use_case", "Annex III point unsettled"),
            ("employment_derogation", "Art. 6(3) derogation asserted"),
            ("foundation_model_unknown_compute", "GPAI model, compute undisclosed"),
        ],
    ),
    (
        "Limited risk",
        [
            ("support_chatbot", "Support chatbot"),
            ("deepfake_generator", "Deepfake generator"),
        ],
    ),
    (
        "Minimal risk and GPAI models",
        [
            ("spam_filter", "Spam filter"),
            ("gpai_non_systemic", "GPAI model, no systemic risk"),
            ("gpai_systemic_by_flops", "GPAI model, systemic by compute"),
            ("gpai_systemic_designated", "GPAI model, designated systemic"),
            ("foundation_model_systemic", "Foundation model, systemic"),
        ],
    ),
]
DEFAULT_SAMPLE = "credit_scoring"

# Grouping and article pointers follow the comments and docstrings in models.py.
FIELD_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "System",
        [
            ("name", "Required. Shown as the system name in the report."),
            ("description", ""),
            ("roles", "Operator roles under the AIA. A single company often holds several."),
            ("purpose", ""),
            ("sector", ""),
        ],
    ),
    (
        "Scope and intake",
        [
            ("is_ai_system", "Treated as an in-scope AI system unless set otherwise."),
            ("intended_purpose_source", ""),
            ("eu_nexus", ""),
            ("excluded_use_flags", "Scope exclusions or carve-outs that need visible review."),
            (
                "assessment_date",
                "ISO date of the placing on the market, putting into service or use under "
                "assessment. Selects the rules in force (Art. 5(1)(ba) and (bb) from "
                "2026-12-02); null leaves date-dependent results UNKNOWN.",
            ),
            (
                "placing_on_market_date",
                "ISO date. Dates GPAI obligations (Art. 111(3) AIA) and Art. 50(2) "
                "(Art. 111(4) AIA); null leaves those dates UNKNOWN.",
            ),
            ("putting_into_service_date", "ISO date, for transitional status."),
            ("significant_change_after_application_date", ""),
            ("public_authority_use", ""),
            ("deployer_public_law_body", "Art. 27 AIA: fundamental rights impact assessment."),
            (
                "deployer_private_public_service",
                "Art. 27 AIA: fundamental rights impact assessment.",
            ),
            ("provider_established_outside_eu", "Art. 22 AIA: authorised representative."),
            ("has_authorised_representative", "Art. 22 AIA."),
            ("substantially_modifies_system", "Value-chain obligations."),
            ("puts_name_or_trademark_on_system", "Value-chain obligations."),
        ],
    ),
    (
        "General-purpose AI model (Chapter V AIA)",
        [
            ("is_gpai_model", ""),
            ("training_flops", "Cumulative training compute in FLOP; drives Art. 51(2) AIA."),
            ("gpai_systemic_risk_designated", "Commission designation under Art. 51(1)(b) AIA."),
        ],
    ),
    (
        "Prohibited-practice screens (Art. 5(1) AIA)",
        [
            ("prohibited_practices", "Keyed to the letters (a) to (h) of Art. 5(1) AIA."),
            (
                "intimate_imagery",
                "Art. 5(1)(ba), (1a) and (1b) AIA, from 2026-12-02: facts on generating or "
                "manipulating intimate imagery of identifiable persons without consent. Each "
                "fact is true, false or null (not established).",
            ),
            (
                "child_sexual_abuse_material",
                "Art. 5(1)(bb) and (1a) AIA, from 2026-12-02: facts on material within "
                "Art. 2(c) and (e) of Directive 2011/93/EU. Each fact is true, false or null.",
            ),
        ],
    ),
    (
        "High-risk screens (Art. 6 AIA)",
        [
            ("annex_i_safety_component", "Art. 6(1)(a): product or safety component."),
            ("annex_i_third_party_assessment", "Art. 6(1)(b): third-party conformity assessment."),
            (
                "annex_i_legislation",
                "Annex I point covering the product; decides Section A or B. Section B "
                "(including machinery, I.B.21): only Art. 6(1), 60a and 102 to 112 apply "
                "(Art. 2(2) AIA).",
            ),
            (
                "annex_iii_area",
                "Art. 6(2) and Annex III. III.unsure: an area is implicated but the point is "
                "unsettled; treated as high-risk and routed to review.",
            ),
            (
                "derogation",
                "Art. 6(3) AIA derogation facts. Profiling always keeps the system high-risk.",
            ),
        ],
    ),
    (
        "Transparency screens (Art. 50 AIA)",
        [
            ("interacts_with_natural_persons", "Art. 50(1) AIA."),
            ("generates_synthetic_content", "Art. 50(2) AIA."),
            ("deploys_emotion_or_biometric_categorisation", "Art. 50(3) AIA."),
            ("generates_deepfakes", "Art. 50(4) AIA."),
        ],
    ),
]

_ENUMS: dict[str, type[StrEnum]] = {
    "roles": Role,
    "excluded_use_flags": ExcludedUse,
    "prohibited_practices": ProhibitedPractice,
    "annex_i_legislation": AnnexILegislation,
    "annex_iii_area": AnnexIII,
}
# Nested fact objects and the model that lists their keys.
_OBJECTS: dict[str, type[BaseModel]] = {
    "derogation": Derogation,
    "intimate_imagery": IntimateImageryScreen,
    "child_sexual_abuse_material": ChildSexualAbuseMaterialScreen,
}


def _option_label(member: StrEnum) -> str:
    return member.name.replace("_", " ").capitalize()


def _field_type(name: str, schema: dict) -> str:
    if name == "derogation":
        return "object"
    if name in _OBJECTS:
        return "object or null"
    if name in _ENUMS:
        return "list" if schema.get("type") == "array" else "choice"
    types = [schema["type"]] if "type" in schema else [t["type"] for t in schema["anyOf"]]
    base = next(t for t in types if t != "null")
    return f"{base} or null" if "null" in types else base


def build_samples() -> dict:
    groups = []
    profiles = {}
    for group, entries in SAMPLE_GROUPS:
        groups.append({"label": group, "samples": [{"key": k, "label": lb} for k, lb in entries]})
        for key, _label in entries:
            path = ROOT / "examples" / f"{key}.json"
            profiles[key] = json.loads(path.read_text(encoding="utf-8"))
    return {"default": DEFAULT_SAMPLE, "groups": groups, "profiles": profiles}


def build_fields() -> dict:
    properties = SystemProfile.model_json_schema()["properties"]
    defaults = SystemProfile(name="x").model_dump(mode="json")
    groups = []
    for group, entries in FIELD_GROUPS:
        fields = []
        for name, hint in entries:
            field = {
                "name": name,
                "type": _field_type(name, properties[name]),
                "default": None if name == "name" else defaults[name],
                "hint": hint,
            }
            if name in _ENUMS:
                field["options"] = [
                    {"value": m.value, "label": _option_label(m)} for m in _ENUMS[name]
                ]
            if name in _OBJECTS:
                field["keys"] = list(_OBJECTS[name].model_fields)
            fields.append(field)
        groups.append({"label": group, "fields": fields})
    return {"version": __version__, "groups": groups}


def render(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def wheel_name() -> str:
    return f"eu_ai_act_classifier-{__version__}-py3-none-any.whl"


def build_wheel() -> None:
    with tempfile.TemporaryDirectory() as out:
        subprocess.run(["uv", "build", "--wheel", "--out-dir", out], cwd=ROOT, check=True)
        built = Path(out) / wheel_name()
        for old in PLAYGROUND.glob("eu_ai_act_classifier-*.whl"):
            old.unlink()
        shutil.copy2(built, PLAYGROUND / built.name)
    index = PLAYGROUND / "index.html"
    html = index.read_text(encoding="utf-8")
    html = re.sub(r'data-wheel="[^"]+"', f'data-wheel="{wheel_name()}"', html)
    index.write_text(html, encoding="utf-8")


def main() -> int:
    (PLAYGROUND / "samples.json").write_text(render(build_samples()), encoding="utf-8")
    (PLAYGROUND / "fields.json").write_text(render(build_fields()), encoding="utf-8")
    build_wheel()
    print(f"playground rebuilt for eu-ai-act-classifier {__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
