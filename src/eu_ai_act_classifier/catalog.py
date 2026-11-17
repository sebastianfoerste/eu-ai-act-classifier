"""The substantive legal mapping: areas, practices, and obligation sets.

This module is the lawyer's contribution. The engine in :mod:`.engine` is
generic; the rule sets here are what encode Regulation (EU) 2024/1689. Each
entry carries its pinpoint citation, so every line of output traces back to a
provision a reviewer can open.
"""

from __future__ import annotations

from .citations import Citation, cite
from .models import AnnexIII, Obligation, ProhibitedPractice, RiskTier, Role

# Article labels other modules match on. Use these constants, not copies of the
# string, so a wording change cannot silently break the match.
ART_2_2 = "Art. 2(2) AIA"
ART_4 = "Art. 4 AIA"
ART_49 = "Art. 49 AIA"
ART_49_2 = "Art. 49(2) AIA"
ART_49_3 = "Art. 49(3) AIA"
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
    # Point 5(b) excepts AI systems used for the purpose of detecting financial fraud;
    # rules/high_risk.py raises that exception as a review question.
    AnnexIII.CREDITWORTHINESS: (
        cite("Annex III(5)(b) AIA"),
        "Creditworthiness evaluation and credit scoring of natural persons",
    ),
    AnnexIII.INSURANCE_LIFE_HEALTH: (
        cite("Annex III(5)(c) AIA"),
        "Risk assessment and pricing for natural persons in life and health insurance",
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


# --- AI literacy (Art. 4 AIA, Chapter I) -------------------------------------
# Art. 4(1) AIA as replaced by Regulation (EU) 2026/1744, Art. 1, point (5), in force
# 27 July 2026, in the words of the consolidated text. Chapter I applies from
# citations.POINT_A_DATE (Art. 113, third paragraph, point (a)). The duty binds providers
# and deployers of AI systems whatever the risk tier; it asks for measures, not for a
# level of literacy. Importers, distributors, authorised representatives and the
# provider of a general-purpose AI model, as such, are not addressed.
AI_LITERACY_REQUIREMENT = (
    "Take measures to support the development of AI literacy of staff and other persons "
    "dealing with the operation and use of the system on the operator's behalf, taking into "
    "account their technical knowledge, experience, education and training, the context the "
    "system is to be used in and the persons or groups of persons it is to be used on. No "
    "specific level of AI literacy of any individual has to be guaranteed. Wording: "
    "Art. 4(1) AIA as replaced by Art. 1, point (5) of Regulation (EU) 2026/1744, in force "
    "27 July 2026."
)
_AI_LITERACY_ROLES = (Role.PROVIDER, Role.DEPLOYER)
# Art. 4 AIA names no exception for a system under an Art. 5 AIA prohibition, and a
# prohibition can apply from a later date (Art. 113, third paragraph, point (a): Art. 5(1),
# first subparagraph, points (ba) and (bb), from 2 December 2026) or be subject to an
# exception. The report keeps the duty for a prohibited system and flags it.
PROHIBITED_LITERACY_FLAG = (
    "Literal reading, confirm with counsel: Art. 4 AIA names no exception for a system "
    "this report classifies as prohibited under Art. 5 AIA, so the report keeps the Art. 4 "
    "duty. A prohibition can apply from a later date, as Art. 5(1), first subparagraph, "
    "points (ba) and (bb) do from 2 December 2026, or be subject to an exception."
)


def ai_literacy_applies(final_tier: RiskTier) -> bool:
    """Art. 4 AIA binds providers and deployers of every AI system within the Regulation's
    scope, whatever its tier. A prohibited system keeps the duty, flagged
    (PROHIBITED_LITERACY_FLAG). The engine and the obligation graph both ask this."""

    return final_tier is not RiskTier.OUT_OF_SCOPE


def ai_literacy_roles(roles: list[Role]) -> list[Role]:
    """The roles Art. 4 AIA addresses that ``roles`` holds, each once: provider, then
    deployer."""

    return [role for role in _AI_LITERACY_ROLES if role in roles]


def ai_literacy_listed_requirement(flag: str = "") -> str:
    """The Art. 4 AIA requirement of the obligations list, with ``flag`` appended where
    the report keeps the duty under a counsel flag (a Section B product, a prohibited
    system)."""

    return f"{AI_LITERACY_REQUIREMENT} {flag}" if flag else AI_LITERACY_REQUIREMENT


# Art. 72(3) AIA as replaced by Regulation (EU) 2026/1744, Art. 1, point (30): the plan
# is part of the Annex IV technical documentation and the Commission adopts guidance,
# including a template, by 2 September 2027.
ART_72_REQUIREMENT = (
    "Operate a post-market monitoring system based on a post-market monitoring plan, which "
    "is part of the Annex IV technical documentation. The Commission's guidance on the plan, "
    "including a template, is due by 2 September 2027 (Art. 72(3) AIA as replaced by Art. 1, "
    "point (30) of Regulation (EU) 2026/1744)."
)
# Art. 73(1) AIA names the market surveillance authorities; Art. 75(1a), inserted by
# Regulation (EU) 2026/1744, Art. 1, point (31)(c), routes the providers of the systems
# under the AI Office's exclusive competence (Art. 75(1)) to the AI Office instead. The
# profile does not record that competence, so the text states both routes.
ART_73_REQUIREMENT = (
    "Report serious incidents to the market surveillance authorities of the Member States "
    "where the incident occurred (Art. 73(1) AIA), or to the AI Office where it is exclusively "
    "competent for the system under Art. 75(1), as for AI systems based on a general-purpose "
    "AI model developed by the same provider or its undertaking, with the exceptions listed "
    "there, and systems of designated very large online platforms or search engines "
    "(Art. 75(1a) AIA, inserted by Art. 1, point (31) of Regulation (EU) 2026/1744)."
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


# Arts. 9 to 15 AIA (Chapter III, Section 2): article number, requirement and evidence
# artifact of each provider duty. The titles are in DUTY_TITLES.
HIGH_RISK_SECTION_2_DUTIES: tuple[tuple[int, str, str], ...] = (
    (
        9,
        "Establish, document and maintain a continuous risk management system.",
        "Risk management file.",
    ),
    (
        10,
        "Apply data governance to training, validation and testing data sets.",
        "Data governance record.",
    ),
    (
        11,
        "Draw up technical documentation (Annex IV) before placing on the market.",
        "Annex IV technical documentation.",
    ),
    (
        12,
        "Enable automatic recording of events (logs) over the system's lifetime.",
        "Event logging design record.",
    ),
    (
        13,
        "Provide instructions for use enabling deployers to comply.",
        "Instructions for use.",
    ),
    (
        14,
        "Design the system for effective oversight by natural persons.",
        "Human oversight design record.",
    ),
    (
        15,
        "Achieve appropriate accuracy, robustness and cybersecurity.",
        "Accuracy, robustness and cybersecurity test record.",
    ),
)

# One title per article. report.obligations takes each entry from the graph item of the
# same article (obligation_graph.listed_obligations), which has no title of its own.
DUTY_TITLES: dict[str, str] = {
    ART_2_2: "Annex I, Section B product: limited application",
    ART_4: "AI literacy",
    "Art. 9 AIA": "Risk management system",
    "Art. 10 AIA": "Data and data governance",
    "Art. 11 AIA": "Technical documentation",
    "Art. 12 AIA": "Record-keeping (logging)",
    "Art. 13 AIA": "Transparency to deployers",
    "Art. 14 AIA": "Human oversight",
    "Art. 15 AIA": "Accuracy, robustness, cybersecurity",
    "Art. 16 AIA": "Provider obligations",
    "Art. 17 AIA": "Quality management system",
    "Art. 18 AIA": "Document retention",
    "Art. 19 AIA": "Log retention",
    "Art. 20 AIA": "Corrective action and notification",
    "Art. 21 AIA": "Authority cooperation",
    "Art. 22 AIA": "Authorised representative obligations",
    "Art. 23 AIA": "Importer obligations",
    "Art. 24 AIA": "Distributor obligations",
    "Art. 25 AIA": "Value-chain provider responsibility",
    "Art. 26 AIA": "Deployer obligations",
    "Art. 27 AIA": "Fundamental rights impact assessment",
    "Art. 43 AIA": "Conformity assessment",
    "Art. 43(2) AIA": "Conformity assessment based on internal control",
    "Art. 47 AIA": "EU declaration of conformity",
    "Art. 48 AIA": "CE marking",
    ART_49: "Registration",
    ART_49_2: "Registration when relying on Art. 6(3)",
    ART_49_3: "Registration of use by a public-authority deployer",
    "Art. 49(5) AIA": "Registration at national level",
    "Art. 53(1)(a) AIA": "Model technical documentation",
    "Art. 53(1)(b) AIA": "Information to downstream providers",
    "Art. 53(1)(c) AIA": "Copyright policy",
    "Art. 53(1)(d) AIA": "Training-content summary",
    "Art. 55(1)(a) AIA": "Model evaluation",
    "Art. 55(1)(b) AIA": "Systemic-risk mitigation",
    "Art. 55(1)(c) AIA": "Serious-incident tracking",
    "Art. 55(1)(d) AIA": "Cybersecurity",
    "Art. 72 AIA": "Post-market monitoring",
    "Art. 73 AIA": "Serious incident reporting",
    ART_111_2: "System already placed on the market or put into service",
}


def section_b_requirement(*, annex_iii: bool = False, flag: str = "") -> str:
    """The Art. 2(2) AIA requirement; for a Section B product also in an Annex III area
    (``annex_iii``) limited to the Art. 6(1) route, with ``flag`` appended if given."""

    requirement = f"{SECTION_B_PROVISIONS}. {SECTION_B_ROUTE}"
    if not annex_iii:
        return f"{requirement[0].upper()}{requirement[1:]}"
    return f"Through the Art. 6(1) route, {requirement}{f' {flag}' if flag else ''}"


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
