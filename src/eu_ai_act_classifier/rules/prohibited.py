"""Gate 1: prohibited practices (Art. 5 AIA).

A prohibited practice is a hard stop: the system may not be placed on the
market or put into service. This gate runs first and, if it fires, dominates
every other tier.

Points (a) to (h) are asserted by the reviewer in ``prohibited_practices``.
Points (ba) and (bb), inserted by Art. 1(7) of Regulation (EU) 2026/1744,
are subsumed here from the facts in ``intimate_imagery`` and
``child_sexual_abuse_material``, read with Art. 5(1a) and (1b), and apply
only from 2 December 2026 (Art. 113, third paragraph, point (a) AIA). The
rule text was taken from the Official Journal snapshot in
``sources/oj/32026R1744.en.xhtml``; reading choices the text leaves open are
labelled "interpretation" in the finding text.
"""

from __future__ import annotations

from collections.abc import Callable
from itertools import product

from ..catalog import NEW_PROHIBITIONS, PROHIBITED
from ..citations import NEW_PROHIBITIONS_APPLY_FROM
from ..models import Finding, RiskTier, Role, Severity, SystemProfile
from .base import GateOutput, Tri, on_or_after, t_and, t_not, t_or

Facts = dict[str, Tri]

_PLACING_ROLES = {Role.PROVIDER, Role.IMPORTER}  # placing on the market, putting into service
_USE_ROLES = {Role.DEPLOYER}  # use


def evaluate(profile: SystemProfile) -> GateOutput:
    out = GateOutput()
    for practice in profile.prohibited_practices:
        citation, label = PROHIBITED[practice]
        out.findings.append(
            Finding(
                rule_id=f"PROHIBITED.{practice.value}",
                citation=citation.ref,
                citation_verified=citation.verified,
                title=label,
                detail=(
                    "Prohibited practice under Art. 5 AIA. The system may not be "
                    "placed on the market, put into service, or used."
                ),
                severity=Severity.BLOCKER,
                tier=RiskTier.PROHIBITED,
            )
        )
    if out.findings:
        out.tier_vote = RiskTier.PROHIBITED

    _screen_new_prohibitions(profile, out)
    return out


# --- Art. 5(1)(ba) and (bb) -------------------------------------------------


def _modality(f: Facts) -> Tri:
    """Art. 5(1a)(a): intended purpose, or a foreseeable and reproducible outcome
    without reasonable and adequate safeguards."""
    return t_or(
        f["intended_purpose"],
        t_and(f["foreseeable_and_reproducible"], t_not(f["adequate_safeguards"])),
    )


def _ba_content(f: Facts) -> Tri:
    """Art. 5(1)(ba) without consent. Art. 5(1b): manipulation counts only where it
    increases exposure or alters the depicted activity, which the fact states."""
    generates = t_or(f["generates_material"], f["manipulates_material_increasing_exposure"])
    return t_and(generates, t_not(f["consent_ensured"]))


def _bb_content(f: Facts) -> Tri:
    """Art. 5(1)(bb), unless a 'without right' defence applies under national law."""
    return t_and(f["generates_or_manipulates"], t_not(f["without_right_defence_applies"]))


def _ba_placing(f: Facts) -> Tri:
    return t_and(_ba_content(f), _modality(f))


def _bb_placing(f: Facts) -> Tri:
    return t_and(_bb_content(f), _modality(f))


# interpretation (INT-5-deployer-route): Art. 5(1a)(b) keeps the content element
# ("the use of an AI system that generates or manipulates the material") and adds
# the deployer's purpose; the Art. 5(1a)(a) conditions do not apply to use.
def _ba_use(f: Facts) -> Tri:
    return t_and(_ba_content(f), f["deployer_uses_for_that_purpose"])


def _bb_use(f: Facts) -> Tri:
    return t_and(_bb_content(f), f["deployer_uses_for_that_purpose"])


_RULES: dict[str, tuple[str, Callable[[Facts], Tri], Callable[[Facts], Tri]]] = {
    "ba": ("intimate_imagery", _ba_placing, _ba_use),
    "bb": ("child_sexual_abuse_material", _bb_placing, _bb_use),
}


