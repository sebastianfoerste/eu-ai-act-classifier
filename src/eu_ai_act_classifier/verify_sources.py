"""Check the official source URLs and, with ``update``, record today as their retrieval date.

The retrieval dates in citations.py reach every report's source manifest, so ``update``
rewrites them only in a source checkout and only after every configured URL answered 2xx.
"""

import json
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path

try:
    from .citations import (
        AI_ACT_AMENDMENT_URL,
        AI_ACT_SERVICE_DESK_URL,
        AI_ACT_URL,
        AI_SYSTEM_DEFINITION_GUIDELINES_URL,
        ART_50_CODE_OF_PRACTICE_URL,
        ART_50_GUIDELINES_URL,
        GPAI_CODE_URL,
        GPAI_PROVIDER_GUIDELINES_URL,
        HIGH_RISK_GUIDELINES_URL,
        PROHIBITED_GUIDELINES_URL,
    )
except (ImportError, ValueError):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from eu_ai_act_classifier.citations import (
        AI_ACT_AMENDMENT_URL,
        AI_ACT_SERVICE_DESK_URL,
        AI_ACT_URL,
        AI_SYSTEM_DEFINITION_GUIDELINES_URL,
        ART_50_CODE_OF_PRACTICE_URL,
        ART_50_GUIDELINES_URL,
        GPAI_CODE_URL,
        GPAI_PROVIDER_GUIDELINES_URL,
        HIGH_RISK_GUIDELINES_URL,
        PROHIBITED_GUIDELINES_URL,
    )

URLS = {
    "AI_ACT_URL": AI_ACT_URL,
    "AI_ACT_AMENDMENT_URL": AI_ACT_AMENDMENT_URL,
    "AI_ACT_SERVICE_DESK_URL": AI_ACT_SERVICE_DESK_URL,
    "HIGH_RISK_GUIDELINES_URL": HIGH_RISK_GUIDELINES_URL,
    "PROHIBITED_GUIDELINES_URL": PROHIBITED_GUIDELINES_URL,
    "AI_SYSTEM_DEFINITION_GUIDELINES_URL": AI_SYSTEM_DEFINITION_GUIDELINES_URL,
    "GPAI_CODE_URL": GPAI_CODE_URL,
    "GPAI_PROVIDER_GUIDELINES_URL": GPAI_PROVIDER_GUIDELINES_URL,
    "ART_50_CODE_OF_PRACTICE_URL": ART_50_CODE_OF_PRACTICE_URL,
    "ART_50_GUIDELINES_URL": ART_50_GUIDELINES_URL,
}


PROJECT_NAME = "eu-ai-act-classifier"
# The repository root when the package runs from a clone. From an installed wheel this is
# a directory above site-packages, which holds no pyproject.toml naming the project.
CHECKOUT_ROOT = Path(__file__).resolve().parents[2]
ATTEMPTS = 3
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class NotASourceCheckoutError(RuntimeError):
    """``update`` was asked for outside a source checkout of the project."""


def fetch_status(url: str) -> int:
    """GET ``url`` and return its HTTP status, trying up to ATTEMPTS times.

    urllib raises HTTPError for a 4xx or 5xx answer and URLError or another OSError when no
    answer came; the last error propagates once the attempts run out.
    """

    request = urllib.request.Request(url, headers=HEADERS, method="GET")
    for _ in range(ATTEMPTS - 1):
        try:
            return _status(request)
        except Exception:
            time.sleep(1)
    return _status(request)


def _status(request: urllib.request.Request) -> int:
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status


def _checkout_citations(root: Path) -> Path:
    """The citations.py of the source checkout at ``root``, or NotASourceCheckoutError."""

    citations_file = root / "src" / "eu_ai_act_classifier" / "citations.py"
    try:
        pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        name = pyproject["project"]["name"]
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError):
        name = None
    if name != PROJECT_NAME or not citations_file.is_file():
        raise NotASourceCheckoutError(
            f"--update runs only in a source checkout of {PROJECT_NAME}, and {root} is not "
            f"one: it needs a pyproject.toml naming {PROJECT_NAME} and "
            "src/eu_ai_act_classifier/citations.py. Run it from a clone of the repository. "
            "Nothing was checked or changed."
        )
    return citations_file


def verify_sources(
    update: bool = False,
    *,
    fetch: Callable[[str], int] | None = None,
    root: Path | None = None,
) -> bool:
    """Check every URL in URLS; True only if each one answered with a 2xx status.

    ``fetch`` returns a URL's HTTP status and raises when there is none (fetch_status by
    default). With ``update``, and only when every URL passed, write dist/verified_sources.json
    and set both retrieval dates in citations.py to today. ``root`` is the checkout to update
    (CHECKOUT_ROOT by default); if it is not a source checkout, ``update`` raises
    NotASourceCheckoutError before any request is made.
    """

    fetch = fetch or fetch_status
    root = CHECKOUT_ROOT if root is None else root
    citations_file = _checkout_citations(root) if update else None

    print("Verifying EU AI Act source URLs...")
    retrieved_on = date.today().isoformat()
    results = []
    failed = []

    for name, url in URLS.items():
        try:
            status, error_msg = fetch(url), None
        except urllib.error.HTTPError as e:
            status, error_msg = e.code, str(e)
        except Exception as e:  # URLError, timeouts, TLS and other transport failures
            status, error_msg = None, str(e)

        print(f"[{status or 'Error'}] {name}: {url}")
        if error_msg:
            print(f"  Warning: {error_msg}")
        if status is None or not 200 <= status < 300:
            failed.append(name)

        results.append(
            {
                "name": name,
                "url": url,
                "status": status,
                "error": error_msg,
                "verified_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
        )

    if failed:
        print(
            f"error: {len(failed)} of {len(URLS)} source URLs failed: {', '.join(failed)}",
            file=sys.stderr,
        )
        if update:
            print(
                "Nothing was updated: the retrieval dates move only when every URL passes.",
                file=sys.stderr,
            )
        return False

    if citations_file is None:
        return True

    meta_file = root / "dist" / "verified_sources.json"
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    meta_data = {"retrieved_on": retrieved_on, "results": results}
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2)
    print(f"Wrote verification metadata to {meta_file}")

    # Every configured URL passed, so both source retrieval dates move to today.
    content = citations_file.read_text(encoding="utf-8")
    new_content = re.sub(
        r'(?:BINDING|ADVISORY)_SOURCE_RETRIEVED_ON\s*=\s*"[^"]+"',
        lambda match: (
            f'{match.group(0).split("_SOURCE_")[0]}_SOURCE_RETRIEVED_ON = "{retrieved_on}"'
        ),
        content,
    )
    citations_file.write_text(new_content, encoding="utf-8")
    print(f"Updated source retrieval dates to '{retrieved_on}' in {citations_file}")
    return True


if __name__ == "__main__":
    try:
        sys.exit(0 if verify_sources(update="--update" in sys.argv) else 1)
    except NotASourceCheckoutError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
