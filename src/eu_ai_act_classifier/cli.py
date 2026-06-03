"""Command-line interface.

    eu-ai-act-classify profile.json            # human-readable report
    eu-ai-act-classify profile.json --json     # machine-readable report
    cat profile.json | eu-ai-act-classify -    # read from stdin
    eu-ai-act-classify profile.json --strict   # exit 1 if prohibited or requires_review

``--strict`` lets the classifier sit in a CI step or an intake pipeline as a
quality gate, the same way a linter does.
"""

from __future__ import annotations

import argparse
import sys

from pydantic import ValidationError

from .engine import classify
from .models import Disposition, RiskTier, SystemProfile
from .report import render_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="eu-ai-act-classify",
        description="Classify an AI system under the EU AI Act (Reg (EU) 2024/1689).",
    )
    parser.add_argument("profile", help="Path to a SystemProfile JSON file, or '-' for stdin.")
    parser.add_argument(
        "--json", action="store_true", help="Emit the ClassificationReport as JSON."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if the system is prohibited or the classification requires review.",
    )
    args = parser.parse_args(argv)

    try:
        if args.profile == "-":
            raw = sys.stdin.read()
        else:
            with open(args.profile, encoding="utf-8") as fh:
                raw = fh.read()
    except OSError as exc:
        print(f"error: cannot read profile: {exc}", file=sys.stderr)
        return 2

    try:
        profile = SystemProfile.model_validate_json(raw)
    except ValidationError as exc:
        print(f"error: invalid SystemProfile:\n{exc}", file=sys.stderr)
        return 2

    report = classify(profile)

    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(render_report(report))

    if args.strict and (
        report.risk_tier is RiskTier.PROHIBITED or report.disposition is Disposition.REQUIRES_REVIEW
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
