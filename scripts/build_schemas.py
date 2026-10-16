"""Write schemas/*.schema.json from the models. tests/test_schemas.py checks drift."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from eu_ai_act_classifier.schemas import SCHEMAS, schema  # noqa: E402

if __name__ == "__main__":
    for kind, (filename, _model) in SCHEMAS.items():
        path = ROOT / "schemas" / filename
        path.write_text(json.dumps(schema(kind), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
