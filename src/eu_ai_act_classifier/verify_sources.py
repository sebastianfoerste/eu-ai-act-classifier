import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

try:
    from .citations import (
        AI_ACT_SERVICE_DESK_URL,
        AI_ACT_URL,
        AI_OMNIBUS_COUNCIL_URL,
        AI_SYSTEM_DEFINITION_GUIDELINES_URL,
        GPAI_CODE_URL,
        GPAI_PROVIDER_GUIDELINES_URL,
        HIGH_RISK_GUIDELINES_URL,
        PROHIBITED_GUIDELINES_URL,
        TRANSPARENCY_GUIDANCE_URL,
    )
except (ImportError, ValueError):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from eu_ai_act_classifier.citations import (
        AI_ACT_SERVICE_DESK_URL,
        AI_ACT_URL,
        AI_OMNIBUS_COUNCIL_URL,
        AI_SYSTEM_DEFINITION_GUIDELINES_URL,
        GPAI_CODE_URL,
        GPAI_PROVIDER_GUIDELINES_URL,
        HIGH_RISK_GUIDELINES_URL,
        PROHIBITED_GUIDELINES_URL,
        TRANSPARENCY_GUIDANCE_URL,
    )

URLS = {
    "AI_ACT_URL": AI_ACT_URL,
    "AI_OMNIBUS_COUNCIL_URL": AI_OMNIBUS_COUNCIL_URL,
    "AI_ACT_SERVICE_DESK_URL": AI_ACT_SERVICE_DESK_URL,
    "HIGH_RISK_GUIDELINES_URL": HIGH_RISK_GUIDELINES_URL,
    "PROHIBITED_GUIDELINES_URL": PROHIBITED_GUIDELINES_URL,
    "AI_SYSTEM_DEFINITION_GUIDELINES_URL": AI_SYSTEM_DEFINITION_GUIDELINES_URL,
    "GPAI_CODE_URL": GPAI_CODE_URL,
    "GPAI_PROVIDER_GUIDELINES_URL": GPAI_PROVIDER_GUIDELINES_URL,
    "TRANSPARENCY_GUIDANCE_URL": TRANSPARENCY_GUIDANCE_URL,
}


def verify_sources(update: bool = False):
    print("Verifying EU AI Act source URLs...")
    results = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    retrieved_on = date.today().isoformat()
    success = True

    for name, url in URLS.items():
        status = None
        error_msg = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=headers)
                req.get_method = lambda: "GET"
                with urllib.request.urlopen(req, timeout=15) as response:
                    status = response.status
                    error_msg = None
                    break
            except urllib.error.HTTPError as e:
                status = e.code
                error_msg = str(e)
            except Exception as e:
                status = 0
                error_msg = str(e)
            if attempt < 2:
                time.sleep(1)

        print(f"[{status or 'Error'}] {name}: {url}")
        if error_msg:
            print(f"  Warning: {error_msg}")
        if status is None or status < 200 or status >= 300:
            success = False

        results.append(
            {
                "name": name,
                "url": url,
                "status": status,
                "error": error_msg,
                "verified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        )

    if update:
        # Write metadata to dist/verified_sources.json
        dist_dir = Path(__file__).resolve().parent.parent.parent / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        meta_file = dist_dir / "verified_sources.json"

        meta_data = {"retrieved_on": retrieved_on, "results": results}
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)
        print(f"Wrote verification metadata to {meta_file}")

        # Update citations.py SOURCE_RETRIEVED_ON
        citations_file = Path(__file__).resolve().parent / "citations.py"
        if citations_file.exists():
            content = citations_file.read_text(encoding="utf-8")
            new_content = re.sub(
                r'SOURCE_RETRIEVED_ON\s*=\s*"[^"]+"',
                f'SOURCE_RETRIEVED_ON = "{retrieved_on}"',
                content,
            )
            citations_file.write_text(new_content, encoding="utf-8")
            print(f"Updated SOURCE_RETRIEVED_ON to '{retrieved_on}' in {citations_file}")
    return success


if __name__ == "__main__":
    update_flag = "--update" in sys.argv
    verify_sources(update=update_flag)