def _decide(
    facts: Facts,
    placing: Callable[[Facts], Tri],
    use: Callable[[Facts], Tri],
    roles: set[Role],
) -> Tri:
    results: list[Tri] = []
    if roles & _PLACING_ROLES:
        results.append(placing(facts))
    if roles & _USE_ROLES:
        results.append(use(facts))
    if not results:
        # interpretation (INT-5-routes-by-role): no declared role places the
        # system on the market, puts it into service or uses it, so the result
        # stays UNKNOWN unless the facts exclude both limbs. Testing only the
        # placing limb here turned a met use limb into a silent "not met".
        return t_and(t_or(placing(facts), use(facts)), None)
    return t_or(*results)


def _material_unknowns(
    facts: Facts,
    placing: Callable[[Facts], Tri],
    use: Callable[[Facts], Tri],
    roles: set[Role],
) -> list[str]:
    """The null facts that decide the result under some answer to the other nulls.

    Brute force over at most seven facts. Requires a role that places the system
    on the market, puts it into service or uses it; otherwise the role is the open
    point and no fact is listed.
    """
    if not roles & (_PLACING_ROLES | _USE_ROLES):
        return []
    unknown = [name for name, value in facts.items() if value is None]
    material = []
    for name in unknown:
        others = [n for n in unknown if n != name]
        for values in product((True, False), repeat=len(others)):
            completed = {**facts, **dict(zip(others, values, strict=True))}
            if _decide({**completed, name: True}, placing, use, roles) != _decide(
                {**completed, name: False}, placing, use, roles
            ):
                material.append(name)
                break
    return material


def _screen_new_prohibitions(profile: SystemProfile, out: GateOutput) -> None:
    missing = [
        field for field, _placing, _use in _RULES.values() if getattr(profile, field) is None
    ]
    generative = profile.generates_synthetic_content or profile.generates_deepfakes
    if missing and generative:
        _not_screened(missing, out)

    in_force = on_or_after(profile.assessment_date, NEW_PROHIBITIONS_APPLY_FROM)
    roles = set(profile.roles)
    for point, (field, placing, use) in _RULES.items():
        screen = getattr(profile, field)
        if screen is None:
            continue
        facts: Facts = screen.model_dump()
        result = _decide(facts, placing, use, roles)
        citation, label = NEW_PROHIBITIONS[point]
        rule_id = f"PROHIBITED.5.1.{point}"
        first_new = len(out.findings)
        if result is False:
            out.findings.append(
                Finding(
                    rule_id=f"{rule_id}.not_met",
                    citation=citation.ref,
                    title=f"Not met: {label}",
                    detail=(
                        f"The facts in {field} do not meet Art. 5(1)({point}) read with "
                        "Art. 5(1a) AIA for the declared roles."
                    ),
                    severity=Severity.INFO,
                )
            )
        elif result is None:
            _unknown(point, field, facts, placing, use, roles, rule_id, citation.ref, label, out)
        else:
            _met(point, profile.assessment_date, in_force, rule_id, citation.ref, label, out)
        notes = _interpretation_notes(point, facts, roles)
        for finding in out.findings[first_new:]:
            finding.detail = " ".join([finding.detail, *notes])


def _interpretation_notes(point: str, facts: Facts, roles: set[Role]) -> list[str]:
    """Label the reading choices that decide this result (docs/methodology.md).

    A choice is named only where the result turns on it: a fact that settles the
    point under every reading needs no label.
    """
    notes = []
    if point == "ba" and roles & _PLACING_ROLES and facts["consent_ensured"] is not False:
        notes.append(
            "Interpretation: for placing on the market or putting into service, consent is "
            "read at system level; the point is not met where the system generates or "
            "manipulates the material only with the depicted person's consent."
        )
    if roles & _USE_ROLES and facts["deployer_uses_for_that_purpose"] is not False:
        notes.append(
            "Interpretation: for use, Art. 5(1a)(b) keeps the content element and the "
            "conditions of Art. 5(1a)(a) do not apply."
        )
    if point == "bb" and facts["generates_or_manipulates"] is not False:
        notes.append(
            "Interpretation: whether a 'without right' defence applies under national law "
            "is a fact the reviewer establishes; the engine does not evaluate national law."
        )
    return notes


