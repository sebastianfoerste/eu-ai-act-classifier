"""The substantive legal mapping: areas, practices, and obligation sets.

This module is the lawyer's contribution. The engine in :mod:`.engine` is
generic; the rule sets here are what encode Regulation (EU) 2024/1689. Each
entry carries its pinpoint citation, so every line of output traces back to a
provision a reviewer can open.
"""

from __future__ import annotations

from .citations import Citation, cite
from .models import AnnexIII, Obligation, ProhibitedPractice, Role

# --- Annex III high-risk areas (Art. 6(2) AIA) -----------------------------
# Sub-point lettering for areas 6 (law enforcement) and 7 (migration) is
# verified against the consolidated Annex III text. The residual UNSURE entry
# carries the only `noch zu verifizieren` flag, for genuinely unsettled cases.
ANNEX_III: dict[AnnexIII, tuple[Citation, str]] = {
    AnnexIII.BIOMETRICS_REMOTE_ID: (cite("Annex III(1)(a) AIA"), "Remote biometric identification"),
    AnnexIII.BIOMETRICS_CATEGORISATION: (
        cite("Annex III(1)(b) AIA"),
        "Biometric categorisation by sensitive/protected attributes",
    ),
    AnnexIII.BIOMETRICS_EMOTION: (cite("Annex III(1)(c) AIA"), "Emotion recognition"),
    AnnexIII.CRITICAL_INFRASTRUCTURE: (
        cite("Annex III(2) AIA"),
        "Safety component of critical infrastructure",
    ),
    AnnexIII.EDUCATION_ACCESS: (cite("Annex III(3)(a) AIA"), "Education: access and admission"),
    AnnexIII.EDUCATION_EVALUATION: (
        cite("Annex III(3)(b) AIA"),
        "Education: evaluating learning outcomes",
    ),
    AnnexIII.EDUCATION_ASSESSMENT_LEVEL: (
        cite("Annex III(3)(c) AIA"),
        "Education: assessing appropriate level",
    ),
    AnnexIII.EDUCATION_PROCTORING: (
        cite("Annex III(3)(d) AIA"),
        "Education: monitoring prohibited behaviour during tests",
    ),
    AnnexIII.EMPLOYMENT_RECRUITMENT: (
        cite("Annex III(4)(a) AIA"),
        "Employment: recruitment and selection",
    ),
    AnnexIII.EMPLOYMENT_MANAGEMENT: (
        cite("Annex III(4)(b) AIA"),
        "Employment: decisions on terms, promotion, termination, task allocation",
    ),
    AnnexIII.ESSENTIAL_PUBLIC_BENEFITS: (
        cite("Annex III(5)(a) AIA"),
        "Eligibility for essential public assistance benefits and services",
    ),
    AnnexIII.CREDITWORTHINESS: (
        cite("Annex III(5)(b) AIA"),
        "Creditworthiness evaluation and credit scoring",
    ),
    AnnexIII.INSURANCE_LIFE_HEALTH: (
        cite("Annex III(5)(c) AIA"),
        "Risk assessment and pricing in life and health insurance",
    ),
    AnnexIII.EMERGENCY_DISPATCH: (
        cite("Annex III(5)(d) AIA"),
        "Emergency call dispatch and triage",
    ),
    AnnexIII.LAW_ENFORCEMENT_VICTIM_RISK: (
        cite("Annex III(6)(a) AIA"),
        "Law enforcement: risk of a person becoming a victim of crime",
    ),
    AnnexIII.LAW_ENFORCEMENT_POLYGRAPH: (
        cite("Annex III(6)(b) AIA"),
        "Law enforcement: polygraphs and similar tools",
    ),
    AnnexIII.LAW_ENFORCEMENT_EVIDENCE_RELIABILITY: (
        cite("Annex III(6)(c) AIA"),
        "Law enforcement: evaluating the reliability of evidence",
    ),
    AnnexIII.LAW_ENFORCEMENT_REOFFENDING_RISK: (
        cite("Annex III(6)(d) AIA"),
        "Law enforcement: assessing the risk of offending or re-offending",
    ),
    AnnexIII.LAW_ENFORCEMENT_PROFILING: (
        cite("Annex III(6)(e) AIA"),
        "Law enforcement: profiling during detection, investigation or prosecution",
    ),
    AnnexIII.MIGRATION_POLYGRAPH: (
        cite("Annex III(7)(a) AIA"),
        "Migration: polygraphs and similar tools",
    ),
    AnnexIII.MIGRATION_RISK_ASSESSMENT: (
        cite("Annex III(7)(b) AIA"),
        "Migration: risk assessment for persons entering a Member State",
    ),
    AnnexIII.MIGRATION_APPLICATION_EXAMINATION: (
        cite("Annex III(7)(c) AIA"),
        "Migration: examining asylum, visa and residence-permit applications",
    ),
    AnnexIII.MIGRATION_IDENTIFICATION: (
        cite("Annex III(7)(d) AIA"),
        "Migration: detecting, recognising or identifying natural persons",
    ),
    AnnexIII.JUSTICE: (
        cite("Annex III(8)(a) AIA"),
        "Administration of justice: assisting a judicial authority",
    ),
    AnnexIII.DEMOCRATIC_PROCESSES: (
        cite("Annex III(8)(b) AIA"),
        "Influencing elections, referenda or voting behaviour",
    ),
    AnnexIII.UNSURE: (
        cite("Annex III AIA", verified=False),
        "An Annex III area is implicated but the specific point is unsettled",
    ),
}

