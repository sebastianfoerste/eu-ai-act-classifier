"""--verify-sources and --update, offline: a stubbed fetch and a temporary source checkout.

No test here reaches the network or the repository's own citations.py.
"""

from __future__ import annotations

import json
import re
import shutil
import urllib.error
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest

import eu_ai_act_classifier.verify_sources as verify_sources_module
from eu_ai_act_classifier.cli import main
from eu_ai_act_classifier.verify_sources import URLS, NotASourceCheckoutError, verify_sources

ROOT = Path(__file__).resolve().parents[1]
REAL_CITATIONS = ROOT / "src" / "eu_ai_act_classifier" / "citations.py"
DATE_LINE = re.compile(r'^(BINDING|ADVISORY)_SOURCE_RETRIEVED_ON = "([^"]*)"$', re.MULTILINE)
# A date no run of --update can produce, so a moved date is visible.
OLD_DATE = "2000-01-01"
FAILING = "AI_ACT_URL"


@pytest.fixture(autouse=True)
def _offline_and_away_from_the_real_tree(monkeypatch, tmp_path):
    real_citations = REAL_CITATIONS.read_bytes()

    def no_network(url: str) -> int:
        # pytest.fail raises a BaseException, so the verifier cannot count it as a failed URL.
        pytest.fail(f"unstubbed fetch of {url}")

    monkeypatch.setattr(verify_sources_module, "fetch_status", no_network)
    monkeypatch.setattr(verify_sources_module, "CHECKOUT_ROOT", tmp_path / "not-a-checkout")
    yield
    assert REAL_CITATIONS.read_bytes() == real_citations


@pytest.fixture
def checkout(tmp_path) -> Path:
    """A source checkout: the real pyproject.toml and a copy of citations.py with old dates."""

    root = tmp_path / "checkout"
    package = root / "src" / "eu_ai_act_classifier"
    package.mkdir(parents=True)
    shutil.copy(ROOT / "pyproject.toml", root / "pyproject.toml")
    text, count = DATE_LINE.subn(
        lambda match: f'{match[1]}_SOURCE_RETRIEVED_ON = "{OLD_DATE}"',
        REAL_CITATIONS.read_text(encoding="utf-8"),
    )
    assert count == 2
    (package / "citations.py").write_text(text, encoding="utf-8")
    return root


def _citations(root: Path) -> Path:
    return root / "src" / "eu_ai_act_classifier" / "citations.py"


def _dates(root: Path) -> dict[str, str]:
    return dict(DATE_LINE.findall(_citations(root).read_text(encoding="utf-8")))


def _fetch(outcomes: dict[str, int | Exception] | None = None) -> Callable[[str], int]:
    """Answers 200, except for the URLs in ``outcomes``: a status to return or an error to raise.

    Every requested URL is appended to ``fetch.calls``.
    """

    outcomes = outcomes or {}

    def fetch(url: str) -> int:
        fetch.calls.append(url)
        outcome = outcomes.get(url, 200)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    fetch.calls = []
    return fetch


def _http_error(code: int, reason: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(URLS[FAILING], code, reason, hdrs=None, fp=None)


def _failed_names(stderr: str) -> set[str]:
    match = re.search(r"source URLs failed: (.+)$", stderr, re.MULTILINE)
    assert match, stderr
    return set(match[1].split(", "))


def test_all_sources_passing_updates_both_dates_and_nothing_else(checkout) -> None:
    before = _citations(checkout).read_text(encoding="utf-8")
    fetch = _fetch()
    first_day = date.today().isoformat()

    assert verify_sources(update=True, fetch=fetch, root=checkout) is True

    days = {first_day, date.today().isoformat()}
    dates = _dates(checkout)
    assert set(dates) == {"BINDING", "ADVISORY"}
    assert dates["BINDING"] == dates["ADVISORY"]
    assert dates["BINDING"] in days
    after = _citations(checkout).read_text(encoding="utf-8")
    assert DATE_LINE.sub("", after) == DATE_LINE.sub("", before)
    assert fetch.calls == list(URLS.values())

    meta = json.loads((checkout / "dist" / "verified_sources.json").read_text(encoding="utf-8"))
    assert meta["retrieved_on"] == dates["BINDING"]
    assert [(row["name"], row["status"], row["error"]) for row in meta["results"]] == [
        (name, 200, None) for name in URLS
    ]


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param(_http_error(404, "Not Found"), id="http-404"),
        pytest.param(_http_error(403, "Forbidden"), id="http-403"),
        pytest.param(_http_error(503, "Service Unavailable"), id="http-503"),
        pytest.param(urllib.error.URLError("Name or service not known"), id="dns"),
        pytest.param(TimeoutError("The read operation timed out"), id="timeout"),
        pytest.param(ConnectionResetError("Connection reset by peer"), id="connection-reset"),
        pytest.param(301, id="status-301"),
        pytest.param(500, id="status-500"),
    ],
)
def test_one_failed_url_changes_nothing_and_returns_false(checkout, capsys, outcome) -> None:
    before = _citations(checkout).read_bytes()
    fetch = _fetch({URLS[FAILING]: outcome})

    assert verify_sources(update=True, fetch=fetch, root=checkout) is False

    assert _citations(checkout).read_bytes() == before
    assert _dates(checkout) == {"BINDING": OLD_DATE, "ADVISORY": OLD_DATE}
    assert not (checkout / "dist").exists()
    # The failure does not cut the check short: every URL is still reported.
    assert fetch.calls == list(URLS.values())
    err = capsys.readouterr().err
    assert _failed_names(err) == {FAILING}
    assert "Nothing was updated" in err


