"""The substantive legal mapping: areas, practices, and obligation sets.

This module is the lawyer's contribution. The engine in :mod:`.engine` is
generic; the rule sets here are what encode Regulation (EU) 2024/1689. Each
entry carries its pinpoint citation, so every line of output traces back to a
provision a reviewer can open.

Each duty is one :class:`Duty`, the single source of both its
``report.obligations`` entry and its ``report.obligation_graph`` item.
"""

from __future__ import annotations

from dataclasses import dataclass

from .citations import Citation, cite
from .models import AnnexIII, Obligation, ProhibitedPractice, Role

# Article labels other modules match on. Use these constants, not copies of the
# string, so a wording change cannot silently break the match.
ART_2_2 = "Art. 2(2) AIA"
ART_49 = "Art. 49 AIA"
ART_49_2 = "Art. 49(2) AIA"
ART_49_3 = "Art. 49(3) AIA"
ART_49_5 = "Art. 49(5) AIA"
ART_50_2 = "Art. 50(2) AIA"
ART_111_2 = "Art. 111(2) AIA"

# Art. 2(2) AIA, as replaced by Regulation (EU) 2026/1744, Art. 1, point (2)(a): what
# still applies to an Art. 6(1) high-risk system for an Annex I, Section B product.
SECTION_B_PROVISIONS = (
    "only Art. 6(1), Art. 60a and Arts. 102 to 112 AIA apply; Arts. 57, 58 and 59 apply "
    "only in so far as the high-risk requirements have been integrated in the sectoral "
    "Union harmonisation legislation"
)

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
    AnnexIII.EMPLOYMENT_SELECTION: (
        cite("Annex III(4)(a) AIA"),
        "Employment selection and worker management",
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
    ProhibitedPractice.NON_CONSENSUAL_INTIMATE_IMAGERY: (
        cite("Art. 5(1)(ba) AIA"),
        "Generating or manipulating realistic intimate material of an identifiable person "
        "without consent",
    ),
    ProhibitedPractice.CHILD_SEXUAL_ABUSE_MATERIAL: (
        cite("Art. 5(1)(bb) AIA"),
        "Generating or manipulating child sexual abuse material under Directive 2011/93/EU, "
        "save a 'without right' defence under national law",
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


# Art. 5(1)(ba) and (bb) AIA, inserted by Regulation (EU) 2026/1744, Art. 1, point (7)(a),
# in the words of the consolidated text. With Art. 5(1a) and (1b) they apply from
# citations.POINT_A_EXCEPTION_DATE (Art. 113, third paragraph, point (a)), not from
# 2 February 2025.
LATER_PROHIBITIONS: dict[ProhibitedPractice, str] = {
    ProhibitedPractice.NON_CONSENSUAL_INTIMATE_IMAGERY: (
        "the placing on the market, the putting into service or the use of an AI system that "
        "generates or manipulates realistic images, videos, audio or similar material of an "
        "identifiable natural person's intimate parts, or of an identifiable natural person "
        "engaged in sexually explicit activities, without that person's freely-given, "
        "specific, informed, unambiguous and explicit consent for that generation or "
        "manipulation"
    ),
    ProhibitedPractice.CHILD_SEXUAL_ABUSE_MATERIAL: (
        "the placing on the market, the putting into service or the use of an AI system that "
        "generates or manipulates material or performance within the meaning of Article 2, "
        "points (c) and (e), of Directive 2011/93/EU, except where a 'without right' defence "
        "applies under national law"
    ),
}
# Art. 5(1a) and, for point (ba) only, Art. 5(1b) AIA, in the words of the
# consolidated text (Regulation (EU) 2026/1744, Art. 1, point (7)(b)).
ART_5_1A = (
    "(a) the placing on the market or putting into service of an AI system that generates "
    "or manipulates the material or performance referred to in paragraph 1, first "
    "subparagraph, point (ba) or (bb) is only prohibited where: (i) that generation or "
    "manipulation is the intended purpose of the AI system; or (ii) the system's design, "
    "training, architecture, capabilities or user-facing functionalities make that "
    "generation or manipulation a reasonably foreseeable and reproducible outcome, without "
    "requiring significant technical modification, and the system does not have reasonable "
    "and adequate technical safety measures and other safeguards to reliably prevent that "
    "generation or manipulation, taking into account reasonably foreseeable misuse, and to "
    "correct observed or reported misuse; (b) the use of an AI system that generates or "
    "manipulates the material or performance referred to in paragraph 1, first "
    "subparagraph, points (ba) and (bb) is only prohibited where the deployer uses the "
    "system for the purpose of generating or manipulating such material or performance"
)
ART_5_1B = (
    "an AI system that manipulates material in a way that does not increase the exposure of "
    "any depicted intimate parts or alter the nature of any depicted sexually explicit "
    "activities shall not constitute manipulation"
)


# Arts. 102 to 109 have the high-risk requirements taken into account in sectoral
# delegated and implementing acts. Machinery is reached through Regulation (EU) 2026/1744,
# Art. 3, point (1): delegated acts adding them to Annex III to Regulation (EU) 2023/1230,
# which apply by 2 August 2028. Art. 2(2) adds no duty of its own.
SECTION_B_ROUTE = (
    "The high-risk requirements reach the product only through the sectoral legislation, as "
    "far as its delegated or implementing acts integrate them."
)


# Contested Section B points. As in PR #26 the text opens with the counsel flag
# ("Literal reading, confirm with counsel"), states the reading the report departs
# from, then what the report does.
def section_b_kept_flag(provision: str, kept: str) -> str:
    """Art. 2(2) AIA does not list ``provision`` for a Section B product; the report
    keeps ``kept`` as the conservative reading."""

    return (
        "Literal reading, confirm with counsel: for an Annex I, Section B product Art. 2(2) "
        "AIA lists only Art. 6(1), Art. 60a and Arts. 102 to 112 (and Arts. 57 to 59 in so "
        "far as the sectoral legislation integrates the high-risk requirements), so on its "
        f"wording {provision} does not apply. This report keeps {kept} as the conservative "
        "reading."
    )


def section_b_annex_iii_flag(derogation_asserted: bool) -> str:
    """A Section B product also in an Annex III area: the report keeps the Annex III
    duties, although on its wording Art. 2(2) AIA leaves only the listed provisions."""

    classified = "is also classified high-risk under Art. 6(2) and Annex III"
    if derogation_asserted:
        classified += (
            " unless the asserted Art. 6(3) derogation is established, in which case only the "
            "Art. 2(2) provisions apply"
        )
    return (
        "Literal reading, confirm with counsel: on its wording Art. 2(2) AIA covers any AI "
        "system classified high-risk in accordance with Art. 6(1) for a Section B product, and "
        "Art. 6(2) is not among the provisions it lists, so only those would apply. This system "
        f"{classified}, and this report keeps the Annex III duties as the conservative reading."
    )


# --- High-risk obligation sets ---------------------------------------------
def eu_database_registration_applies(annex_iii_area: AnnexIII | None) -> bool:
    """Art. 49(1) AIA provider registration in the EU database covers only high-risk
    systems listed in Annex III, except point 2 (critical infrastructure), which
    Art. 49(5) registers at national level. ``UNSURE`` keeps the duty, since the point
    may not be point 2."""

    return annex_iii_area is not None and annex_iii_area is not AnnexIII.CRITICAL_INFRASTRUCTURE


def public_authority_users(annex_iii_area: AnnexIII | None) -> str | None:
    """Who Annex III, points 5(a), 6 and 7 describe as using the system, in the words of
    each point, as a phrase after "used" or "use": public authorities or Union bodies,
    the deployers Art. 49(3) AIA names. None for every other point; point 8(a) is not
    here, as its alternative dispute resolution limb may be private."""

    area = annex_iii_area.value if annex_iii_area else ""
    if area == AnnexIII.ESSENTIAL_PUBLIC_BENEFITS.value:
        return "by or on behalf of public authorities"
    if area.startswith("III.6."):
        users = (
            "by or on behalf of law enforcement authorities, or by Union institutions, "
            "bodies, offices or agencies in support of law enforcement authorities"
        )
        # Point 6(a) alone adds "or on their behalf" for the Union bodies.
        return f"{users} or on their behalf" if area == "III.6.a" else users
    if area.startswith("III.7."):
        return (
            "by or on behalf of competent public authorities, or by Union institutions, "
            "bodies, offices or agencies"
        )
    return None


def public_authority_area(annex_iii_area: AnnexIII | None) -> bool:
    """Whether the Annex III point itself describes use by public authorities."""

    return public_authority_users(annex_iii_area) is not None


def public_authority_registration_applies(
    annex_iii_area: AnnexIII | None,
    deployer_public_authority: bool | None,
    public_authority_use: bool,
) -> bool:
    """Art. 49(3) AIA: deployers that are public authorities, Union institutions, bodies,
    offices or agencies, or persons acting on their behalf, register their use of an
    Annex III system other than point 2. An unknown deployer status counts where the
    system is intended to be used by public authorities, or its Annex III point describes
    such use, for the reviewer to confirm."""

    if not eu_database_registration_applies(annex_iii_area):
        return False
    if deployer_public_authority is None:
        return public_authority_use or public_authority_area(annex_iii_area)
    return deployer_public_authority


def national_registration_for_public_authority_deployer(
    annex_iii_area: AnnexIII | None,
    deployer_public_authority: bool | None,
    public_authority_use: bool,
) -> bool:
    """Art. 49(3) AIA excepts Annex III point 2, which Art. 49(5) registers at national
    level: a deployer Art. 49(3) would otherwise cover gets that pointer instead."""

    if annex_iii_area is not AnnexIII.CRITICAL_INFRASTRUCTURE:
        return False
    if deployer_public_authority is None:
        return public_authority_use
    return deployer_public_authority


# Art. 49(4) AIA: what the restricted section holds and who can see it.
_SECURE_SECTION = (
    "register in the secure non-public section of the EU database, with only the Annex VIII "
    "and Annex IX information Art. 49(4) lists; only the Commission and the national "
    "authorities referred to in Art. 74(8) have access to it (Art. 49(4) AIA)."
)


def secure_section_note(annex_iii_area: AnnexIII | None) -> str:
    """Art. 49(4) AIA: the registration under Art. 49(1), (2) and (3) of points 6 and 7
    of Annex III is in the secure non-public section of the EU database; point 1 is
    there where used in law enforcement, migration, asylum or border control
    management. ``UNSURE`` states the condition, since the point may be one of them."""

    area = annex_iii_area.value if annex_iii_area else ""
    if area.startswith(("III.6.", "III.7.")):
        return f" {_SECURE_SECTION[0].upper()}{_SECURE_SECTION[1:]}"
    if area.startswith("III.1."):
        return (
            " Where used in law enforcement, migration, asylum or border control management, "
            f"{_SECURE_SECTION}"
        )
    if annex_iii_area is AnnexIII.UNSURE:
        return (
            " If the Annex III point is 6 or 7, or 1 where used in law enforcement, migration, "
            f"asylum or border control management, {_SECURE_SECTION}"
        )
    return ""


# Art. 26(8), second sentence, AIA binds deployers that are public authorities or Union
# institutions, bodies, offices or agencies themselves, not persons acting on their
# behalf. It is a Chapter III, Section 3 duty, so it goes with the Art. 26 item and its
# date, not with Art. 49(3).
ART_26_8 = (
    "Where the deployer is itself a public authority or Union institution, body, office or "
    "agency and finds that the system has not been registered in the EU database, do not "
    "use it and inform the provider or the distributor (Art. 26(8) AIA)."
)


def public_authority_registration_requirement(
    annex_iii_area: AnnexIII | None, deployer_public_authority: bool | None
) -> str:
    """Art. 49(3) AIA with any Art. 49(4) note. Conditional where the deployer's status
    is inferred, not given."""

    requirement = (
        "Register as deployer, select the system and register its use in the EU database "
        "before putting it into service or using it. Selecting the system presupposes that "
        "it is registered there, so do not use a system that is not."
        f"{secure_section_note(annex_iii_area)}"
    )
    if deployer_public_authority is None:
        return (
            "Where the deployer is, or acts on behalf of, a public authority or Union "
            f"institution, body, office or agency: {requirement[0].lower()}{requirement[1:]}"
        )
    return requirement


# --- Duties: one catalog for the obligations list and the obligation graph -------
@dataclass(frozen=True, slots=True)
class Duty:
    """One duty, the single source of a ``report.obligations`` entry and its
    ``report.obligation_graph`` item. The list shows the article, title, actor and
    requirement; the graph item shows the same article, actor and requirement with the id,
    trigger and evidence artifact. :mod:`.obligation_graph` decides which duties a profile
    gets, dates each item and sets its review status; ``review_required`` marks a duty
    that goes to review whatever its date."""

    obligation_id: str
    article: str
    actor: Role
    title: str
    requirement: str
    trigger: str
    evidence_artifact: str
    review_required: bool = False

    def obligation(self) -> Obligation:
        return Obligation(
            article=self.article,
            title=self.title,
            applies_to=self.actor,
            requirement=self.requirement,
        )


_HIGH_RISK_PROVIDER = "Provider of a high-risk AI system."


def _provider_duty(
    article: int,
    title: str,
    requirement: str,
    evidence_artifact: str,
    trigger: str = _HIGH_RISK_PROVIDER,
    *,
    review_required: bool = False,
) -> Duty:
    return Duty(
        obligation_id=f"high-risk.provider.{article}",
        article=f"Art. {article} AIA",
        actor=Role.PROVIDER,
        title=title,
        requirement=requirement,
        trigger=trigger,
        evidence_artifact=evidence_artifact,
        review_required=review_required,
    )


# Arts. 9 to 21, within Chapter III, Sections 1 to 3 (Arts. 6 to 27): dated by Art. 113,
# third paragraph, point (c) AIA (docs/REGULATORY_CLAIM_LEDGER.md).
HIGH_RISK_PROVIDER_DUTIES: tuple[Duty, ...] = (
    _provider_duty(
        9,
        "Risk management system",
        "Establish, document and maintain a continuous risk management system.",
        "Risk management file.",
    ),
    _provider_duty(
        10,
        "Data and data governance",
        "Apply data governance to training, validation and testing data sets.",
        "Data governance record.",
    ),
    _provider_duty(
        11,
        "Technical documentation",
        "Draw up technical documentation (Annex IV) before placing on the market.",
        "Annex IV technical documentation.",
    ),
    _provider_duty(
        12,
        "Record-keeping (logging)",
        "Enable automatic recording of events (logs) over the system's lifetime.",
        "Event logging design record.",
    ),
    _provider_duty(
        13,
        "Transparency to deployers",
        "Provide instructions for use enabling deployers to comply.",
        "Instructions for use.",
    ),
    _provider_duty(
        14,
        "Human oversight",
        "Design the system for effective oversight by natural persons.",
        "Human oversight design record.",
    ),
    _provider_duty(
        15,
        "Accuracy, robustness, cybersecurity",
        "Achieve appropriate accuracy, robustness and cybersecurity.",
        "Accuracy, robustness and cybersecurity test record.",
    ),
    _provider_duty(
        16,
        "Provider obligations",
        "Ensure the high-risk system complies with Chapter III requirements.",
        "Provider compliance responsibility matrix.",
    ),
    _provider_duty(
        17,
        "Quality management system",
        "Maintain a quality management system.",
        "Quality management system file.",
    ),
    _provider_duty(
        18,
        "Document retention",
        "Keep technical documentation, logs and conformity documentation.",
        "Document retention register.",
    ),
    _provider_duty(
        19,
        "Log retention",
        "Keep automatically generated logs where under provider control.",
        "Logging retention policy.",
    ),
    _provider_duty(
        20,
        "Corrective action and notification",
        "Take corrective action and inform relevant parties where required.",
        "Corrective-action and notification log.",
        "Risk or nonconformity after placing on the market.",
        review_required=True,
    ),
    _provider_duty(
        21,
        "Authority cooperation",
        "Cooperate with competent authorities and provide requested information.",
        "Authority cooperation protocol.",
        "Competent-authority request.",
        review_required=True,
    ),
)

# Chapter III, Section 5 (Arts. 40 to 49), apart from the Art. 49 registration duties below.
HIGH_RISK_PROVIDER_SECTION_5_DUTIES: tuple[Duty, ...] = (
    _provider_duty(
        40,
        "Harmonised standards",
        "Track applicable harmonised standards and standardisation deliverables.",
        "Standards applicability matrix.",
        "High-risk requirements where harmonised standards are available.",
    ),
    _provider_duty(
        41,
        "Common specifications",
        "Assess common specifications where harmonised standards are unavailable or insufficient.",
        "Common specifications assessment.",
        "Common specifications become applicable.",
    ),
    _provider_duty(
        42,
        "Presumption of conformity",
        "Map implemented controls to standards, specifications or alternative evidence.",
        "Presumption of conformity mapping.",
        "Use of standards or specifications for presumption of conformity.",
    ),
    _provider_duty(
        43,
        "Conformity assessment",
        "Complete the applicable conformity assessment.",
        "Conformity assessment file.",
        "Before placing high-risk AI system on the market or putting into service.",
    ),
    _provider_duty(
        44,
        "Notified body certificates",
        "Track certificate validity, changes and renewal obligations.",
        "Certificate register.",
        "Certificate issued by notified body where applicable.",
    ),
    _provider_duty(
        47,
        "EU declaration of conformity",
        "Draw up and keep the EU declaration of conformity.",
        "EU declaration of conformity.",
        "Conformity established.",
    ),
    _provider_duty(
        48,
        "CE marking",
        "Affix CE marking where required.",
        "CE marking record.",
        "Conformity established for a high-risk AI system.",
    ),
)

# Chapter IX (Arts. 72 and 73).
HIGH_RISK_PROVIDER_CHAPTER_IX_DUTIES: tuple[Duty, ...] = (
    _provider_duty(
        72,
        "Post-market monitoring",
        "Operate a post-market monitoring system and plan.",
        "Post-market monitoring plan.",
        "High-risk AI system lifecycle.",
    ),
    _provider_duty(
        73,
        "Serious incident reporting",
        "Report serious incidents to the market surveillance authority.",
        "Serious incident register.",
        "Serious incident identified.",
    ),
)

_NATIONAL_REGISTRATION = "Registration at national level"
_NATIONAL_REGISTRATION_RECORD = "National registration record."


def provider_registration_duty(annex_iii_area: AnnexIII | None) -> Duty:
    """Art. 49(1) AIA, where :func:`eu_database_registration_applies`, with any
    Art. 49(4) note for ``annex_iii_area``."""

    return Duty(
        obligation_id="high-risk.provider.49",
        article=ART_49,
        actor=Role.PROVIDER,
        title="Registration",
        requirement=(
            "Register the provider and system in the EU database where required."
            f"{secure_section_note(annex_iii_area)}"
        ),
        trigger=(
            "Before placing an Annex III high-risk AI system on the market or putting it into "
            "service."
        ),
        evidence_artifact="EU database registration record.",
    )


PROVIDER_NATIONAL_REGISTRATION = Duty(
    obligation_id="high-risk.provider.49.5",
    article=ART_49_5,
    actor=Role.PROVIDER,
    title=_NATIONAL_REGISTRATION,
    requirement=(
        "Have the system registered at national level, not in the EU database; confirm the "
        "national procedure and who registers."
    ),
    trigger="Annex III point 2 high-risk AI system (critical infrastructure).",
    evidence_artifact=_NATIONAL_REGISTRATION_RECORD,
)


def derogation_registration_duty(annex_iii_area: AnnexIII | None) -> Duty:
    """Art. 49(2) AIA for a provider relying on Art. 6(3), with any Art. 49(4) note."""

    return Duty(
        obligation_id="high-risk.provider.49.2",
        article=ART_49_2,
        actor=Role.PROVIDER,
        title="Registration when relying on Art. 6(3)",
        requirement=(
            "If the provider concludes under Art. 6(3) that the system is not high-risk, "
            "register the provider and system in the EU database before placing it on the "
            f"market or putting it into service.{secure_section_note(annex_iii_area)}"
        ),
        trigger="Art. 6(3) derogation asserted for an Annex III AI system.",
        evidence_artifact="Art. 6(4) assessment and EU database registration record.",
    )


def deployer_duty(*, public_authority_registration: bool) -> Duty:
    """Art. 26 AIA, with the Art. 26(8) check where ``public_authority_registration``."""

    art_26_8 = f" {ART_26_8}" if public_authority_registration else ""
    return Duty(
        obligation_id="high-risk.deployer.26",
        article="Art. 26 AIA",
        actor=Role.DEPLOYER,
        title="Deployer obligations",
        requirement=(
            "Use the system per instructions, assign oversight, monitor operation and keep "
            f"logs.{art_26_8}"
        ),
        trigger="Deployer of a high-risk AI system.",
        evidence_artifact="Deployer operating procedure and monitoring log.",
    )


FRIA = Duty(
    obligation_id="high-risk.deployer.27",
    article="Art. 27 AIA",
    actor=Role.DEPLOYER,
    title="Fundamental rights impact assessment",
    requirement=("Perform and maintain a fundamental rights impact assessment before first use."),
    trigger="FRIA trigger under Art. 27(1) AIA.",
    evidence_artifact="Draft FRIA and notification record.",
    review_required=True,
)


def public_authority_registration_duty(
    annex_iii_area: AnnexIII | None,
    deployer_public_authority: bool | None,
    public_authority_use: bool,
) -> Duty:
    """Art. 49(3) AIA: public-authority deployers of Annex III systems other than point 2,
    where :func:`public_authority_registration_applies`. The trigger says on what the
    duty rests where the deployer's status is not given."""

    if annex_iii_area is AnnexIII.UNSURE:
        system = (
            "an Annex III high-risk AI system whose point is not settled (if it is point 2, "
            "national registration under Art. 49(5) AIA applies instead)"
        )
    else:
        system = "an Annex III high-risk AI system (not point 2)"
    if deployer_public_authority:
        trigger = (
            "Deployer that is, or acts on behalf of, a public authority or Union institution, "
            f"body, office or agency, using {system}."
        )
    else:
        use = "intended to be used by public authorities"
        if not public_authority_use and (users := public_authority_users(annex_iii_area)):
            # Annex III, points 5(a), 6 and 7 describe use by the deployers Art. 49(3) names.
            use = f"which {ANNEX_III[annex_iii_area][0].ref} describes as used {users}"
        trigger = (
            f"{system[0].upper()}{system[1:]}, {use}. Confirm that the deployer is, or acts on "
            "behalf of, a public authority or Union institution, body, office or agency."
        )
    return Duty(
        obligation_id="high-risk.deployer.49.3",
        article=ART_49_3,
        actor=Role.DEPLOYER,
        title="Registration of use by a public-authority deployer",
        requirement=public_authority_registration_requirement(
            annex_iii_area, deployer_public_authority
        ),
        trigger=trigger,
        evidence_artifact="EU database registration-of-use record.",
    )


def deployer_national_registration_duty(deployer_public_authority: bool | None) -> Duty:
    """Art. 49(5) AIA for a deployer Art. 49(3) would otherwise cover, where
    :func:`national_registration_for_public_authority_deployer`."""

    system = "an Annex III point 2 high-risk AI system (critical infrastructure)"
    trigger = (
        "Deployer that is, or acts on behalf of, a public authority or Union "
        f"institution, body, office or agency, using {system}."
        if deployer_public_authority
        else f"{system[0].upper()}{system[1:]}, intended to be used by public "
        "authorities; the deployer's own status is not given."
    )
    return Duty(
        obligation_id="high-risk.deployer.49.5",
        article=ART_49_5,
        actor=Role.DEPLOYER,
        title=_NATIONAL_REGISTRATION,
        requirement=(
            "Art. 49(3) AIA excepts point 2, so there is no registration of use in the EU "
            "database; the system is registered at national level. Confirm what the national "
            "procedure asks of the deployer."
        ),
        trigger=trigger,
        evidence_artifact=_NATIONAL_REGISTRATION_RECORD,
    )


IMPORTER = Duty(
    obligation_id="high-risk.importer.23",
    article="Art. 23 AIA",
    actor=Role.IMPORTER,
    title="Importer obligations",
    requirement=(
        "Verify provider conformity, documentation, CE marking and instructions before "
        "placing on the market."
    ),
    trigger="Importer of a high-risk AI system.",
    evidence_artifact="Importer due-diligence checklist.",
    review_required=True,
)

DISTRIBUTOR = Duty(
    obligation_id="high-risk.distributor.24",
    article="Art. 24 AIA",
    actor=Role.DISTRIBUTOR,
    title="Distributor obligations",
    requirement=(
        "Verify CE marking, EU declaration, instructions and provider/importer compliance signals."
    ),
    trigger="Distributor of a high-risk AI system.",
    evidence_artifact="Distributor pre-supply checklist.",
    review_required=True,
)

AUTHORISED_REPRESENTATIVE = Duty(
    obligation_id="high-risk.authorised-representative.22",
    article="Art. 22 AIA",
    actor=Role.AUTHORIZED_REPRESENTATIVE,
    title="Authorised representative obligations",
    requirement=(
        "Maintain mandate, documentation access and competent-authority cooperation process."
    ),
    trigger="Provider established outside the EU or authorised representative role selected.",
    evidence_artifact="Authorised representative mandate and document-access file.",
    review_required=True,
)

VALUE_CHAIN = Duty(
    obligation_id="high-risk.value-chain.25",
    article="Art. 25 AIA",
    actor=Role.PROVIDER,
    title="Value-chain provider responsibility",
    requirement="Assess whether provider responsibilities shift along the AI value chain.",
    trigger=(
        "Substantial modification or market placement under own name or trademark is asserted."
    ),
    evidence_artifact="Value-chain responsibility assessment.",
    review_required=True,
)


def legacy_system_duty(actor: Role, trigger: str, requirement: str) -> Duty:
    """Art. 111(2) AIA for one operator role of a high-risk system placed on the market or
    put into service before its Chapter III date. :mod:`.obligation_graph` words the
    trigger and requirement from the profile's dates."""

    slug = (
        "authorised-representative"
        if actor is Role.AUTHORIZED_REPRESENTATIVE
        else actor.value.replace("_", "-")
    )
    return Duty(
        obligation_id=f"high-risk.{slug}.111.2",
        article=ART_111_2,
        actor=actor,
        title="System already placed on the market or put into service",
        requirement=requirement,
        trigger=trigger,
        evidence_artifact=(
            "First placing-on-market or putting-into-service record and design-change log."
        ),
        review_required=True,
    )


def section_b_requirement(*, annex_iii: bool = False) -> str:
    """The Art. 2(2) AIA requirement; for a Section B product also in an Annex III area
    (``annex_iii``) limited to the Art. 6(1) route."""

    requirement = f"{SECTION_B_PROVISIONS}. {SECTION_B_ROUTE}"
    if not annex_iii:
        return f"{requirement[0].upper()}{requirement[1:]}"
    return f"Through the Art. 6(1) route, {requirement}"


def section_b_duty(actor: Role, *, annex_iii: bool) -> Duty:
    """Art. 2(2) AIA: an Art. 6(1) high-risk system for an Annex I, Section B product gets
    none of the Chapter III duties, only the provisions listed there. With an Annex III
    area (``annex_iii``) the Annex III duties stay, and :mod:`.obligation_graph` notes
    the flag of :func:`section_b_annex_iii_flag` on this duty."""

    return Duty(
        obligation_id="high-risk.section-b.2.2",
        article=ART_2_2,
        actor=actor,
        title="Annex I, Section B product: limited application",
        requirement=section_b_requirement(annex_iii=annex_iii),
        trigger="Art. 6(1) high-risk AI system for a product in Annex I, Section B.",
        evidence_artifact="Sectoral legislation mapping for the Annex I, Section B product.",
        review_required=True,
    )


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


# --- GPAI duties (Chapter V AIA) -------------------------------------------
_GPAI_PROVIDER = "Provider of a general-purpose AI model."
_GPAI_SYSTEMIC = "GPAI model with systemic risk."


def _gpai_duty(
    point: str,
    article: str,
    title: str,
    requirement: str,
    trigger: str,
    evidence_artifact: str,
    *,
    review_required: bool = True,
) -> Duty:
    return Duty(
        obligation_id=f"gpai.provider.{point}",
        article=article,
        actor=Role.GPAI_PROVIDER,
        title=title,
        requirement=requirement,
        trigger=trigger,
        evidence_artifact=evidence_artifact,
        review_required=review_required,
    )


GPAI_DUTIES: tuple[Duty, ...] = (
    _gpai_duty(
        "53.a",
        "Art. 53(1)(a) AIA",
        "Model technical documentation",
        "Keep model technical documentation per Annex XI.",
        _GPAI_PROVIDER,
        "GPAI model documentation checklist.",
        review_required=False,
    ),
    _gpai_duty(
        "53.b",
        "Art. 53(1)(b) AIA",
        "Information to downstream providers",
        "Provide downstream providers with information per Annex XII.",
        _GPAI_PROVIDER,
        "Downstream provider information pack.",
        review_required=False,
    ),
    _gpai_duty(
        "53.c",
        "Art. 53(1)(c) AIA",
        "Copyright policy",
        "Maintain a policy to comply with Union copyright law.",
        _GPAI_PROVIDER,
        "Copyright compliance policy.",
    ),
    _gpai_duty(
        "53.d",
        "Art. 53(1)(d) AIA",
        "Training-content summary",
        "Publish a sufficiently detailed summary of training content.",
        _GPAI_PROVIDER,
        "Training-content summary.",
    ),
    _gpai_duty(
        "56",
        "Art. 56 AIA",
        "Code of Practice adherence",
        "Track Code of Practice adherence or alternative means of compliance.",
        "Provider choosing a Code of Practice route or alternative compliance evidence.",
        "GPAI Code of Practice adherence record.",
    ),
)

GPAI_SYSTEMIC_DUTIES: tuple[Duty, ...] = (
    _gpai_duty(
        "55.a",
        "Art. 55(1)(a) AIA",
        "Model evaluation",
        "Perform model evaluation, including adversarial testing.",
        _GPAI_SYSTEMIC,
        "Systemic model evaluation file.",
    ),
    _gpai_duty(
        "55.b",
        "Art. 55(1)(b) AIA",
        "Systemic-risk mitigation",
        "Assess and mitigate systemic risks at Union level.",
        _GPAI_SYSTEMIC,
        "Systemic risk assessment and mitigation plan.",
    ),
    _gpai_duty(
        "55.c",
        "Art. 55(1)(c) AIA",
        "Serious-incident tracking",
        "Track, document and report serious incidents.",
        _GPAI_SYSTEMIC,
        "GPAI serious incident register.",
    ),
    _gpai_duty(
        "55.d",
        "Art. 55(1)(d) AIA",
        "Cybersecurity",
        "Ensure an adequate level of cybersecurity protection.",
        _GPAI_SYSTEMIC,
        "Cybersecurity control file.",
    ),
)


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
        article=ART_50_2,
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
