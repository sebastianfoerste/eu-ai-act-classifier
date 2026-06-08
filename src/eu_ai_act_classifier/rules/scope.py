"""Gate 0 - scope and intake screening.

The classifier is useful only if the submitted profile is an AI system with a
relevant EU nexus. Existing alpha profiles remain in scope by default; callers
can now make scope uncertainty explicit.
"""

from __future__ import annotations

from ..models import Finding, RiskTier, ScopeAssessment, ScopeStatus, Severity, SystemProfile


def evaluate(profile: SystemProfile) -> tuple[ScopeAssessment, list[Finding], list[str]]:
    findings: list[Finding] = []
    open_questions: list[str] = []
    notes: list[str] = []
    status = ScopeStatus.IN_SCOPE

    if profile.is_ai_system is False:
        status = ScopeStatus.OUTSIDE_SCOPE
        findings.append(
            Finding(
                rule_id="SCOPE.not_ai_system",
                citation="Art. 3(1) AIA",
                title="Outside scope: submitted system is not an AI system",
                detail="The profile states that the software does not qualify as an AI system.",
                severity=Severity.INFO,
                tier=RiskTier.OUT_OF_SCOPE,
            )
        )
        notes.append("No AI Act classification is performed because the profile is outside scope.")

    if profile.is_ai_system is None:
        status = ScopeStatus.REQUIRES_REVIEW
        open_questions.append(
            "Scope: confirm whether the software qualifies as an AI system under Art. 3(1) AIA."
        )
        findings.append(
            Finding(
                rule_id="SCOPE.ai_system_unknown",
                citation="Art. 3(1) AIA",
                title="Scope requires review: AI-system status not confirmed",
                severity=Severity.MEDIUM,
            )
        )

    if profile.eu_nexus is False:
        status = ScopeStatus.OUTSIDE_SCOPE
        open_questions = [
            q
            for q in open_questions
            if not q.startswith("Scope: confirm whether the system has an EU nexus")
        ]
        findings.append(
            Finding(
                rule_id="SCOPE.no_eu_nexus",
                citation="Art. 2 AIA",
                title="Outside scope: no EU nexus",
                detail=(
                    "The profile states that the system is not placed on, put into service "
                    "in, or used in the EU market."
                ),
                severity=Severity.INFO,
                tier=RiskTier.OUT_OF_SCOPE,
            )
        )
        notes.append("No EU nexus is asserted in the submitted profile.")
    elif profile.eu_nexus is None:
        if status is not ScopeStatus.OUTSIDE_SCOPE:
            status = ScopeStatus.REQUIRES_REVIEW
        open_questions.append("Scope: confirm whether the system has an EU nexus under Art. 2 AIA.")
        findings.append(
            Finding(
                rule_id="SCOPE.eu_nexus_unknown",
                citation="Art. 2 AIA",
                title="Scope requires review: EU nexus not confirmed",
                severity=Severity.MEDIUM,
            )
        )

    if profile.excluded_use_flags:
        if status is not ScopeStatus.OUTSIDE_SCOPE:
            status = ScopeStatus.REQUIRES_REVIEW
        flags = ", ".join(flag.value for flag in profile.excluded_use_flags)
        open_questions.append(
            f"Scope: excluded-use flags are asserted ({flags}); confirm whether an Art. 2 "
            "exclusion applies."
        )
        findings.append(
            Finding(
                rule_id="SCOPE.excluded_use_flags",
                citation="Art. 2 AIA",
                title="Scope requires review: potential exclusion or carve-out asserted",
                detail=f"Submitted excluded-use flags: {flags}.",
                severity=Severity.MEDIUM,
            )
        )

    transitional_status = _transitional_status(profile)
    if transitional_status:
        notes.append(transitional_status)

    return (
        ScopeAssessment(
            status=status,
            is_ai_system=profile.is_ai_system,
            intended_purpose_source=profile.intended_purpose_source,
            eu_nexus=profile.eu_nexus,
            excluded_use_flags=profile.excluded_use_flags,
            transitional_status=transitional_status
            or "No transitional limitation identified from the submitted facts.",
            notes=notes,
        ),
        findings,
        open_questions,
    )


def _transitional_status(profile: SystemProfile) -> str:
    if (
        profile.placing_on_market_date
        and profile.significant_change_after_application_date is False
    ):
        return (
            "Article 111 check: the system was placed on the market before the relevant "
            "application date and no significant change is asserted. Confirm the exact "
            "legacy treatment before relying on this classification."
        )
    if profile.significant_change_after_application_date is True:
        return (
            "Article 111 check: a significant change after the relevant application date is "
            "asserted, so AI Act requirements may apply to the changed system."
        )
    if profile.public_authority_use:
        return (
            "Article 111 check: public-authority use may be subject to the special 2 August "
            "2030 transition for certain high-risk systems."
        )
    return ""
