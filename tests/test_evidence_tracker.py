"""The obligation tracker's derived state (src/eu_ai_act_classifier/evidence_tracker.py)."""

from __future__ import annotations

import hashlib
import json
import re
from itertools import product
from pathlib import Path

import pytest
from pydantic import ValidationError

from eu_ai_act_classifier.artifacts import DRAFT_NOTICE
from eu_ai_act_classifier.engine import classify
from eu_ai_act_classifier.evidence_tracker import (
    EVIDENCE_STATES,
    LANES,
    STALE_REASONS,
    VIEW_SCHEMA,
    EvidenceRecord,
    build_evidence_view,
    check_system_id,
    find_item,
    item_digest,
    lane_for,
    report_digest,
    retrieved_on_for,
    stale_reasons,
)
from eu_ai_act_classifier.models import (
    ClassificationReport,
    ObligationGraphItem,
    ReviewStatus,
    RiskTier,
    Role,
    SourceStatus,
    SystemProfile,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted(
    path for path in (ROOT / "examples").glob("*.json") if path.name != "classification-packet.json"
)
ASSESSMENT_DATES = [
    None,
    "2024-08-01",
    "2025-02-02",
    "2025-08-02",
    "2026-08-02",
    "2026-11-17",
    "2027-08-02",
    "2028-01-01",
]
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def _profile(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _report(path: Path, **changes: object) -> ClassificationReport:
    return classify(SystemProfile.model_validate({**_profile(path), **changes}))


def _example(name: str) -> Path:
    return ROOT / "examples" / f"{name}.json"


def _item(
    *,
    applies: bool | None = None,
    date: str | None = "2026-08-02",
    note: str | None = None,
    source_url: str = "https://example.test/source",
) -> ObligationGraphItem:
    return ObligationGraphItem(
        obligation_id="synthetic.1",
        article="Art. 9 AIA",
        actor=Role.PROVIDER,
        trigger="Synthetic trigger.",
        requirement="Synthetic requirement.",
        evidence_artifact="Synthetic evidence.",
        source_status=SourceStatus.BINDING_LEVEL_1,
        source_url=source_url,
        application_date=date,
        review_status=ReviewStatus.DETERMINED,
        application_date_note=note,
        applies_on_assessment_date=applies,
    )


def _record(**changes: object) -> EvidenceRecord:
    data: dict[str, object] = {
        "system_id": "credit-provider",
        "obligation_id": "high-risk.provider.9",
        "obligation_actor": "provider",
        "state": "in_progress",
        "owner": None,
        "reviewed_on": None,
        "report_digest": DIGEST_A,
        "item_digest": DIGEST_A,
        "revision": 1,
        "updated_by": "Local reviewer",
        "updated_at": "2026-11-17T00:00:00+00:00",
    }
    data.update(changes)
    return EvidenceRecord.model_validate(data)


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda path: path.stem)
def test_report_digest_is_stable_and_hex_for_every_example(path: Path) -> None:
    digest = report_digest(_report(path))
    assert digest == report_digest(_report(path))
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")


def test_report_digest_pins_its_algorithm() -> None:
    report = _report(_example("credit_scoring"))
    view = report.model_dump(
        mode="json", exclude={"advisory_notes", "classifier_version", "system"}
    )
    del view["scope"]["assessment_date"]
    for item in view["obligation_graph"]:
        del item["applies_on_assessment_date"]
    canonical = json.dumps(view, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert report_digest(report) == hashlib.sha256(canonical.encode()).hexdigest()

    item = report.obligation_graph[0]
    item_view = item.model_dump(mode="json")
    del item_view["applies_on_assessment_date"]
    item_canonical = json.dumps(
        item_view, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    assert item_digest(item) == hashlib.sha256(item_canonical.encode()).hexdigest()


@pytest.mark.parametrize("name", ["credit_scoring", "support_chatbot"])
def test_report_digest_ignores_advisory_version_name_and_assessment_date(name: str) -> None:
    path = _example(name)
    profile = SystemProfile.model_validate(_profile(path))
    baseline = report_digest(classify(profile))

    with_advisory = classify(profile, include_advisory=True)
    assert with_advisory.advisory_notes
    assert report_digest(with_advisory) == baseline
    bumped = classify(profile).model_copy(update={"classifier_version": "99.0.0"})
    assert report_digest(bumped) == baseline
    assert report_digest(_report(path, name="Renamed synthetic system")) == baseline
    assert report_digest(_report(path, assessment_date=None)) == baseline
    assert report_digest(_report(path, assessment_date="2026-11-17")) == baseline


def _with_first_item(report: ClassificationReport, **changes: object) -> ClassificationReport:
    graph = list(report.obligation_graph)
    graph[0] = graph[0].model_copy(update=changes)
    return report.model_copy(update={"obligation_graph": graph})


def _with_first_source(report: ClassificationReport, **changes: object) -> ClassificationReport:
    manifest = list(report.source_manifest)
    manifest[0] = manifest[0].model_copy(update=changes)
    return report.model_copy(update={"source_manifest": manifest})


@pytest.mark.parametrize(
    "change",
    [
        lambda report: _with_first_item(report, application_date="2030-01-01"),
        lambda report: _with_first_source(report, retrieved_on="2030-01-01"),
        lambda report: report.model_copy(update={"risk_tier": RiskTier.MINIMAL}),
    ],
    ids=["item-date", "manifest-retrieved-on", "risk-tier"],
)
def test_report_digest_changes_with_a_binding_change(change) -> None:
    report = _report(_example("credit_scoring"))
    assert report_digest(change(report)) != report_digest(report)


def test_report_digest_changes_where_the_assessment_date_changes_substance() -> None:
    # Art. 5(1)(ba) AIA applies from 2026-12-02: here the assessment date changes the
    # tier, findings and obligations, not only the lane flags.
    path = _example("intimate_imagery_generator")
    before = _report(path, assessment_date="2026-11-17")
    after = _report(path, assessment_date="2026-12-02")
    assert report_digest(before) != report_digest(after)


def test_report_digest_ignores_the_date_written_into_art_5_1_ba_prose() -> None:
    # The engine writes the assessment date into the (ba)/(bb) finding and open
    # question ("on the assessment date 2027-08-02 ..."). The digest leaves that value
    # out, so a new date stales nothing unless the outcome changes (2026-12-02).
    path = _example("intimate_imagery_generator")
    digests = {
        day: report_digest(_report(path, assessment_date=day))
        for day in ("2026-06-01", "2026-12-01", "2026-12-02", "2027-08-02", "2027-08-03")
    }
    assert digests["2026-06-01"] == digests["2026-12-01"]
    assert digests["2026-12-02"] == digests["2027-08-02"] == digests["2027-08-03"]
    assert digests["2026-12-01"] != digests["2026-12-02"]

    saved_on = _report(path, assessment_date="2027-08-02")
    first = saved_on.obligation_graph[0]
    record = _record(
        obligation_id=first.obligation_id,
        obligation_actor=first.actor.value,
        report_digest=report_digest(saved_on),
        item_digest=item_digest(first),
    )
    view = build_evidence_view(
        system_id="credit-provider",
        report=_report(path, assessment_date="2027-08-03"),
        records=[record],
        draft_notice=DRAFT_NOTICE,
    )
    assert view["counts"]["stale"] == 0


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda path: path.stem)
def test_item_digests_are_distinct_within_every_example_report(path: Path) -> None:
    report = _report(path)
    digests = [item_digest(item) for item in report.obligation_graph]
    keys = [(item.obligation_id, item.actor.value) for item in report.obligation_graph]
    assert len(set(digests)) == len(digests)
    assert len(set(keys)) == len(keys)


def test_item_digest_changes_when_a_positional_transparency_item_changes() -> None:
    # transparency.N is numbered by position, so the same id can name another duty.
    path = _example("support_chatbot")
    chatbot = find_item(_report(path), "transparency.1", "provider")
    generator = find_item(
        _report(path, interacts_with_natural_persons=False, generates_synthetic_content=True),
        "transparency.1",
        "provider",
    )
    assert chatbot is not None and generator is not None
    assert chatbot.article != generator.article
    assert item_digest(chatbot) != item_digest(generator)


@pytest.mark.parametrize(
    ("path", "assessment_date"),
    list(product(EXAMPLES, ASSESSMENT_DATES)),
    ids=lambda value: value.stem if isinstance(value, Path) else str(value),
)
def test_lane_grid_over_examples_and_assessment_dates(
    path: Path, assessment_date: str | None
) -> None:
    report = _report(path, assessment_date=assessment_date)
    for item in report.obligation_graph:
        lane = lane_for(item, report.scope.assessment_date)
        assert lane in LANES
        if item.applies_on_assessment_date is True:
            assert lane == "applies_now"
        elif item.application_date_note or item.application_date is None:
            assert lane == "contested_or_open"
        if item.applies_on_assessment_date is False:
            assert lane != "applies_now"
        # The lanes are relative to the assessment date: without one nothing is
        # "upcoming" or "applies now" unless the engine itself says it applies.
        if assessment_date is None:
            assert lane in ("applies_now", "no_assessment_date", "contested_or_open")
            if lane == "applies_now":
                assert item.applies_on_assessment_date is True
        else:
            assert lane != "no_assessment_date"
    view = build_evidence_view(
        system_id="grid", report=report, records=[], draft_notice=DRAFT_NOTICE
    )
    listed = [entry["obligationId"] for lane in view["lanes"] for entry in lane["items"]]
    assert sorted(listed) == sorted(item.obligation_id for item in report.obligation_graph)


@pytest.mark.parametrize(
    ("applies", "date", "note", "assessment_date", "lane"),
    [
        (True, "2026-08-02", "A note.", "2026-11-17", "applies_now"),
        (True, None, None, "2026-11-17", "applies_now"),
        (None, "2026-08-02", "A note.", "2026-11-17", "contested_or_open"),
        (False, "2026-08-02", "A note.", "2026-11-17", "contested_or_open"),
        (None, None, None, "2026-11-17", "contested_or_open"),
        (False, "2026-08-02", None, "2026-11-17", "upcoming"),
        (None, "2025-02-02", None, "2026-11-17", "applies_now"),
        (None, "2026-11-17", None, "2026-11-17", "applies_now"),
        (None, "2027-08-02", None, "2026-11-17", "upcoming"),
        # Without an assessment date a dated item is neither before nor after it.
        (None, "2025-02-02", None, None, "no_assessment_date"),
        (None, "2027-08-02", None, None, "no_assessment_date"),
        (None, "2025-02-02", "A note.", None, "contested_or_open"),
    ],
)
def test_lane_precedence_on_handmade_items(applies, date, note, assessment_date, lane) -> None:
    assert lane_for(_item(applies=applies, date=date, note=note), assessment_date) == lane


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda path: path.stem)
def test_retrieved_on_matches_the_item_source_for_every_example(path: Path) -> None:
    report = _report(path)
    for item in report.obligation_graph:
        source = next(s for s in report.source_manifest if s.url == item.source_url)
        assert retrieved_on_for(item, report) == source.retrieved_on == "2026-10-18"


def test_retrieved_on_falls_back_to_the_binding_source_then_the_first() -> None:
    report = _report(_example("credit_scoring"))
    unknown = _item(source_url="https://example.test/not-in-the-manifest")
    binding = next(s for s in report.source_manifest if s.source_id == "ai-act-2024-1689")
    assert retrieved_on_for(unknown, report) == binding.retrieved_on

    without_binding = report.model_copy(
        update={
            "source_manifest": [
                s.model_copy(update={"retrieved_on": "2026-06-18"})
                for s in report.source_manifest
                if s.source_id != "ai-act-2024-1689"
            ]
        }
    )
    assert retrieved_on_for(unknown, without_binding) == "2026-06-18"
    assert retrieved_on_for(unknown, report.model_copy(update={"source_manifest": []})) is None


@pytest.mark.parametrize(
    ("state", "same_report", "same_item", "reviewed_on"),
    [
        # A reviewed record without a reviewed-on date cannot be stored.
        case
        for case in product(
            ["not_started", "in_progress", "evidence_attached", "reviewed"],
            [True, False],
            [True, False],
            [None, "2026-10-01", "2026-10-18", "2026-11-01"],
        )
        if not (case[0] == "reviewed" and case[3] is None)
    ],
)
def test_stale_reasons_matrix(state, same_report, same_item, reviewed_on) -> None:
    record = _record(state=state, reviewed_on=reviewed_on)
    reasons = stale_reasons(
        record,
        current_report_digest=DIGEST_A if same_report else DIGEST_B,
        current_item_digest=DIGEST_A if same_item else DIGEST_B,
        retrieved_on="2026-10-18",
    )
    expected = []
    if state != "not_started":
        if not same_report:
            expected.append("report_changed")
        if not same_item:
            expected.append("item_changed")
        if reviewed_on == "2026-10-01":
            expected.append("reviewed_before_source_retrieval")
    assert reasons == expected
    assert reasons == [reason for reason in STALE_REASONS if reason in reasons]


def test_stale_reasons_without_a_record_or_a_retrieval_date() -> None:
    assert (
        stale_reasons(
            None,
            current_report_digest=DIGEST_B,
            current_item_digest=DIGEST_B,
            retrieved_on="2026-10-18",
        )
        == []
    )
    record = _record(reviewed_on="2020-01-01")
    assert (
        stale_reasons(
            record, current_report_digest=DIGEST_A, current_item_digest=DIGEST_A, retrieved_on=None
        )
        == []
    )


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda path: path.stem)
def test_view_lists_every_item_once_in_lane_order_with_counts_for_every_example(
    path: Path,
) -> None:
    report = _report(path, assessment_date="2026-11-17")
    first = report.obligation_graph[0] if report.obligation_graph else None
    records = []
    if first is not None:
        records.append(
            _record(
                system_id="sample",
                obligation_id=first.obligation_id,
                obligation_actor=first.actor.value,
                report_digest=report_digest(report),
                item_digest=item_digest(first),
                state="evidence_attached",
            )
        )
    view = build_evidence_view(
        system_id="sample", report=report, records=records, draft_notice=DRAFT_NOTICE
    )
    assert [lane["lane"] for lane in view["lanes"]] == list(LANES)
    items = [entry for lane in view["lanes"] for entry in lane["items"]]
    keys = [(entry["obligationId"], entry["actor"]) for entry in items]
    assert sorted(keys) == sorted(
        (item.obligation_id, item.actor.value) for item in report.obligation_graph
    )
    order = {
        (item.obligation_id, item.actor.value): i for i, item in enumerate(report.obligation_graph)
    }
    for lane in view["lanes"]:
        positions = [order[(entry["obligationId"], entry["actor"])] for entry in lane["items"]]
        assert positions == sorted(positions)
    assert list(view["counts"]) == list(EVIDENCE_STATES)
    assert sum(view["counts"].values()) == len(items)
    if first is not None:
        assert view["counts"]["evidence_attached"] == 1
        assert view["counts"]["not_started"] == len(items) - 1
    assert view["orphanedRecords"] == []
    assert view["schema"] == VIEW_SCHEMA
    assert view["assessmentDate"] == "2026-11-17"
    assert view["reportDigest"] == report_digest(report)


