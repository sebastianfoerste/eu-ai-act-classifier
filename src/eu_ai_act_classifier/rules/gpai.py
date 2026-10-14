"""Gate 3: general-purpose AI models (Chapter V AIA).

GPAI status is orthogonal to the system risk tier: a model provider carries
Chapter V duties whatever tier the downstream system lands in. Systemic risk
is presumed above 10^25 FLOP of training compute (Art. 51(2)), or follows a
Commission designation (Art. 51(1)(b)). Where compute is unknown and there is
no designation, systemic-risk status is left open rather than assumed away.
"""

from __future__ import annotations

from ..citations import CHAPTER_V_APPLIES_FROM, GPAI_LEGACY_DEADLINE
from ..models import Finding, Severity
from .base import GateOutput

SYSTEMIC_FLOP_THRESHOLD = 1e25  # Art. 51(2) AIA presumption


def evaluate(profile) -> GateOutput:
    out = GateOutput()
    if not profile.is_gpai_model:
        return out

    out.is_gpai = True
    over_threshold = (
        profile.training_flops is not None and profile.training_flops > SYSTEMIC_FLOP_THRESHOLD
    )
    out.gpai_systemic = profile.gpai_systemic_risk_designated or over_threshold

    if out.gpai_systemic:
        basis = (
            "Commission designation (Art. 51(1)(b) AIA)"
            if profile.gpai_systemic_risk_designated
            else "training compute above the 10^25 FLOP presumption (Art. 51(2) AIA)"
        )
        out.findings.append(
            Finding(
                rule_id="GPAI.systemic",
                citation="Art. 51 AIA",
                title="General-purpose AI model with systemic risk",
                detail=f"Systemic risk on the basis of {basis}.",
                severity=Severity.HIGH,
            )
        )
    else:
        out.findings.append(
            Finding(
                rule_id="GPAI.baseline",
                citation="Art. 53 AIA",
                title="General-purpose AI model",
                detail="GPAI model provider obligations apply (Chapter V AIA).",
                severity=Severity.MEDIUM,
            )
        )

    if profile.training_flops is None and not profile.gpai_systemic_risk_designated:
        out.open_questions.append(
            "GPAI model: training compute (FLOP) not provided and no Commission designation, "
            "systemic-risk status under Art. 51 AIA cannot be determined. Provide training_flops "
            "or confirm designation."
        )

    _legacy_model_deadline(profile.placing_on_market_date, out)
    return out


def _legacy_model_deadline(placed_on: str | None, out: GateOutput) -> None:
    """Art. 111(3) AIA (original text): models placed before 2 August 2025 comply by
    2 August 2027. The obligation graph dates the Chapter V duties accordingly."""
    if placed_on is None:
        out.findings.append(
            Finding(
                rule_id="GPAI.111.3.placement_unknown",
                citation="Art. 111(3) AIA",
                title="GPAI obligations: application date unknown",
                detail=(
                    "The model's placing-on-the-market date is not given. Models placed before "
                    "2 August 2025 comply by 2 August 2027 (Art. 111(3) AIA); later models are "
                    "bound from placement (Art. 113, third paragraph, point (b) AIA)."
                ),
                severity=Severity.MEDIUM,
            )
        )
        out.open_questions.append(
            "Art. 111(3) AIA: give the GPAI model's placing_on_market_date. Models placed "
            "before 2 August 2025 comply by 2 August 2027; the application date of the "
            "Chapter V obligations is UNKNOWN until then."
        )
        return
    if placed_on < CHAPTER_V_APPLIES_FROM:
        out.findings.append(
            Finding(
                rule_id="GPAI.111.3.legacy",
                citation="Art. 111(3) AIA",
                title="GPAI model placed before 2 August 2025: comply by 2 August 2027",
                detail=(
                    f"Placed on the market on {placed_on}. Providers of general-purpose AI "
                    "models placed on the market before 2 August 2025 must comply by "
                    f"{GPAI_LEGACY_DEADLINE} (Art. 111(3) AIA)."
                ),
                severity=Severity.INFO,
            )
        )