def _not_screened(missing: list[str], out: GateOutput) -> None:
    fields = " and ".join(missing)
    out.findings.append(
        Finding(
            rule_id="PROHIBITED.5.1.ba_bb.not_screened",
            citation="Art. 5(1)(ba) and (bb) AIA",
            title="Art. 5(1)(ba) and (bb) screen not completed for a generative system",
            detail=(
                "The profile marks the system as generating synthetic content or deep fakes. "
                "From 2 December 2026, Art. 5(1)(ba) and (bb) AIA prohibit systems that "
                "generate or manipulate non-consensual intimate imagery or child sexual abuse "
                "material. Interpretation: a missing screen is not read as a negative answer."
            ),
            severity=Severity.MEDIUM,
        )
    )
    out.open_questions.append(
        f"Art. 5(1)(ba) and (bb) AIA (from 2 December 2026): complete {fields} for this "
        "system that generates synthetic content or deep fakes."
    )


def _unknown(
    point: str,
    field: str,
    facts: Facts,
    placing: Callable[[Facts], Tri],
    use: Callable[[Facts], Tri],
    roles: set[Role],
    rule_id: str,
    citation: str,
    label: str,
    out: GateOutput,
) -> None:
    unknowns = _material_unknowns(facts, placing, use, roles)
    if unknowns:
        needed = ", ".join(f"{field}.{name}" for name in unknowns)
        question = (
            f"Art. 5(1)({point}) AIA (from 2 December 2026): the result turns on facts not "
            f"established: {needed}. Establish them before relying on this classification."
        )
    else:
        question = (
            f"Art. 5(1)({point}) AIA (from 2 December 2026): the declared roles do not place "
            "the system on the market, put it into service or use it. Confirm the operator's "
            "roles; interpretation: a distributor's making available is not one of those acts."
        )
    out.findings.append(
        Finding(
            rule_id=f"{rule_id}.unknown",
            citation=citation,
            title=f"Cannot be determined: {label}",
            detail=(
                f"Art. 5(1)({point}) AIA may apply. A material fact is UNKNOWN, so the engine "
                "neither applies nor excludes the prohibition."
            ),
            severity=Severity.MEDIUM,
        )
    )
    out.open_questions.append(question)


def _met(
    point: str,
    assessment_date: str | None,
    in_force: Tri,
    rule_id: str,
    citation: str,
    label: str,
    out: GateOutput,
) -> None:
    applies_from = "Art. 113, third paragraph, point (a) AIA: applies from 2 December 2026."
    if in_force is True:
        out.tier_vote = RiskTier.PROHIBITED
        out.findings.append(
            Finding(
                rule_id=rule_id,
                citation=citation,
                title=label,
                detail=(
                    "Prohibited practice under Art. 5 AIA on the assessment date "
                    f"{assessment_date}. The system may not be placed on the market, put into "
                    f"service, or used for this purpose. {applies_from}"
                ),
                severity=Severity.BLOCKER,
                tier=RiskTier.PROHIBITED,
            )
        )
        return
    if in_force is False:
        out.findings.append(
            Finding(
                rule_id=f"{rule_id}.not_yet_applicable",
                citation=citation,
                title=f"Prohibited from 2 December 2026: {label}",
                detail=(
                    f"The facts meet Art. 5(1)({point}) AIA, but on the assessment date "
                    f"{assessment_date} the point does not yet apply. {applies_from}"
                ),
                severity=Severity.HIGH,
            )
        )
        out.open_questions.append(
            f"Art. 5(1)({point}) AIA applies from 2 December 2026, after the assessment date "
            f"{assessment_date}. From that date the system may not be placed on the market, "
            "put into service or used as described. Interpretation: plan withdrawal or "
            "redesign before that date."
        )
        return
    out.tier_vote = RiskTier.PROHIBITED
    out.findings.append(
        Finding(
            rule_id=f"{rule_id}.date_unknown",
            citation=citation,
            title=f"Prohibited at the latest from 2 December 2026: {label}",
            detail=(
                f"The facts meet Art. 5(1)({point}) AIA. No assessment date is given, so whether "
                "the point already applies is UNKNOWN. Interpretation: the prohibited tier is "
                f"kept until the date is confirmed. {applies_from}"
            ),
            severity=Severity.BLOCKER,
            tier=RiskTier.PROHIBITED,
        )
    )
    out.open_questions.append(
        f"Art. 5(1)({point}) AIA: give the assessment_date (the date of the placing on the "
        "market, putting into service or use under assessment). The point applies from "
        "2 December 2026."
    )
