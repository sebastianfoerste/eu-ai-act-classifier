"""Evidence state for the cockpit's obligation tracker (ADR 0006).

The binding report stays as the engine wrote it. Reviewers record, per cockpit system
and obligation graph item, how far the evidence has come: a state, an owner and a
reviewed-on date. This module derives everything else from the report: the report and
item digests a record is checked against, the lane an item sits in, the retrieval date
of the item's source and the reasons a stored record has gone stale. Nothing here reads
a clock, a file or a model; the collaboration workspace stores the records.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .models import ClassificationReport, IsoDate, ObligationGraphItem, Role

EVIDENCE_STATES = ("not_started", "in_progress", "evidence_attached", "reviewed", "stale")
# "stale" is derived from the report and the source dates, never stored.
SettableState = Literal["not_started", "in_progress", "evidence_attached", "reviewed"]
# Lanes are relative to the report's assessment date (ADR 0006 D6).
LANES = ("applies_now", "upcoming", "no_assessment_date", "contested_or_open")
STALE_REASONS = ("report_changed", "item_changed", "reviewed_before_source_retrieval")
VIEW_SCHEMA = "cockpit.obligation-evidence.v1"
BINDING_SOURCE_ID = "ai-act-2024-1689"

# A cockpit sample id (web/lib/samples.ts), such as "credit-provider".
SYSTEM_ID_PATTERN = r"^[a-z0-9][a-z0-9-]{0,63}$"
OBLIGATION_ID_PATTERN = r"^[a-z0-9][a-z0-9._-]{0,79}$"
DIGEST_PATTERN = r"^[0-9a-f]{64}$"
# The cockpit's blank intake has no stable identity, so it keeps no evidence.
BLANK_INTAKE_ID = "new"


class EvidenceRecord(BaseModel):
    """One reviewer's record for one obligation graph item of one cockpit system."""

    system_id: str = Field(pattern=SYSTEM_ID_PATTERN)
    obligation_id: str = Field(pattern=OBLIGATION_ID_PATTERN)
    obligation_actor: Role
    state: SettableState
    owner: str | None = Field(None, max_length=120)
    reviewed_on: IsoDate | None = None
    report_digest: str = Field(pattern=DIGEST_PATTERN)
    item_digest: str = Field(pattern=DIGEST_PATTERN)
    revision: int = Field(ge=1)
    updated_by: str = Field(max_length=120)
    updated_at: str

    @field_validator("updated_at")
    @classmethod
    def _updated_at_is_iso(cls, value: str) -> str:
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise ValueError("updated_at must be an ISO 8601 date and time") from None
        return value

    @model_validator(mode="after")
    def _reviewed_has_a_date(self) -> EvidenceRecord:
        if self.state == "reviewed" and self.reviewed_on is None:
            raise ValueError("a reviewed item needs a reviewed-on date")
        return self

    def key(self) -> tuple[str, str, str]:
        return (self.system_id, self.obligation_id, self.obligation_actor.value)


def check_system_id(system_id: str) -> str:
    """``system_id`` when it names a cockpit system; the message never repeats it."""

    if system_id == BLANK_INTAKE_ID:
        raise ValueError("the blank intake keeps no evidence")
    if re.fullmatch(SYSTEM_ID_PATTERN, system_id) is None:
        raise ValueError("systemId is not a cockpit system id")
    return system_id


def _canonical(data: object) -> bytes:
    # surrogatepass: a lone surrogate copied from profile text still hashes; valid text
    # encodes exactly as with plain UTF-8.
    text = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8", errors="surrogatepass")


def _digest(data: object) -> str:
    return hashlib.sha256(_canonical(data)).hexdigest()


def report_digest(report: ClassificationReport) -> str:
    """The digest of what a report decides, for a cockpit system.

    Left out: the advisory notes (non-binding, they follow the advisory toggle), the
    classifier version (a version bump that changes no content changes nothing here),
    the system name (the record's key names the system) and the assessment date with
    the per-item ``applies_on_assessment_date`` flags (lane inputs). The engine also
    writes the date into the prose of Art. 5(1)(ba)/(bb) findings and open questions
    ("the assessment date 2027-08-02"); that value is removed from the hashed text, so
    only a change of substance (other fields, other sentences) moves the digest.
    """

    view = report.model_dump(
        mode="json", exclude={"advisory_notes", "classifier_version", "system"}
    )
    day = view["scope"].pop("assessment_date", None)
    for item in view["obligation_graph"]:
        item.pop("applies_on_assessment_date", None)
    if day:
        dated, undated = f"assessment date {day}", "assessment date"
        for finding in view["findings"]:
            for field, value in finding.items():
                if isinstance(value, str):
                    finding[field] = value.replace(dated, undated)
        view["open_questions"] = [text.replace(dated, undated) for text in view["open_questions"]]
    return _digest(view)


def item_digest(item: ObligationGraphItem) -> str:
    """The digest of one obligation graph item, without its assessment-date flag."""

    view = item.model_dump(mode="json")
    view.pop("applies_on_assessment_date", None)
    return _digest(view)


