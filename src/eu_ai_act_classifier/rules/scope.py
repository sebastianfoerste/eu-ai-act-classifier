"""Gate 0 - scope and intake screening.

The classifier is useful only if the submitted profile is an AI system with a
relevant EU nexus. Existing alpha profiles remain in scope by default; callers
can now make scope uncertainty explicit.
"""

from __future__ import annotations

from ..catalog import SECTION_B_PROVISIONS
from ..citations import (
    ART_111_3_DEADLINE,
    ART_111_4_DEADLINE,
    GENERAL_APPLICATION_DATE,
    POINT_B_DATE,
)
from ..models import Finding, RiskTier, ScopeAssessment, ScopeStatus, Severity, SystemProfile
from ..transitions import (
    ANNEX_X_CARVE_OUT,
    PUBLIC_AUTHORITY_DUTY,
    before,
    chapter_iii_date,
    chapter_iii_point,
    cut_off_flag,
    derogation_note,
    describe_dates,
    gpai_model_date,
    legacy_dates,
    market_dates,
    public_authority_sentence,
    section_b_only,
    undated_public_authority_sentence,
)


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

    # Outside scope, no AI Act provision applies, so there is no transition to check.
    transitional_status = (
        "" if status is ScopeStatus.OUTSIDE_SCOPE else _transitional_status(profile)
    )
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
    """The Art. 111 AIA transitions the submitted facts touch: Art. 111(2) for a high-risk
    system, Art. 111(3) for a general-purpose AI model and Art. 111(4) for Art. 50(2)."""

    parts = [_art_111_2_status(profile), _art_111_3_status(profile), _art_111_4_status(profile)]
    return " ".join(part for part in parts if part)


def _art_111_2_status(profile: SystemProfile) -> str:
    """Art. 111(2) AIA check: the given dates against the Chapter III date for the
    system's high-risk route (Art. 113, third paragraph, point (c) AIA)."""

    facts = bool(market_dates(profile)) or (
        profile.significant_change_after_application_date is not None
        or profile.public_authority_use
        or bool(profile.deployer_public_authority)
    )
    if not facts:
        return ""
    if profile.prohibited_practices:
        return (
            "Article 111(2) check: not applied, as an Art. 5 prohibited practice is screened. "
            "Art. 111(2) is without prejudice to Art. 5, so the transition does not defer the "
            "prohibition, whatever the placing-on-market or putting-into-service date."
        )
    if section_b_only(profile):
        return (
            f"Article 111(2) check: Annex I, Section B product: {SECTION_B_PROVISIONS} "
            "(Art. 2(2) AIA). Art. 111 is among them, but no Chapter III duty attaches to the "
            "product through this Regulation, so the transition has nothing to defer and the "
            "submitted facts are not compared with a Chapter III date."
        )
    cut_off = chapter_iii_date(profile)
    if cut_off is None:
        return _no_high_risk_route(profile)

    dates = market_dates(profile)
    applies = (
        f"{cut_off}, when Chapter III, Sections 1 to 3 apply to this system (Art. 113, "
        f"third paragraph, {chapter_iii_point(cut_off)} AIA)"
    )
    # Which Chapter III date Art. 111(2) means is contested, so every result that rests
    # on it carries the flag.
    flag = f" {cut_off_flag(profile, cut_off)}"
    if not dates:
        return (
            "Article 111(2) check: no placing-on-market or putting-into-service date is "
            f"given to compare with {applies}. {_undated_change_sentence(profile)}"
            f"{undated_public_authority_sentence(profile)}{flag}"
        )
    legacy = legacy_dates(profile, cut_off)
    derogation = derogation_note(profile, cut_off)
    if not legacy:
        text = (
            f"Article 111(2) check: the system was {describe_dates(dates)}, not before "
            f"{applies}, so the Art. 111(2) transition does not apply."
        )
        return f"{text} {derogation}" if derogation else text
    # Either date before the cut-off makes it a legacy system; a later one is stated as given.
    later = [date for date in dates if date not in legacy]
    text = f"Article 111(2) check: the system was {describe_dates(legacy)}, before {applies}"
    if later:
        text += f", and {describe_dates(later)}"
    text += (
        f": {_change_clause(profile)}.{public_authority_sentence(profile)} Art. 111(2) "
        f"excludes {ANNEX_X_CARVE_OUT}."
    )
    if derogation:
        text += f" {derogation}"
    return f"{text}{flag}"