# --- Prohibited practices (Art. 5(1) AIA) ----------------------------------
PROHIBITED: dict[ProhibitedPractice, tuple[Citation, str]] = {
    ProhibitedPractice.SUBLIMINAL_MANIPULATION: (
        cite("Art. 5(1)(a) AIA"),
        "Subliminal, manipulative or deceptive techniques causing significant harm",
    ),
    ProhibitedPractice.EXPLOITS_VULNERABILITIES: (
        cite("Art. 5(1)(b) AIA"),
        "Exploiting vulnerabilities of age, disability or socio-economic situation",
    ),
    ProhibitedPractice.SOCIAL_SCORING: (
        cite("Art. 5(1)(c) AIA"),
        "Social scoring leading to detrimental or unfavourable treatment",
    ),
    ProhibitedPractice.PREDICTIVE_POLICING_INDIVIDUAL: (
        cite("Art. 5(1)(d) AIA"),
        "Predicting criminal offending based solely on profiling or personality",
    ),
    ProhibitedPractice.FACIAL_SCRAPING: (
        cite("Art. 5(1)(e) AIA"),
        "Untargeted scraping of facial images to build recognition databases",
    ),
    ProhibitedPractice.EMOTION_RECOGNITION_WORK_EDUCATION: (
        cite("Art. 5(1)(f) AIA"),
        "Emotion recognition in the workplace or education (no medical/safety exception)",
    ),
    ProhibitedPractice.BIOMETRIC_CATEGORISATION_SENSITIVE: (
        cite("Art. 5(1)(g) AIA"),
        "Biometric categorisation inferring sensitive attributes",
    ),
    ProhibitedPractice.REALTIME_REMOTE_BIOMETRIC_ID: (
        cite("Art. 5(1)(h) AIA"),
        "Real-time remote biometric identification in public spaces for law enforcement",
    ),
}


# --- High-risk obligation sets ---------------------------------------------
def high_risk_provider_obligations() -> list[Obligation]:
    """Provider duties for a high-risk system (Arts. 9-21, 43-49, 72-73 AIA)."""
    p = Role.PROVIDER
    return [
        Obligation(
            article="Art. 9 AIA",
            title="Risk management system",
            applies_to=p,
            requirement="Establish, document and maintain a continuous risk management system.",
        ),
        Obligation(
            article="Art. 10 AIA",
            title="Data and data governance",
            applies_to=p,
            requirement="Apply data governance to training, validation and testing data sets.",
        ),
        Obligation(
            article="Art. 11 AIA",
            title="Technical documentation",
            applies_to=p,
            requirement="Draw up technical documentation (Annex IV) before placing on the market.",
        ),
        Obligation(
            article="Art. 12 AIA",
            title="Record-keeping (logging)",
            applies_to=p,
            requirement="Enable automatic recording of events (logs) over the system's lifetime.",
        ),
        Obligation(
            article="Art. 13 AIA",
            title="Transparency to deployers",
            applies_to=p,
            requirement="Provide instructions for use enabling deployers to comply.",
        ),
        Obligation(
            article="Art. 14 AIA",
            title="Human oversight",
            applies_to=p,
            requirement="Design the system for effective oversight by natural persons.",
        ),
        Obligation(
            article="Art. 15 AIA",
            title="Accuracy, robustness, cybersecurity",
            applies_to=p,
            requirement="Achieve appropriate accuracy, robustness and cybersecurity.",
        ),
        Obligation(
            article="Art. 17 AIA",
            title="Quality management system",
            applies_to=p,
            requirement="Put a quality management system in place.",
        ),
        Obligation(
            article="Art. 43 AIA",
            title="Conformity assessment",
            applies_to=p,
            requirement="Undergo the applicable conformity assessment before market placement.",
        ),
        Obligation(
            article="Art. 47 AIA",
            title="EU declaration of conformity",
            applies_to=p,
            requirement="Draw up and keep an EU declaration of conformity.",
        ),
        Obligation(
            article="Art. 48 AIA",
            title="CE marking",
            applies_to=p,
            requirement="Affix the CE marking to indicate conformity.",
        ),
        Obligation(
            article="Art. 49 AIA",
            title="Registration",
            applies_to=p,
            requirement="Register the system in the EU database before market placement.",
        ),
        Obligation(
            article="Art. 72 AIA",
            title="Post-market monitoring",
            applies_to=p,
            requirement="Operate a post-market monitoring system.",
        ),
        Obligation(
            article="Art. 73 AIA",
            title="Serious incident reporting",
            applies_to=p,
            requirement="Report serious incidents to the market surveillance authority.",
        ),
    ]


