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
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .artifacts import ARTIFACT_NAMES, selected_artifacts, write_artifacts
from .dossier import write_review_dossier
from .engine import classify
from .models import Disposition, RiskTier, SystemProfile
from .report import render_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="eu-ai-act-classify",
        description="Classify an AI system under the EU AI Act (Reg (EU) 2024/1689).",
    )
    parser.add_argument(
        "profile",
        nargs="?",
        default=None,
        help="Path to a SystemProfile JSON file, or '-' for stdin.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit the ClassificationReport as JSON."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if the system is prohibited or the classification requires review.",
    )
    parser.add_argument(
        "--advisory",
        action="store_true",
        help="Include nonbinding Commission guidance notes in the report.",
    )
    parser.add_argument(
        "--sources",
        action="store_true",
        help="Emit the regulatory source manifest as JSON.",
    )
    parser.add_argument(
        "--artifact",
        choices=sorted(ARTIFACT_NAMES | {"all"}),
        help="Generate one draft legal work product, or all work products.",
    )
    parser.add_argument(
        "--artifacts-dir",
        help="Directory for draft legal work products. Required with --artifact.",
    )
    parser.add_argument(
        "--dossier-dir",
        help="Directory for a complete draft review dossier bundle.",
    )
    parser.add_argument(
        "--verify-sources",
        action="store_true",
        help="Verify official regulatory source URLs.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update source retrieval date to today.",
    )
    args = parser.parse_args(argv)

    if args.verify_sources:
        from .verify_sources import verify_sources

        return 0 if verify_sources(update=args.update) else 1

    if not args.profile:
        print("error: the following arguments are required: profile", file=sys.stderr)
        parser.print_help()
        return 2

    if args.artifact and not args.artifacts_dir:
        print("error: --artifact requires --artifacts-dir", file=sys.stderr)
        return 2

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

    report = classify(profile, include_advisory=args.advisory)

    if args.sources:
        source_json = [source.model_dump(mode="json") for source in report.source_manifest]
        print(json.dumps(source_json, indent=2))
    elif args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(render_report(report))

    if args.artifact and args.artifacts_dir:
        try:
            selected_artifacts(args.artifact)
            paths = write_artifacts(args.artifact, Path(args.artifacts_dir), report)
        except OSError as exc:
            print(f"error: cannot write artifacts: {exc}", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        for path in paths:
            output = sys.stderr if args.json or args.sources else sys.stdout
            print(f"artifact: {path}", file=output)

    if args.dossier_dir:
        try:
            paths = write_review_dossier(Path(args.dossier_dir), report)
        except OSError as exc:
            print(f"error: cannot write dossier: {exc}", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        for path in paths:
            output = sys.stderr if args.json or args.sources else sys.stdout
            print(f"dossier: {path}", file=output)

    if args.strict and (
        report.risk_tier is RiskTier.PROHIBITED or report.disposition is Disposition.REQUIRES_REVIEW
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