def _change_clause(profile: SystemProfile) -> str:
    """The clause after "before <cut-off>, when Chapter III ... applies", so "that date"
    is the cut-off. An asserted change is not dated: which date it must follow is the
    contested point the flag states."""

    change = profile.significant_change_after_application_date
    if change is True:
        return (
            "a significant change in design is asserted, so the Regulation applies to the "
            "changed system"
        )
    if change is False:
        return (
            "no significant change in design is asserted, so apart from Art. 5 the Regulation "
            "applies to it only if its design changes significantly as from that date"
        )
    return (
        "apart from Art. 5 the Regulation applies to it only if its design changes "
        "significantly as from that date; confirm whether it has"
    )


def _art_111_3_status(profile: SystemProfile) -> str:
    """Art. 111(3) AIA: a general-purpose AI model placed on the market before
    2 August 2025 has until 2 August 2027. Not for a prohibited practice, which gets no
    Chapter V items."""

    if not profile.is_gpai_model:
        if profile.gpai_model_placing_on_market_date is None:
            return ""
        return (
            "Article 111(3) check: gpai_model_placing_on_market_date is given, but no "
            "general-purpose AI model is screened (is_gpai_model is false), so the date is "
            "not used."
        )
    model_date, fallback = gpai_model_date(profile)
    if model_date is None or profile.prohibited_practices:
        return ""
    if fallback:
        dated = (
            "with no gpai_model_placing_on_market_date given, the general-purpose AI model is "
            f"dated by the AI system's placing_on_market_date, {model_date}"
        )
    else:
        dated = f"the general-purpose AI model was placed on the market on {model_date}"
    if before(model_date, POINT_B_DATE):
        return (
            f"Article 111(3) check: {dated}, before {POINT_B_DATE}, so its provider takes the "
            "necessary steps to comply with the obligations laid down in this Regulation by "
            f"{ART_111_3_DEADLINE}."
        )
    return (
        f"Article 111(3) check: {dated}, not before {POINT_B_DATE}, so the Art. 111(3) "
        "transition does not apply."
    )


def _art_111_4_status(profile: SystemProfile) -> str:
    """Art. 111(4) AIA: Art. 50(2) for a system placed on the market before
    2 August 2026 applies from 2 December 2026."""

    placed = profile.placing_on_market_date
    if not profile.generates_synthetic_content or placed is None:
        return ""
    if before(placed, GENERAL_APPLICATION_DATE):
        return (
            f"Article 111(4) check: the system was placed on the market on {placed}, before "
            f"{GENERAL_APPLICATION_DATE}, so its provider takes the necessary steps to comply "
            f"with Art. 50(2) by {ART_111_4_DEADLINE}."
        )
    return (
        f"Article 111(4) check: the system was placed on the market on {placed}, not before "
        f"{GENERAL_APPLICATION_DATE}, so the Art. 111(4) transition does not apply."
    )


def _undated_change_sentence(profile: SystemProfile) -> str:
    change = profile.significant_change_after_application_date
    if change is True:
        # Art. 111(2): for a system already on the market the change counts only "as from
        # that date"; the undated profile cannot show which case it is.
        return (
            "A significant change in design is asserted, so the Regulation applies to the "
            "changed system even if it was placed on the market or put into service before "
            "that date, provided the change was made as from that date."
        )
    if_legacy = "If the system was placed on the market or put into service before that date"
    if change is False:
        return (
            f"No significant change in design is asserted. {if_legacy}, apart from Art. 5 "
            "the Regulation applies to it only if its design changes significantly as from "
            "that date."
        )
    return (
        f"{if_legacy}, apart from Art. 5 the Regulation applies to it only if its design "
        "changes significantly as from that date."
    )


def _no_high_risk_route(profile: SystemProfile) -> str:
    dates = market_dates(profile)
    if dates:
        return (
            f"Article 111(2) check: the system was {describe_dates(dates)}, but no high-risk "
            "route is screened, so there is no Chapter III date to compare with."
        )
    if profile.significant_change_after_application_date is True:
        return (
            "Article 111(2) check: a significant change in design is asserted, which matters "
            "only for a high-risk system placed on the market or put into service before its "
            "Chapter III date."
        )
    if profile.public_authority_use:
        return (
            "Article 111(2) check: public-authority use is asserted, but no high-risk route is "
            "screened. The providers and deployers of a high-risk system intended to be used "
            "by public authorities and placed on the market or put into service before its "
            f"Chapter III date {PUBLIC_AUTHORITY_DUTY}."
        )
    return ""
