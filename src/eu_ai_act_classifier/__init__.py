"""Deterministic EU AI Act (Reg (EU) 2024/1689) classifier.

Public API::

    from eu_ai_act_classifier import classify, SystemProfile
    report = classify(SystemProfile(name="...", annex_iii_area=...))
    print(report.risk_tier, report.disposition)
"""

from __future__ import annotations

from .engine import classify
from .models import (
    AnnexIII,
    ClassificationReport,
    Derogation,
    Disposition,
    ExcludedUse,
    ProhibitedPractice,
    ReviewStatus,
    RiskTier,
    Role,
    ScopeStatus,
    SourceStatus,
    SystemProfile,
)
from .report import render_report

__version__ = "0.2.0"
__all__ = [
    "AnnexIII",
    "ClassificationReport",
    "Derogation",
    "Disposition",
    "ExcludedUse",
    "ProhibitedPractice",
    "ReviewStatus",
    "RiskTier",
    "Role",
    "ScopeStatus",
    "SourceStatus",
    "SystemProfile",
    "classify",
    "render_report",
]