def lane_for(item: ObligationGraphItem, assessment_date: str | None) -> str:
    """The tracker lane for ``item`` under ADR 0006's precedence.

    1. The engine says the item applies on the assessment date: applies now, even with
       a note, since it applies on every reading.
    2. A note or no application date: contested or open.
    3. The engine says it does not apply yet: upcoming (after the assessment date).
    4. A defensive fallback the engine's output does not reach today: a date on or
       before the assessment date applies now.
    5. Otherwise upcoming, or ``no_assessment_date`` when the report has none: without
       it the tracker cannot place a dated item before or after anything.
    """

    if item.applies_on_assessment_date is True:
        return "applies_now"
    if item.application_date_note or item.application_date is None:
        return "contested_or_open"
    if item.applies_on_assessment_date is False:
        return "upcoming"
    if assessment_date is None:
        return "no_assessment_date"
    if item.application_date <= assessment_date:
        return "applies_now"
    return "upcoming"


def retrieved_on_for(item: ObligationGraphItem, report: ClassificationReport) -> str | None:
    """When the source the item cites was retrieved, from the report's own manifest.

    The manifest entry whose url is the item's source url; failing that the binding
    act's entry, then the first entry (the lookup the inventory uses). None for an
    empty manifest.
    """

    manifest = report.source_manifest
    source = next((entry for entry in manifest if entry.url == item.source_url), None)
    if source is None:
        source = next((entry for entry in manifest if entry.source_id == BINDING_SOURCE_ID), None)
    if source is None and manifest:
        source = manifest[0]
    return source.retrieved_on if source is not None else None


def find_item(
    report: ClassificationReport, obligation_id: str, actor: str
) -> ObligationGraphItem | None:
    return next(
        (
            item
            for item in report.obligation_graph
            if item.obligation_id == obligation_id and item.actor.value == actor
        ),
        None,
    )


def stale_reasons(
    record: EvidenceRecord | None,
    *,
    current_report_digest: str,
    current_item_digest: str,
    retrieved_on: str | None,
) -> list[str]:
    """Why a stored record no longer holds, in STALE_REASONS order; empty if it does.

    A missing record and a stored ``not_started`` are never stale. A reviewed-on date
    equal to the retrieval date is not older than it, so it is not stale either.
    """

    if record is None or record.state == "not_started":
        return []
    reasons = []
    if record.report_digest != current_report_digest:
        reasons.append("report_changed")
    if record.item_digest != current_item_digest:
        reasons.append("item_changed")
    # ISO dates compare as strings.
    if (
        record.reviewed_on is not None
        and retrieved_on is not None
        and (record.reviewed_on < retrieved_on)
    ):
        reasons.append("reviewed_before_source_retrieval")
    return reasons


def build_evidence_view(
    *,
    system_id: str,
    report: ClassificationReport,
    records: Sequence[EvidenceRecord],
    draft_notice: str,
) -> dict[str, object]:
    """The tracker as the cockpit shows and exports it, draft notice first.

    Every graph item appears once, in its lane, in the engine's order. Records of this
    system whose item is no longer in the report are listed as orphaned; they stay in
    the workspace.
    """

    by_key = {
        (record.obligation_id, record.obligation_actor.value): record
        for record in records
        if record.system_id == system_id
    }
    current_report = report_digest(report)
    assessment_date = report.scope.assessment_date
    counts = dict.fromkeys(EVIDENCE_STATES, 0)
    lanes: dict[str, list[dict[str, object]]] = {lane: [] for lane in LANES}
    seen: set[tuple[str, str]] = set()
    for item in report.obligation_graph:
        key = (item.obligation_id, item.actor.value)
        seen.add(key)
        record = by_key.get(key)
        retrieved_on = retrieved_on_for(item, report)
        reasons = stale_reasons(
            record,
            current_report_digest=current_report,
            current_item_digest=item_digest(item),
            retrieved_on=retrieved_on,
        )
        stored = record.state if record is not None else "not_started"
        state = "stale" if reasons else stored
        counts[state] += 1
        lanes[lane_for(item, assessment_date)].append(
            {
                "obligationId": item.obligation_id,
                "article": item.article,
                "actor": item.actor.value,
                "evidenceArtifact": item.evidence_artifact,
                "applicationDate": item.application_date,
                "applicationDateNote": item.application_date_note,
                "reviewStatus": item.review_status.value,
                "sourceRetrievedOn": retrieved_on,
                "state": state,
                "storedState": stored,
                "staleReasons": reasons,
                "owner": record.owner if record else None,
                "reviewedOn": record.reviewed_on if record else None,
                "revision": record.revision if record else 0,
                "updatedBy": record.updated_by if record else None,
                "updatedAt": record.updated_at if record else None,
            }
        )
    orphaned = [
        {
            "obligationId": record.obligation_id,
            "obligationActor": record.obligation_actor.value,
            "state": record.state,
            "owner": record.owner,
            "reviewedOn": record.reviewed_on,
            "revision": record.revision,
        }
        for key, record in by_key.items()
        if key not in seen
    ]
    return {
        "draftNotice": draft_notice,
        "schema": VIEW_SCHEMA,
        "systemId": system_id,
        "system": report.system,
        "classifierVersion": report.classifier_version,
        "assessmentDate": assessment_date,
        "reportDigest": current_report,
        "counts": counts,
        "lanes": [{"lane": lane, "items": lanes[lane]} for lane in LANES],
        "orphanedRecords": orphaned,
    }
