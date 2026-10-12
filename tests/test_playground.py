"""The browser playground must run the same rules as the CLI.

docs/playground/ ships a wheel of this package plus generated samples and a
field guide. These tests fail when any of them drifts from the source, so a
rule change cannot reach the CLI without reaching the playground too.
Rebuild with: uv run python scripts/build_playground.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import zipfile
from pathlib import Path

import pytest

from eu_ai_act_classifier import SystemProfile, classify, render_report

ROOT = Path(__file__).resolve().parents[1]
PLAYGROUND = ROOT / "docs" / "playground"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load("build_playground", ROOT / "scripts" / "build_playground.py")
bridge = _load("playground_bridge", PLAYGROUND / "classify.py")
SAMPLES = json.loads((PLAYGROUND / "samples.json").read_text(encoding="utf-8"))


def test_samples_and_field_guide_are_current() -> None:
    for filename, data in (
        ("samples.json", build.build_samples()),
        ("fields.json", build.build_fields()),
    ):
        on_disk = (PLAYGROUND / filename).read_text(encoding="utf-8")
        assert on_disk == build.render(data), f"{filename} is stale: rebuild the playground"


def test_field_guide_covers_every_profile_field() -> None:
    documented = [name for _group, fields in build.FIELD_GROUPS for name, _hint in fields]
    assert sorted(documented) == sorted(SystemProfile.model_fields)
    assert len(documented) == len(set(documented))


def test_samples_cover_the_base_eval_set() -> None:
    examples = {p.stem for p in (ROOT / "examples").glob("*.json")} - {"classification-packet"}
    assert set(SAMPLES["profiles"]) == examples
    assert SAMPLES["default"] in SAMPLES["profiles"]


def test_committed_wheel_matches_the_source() -> None:
    html = (PLAYGROUND / "index.html").read_text(encoding="utf-8")
    referenced = re.search(r'data-wheel="([^"]+)"', html).group(1)
    wheels = sorted(p.name for p in PLAYGROUND.glob("*.whl"))
    assert wheels == [build.wheel_name()] == [referenced]

    package = ROOT / "src" / "eu_ai_act_classifier"
    expected = {
        f"eu_ai_act_classifier/{p.relative_to(package).as_posix()}": p.read_bytes()
        for p in package.rglob("*.py")
    }
    with zipfile.ZipFile(PLAYGROUND / wheels[0]) as wheel:
        shipped = {n: wheel.read(n) for n in wheel.namelist() if n.endswith(".py")}
    assert shipped.keys() == expected.keys(), "wheel modules differ: rebuild the playground"
    stale = sorted(name for name in expected if shipped[name] != expected[name])
    assert not stale, f"wheel is stale for {stale}: rebuild the playground"


@pytest.mark.parametrize("key", sorted(SAMPLES["profiles"]))
@pytest.mark.parametrize("advisory", [False, True])
def test_bridge_matches_the_cli(key: str, advisory: bool) -> None:
    text = json.dumps(SAMPLES["profiles"][key])
    result = json.loads(bridge.classify_profile(text, advisory))
    report = classify(SystemProfile.model_validate_json(text), include_advisory=advisory)
    assert result["report"] == json.loads(report.model_dump_json())
    assert result["text"] == render_report(report)


def test_bridge_returns_field_errors_without_echoing_input() -> None:
    secret = "CONFIDENTIAL-matter-4711"
    text = json.dumps(
        {"name": secret, "roles": [secret], "annex_iii_area": "III.9", "typo": secret}
    )
    result = json.loads(bridge.classify_profile(text))
    assert "report" not in result
    locations = {error["loc"] for error in result["errors"]}
    assert {"roles.0", "annex_iii_area", "typo"} <= locations
    assert secret not in json.dumps(result)