def test_view_marks_a_stale_item_and_keeps_its_stored_state() -> None:
    report = _report(_example("credit_scoring"))
    item = report.obligation_graph[0]
    record = _record(
        obligation_id=item.obligation_id,
        obligation_actor=item.actor.value,
        state="reviewed",
        reviewed_on="2026-10-01",
        owner="Owner A",
        report_digest=DIGEST_B,
        item_digest=item_digest(item),
        revision=3,
    )
    view = build_evidence_view(
        system_id="credit-provider", report=report, records=[record], draft_notice=DRAFT_NOTICE
    )
    entry = next(
        e
        for lane in view["lanes"]
        for e in lane["items"]
        if e["obligationId"] == item.obligation_id
    )
    assert entry["state"] == "stale"
    assert entry["storedState"] == "reviewed"
    assert entry["staleReasons"] == ["report_changed", "reviewed_before_source_retrieval"]
    assert (entry["owner"], entry["reviewedOn"], entry["revision"]) == ("Owner A", "2026-10-01", 3)
    assert entry["sourceRetrievedOn"] == "2026-10-18"
    assert view["counts"]["stale"] == 1


def test_view_lists_orphaned_records() -> None:
    report = _report(_example("credit_scoring"))
    orphan = _record(obligation_id="high-risk.provider.999", owner="Owner A")
    other_system = _record(system_id="chatbot", obligation_id="high-risk.provider.998")
    view = build_evidence_view(
        system_id="credit-provider",
        report=report,
        records=[orphan, other_system],
        draft_notice=DRAFT_NOTICE,
    )
    assert view["orphanedRecords"] == [
        {
            "obligationId": "high-risk.provider.999",
            "obligationActor": "provider",
            "state": "in_progress",
            "owner": "Owner A",
            "reviewedOn": None,
            "revision": 1,
        }
    ]


