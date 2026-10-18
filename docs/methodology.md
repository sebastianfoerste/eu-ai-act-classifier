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
2. Prohibited practices: Art. 5(1)(a) to (h) AIA. A hit is a hard stop.
3. High-risk classification: Art. 6(1), Art. 6(2), Art. 6(3), Annex I and
   Annex III.
4. GPAI: Art. 51 systemic threshold and Arts. 53, 55 and 56 obligations.
5. Transparency: Art. 50(1) to (4) AIA.
6. Resolution: highest tier, review disposition, source-backed obligations,
   timeline and open legal questions.

## Source Statuses

Binding Level 1 text drives classification and obligations. The current source
layer is Regulation (EU) 2024/1689 as consolidated on 27 July 2026 together
with Regulation (EU) 2026/1744. The latter was adopted on 8 July 2026 and
published in the Official Journal on 24 July 2026. Its amended application
dates are therefore binding source data rather than provisional context.

The source-status model retains a provisional category for future political
agreements. No provisional AI Omnibus source remains in the current manifest.

Nonbinding guidance appears only as advisory overlay or eval context. The
overlay can point reviewers to Commission materials, the AI Act Service Desk,
the GPAI Code of Practice and draft high-risk guidance. It never changes the
binding classification.

## High-Risk Logic

Annex I product-safety systems are high-risk where both the safety-component
route and third-party assessment route are asserted.

Annex III systems are treated as high-risk unless an Art. 6(3) derogation is
asserted. An asserted derogation keeps the tier high-risk and changes the
disposition to `requires_review`, because Art. 6(4) requires documentation and
registration. Profiling of natural persons forecloses the derogation.

The residual `AnnexIII.UNSURE` value is conservative. It marks the system
high-risk and records an unverified citation for review.

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
11. Application date note, where the date rests on a contestable reading or a
    transitional rule.

The graph covers high-risk provider, deployer, importer, distributor,
authorised representative, value-chain, GPAI, transparency, post-market
monitoring and serious-incident duties.

## Application Dates

Dates follow Art. 113 AIA as amended by Regulation (EU) 2026/1744, checked on
18 October 2026 against the consolidated text of 27 July 2026.

Chapter III, Sections 1, 2 and 3 (Arts. 6 to 27, except Art. 6(5)) apply from
2 December 2027 for Annex III systems and from 2 August 2028 for Annex I
systems (Art. 113, third paragraph, point (c)). Graph items for Arts. 16 to 27
carry that date.

Point (c) does not defer Chapter III, Section 5 (Arts. 40 to 49) or Chapter IX
(Arts. 72 and 73). Read literally, those duties apply from the general date of
2 August 2026 (Art. 113, second paragraph). That reading is contested: the
duties bite only on systems classified high-risk under Art. 6, which is itself
deferred. Art. 16(f) to (i) also makes Arts. 43, 47, 48 and 49(1) provider
duties, and Art. 17(1)(h) and (i) builds Arts. 72 and 73 into the quality
management system; both sit in Section 3 and are deferred too. The graph
therefore gives these items
2026-08-02 with the note "Literal reading, confirm with counsel", names the
deferred date that applies if they follow Sections 1 to 3, and marks them
`review_required`. The engine does not pick a side.

Art. 50 items (Chapter IV) carry 2 August 2026. Under Art. 111(4), providers of
generative systems placed on the market before that date have until
2 December 2026 to comply with Art. 50(2); the Art. 50(2) item carries that
transition as its note unless the profile gives a later placing-on-market date. GPAI items (Chapter V) carry 2 August 2025.

The binding timeline also lists the point (a) exception (Art. 5(1), first
subparagraph, points (ba) and (bb), and Art. 5(1a) and (1b), from
2 December 2026), the full point (b) list (Chapter III Section 4, Chapters V,
VII and XII except Art. 101, and Art. 78, from 2 August 2025) and point (d)
(Arts. 102 to 110, from 27 July 2026).

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
