"""Browser bridge. Runs the same engine and renderer as the CLI on a pasted profile."""

import json

from pydantic import ValidationError

from eu_ai_act_classifier import SystemProfile, classify, render_report


def classify_profile(profile_text: str, include_advisory: bool = False) -> str:
    try:
        profile = SystemProfile.model_validate_json(profile_text)
    except ValidationError as exc:
        # Field locations and messages only: never echo submitted values back.
        errors = [
            {"loc": ".".join(str(part) for part in error["loc"]) or "profile", "msg": error["msg"]}
            for error in exc.errors(include_url=False, include_input=False, include_context=False)
        ]
        return json.dumps({"errors": errors})
    report = classify(profile, include_advisory=include_advisory)
    return json.dumps(
        {"report": json.loads(report.model_dump_json()), "text": render_report(report)}
    )
