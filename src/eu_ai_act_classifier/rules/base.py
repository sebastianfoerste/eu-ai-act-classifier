"""Shared types for the classification gates.

Each gate is a pure function ``evaluate(profile) -> GateOutput``. A gate never
asserts a final conclusion; it votes a tier, records findings with citations,
and raises open questions where a fact must be characterised by a lawyer. The
engine aggregates the votes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import Finding, Obligation, RiskTier


@dataclass
class GateOutput:
    tier_vote: RiskTier | None = None
    findings: list[Finding] = field(default_factory=list)
    transparency: list[Obligation] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    is_gpai: bool = False
    gpai_systemic: bool = False
