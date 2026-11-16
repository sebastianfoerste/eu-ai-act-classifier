"""Gate 1: prohibited practices (Art. 5 AIA).

A prohibited practice is a hard stop: the system may not be placed on the
market or put into service. This gate runs first and, if it fires, dominates
every other tier.

Points (a) to (h) are asserted by the reviewer in ``prohibited_practices``.
Points (ba) and (bb), inserted by Regulation (EU) 2026/1744, Art. 1, point (7),
apply from 2 December 2026 (Art. 113, third paragraph, point (a) AIA). They are
decided either from a declared 5.1.ba or 5.1.bb, which stands for every element,
or from the element facts in ``intimate_imagery`` and ``child_sexual_abuse_material``
read with Art. 5(1a) and (1b). The rule text was taken from the Official Journal
snapshot in ``sources/oj/32026R1744.en.xhtml``; reading choices the text leaves
open are labelled "Interpretation" in the finding or question that turns on them
(docs/methodology.md).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from itertools import product

from ..catalog import (
    ART_5_1A,
    ART_5_1B,
    LATER_PROHIBITIONS,
    PROHIBITED,
    section_b_kept_flag,
)
from ..citations import POINT_A_EXCEPTION_DATE, long_date
from ..models import Finding, ProhibitedPractice, RiskTier, Role, Severity, SystemProfile
from ..transitions import section_b_product
from .base import GateOutput, Tri, on_or_after, t_and, t_not, t_or

_LATER_FROM = long_date(POINT_A_EXCEPTION_DATE)  # "2 December 2026"
_SECTION_B_FLAG = section_b_kept_flag("Art. 5", "the prohibition")
# Asked where the profile records synthetic content or deep fakes but neither declares nor
# screens Art. 5(1)(ba) or (bb): from 2 December 2026 a general generator can fall under
# them through Art. 5(1a)(a)(ii) without generating such material being its purpose.
LATER_SCREEN_QUESTION = (
    f"Art. 5(1)(ba) and (bb) AIA (from {_LATER_FROM}): the profile records synthetic "
    "content or deep fakes but declares neither point. Confirm whether the system generates "
    "or manipulates the material these points describe within the limits of Art. 5(1a) "
    "and, for point (ba), Art. 5(1b). If so, declare 5.1.ba or 5.1.bb, or record the element "
    "facts in intimate_imagery and child_sexual_abuse_material. "
    # The limits in the Act's words, as the findings quote them: a paraphrase loses elements.
    f'Art. 5(1a): "{ART_5_1A}". Art. 5(1b): "{ART_5_1B}".'
)

Facts = dict[str, Tri]

# Art. 3(3) and (6) AIA: providers and importers place on the market or put into service;
# Art. 3(4): deployers use. A distributor makes available (Art. 3(7)), which is not the
# first making available that Art. 3(9) calls placing on the market.
_PLACING_ROLES = frozenset({Role.PROVIDER, Role.IMPORTER})
_USE_ROLES = frozenset({Role.DEPLOYER})


def evaluate(profile: SystemProfile) -> GateOutput:
    out = GateOutput()
    for practice in profile.prohibited_practices:
        if practice in LATER_PROHIBITIONS:
            continue  # decided with its date and roles in _later_points
        citation, label = PROHIBITED[practice]
        detail = (
            "Prohibited practice under Art. 5 AIA. The system may not be placed on the market, "
            "put into service, or used."
        )
        if section_b_product(profile):
            # Art. 2(2) AIA does not list Art. 5 for a Section B product.
            detail += f" {_SECTION_B_FLAG}"
        out.findings.append(
            Finding(
                rule_id=f"PROHIBITED.{practice.value}",
                citation=citation.ref,
                citation_verified=citation.verified,
                title=label,
                detail=detail,
                severity=Severity.BLOCKER,
                tier=RiskTier.PROHIBITED,
            )
        )
    if out.findings:
        out.tier_vote = RiskTier.PROHIBITED

    met = _later_points(profile, out)
    if (out.tier_vote is RiskTier.PROHIBITED or met) and section_b_product(profile):
        # The dossier and the cockpit list open questions, not finding details.
        out.open_questions.append(f"Art. 2(2) AIA and Art. 5 AIA: {_SECTION_B_FLAG}")
    return out


# --- Art. 5(1)(ba) and (bb) -------------------------------------------------


def _modality(f: Facts) -> Tri:
    """Art. 5(1a)(a): (i) the intended purpose, or (ii) a reasonably foreseeable and
    reproducible outcome, without requiring significant technical modification, of a system
    without reasonable and adequate technical safety measures and other safeguards."""

    return t_or(
        f["intended_purpose"],
        t_and(f["foreseeable_and_reproducible"], t_not(f["adequate_safeguards"])),
    )


def _ba_generation(f: Facts) -> Tri:
    """Art. 5(1b): manipulation counts only where it increases exposure or alters the
    depicted activity, which the fact states."""

    return t_or(f["generates_material"], f["manipulates_material_increasing_exposure"])


def _ba_content(f: Facts) -> Tri:
    """Art. 5(1)(ba) without consent."""

    return t_and(_ba_generation(f), t_not(f["consent_ensured"]))


def _bb_content(f: Facts) -> Tri:
    """Art. 5(1)(bb), unless a "without right" defence applies under national law."""

    return t_and(f["generates_or_manipulates"], t_not(f["without_right_defence_applies"]))


def _placing(content: Callable[[Facts], Tri]) -> Callable[[Facts], Tri]:
    return lambda f: t_and(content(f), _modality(f))


# Interpretation (C2): Art. 5(1a)(b) keeps the content element ("the use of an AI system that
# generates or manipulates the material") and adds the deployer's purpose; the Art. 5(1a)(a)
# conditions do not apply to use.
def _use(content: Callable[[Facts], Tri]) -> Callable[[Facts], Tri]:
    return lambda f: t_and(content(f), f["deployer_uses_for_that_purpose"])


@dataclass(frozen=True)
class _Point:
    letter: str
    practice: ProhibitedPractice
    field: str
    placing: Callable[[Facts], Tri]
    use: Callable[[Facts], Tri]
    # The content facts on whether the system generates or manipulates the material, and
    # the one that states generation.
    generation: Callable[[Facts], Tri]
    generation_fact: str


_POINTS = (
    _Point(
        "ba",
        ProhibitedPractice.NON_CONSENSUAL_INTIMATE_IMAGERY,
        "intimate_imagery",
        _placing(_ba_content),
        _use(_ba_content),
        _ba_generation,
        "generates_material",
    ),
    _Point(
        "bb",
        ProhibitedPractice.CHILD_SEXUAL_ABUSE_MATERIAL,
        "child_sexual_abuse_material",
        _placing(_bb_content),
        _use(_bb_content),
        lambda f: f["generates_or_manipulates"],
        "generates_or_manipulates",
    ),
)

# Facts that presuppose "that generation or manipulation": a reasonably foreseeable and
# reproducible outcome (Art. 5(1a)(a)(ii)) and the deployer's purpose (Art. 5(1a)(b)).
# Recital 12 of Regulation (EU) 2026/1744 counts a system for which the generation is such
# an outcome among the systems that generate the material, and brings within the use limb
# a deployer who uses for that purpose a lawful system not intended to generate it. A
# profile that affirms one of them and denies the generation contradicts itself; where the
# denial decides the result, the point is UNKNOWN, never "not met". Art. 5(1a)(a)(i) is
# left out: an intended purpose of manipulation that Art. 5(1b) does not count is not a
# contradiction (fixture ba-manipulation-without-increased-exposure-not-met).
_PRESUPPOSE_GENERATION = ("foreseeable_and_reproducible", "deployer_uses_for_that_purpose")
_AFFIRMS = {
    "foreseeable_and_reproducible": "a reasonably foreseeable and reproducible outcome "
    "(Art. 5(1a)(a)(ii))",
    "deployer_uses_for_that_purpose": "the deployer's purpose (Art. 5(1a)(b))",
}


def _decide(facts: Facts, point: _Point, roles: set[Role]) -> Tri:
    results: list[Tri] = []
    if roles & _PLACING_ROLES:
        results.append(point.placing(facts))
    if roles & _USE_ROLES:
        results.append(point.use(facts))
    if not results:
        # Interpretation (C3): no declared role places the system on the market, puts it
        # into service or uses it, so the result stays UNKNOWN unless the facts exclude
        # both limbs.
        return t_and(t_or(point.placing(facts), point.use(facts)), None)
    return t_or(*results)


def _material_unknowns(facts: Facts, point: _Point, roles: set[Role]) -> list[str]:
    """The null facts that decide the result under some answer to the other nulls. Brute
    force over at most seven facts. Empty where no role is covered: the role is then the
    open point."""

    if not roles & (_PLACING_ROLES | _USE_ROLES):
        return []
    unknown = [name for name, value in facts.items() if value is None]
    material = []
    for name in unknown:
        others = [n for n in unknown if n != name]
        for values in product((True, False), repeat=len(others)):
            completed = {**facts, **dict(zip(others, values, strict=True))}
            if _decide({**completed, name: True}, point, roles) != _decide(
                {**completed, name: False}, point, roles
            ):
                material.append(name)
                break
    return material


def _generation_conflicts(facts: Facts, point: _Point, roles: set[Role]) -> list[str]:
    """The facts that affirm the generation or manipulation the content facts deny, where
    the denial decides the result (_PRESUPPOSE_GENERATION). Empty where no role is covered:
    the role is then the open point."""

    if not roles & (_PLACING_ROLES | _USE_ROLES) or point.generation(facts) is not False:
        return []
    affirming = [name for name in _PRESUPPOSE_GENERATION if facts[name] is True]
    if not affirming:
        return []
    generated = {**facts, point.generation_fact: True}
    if _decide(generated, point, roles) == _decide(facts, point, roles):
        return []
    return affirming


def _decisive(name: str, facts: Facts, point: _Point, roles: set[Role]) -> bool:
    """Whether another value of ``name`` (true, false or null) changes the result."""

    result = _decide(facts, point, roles)
    return any(
        _decide({**facts, name: value}, point, roles) != result
        for value in (True, False, None)
        if value is not facts[name]
    )


def _interpretation_notes(facts: Facts, point: _Point, roles: set[Role]) -> list[str]:
    """Label the reading choices a screened result turns on (docs/methodology.md, choices
    C1, C2 and C10). A choice is named only where the result turns on it."""

    notes = []
    if (
        point.letter == "ba"
        and roles & _PLACING_ROLES
        and _decisive("consent_ensured", facts, point, roles)
    ):
        notes.append(
            "Interpretation (C1): for placing on the market or putting into service, consent is "
            "read at system level; the point is not met where the system generates or "
            "manipulates the material only with the depicted person's consent (Recital 12)."
        )
    placing_decides = bool(roles & _PLACING_ROLES) and point.placing(facts) is True
    # The content element C2 keeps also decides where the deployer's purpose is affirmed and
    # the content denied (_generation_conflicts).
    use_open = point.use(facts) is not False or facts["deployer_uses_for_that_purpose"] is True
    if roles & _USE_ROLES and use_open and not placing_decides:
        notes.append(
            "Interpretation (C2): for use, Art. 5(1a)(b) keeps the content element and the "
            "conditions of Art. 5(1a)(a) do not apply."
        )
    if point.letter == "bb" and _decisive("without_right_defence_applies", facts, point, roles):
        notes.append(
            "Interpretation (C10): whether a 'without right' defence applies under national "
            "law is a fact the reviewer establishes; the engine does not evaluate national law."
        )
    return notes


def _later_points(profile: SystemProfile, out: GateOutput) -> bool:
    """Art. 5(1)(ba) and (bb). Returns whether a point is met, whatever the date."""

    roles = set(profile.roles)
    generative = profile.generates_synthetic_content or profile.generates_deepfakes
    unscreened: list[_Point] = []
    met = False
    for point in _POINTS:
        declared = point.practice in profile.prohibited_practices
        screen = getattr(profile, point.field)
        if not declared and screen is None:
            unscreened.append(point)
            continue
        facts: Facts | None = screen.model_dump() if screen is not None else None
        conflicts: list[str] = []
        if declared:
            # The declaration stands for every element of the point; the roles still decide
            # whether the profile performs a prohibited act (C3).
            result: Tri = True if roles & (_PLACING_ROLES | _USE_ROLES) else None
            if facts is not None and _decide(facts, point, roles) is not True:
                out.open_questions.append(
                    f"Art. 5(1)({point.letter}) AIA: {point.practice.value} is declared, but the "
                    f"facts in {point.field} do not establish the point for the declared roles. "
                    "Confirm which is right; the report keeps the declaration."
                )
        else:
            result = _decide(facts or {}, point, roles)
            conflicts = _generation_conflicts(facts or {}, point, roles)
            if conflicts:
                result = None
        first = len(out.findings)
        if result is False:
            _not_met(point, out)
        elif result is None:
            _unknown(point, facts, roles, out, conflicts)
        else:
            met = True
            _met(point, profile, out)
        if not declared and facts is not None:
            notes = _interpretation_notes(facts, point, roles)
            for finding in out.findings[first:]:
                finding.detail = " ".join([finding.detail, *notes])
    # An unscreened point cannot change the result of a system already prohibited.
    if generative and unscreened and out.tier_vote is not RiskTier.PROHIBITED:
        if len(unscreened) == len(_POINTS):
            out.open_questions.append(LATER_SCREEN_QUESTION)
        else:
            (point,) = unscreened
            out.open_questions.append(
                f"Art. 5(1)({point.letter}) AIA (from {_LATER_FROM}): the profile records "
                f"synthetic content or deep fakes but neither declares {point.practice.value} "
                f"nor records the element facts in {point.field}. Confirm whether the system "
                "generates or manipulates the material the point describes."
            )
    return met


def _citation(point: _Point) -> tuple[str, bool, str]:
    citation, label = PROHIBITED[point.practice]
    return citation.ref, citation.verified, label


def _not_met(point: _Point, out: GateOutput) -> None:
    ref, verified, label = _citation(point)
    out.findings.append(
        Finding(
            rule_id=f"PROHIBITED.{point.practice.value}.not_met",
            citation=ref,
            citation_verified=verified,
            title=f"Not met: {label}",
            detail=(
                f"The facts in {point.field} do not meet Art. 5(1)({point.letter}) read with "
                "Art. 5(1a) AIA for the declared roles."
            ),
            severity=Severity.INFO,
        )
    )


def _unknown(
    point: _Point,
    facts: Facts | None,
    roles: set[Role],
    out: GateOutput,
    conflicts: list[str] | None = None,
) -> None:
    ref, verified, label = _citation(point)
    unknowns = _material_unknowns(facts, point, roles) if facts is not None else []
    if conflicts:
        affirming = "; ".join(
            f"{point.field}.{name} says it is {_AFFIRMS[name]}" for name in conflicts
        )
        question = (
            f"Art. 5(1)({point.letter}) AIA (from {_LATER_FROM}): the facts conflict on whether "
            f"the system generates or manipulates the material. {affirming}; but "
            f"{point.field}.{point.generation_fact} and the other content facts say the system "
            "does not generate or manipulate it. Recital 12 of Regulation (EU) 2026/1744 counts "
            "a system for which that generation is a reasonably foreseeable and reproducible "
            "outcome among the systems that generate the material, and covers a deployer who "
            "uses for that purpose a system not intended for it. Correct whichever fact is "
            "wrong; the point stays open until they agree."
        )
        if unknowns:
            needed = ", ".join(f"{point.field}.{name}" for name in unknowns)
            question += f" The result also turns on facts not established: {needed}."
    elif unknowns:
        needed = ", ".join(f"{point.field}.{name}" for name in unknowns)
        question = (
            f"Art. 5(1)({point.letter}) AIA (from {_LATER_FROM}): the result turns on facts not "
            f"established: {needed}. Establish them before relying on this classification."
        )
    else:
        question = (
            f"Art. 5(1)({point.letter}) AIA (from {_LATER_FROM}): no declared role places the "
            "system on the market, puts it into service or uses it. Confirm the operator's "
            "roles. Interpretation (C3): a distributor's making available is not the first "
            "making available that Art. 3(9) AIA calls placing on the market, so a "
            "distributor alone performs none of the acts the point prohibits."
        )
    out.findings.append(
        Finding(
            rule_id=f"PROHIBITED.{point.practice.value}.unknown",
            citation=ref,
            citation_verified=verified,
            title=f"Cannot be determined: {label}",
            detail=(
                f"Art. 5(1)({point.letter}) AIA may apply. "
                + (
                    "The facts conflict on a material point"
                    if conflicts
                    else "A material fact is UNKNOWN"
                )
                + ", so the engine neither applies nor excludes the prohibition."
            ),
            severity=Severity.MEDIUM,
        )
    )
    out.open_questions.append(question)


def _statute(point: _Point) -> str:
    """Art. 5(1)(ba) and (bb) AIA apply from 2 December 2026, not 2 February 2025. The
    sentence does not depend on the run date, so the output stays deterministic."""

    ref, _verified, _label = _citation(point)
    conditions = f'Art. 5(1a): "{ART_5_1A}".'
    if point.practice is ProhibitedPractice.NON_CONSENSUAL_INTIMATE_IMAGERY:
        conditions += f' Art. 5(1b): "{ART_5_1B}".'
    return (
        f"Prohibited practice under Art. 5 AIA from {_LATER_FROM} ({POINT_A_EXCEPTION_DATE}; "
        "Art. 113, third paragraph, point (a) AIA, as replaced by Regulation (EU) "
        "2026/1744), with no transition for systems already on the market: Art. 111(2) "
        "is without prejudice to Art. 5. "
        f'{ref}: "{LATER_PROHIBITIONS[point.practice]}". {conditions}'
    )


def _met(point: _Point, profile: SystemProfile, out: GateOutput) -> None:
    """The point is met. Before 2 December 2026 it does not yet apply and goes to review
    (C4); with no assessment date the prohibited tier is kept with review."""

    ref, verified, label = _citation(point)
    day = profile.assessment_date
    in_force = on_or_after(day, POINT_A_EXCEPTION_DATE)
    detail = _statute(point)
    if section_b_product(profile):
        detail += f" {_SECTION_B_FLAG}"
    if in_force is False:
        out.findings.append(
            Finding(
                rule_id=f"PROHIBITED.{point.practice.value}.not_yet_applicable",
                citation=ref,
                citation_verified=verified,
                title=f"Prohibited from {_LATER_FROM}: {label}",
                detail=(
                    f"The point is met, but on the assessment date {day} it does not yet apply. "
                    f"{detail}"
                ),
                severity=Severity.HIGH,
            )
        )
        out.open_questions.append(
            f"Art. 5(1)({point.letter}) AIA applies from {_LATER_FROM}, after the assessment "
            f"date {day}. From that date the system may not be placed on the market, put into "
            "service or used as described, with no transition for systems already on the "
            "market. Confirm how it is withdrawn or changed before that date."
        )
        return
    out.tier_vote = RiskTier.PROHIBITED
    if in_force is True:
        status = f"On the assessment date {day} the point applies."
    else:
        status = (
            "No assessment_date is given, so whether the point already applies is UNKNOWN. "
            "The prohibited tier is kept until the date is confirmed."
        )
        out.open_questions.append(
            f"Art. 5(1)({point.letter}) AIA applies from {_LATER_FROM}: give the "
            "assessment_date (the date of the placing on the market, putting into service or "
            "use under assessment). Before that date the point does not yet apply."
        )
    out.findings.append(
        Finding(
            rule_id=f"PROHIBITED.{point.practice.value}",
            citation=ref,
            citation_verified=verified,
            title=f"{label} (prohibited from {_LATER_FROM})",
            detail=f"{detail} {status}",
            severity=Severity.BLOCKER,
            tier=RiskTier.PROHIBITED,
        )
    )
