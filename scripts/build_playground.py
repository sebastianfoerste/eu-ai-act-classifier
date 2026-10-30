"""Rebuild the static browser playground in docs/playground/.

    uv run python scripts/build_playground.py

Writes samples.json and fields.json from the canonical examples and the
SystemProfile model, writes the label catalog the web cockpit reads
(web/lib/labels.json), then rebuilds the classifier wheel the page installs.
tests/test_playground.py fails if any of them drifts from the source.
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
WEB_LABELS = ROOT / "web" / "lib" / "labels.json"
INTAKE_FIXTURES = ROOT / "tests" / "playground" / "intake-fixtures.json"
sys.path.insert(0, str(ROOT / "src"))

from eu_ai_act_classifier import Derogation, SystemProfile, __version__  # noqa: E402
from eu_ai_act_classifier.intake import (  # noqa: E402
    QUESTIONS,
    answers_to_profile,
    intake_definition,
    profile_to_answers,
)
from eu_ai_act_classifier.labels import label_catalog, option_label  # noqa: E402
from eu_ai_act_classifier.models import (  # noqa: E402
    AnnexIII,
    AnnexISection,
    ExcludedUse,
    ProhibitedPractice,
    Role,
)

# The 19 base examples, grouped by the outcome tests/test_examples.py asserts.
SAMPLE_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "Prohibited",
        [
            ("social_scoring", "Social scoring"),
            ("emotion_hiring", "Emotion recognition in hiring"),
            ("intimate_imagery_generator", "Non-consensual intimate imagery"),
        ],
    ),
    (
        "High-risk",
        [
            ("credit_scoring", "Credit scoring, provider"),
            ("credit_scoring_deployer", "Credit scoring, deployer"),
            ("life_insurer_pricing", "Life insurance pricing, provider and deployer"),
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
                "placing_on_market_date",
                "YYYY-MM-DD, the AI system's date. Drives Art. 111(2) and (4) AIA; for a GPAI "
                "model without its own date, also Art. 111(3).",
            ),
            ("putting_into_service_date", "YYYY-MM-DD. Drives Art. 111(2) AIA."),
            (
                "significant_change_after_application_date",
                "Art. 111(2) AIA: a significant design change as from the Chapter III date. "
                "Which date is contested: 2027-12-02 (Annex III) or 2028-08-02 (Annex I), or "
                "the general date 2026-08-02.",
            ),
            (
                "public_authority_use",
                "Intended to be used by public authorities: the 2 August 2030 deadline in "
                "Art. 111(2) AIA and, while the deployer's status is unset, the Art. 49(3) "
                "registration of use for review.",
            ),
            (
                "deployer_public_authority",
                "The deployer is, or acts on behalf of, a public authority or Union institution, "
                "body, office or agency: Art. 49(3) AIA registration of use. Unset: inferred for "
                "review from public-authority use or Annex III points 5(a), 6 and 7.",
            ),
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
            (
                "gpai_model_placing_on_market_date",
                "YYYY-MM-DD, the model's own date. Drives Art. 111(3) AIA.",
            ),
        ],
    ),
    (
        "Prohibited-practice screens (Art. 5(1) AIA)",
        [
            (
                "prohibited_practices",
                "Keyed to the letters of Art. 5(1) AIA. 5.1.ba and 5.1.bb apply from "
                "2 December 2026.",
            )
        ],
    ),
    (
        "High-risk screens (Art. 6 AIA)",
        [
            ("annex_i_safety_component", "Art. 6(1)(a): product or safety component."),
            ("annex_i_third_party_assessment", "Art. 6(1)(b): third-party conformity assessment."),
            (
                "annex_i_section",
                "Annex I section of the product. B (incl. machinery, Regulation (EU) 2023/1230): "
                "only Art. 6(1), 60a and 102-112 apply, and 57-59 as far as integrated in the "
                "sectoral legislation (Art. 2(2) AIA). Unset: Section A.",
            ),
            (
                "annex_iii_area",
                "Art. 6(2) and Annex III. III.unsure: an area is implicated but the point is "
                "unsettled; treated as high-risk and routed to review.",
            ),
            (
                "used_for_financial_fraud_detection",
                "Annex III(5)(b) AIA excepts financial-fraud detection. True or null on a "
                "III.5.b profile raises a review question.",
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
    "annex_i_section": AnnexISection,
    "annex_iii_area": AnnexIII,
}


def _field_type(name: str, schema: dict) -> str:
    if name == "derogation":
        return "object"
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
                    {"value": m.value, "label": option_label(m)} for m in _ENUMS[name]
                ]
            if name == "derogation":
                field["keys"] = list(Derogation.model_fields)
            fields.append(field)
        groups.append({"label": group, "fields": fields})
    return {"version": __version__, "groups": groups}


def build_intake_fixtures() -> dict:
    """Python's answers for every example, so the browser interpreter can be held to them."""

    cases = {}
    for _group, entries in SAMPLE_GROUPS:
        for key, _label in entries:
            example = json.loads((ROOT / "examples" / f"{key}.json").read_text(encoding="utf-8"))
            answers = profile_to_answers(example)
            cases[key] = {"answers": answers}
            if key not in ("credit_scoring_deployer", "spam_filter"):
                continue
            for question in QUESTIONS:
                if question.get("unknown") is not None:
                    unknown = {**answers, question["id"]: "unknown"}
                    cases[f"{key}+unknown:{question['id']}"] = {"answers": unknown}
    # Paths the examples never take: padded text and unanswered questions.
    padded = profile_to_answers({"name": "x"})
    padded["system"] = {"name": "  Padded name  ", "purpose": " Credit scoring "}
    padded["dates"] = {"placing_on_market_date": " 2026-03-01 "}
    cases["edge+padded-text"] = {"answers": padded}
    cases["edge+no-answers"] = {"answers": {}}
    partial = profile_to_answers(json.loads((ROOT / "examples" / "cv_screening.json").read_text()))
    for question_id in ("roles", "annex_iii_area", "transparency", "training_flops"):
        partial.pop(question_id, None)
    cases["edge+partly-answered"] = {"answers": partial}
    # The Annex I route asks annex_i_section, a single question with no "none" option.
    route = profile_to_answers(
        {
            "name": "x",
            "annex_i_safety_component": True,
            "annex_i_third_party_assessment": True,
            "annex_i_section": "B",
        }
    )
    for answer in ("A", "B", "none", "unknown"):
        cases[f"edge+annex-i-section:{answer}"] = {"answers": {**route, "annex_i_section": answer}}
    cases["edge+annex-i-section:missing"] = {
        "answers": {k: v for k, v in route.items() if k != "annex_i_section"}
    }
    model = profile_to_answers(
        {
            "name": "x",
            "roles": ["gpai_provider"],
            "is_gpai_model": True,
            "training_flops": 1e24,
            "placing_on_market_date": "2026-01-01",
            "gpai_model_placing_on_market_date": "2025-03-01",
        }
    )
    cases["edge+gpai-date"] = {"answers": model}
    # The Art. 111(2) change question turns on a date before the Chapter III date.
    for label, extra in {
        "annex-iii-day-before": {
            "annex_iii_area": "III.4.a",
            "placing_on_market_date": "2027-12-01",
        },
        "annex-iii-on-the-day": {
            "annex_iii_area": "III.4.a",
            "placing_on_market_date": "2027-12-02",
        },
        "annex-iii-service-date": {
            "annex_iii_area": "III.4.a",
            "putting_into_service_date": "2025-06-01",
        },
        "annex-i-section-a": {
            "annex_i_safety_component": True,
            "annex_i_third_party_assessment": True,
            "annex_i_section": "A",
            "placing_on_market_date": "2028-01-01",
        },
        "annex-i-section-b": {
            "annex_i_safety_component": True,
            "annex_i_third_party_assessment": True,
            "annex_i_section": "B",
            "placing_on_market_date": "2028-01-01",
        },
    }.items():
        legacy = profile_to_answers({"name": "x", **extra})
        for answer in ("yes", "no", "unknown"):
            cases[f"edge+change:{label}:{answer}"] = {
                "answers": {**legacy, "significant_change": answer}
            }
    for flops in ("2e25", " 2e25 ", "0x10", "1_000", ".5e3", "1e", ""):
        cases[f"edge+training-flops:{flops!r}"] = {"answers": {**model, "training_flops": flops}}
    for case in cases.values():
        profile, asked, blocked, missing = answers_to_profile(case["answers"])
        case.update(profile=profile, asked=asked, blocked=blocked, missing=missing)
    return {"cases": dict(sorted(cases.items()))}


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
    WEB_LABELS.write_text(render(label_catalog()), encoding="utf-8")
    (PLAYGROUND / "intake.json").write_text(render(intake_definition()), encoding="utf-8")
    INTAKE_FIXTURES.write_text(render(build_intake_fixtures()), encoding="utf-8")
    build_wheel()
    print(f"playground rebuilt for eu-ai-act-classifier {__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
