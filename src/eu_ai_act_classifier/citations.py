"""Single source of truth for EU AI Act citations.

All references are to Regulation (EU) 2024/1689 (Artificial Intelligence Act),
OJ L, 2024/1689, 12.7.2024 ("AIA"). Pinpoint citations follow the German
convention: ``Art. <article> Abs. <paragraph> lit. <letter> AIA``, rendered
here in the shorter ``Art. 5(1)(f) AIA`` form for readability.

A citation carries a ``verified`` flag. ``verified=False`` means the exact
sub-point lettering is pending confirmation against the consolidated EUR-Lex
text — the two Annex III areas (law enforcement, migration) were renumbered
between trilogue drafts, so their sub-point letters are flagged rather than
asserted. The engine propagates this flag into its output so a reviewing
lawyer sees precisely which pinpoints are not yet locked, instead of trusting
a citation that was guessed.
"""

from __future__ import annotations

from dataclasses import dataclass

REGULATION = (
    "Regulation (EU) 2024/1689 of the European Parliament and of the Council "
    "of 13 June 2024 (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024"
)
SHORT = "AIA"


@dataclass(frozen=True, slots=True)
class Citation:
    """A pinpoint reference into the AIA.

    ``verified`` is False where the sub-point lettering is not yet confirmed
    against the official text. ``noch zu verifizieren`` is preserved verbatim
    in rendered output for any unverified citation.
    """

    ref: str
    verified: bool = True

    def render(self) -> str:
        suffix = "" if self.verified else "  [noch zu verifizieren]"
        return f"{self.ref}{suffix}"


def cite(ref: str, *, verified: bool = True) -> Citation:
    return Citation(ref=ref, verified=verified)


# --- Application timeline (Art. 113 AIA) -----------------------------------
# Entry into force 1.8.2024; staggered application thereafter.
@dataclass(frozen=True, slots=True)
class ApplicationDate:
    provision: str
    date: str
    note: str


APPLICATION_DATES: tuple[ApplicationDate, ...] = (
    ApplicationDate(
        "Chapters I-II, incl. Art. 5 (prohibited practices)",
        "2025-02-02",
        "Prohibitions apply from 2 February 2025 (Art. 113(a) AIA).",
    ),
    ApplicationDate(
        "Chapter V (general-purpose AI models)",
        "2025-08-02",
        "GPAI obligations apply from 2 August 2025 (Art. 113(b) AIA).",
    ),
    ApplicationDate(
        "General application, incl. Annex III high-risk systems",
        "2026-08-02",
        "Most obligations apply from 2 August 2026 (Art. 113 AIA).",
    ),
    ApplicationDate(
        "Art. 6(1) / Annex I high-risk (product-safety route)",
        "2027-08-02",
        "Annex I high-risk obligations apply from 2 August 2027 (Art. 113(c) AIA).",
    ),
)
