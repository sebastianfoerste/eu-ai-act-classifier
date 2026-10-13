# Methodology

This document records how Regulation (EU) 2024/1689 is encoded in the
classifier. It is the legal audit surface.

## Division Of Labour

The engine subsumes characterised facts under rules. It does not characterise
facts. The lawyer or reviewer decides whether the submitted system qualifies as
an AI system, what the intended purpose is, whether Annex I or Annex III is
triggered, and whether an asserted derogation is evidenced.

That division keeps the output deterministic. The `SystemProfile` states the
facts. The engine applies the rules and makes uncertainty visible.

## Gate Order

1. Scope and intake: Art. 2, Art. 3(1), intended purpose, EU nexus, exclusions
   and Article 111 transition facts.
2. Prohibited practices: Art. 5(1)(a) to (h) AIA. A hit is a hard stop. Art. 5(1)(ba)
   and (bb), inserted by Regulation (EU) 2026/1744 and applicable from 2 December
   2026, are not yet encoded.
3. High-risk classification: Art. 6(1), Art. 6(2), Art. 6(3), Annex I and
   Annex III.
4. GPAI: Art. 51 systemic threshold and Arts. 53, 55 and 56 obligations.
5. Transparency: Art. 50(1) to (4) AIA.
6. Resolution: highest tier, review disposition, source-backed obligations,
   timeline and open legal questions.

## Source Statuses

Binding Level 1 text drives classification and obligations. The current source
layer is Regulation (EU) 2024/1689 as amended by Regulation (EU) 2026/1744. The
amending Regulation was adopted on 8 July 2026, published in the Official
Journal on 24 July 2026 and entered into force on 27 July 2026. Its amended
application dates are therefore binding source data rather than provisional
context. The consolidated version of 27 July 2026 is the navigation text. It
states that it has no legal effect; the Official Journal texts are authentic.

The source-status model retains a provisional category for future political
agreements. No provisional AI Omnibus source remains in the current manifest.

Nonbinding guidance appears only as advisory overlay or eval context. The
overlay can point reviewers to Commission materials, the AI Act Service Desk,
the GPAI Code of Practice and draft high-risk guidance. It never changes the
binding classification.

## High-Risk Logic

Annex I product-safety systems are high-risk where both the safety-component
route and third-party assessment route are asserted. The engine does not
distinguish Section A from Section B of Annex I. For Section B products only
Art. 6(1), Art. 60a and Arts. 102 to 112 apply (Art. 2(2) AIA). Regulation (EU)
2026/1744 moved machinery, now Regulation (EU) 2023/1230, from Section A to
Section B (Art. 1(41)). That move is not encoded.

Annex III systems are treated as high-risk unless an Art. 6(3) derogation is
asserted. An asserted derogation keeps the tier high-risk and changes the
disposition to `requires_review`, because Art. 6(4) requires documentation and
registration. Profiling of natural persons forecloses the derogation.

The residual `AnnexIII.UNSURE` value is conservative. It marks the system
high-risk and records an unverified citation for review.

## Application Dates

The binding timeline follows Art. 113 AIA as amended by Regulation (EU)
2026/1744. Chapter III, Sections 1 to 3, except Art. 6(5), apply from
2 December 2027 for Art. 6(2) and Annex III systems and from 2 August 2028 for
Art. 6(1) and Annex I systems (Art. 113, third paragraph, point (c)). The
obligation graph also gives those dates to Arts. 40 to 49 (Chapter III,
Section 5) and Arts. 72 and 73 (Chapter IX). Art. 113 does not name those
provisions, so on the text they fall under the general date of 2 August 2026.
The later date is an inference from the deferred application of Art. 6. The
reviewer should treat it as an open legal question.

## FRIA Logic

Art. 27 is automatic for deployers of Annex III point 5(b) creditworthiness and
point 5(c) life and health insurance.

Art. 27 is also attached where the submitted facts establish a public-law
deployer or a private entity providing public services.

Annex III point 2 critical infrastructure is excluded from the Art. 27 trigger.
The engine suppresses the generic FRIA open question for that case.

Where the deployment is high-risk and the deployer status is incomplete, the
engine raises a review question instead of asserting a FRIA conclusion.

## Obligation Graph

The legacy obligation lists remain for compatibility. The richer
`obligation_graph` is the product surface for review workflows.

Each graph item records:

1. Obligation ID.
2. Article.
3. Actor role.
4. Trigger.
5. Requirement.
6. Evidence artifact.
7. Source status.
8. Source URL.
9. Application date.
10. Review status.

The graph covers high-risk provider, deployer, importer, distributor,
authorised representative, value-chain, GPAI, transparency, post-market
monitoring and serious-incident duties.

## Draft Work Products

Artifact generation is draft-only. Generated files include a source manifest,
open questions and a review status. They do not claim to be legal advice,
conformity assessments or final regulatory filings.

The artifacts are:

1. Art. 6(4) non-high-risk assessment.
2. Art. 27 FRIA.
3. Annex IV technical documentation checklist.
4. Post-market monitoring plan.
5. Serious-incident register.
6. GPAI model documentation checklist.
7. Training-content summary checklist.

## Citation Policy

Citations are pinpoint, for example `Art. 6(2) AIA` and `Annex III(5)(b) AIA`.

Unconfirmed pinpoints are flagged `noch zu verifizieren` and carried in
`report.unverified_citations`. Nothing is invented.

## Boundaries

The classifier is a triage and review tool. It does not replace legal judgment,
conformity assessment work, notified-body processes, regulator filings or
organisation-specific advice.