def test_view_starts_with_the_draft_notice() -> None:
    view = build_evidence_view(
        system_id="credit-provider",
        report=_report(_example("credit_scoring")),
        records=[],
        draft_notice=DRAFT_NOTICE,
    )
    assert list(view)[:2] == ["draftNotice", "schema"]
    assert view["draftNotice"] == DRAFT_NOTICE
    assert next(iter(json.loads(json.dumps(view)))) == "draftNotice"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("state", "stale"),
        ("state", "done"),
        ("system_id", "new-SECRET/../x"),
        ("system_id", "Credit"),
        ("system_id", ""),
        ("obligation_id", "a:b"),
        ("obligation_id", "../x"),
        ("obligation_actor", "lawyer"),
        ("reviewed_on", "2026-13-01"),
        ("reviewed_on", "17.11.2026"),
        ("owner", "x" * 121),
        ("report_digest", "A" * 64),
        ("item_digest", "a" * 63),
        ("revision", 0),
        ("updated_at", "yesterday"),
    ],
)
def test_evidence_record_rejects_stale_bad_ids_bad_date_long_owner_bad_digest(
    field: str, value: object
) -> None:
    with pytest.raises(ValidationError):
        _record(**{field: value})


def test_evidence_record_accepts_a_120_character_owner() -> None:
    assert _record(owner="x" * 120).owner == "x" * 120


