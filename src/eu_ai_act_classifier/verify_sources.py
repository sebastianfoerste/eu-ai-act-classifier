"""Check the official source URLs and, with ``update``, record today as their retrieval date.

The retrieval dates in citations.py reach every report's source manifest, so ``update``
rewrites them only in a source checkout and only after every configured URL was verified.

Each URL ends up in one of three states:

- verified: a 2xx answer that is the page itself;
- unverified: the server answered 202 Accepted or with a recognisable bot challenge, so the
  check never saw the document. EUR-Lex sits behind AWS WAF, which answers a client that runs
  no JavaScript with 202 and a challenge page;
- failed: any other status, or no answer.

An unverified URL is reported apart from the failed ones and keeps ``update`` from writing,
but on its own does not make the check fail.
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
from email.message import Message
from pathlib import Path

try:
    from . import __version__
    from .citations import (
        AI_ACT_AMENDMENT_URL,
        AI_ACT_SERVICE_DESK_URL,
        AI_ACT_URL,
        AI_SYSTEM_DEFINITION_GUIDELINES_URL,
        GPAI_CODE_URL,
        GPAI_PROVIDER_GUIDELINES_URL,
        HIGH_RISK_GUIDELINES_URL,
        PROHIBITED_GUIDELINES_URL,
        TRANSPARENCY_GUIDANCE_URL,
    )
except (ImportError, ValueError):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from eu_ai_act_classifier import __version__
    from eu_ai_act_classifier.citations import (
        AI_ACT_AMENDMENT_URL,
        AI_ACT_SERVICE_DESK_URL,
        AI_ACT_URL,
        AI_SYSTEM_DEFINITION_GUIDELINES_URL,
        GPAI_CODE_URL,
        GPAI_PROVIDER_GUIDELINES_URL,
        HIGH_RISK_GUIDELINES_URL,
        PROHIBITED_GUIDELINES_URL,
        TRANSPARENCY_GUIDANCE_URL,
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
    "TRANSPARENCY_GUIDANCE_URL": TRANSPARENCY_GUIDANCE_URL,
}


PROJECT_NAME = "eu-ai-act-classifier"
PROJECT_URL = "https://github.com/sebastianfoerste/eu-ai-act-classifier"
# The repository root when the package runs from a clone. From an installed wheel this is
# a directory above site-packages, which holds no pyproject.toml naming the project.
CHECKOUT_ROOT = Path(__file__).resolve().parents[2]
ATTEMPTS = 3
# The checker names itself and its version instead of posing as a browser.
HEADERS = {
    "User-Agent": f"{PROJECT_NAME}/{__version__} (+{PROJECT_URL})",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
VERIFIED, UNVERIFIED, FAILED = "verified", "unverified", "failed"
# The start of the body is enough to recognise a challenge page; AWS WAF's is about 2 KB.
CHALLENGE_READ_BYTES = 65536
# AWS WAF names the action it took (challenge or captcha) in this header, and its challenge
# page sets these script variables. Only such specific names count: official pages use the
# word "challenge" too.
CHALLENGE_HEADER = "x-amzn-waf-action"
CHALLENGE_BODY_MARKERS = ("awsWafCookieDomainList", "gokuProps", "AwsWafIntegration")


class NotASourceCheckoutError(RuntimeError):
    """``update`` was asked for outside a source checkout of the project."""


class BotChallengeError(Exception):
    """A 2xx answer that is a bot challenge instead of the requested document."""

    def __init__(self, status: int, marker: str) -> None:
        super().__init__(f"HTTP {status} is a bot challenge ({marker}), not the document")
        self.status = status
        self.marker = marker


def challenge_marker(headers: Message, body: bytes) -> str | None:
    """The first sign that an answer is a bot challenge page, or None."""

    action = headers.get(CHALLENGE_HEADER)
    if action:
        return f"{CHALLENGE_HEADER}: {action}"
    text = body.decode("utf-8", "replace")
    return next((marker for marker in CHALLENGE_BODY_MARKERS if marker in text), None)


def fetch_status(url: str) -> int:
    """GET ``url`` and return its HTTP status, trying up to ATTEMPTS times.

    urllib raises HTTPError for a 4xx or 5xx answer and URLError or another OSError when no
    answer came; the last error propagates once the attempts run out. A 2xx answer that is a
    bot challenge raises BotChallengeError at once, since asking again does not pass it.
    """

    request = urllib.request.Request(url, headers=HEADERS, method="GET")
    for _ in range(ATTEMPTS - 1):
        try:
            return _status(request)
        except BotChallengeError:
            raise
        except Exception:
            time.sleep(1)
    return _status(request)


def _status(request: urllib.request.Request) -> int:
    with urllib.request.urlopen(request, timeout=15) as response:
        marker = challenge_marker(response.headers, response.read(CHALLENGE_READ_BYTES))
        if marker:
            raise BotChallengeError(response.status, marker)
        return response.status


def _outcome(status: int | None, challenged: bool) -> str:
    if status is None or not 200 <= status < 300:
        return FAILED
    # 202 Accepted: the request was taken for processing, so no document came back.
    if challenged or status == 202:
        return UNVERIFIED
    return VERIFIED


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
    """Check every URL in URLS; True unless one of them failed.

    ``fetch`` returns a URL's HTTP status, raises BotChallengeError for a challenge page and
    raises otherwise when there is no answer (fetch_status by default). A URL that answered
    202 or with a challenge is unverified: reported, but not a failure. With ``update``, and
    only when every URL was verified, write dist/verified_sources.json and set both retrieval
    dates in citations.py to today; otherwise nothing is written and the result is False.
    ``root`` is the checkout to update (CHECKOUT_ROOT by default); if it is not a source
    checkout, ``update`` raises NotASourceCheckoutError before any request is made.
    """

    fetch = fetch or fetch_status
    root = CHECKOUT_ROOT if root is None else root
    citations_file = _checkout_citations(root) if update else None

    print("Verifying EU AI Act source URLs...")
    retrieved_on = date.today().isoformat()
    results = []
    failed = []
    unverified = []

    for name, url in URLS.items():
        challenged = False
        try:
            status, error_msg = fetch(url), None
        except BotChallengeError as e:
            status, error_msg, challenged = e.status, str(e), True
        except urllib.error.HTTPError as e:
            status, error_msg = e.code, str(e)
        except Exception as e:  # URLError, timeouts, TLS and other transport failures
            status, error_msg = None, str(e)
        outcome = _outcome(status, challenged)
        if outcome == UNVERIFIED and not error_msg:
            error_msg = f"HTTP {status} Accepted, not the document"

        label = f"{status} unverified" if outcome == UNVERIFIED else status or "Error"
        print(f"[{label}] {name}: {url}")
        if error_msg:
            print(f"  Warning: {error_msg}")
        if outcome == FAILED:
            failed.append(name)
        elif outcome == UNVERIFIED:
            unverified.append(name)

        results.append(
            {
                "name": name,
                "url": url,
                "status": status,
                "error": error_msg,
                "verified_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
        )

    verified = len(URLS) - len(failed) - len(unverified)
    print(
        f"{verified} verified, {len(unverified)} unverified, {len(failed)} failed "
        f"of {len(URLS)} source URLs"
    )
    if unverified:
        print(
            f"warning: {len(unverified)} of {len(URLS)} source URLs unverified, answered with "
            f"202 or a bot challenge instead of the document: {', '.join(unverified)}",
            file=sys.stderr,
        )
    if failed:
        print(
            f"error: {len(failed)} of {len(URLS)} source URLs failed: {', '.join(failed)}",
            file=sys.stderr,
        )
    if failed or (update and unverified):
        if update:
            print(
                "Nothing was updated: the retrieval dates move only when every URL is verified.",
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

    # Every configured URL was verified, so both source retrieval dates move to today.
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
