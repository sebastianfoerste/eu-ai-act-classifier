"""Shared types for the classification gates.

Each gate is a pure function ``evaluate(profile) -> GateOutput``. A gate never
asserts a final conclusion; it votes a tier, records findings with citations,
and raises open questions where a fact must be characterised by a lawyer. The
engine aggregates the votes.

Three-valued facts use Kleene logic: ``None`` is UNKNOWN. A conjunction is
false as soon as one element is false, true only when every element is true,
and UNKNOWN otherwise; a disjunction mirrors that. An unknown fact therefore
never turns into a pass, and an unknown fact that cannot change the result
does not hold the result open.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import Finding, Obligation, RiskTier

Tri = bool | None


def t_and(*values: Tri) -> Tri:
    if any(v is False for v in values):
        return False
    if all(v is True for v in values):
        return True
    return None


def t_or(*values: Tri) -> Tri:
    if any(v is True for v in values):
        return True
    if all(v is False for v in values):
        return False
    return None


def t_not(value: Tri) -> Tri:
    return None if value is None else not value


def on_or_after(day: str | None, threshold: str) -> Tri:
    """Whether an ISO date falls on or after ``threshold``; UNKNOWN without a date."""
    return None if day is None else day >= threshold


@dataclass
class GateOutput:
    tier_vote: RiskTier | None = None
    findings: list[Finding] = field(default_factory=list)
    transparency: list[Obligation] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    is_gpai: bool = False
    gpai_systemic: bool = False
    # "A" or "B" where the Art. 6(1) route applies and the Annex I legislation
    # is named; None otherwise.
    annex_i_section: str | None = None