def test_reviewed_record_requires_a_reviewed_on_date() -> None:
    with pytest.raises(ValidationError, match="a reviewed item needs a reviewed-on date"):
        _record(state="reviewed")
    assert _record(state="reviewed", reviewed_on="2026-10-18").state == "reviewed"


@pytest.mark.parametrize(
    ("system_id", "message"),
    [
        ("new", "the blank intake keeps no evidence"),
        ("SECRET-Upper", "systemId is not a cockpit system id"),
        ("../SECRET", "systemId is not a cockpit system id"),
        ("", "systemId is not a cockpit system id"),
        ("a" * 65, "systemId is not a cockpit system id"),
    ],
)
def test_check_system_id_rejects_new_and_bad_patterns_without_echo(
    system_id: str, message: str
) -> None:
    with pytest.raises(ValueError) as caught:
        check_system_id(system_id)
    assert str(caught.value) == message
    assert "SECRET" not in str(caught.value)


def test_check_system_id_accepts_the_cockpit_samples() -> None:
    samples = (ROOT / "web" / "lib" / "samples.ts").read_text(encoding="utf-8")
    ids = re.findall(r'^\s+id: "([^"]+)",$', samples, re.M)
    assert ids
    for system_id in ids:
        assert check_system_id(system_id) == system_id