def test_every_failed_url_is_named(checkout, capsys) -> None:
    failing = {"AI_ACT_URL", "GPAI_CODE_URL"}
    fetch = _fetch(
        {
            URLS["AI_ACT_URL"]: _http_error(404, "Not Found"),
            URLS["GPAI_CODE_URL"]: urllib.error.URLError("timed out"),
        }
    )

    assert verify_sources(update=True, fetch=fetch, root=checkout) is False

    assert _failed_names(capsys.readouterr().err) == failing
    assert _dates(checkout) == {"BINDING": OLD_DATE, "ADVISORY": OLD_DATE}


@pytest.mark.parametrize(
    ("outcomes", "passed"),
    [
        pytest.param({}, True, id="all-pass"),
        pytest.param({URLS[FAILING]: _http_error(404, "Not Found")}, False, id="one-fails"),
    ],
)
def test_without_update_nothing_is_written(checkout, outcomes, passed) -> None:
    before = _citations(checkout).read_bytes()

    assert verify_sources(fetch=_fetch(outcomes), root=checkout) is passed

    assert _citations(checkout).read_bytes() == before
    assert not (checkout / "dist").exists()


def _installed_wheel(tmp_path: Path) -> Path:
    # parents[2] of site-packages/eu_ai_act_classifier/verify_sources.py
    root = tmp_path / "venv" / "lib" / "python3.13"
    package = root / "site-packages" / "eu_ai_act_classifier"
    package.mkdir(parents=True)
    shutil.copy(REAL_CITATIONS, package / "citations.py")
    return root


def _other_project(tmp_path: Path) -> Path:
    root = tmp_path / "other"
    (root / "src" / "eu_ai_act_classifier").mkdir(parents=True)
    shutil.copy(REAL_CITATIONS, root / "src" / "eu_ai_act_classifier" / "citations.py")
    (root / "pyproject.toml").write_text('[project]\nname = "something-else"\n', encoding="utf-8")
    return root


def _unreadable_pyproject(tmp_path: Path) -> Path:
    root = _other_project(tmp_path)
    (root / "pyproject.toml").write_text("[project\nname = ", encoding="utf-8")
    return root


def _no_citations(tmp_path: Path) -> Path:
    root = tmp_path / "bare"
    root.mkdir()
    shutil.copy(ROOT / "pyproject.toml", root / "pyproject.toml")
    return root


@pytest.mark.parametrize(
    "make_root",
    [
        pytest.param(_installed_wheel, id="installed-wheel"),
        pytest.param(_other_project, id="other-project"),
        pytest.param(_unreadable_pyproject, id="unreadable-pyproject"),
        pytest.param(_no_citations, id="no-citations"),
    ],
)
def test_update_is_refused_outside_a_source_checkout(tmp_path, make_root) -> None:
    root = make_root(tmp_path)
    files_before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}

    # The autouse no_network fetch fails the test if a request goes out.
    with pytest.raises(NotASourceCheckoutError, match="source checkout"):
        verify_sources(update=True, root=root)

    assert {path: path.read_bytes() for path in root.rglob("*") if path.is_file()} == files_before


@pytest.mark.parametrize(
    ("argv", "outcomes", "in_checkout", "code", "dates_move"),
    [
        pytest.param(["--verify-sources"], {}, False, 0, False, id="verify-pass"),
        pytest.param(
            ["--verify-sources"],
            {URLS[FAILING]: _http_error(404, "Not Found")},
            False,
            1,
            False,
            id="verify-fail",
        ),
        pytest.param(["--verify-sources", "--update"], {}, True, 0, True, id="update-pass"),
        pytest.param(
            ["--verify-sources", "--update"],
            {URLS[FAILING]: urllib.error.URLError("Name or service not known")},
            True,
            1,
            False,
            id="update-fail",
        ),
    ],
)
def test_cli_exit_codes(
    monkeypatch, checkout, capsys, argv, outcomes, in_checkout, code, dates_move
) -> None:
    monkeypatch.setattr(verify_sources_module, "fetch_status", _fetch(outcomes))
    if in_checkout:
        monkeypatch.setattr(verify_sources_module, "CHECKOUT_ROOT", checkout)

    assert main(argv) == code

    dates = set(_dates(checkout).values())
    assert (dates != {OLD_DATE}) is dates_move
    assert (checkout / "dist").exists() is dates_move
    if code:
        assert _failed_names(capsys.readouterr().err) == {FAILING}


def test_cli_update_outside_a_source_checkout_exits_2(capsys) -> None:
    # CHECKOUT_ROOT points at a missing directory and fetch_status fails the test if called.
    assert main(["--verify-sources", "--update"]) == 2

    out, err = capsys.readouterr()
    assert err.startswith("error: --update runs only in a source checkout")
    assert "Verifying" not in out


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param(["--update"], id="alone"),
        pytest.param(["examples/credit_scoring.json", "--update"], id="with-profile"),
        pytest.param(["--schema", "profile", "--update"], id="with-schema"),
    ],
)
def test_cli_update_without_verify_sources_is_a_usage_error(capsys, argv) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(argv)

    assert exit_info.value.code == 2
    out, err = capsys.readouterr()
    assert "--update requires --verify-sources" in err
    assert out == ""