def high_risk_deployer_obligations(*, fria_required: bool) -> list[Obligation]:
    """Deployer duties for a high-risk system (Art. 26, and Art. 27 FRIA)."""
    d = Role.DEPLOYER
    out = [
        Obligation(
            article="Art. 26 AIA",
            title="Deployer obligations",
            applies_to=d,
            requirement="Use per instructions, assign human oversight, monitor use, keep logs.",
        ),
    ]
    if fria_required:
        out.append(
            Obligation(
                article="Art. 27 AIA",
                title="Fundamental rights impact assessment",
                applies_to=d,
                requirement="Conduct a fundamental rights impact assessment before deployment.",
            )
        )
    return out


def high_risk_documentation() -> list[Obligation]:
    """The artifacts a high-risk provider must be able to produce on demand."""
    p = Role.PROVIDER
    return [
        Obligation(
            article="Art. 11 AIA + Annex IV",
            title="Technical documentation",
            applies_to=p,
            requirement="Annex IV technical documentation, kept current.",
        ),
        Obligation(
            article="Art. 9 AIA",
            title="Risk management file",
            applies_to=p,
            requirement="Documented risk management system and its results.",
        ),
        Obligation(
            article="Art. 13 AIA",
            title="Instructions for use",
            applies_to=p,
            requirement="Instructions enabling deployer compliance.",
        ),
        Obligation(
            article="Art. 17 AIA",
            title="QMS documentation",
            applies_to=p,
            requirement="Written quality management system policies and procedures.",
        ),
        Obligation(
            article="Art. 47 AIA",
            title="EU declaration of conformity",
            applies_to=p,
            requirement="Signed EU declaration of conformity.",
        ),
    ]


# --- GPAI obligation sets (Chapter V AIA) ----------------------------------
def gpai_obligations(*, systemic_risk: bool) -> list[Obligation]:
    g = Role.GPAI_PROVIDER
    out = [
        Obligation(
            article="Art. 53(1)(a) AIA",
            title="Model technical documentation",
            applies_to=g,
            requirement="Draw up and keep technical documentation per Annex XI.",
        ),
        Obligation(
            article="Art. 53(1)(b) AIA",
            title="Information to downstream providers",
            applies_to=g,
            requirement="Provide downstream providers with information per Annex XII.",
        ),
        Obligation(
            article="Art. 53(1)(c) AIA",
            title="Copyright policy",
            applies_to=g,
            requirement="Put in place a policy to comply with Union copyright law.",
        ),
        Obligation(
            article="Art. 53(1)(d) AIA",
            title="Training-content summary",
            applies_to=g,
            requirement="Publish a sufficiently detailed summary of training content.",
        ),
    ]
    if systemic_risk:
        out += [
            Obligation(
                article="Art. 55(1)(a) AIA",
                title="Model evaluation",
                applies_to=g,
                requirement="Perform model evaluation, including adversarial testing.",
            ),
            Obligation(
                article="Art. 55(1)(b) AIA",
                title="Systemic-risk mitigation",
                applies_to=g,
                requirement="Assess and mitigate systemic risks at Union level.",
            ),
            Obligation(
                article="Art. 55(1)(c) AIA",
                title="Serious-incident tracking",
                applies_to=g,
                requirement="Track, document and report serious incidents.",
            ),
            Obligation(
                article="Art. 55(1)(d) AIA",
                title="Cybersecurity",
                applies_to=g,
                requirement="Ensure an adequate level of cybersecurity protection.",
            ),
        ]
    return out


# --- Transparency obligations (Art. 50 AIA) --------------------------------
TRANSPARENCY = {
    "interaction": Obligation(
        article="Art. 50(1) AIA",
        title="Inform persons of AI interaction",
        applies_to=Role.PROVIDER,
        requirement=(
            "Inform natural persons that they are interacting with an AI system, unless obvious."
        ),
    ),
    "synthetic": Obligation(
        article="Art. 50(2) AIA",
        title="Mark synthetic content",
        applies_to=Role.PROVIDER,
        requirement=(
            "Mark AI-generated audio, image, video or text as artificially generated "
            "(machine-readable)."
        ),
    ),
    "emotion_biometric": Obligation(
        article="Art. 50(3) AIA",
        title="Notify of emotion/biometric categorisation",
        applies_to=Role.DEPLOYER,
        requirement="Inform exposed persons of the operation of the system.",
    ),
    "deepfake": Obligation(
        article="Art. 50(4) AIA",
        title="Disclose deepfakes",
        applies_to=Role.DEPLOYER,
        requirement="Disclose that the content has been artificially generated or manipulated.",
    ),
}
