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
2. Prohibited practices: Art. 5(1)(a) to (h) AIA as asserted by the reviewer,
   and Art. 5(1)(ba) and (bb) with Art. 5(1a) and (1b), inserted by Regulation
   (EU) 2026/1744 and applicable from 2 December 2026, subsumed from fact
   screens. A hit is a hard stop.
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

The rules added for Regulation (EU) 2026/1744 were built from the Official
Journal texts snapshotted in [`sources/`](../sources/README.md), each with its
URL, retrieval date and SHA-256 digest. The legal fixtures in
`tests/legal/fixtures/` were written from those snapshots before the rule code
changed and cite the pinpoint they rest on.

## Prohibitions From 2 December 2026

Art. 5(1), first subparagraph, points (ba) and (bb), and Art. 5(1a) and (1b)
apply from 2 December 2026 (Art. 113, third paragraph, point (a) AIA, as
replaced by Art. 1(40)(a) of Regulation (EU) 2026/1744). The reviewer states
facts in two screens, `intimate_imagery` for point (ba) and
`child_sexual_abuse_material` for point (bb). Each fact is `true`, `false` or
`null` (not established). The engine never reads `null` as `false`.

1. Content. Point (ba): the system generates realistic material of an
   identifiable person's intimate parts or sexually explicit activities, or
   manipulates such material so that exposure increases or the depicted activity
   changes (Art. 5(1b)), without that person's consent. Point (bb): the system
   generates or manipulates material or performance within Art. 2(c) and (e) of
   Directive 2011/93/EU, unless a "without right" defence applies under
   national law.
2. Placing on the market or putting into service (providers, importers): the
   content element plus Art. 5(1a)(a), that is the intended purpose, or a
   reasonably foreseeable and reproducible outcome without reasonable and
   adequate safeguards.
3. Use (deployers): the content element plus the deployer's purpose
   (Art. 5(1a)(b)).
4. Date: `assessment_date` is the date of the placing on the market, putting
   into service or use under assessment. Before 2 December 2026 a met point is
   reported as not yet applicable and routed to review; from that date it is a
   hard stop; without a date the engine keeps the prohibited tier and asks for
   the date.

Where a `null` fact could change the result, the open question names the facts
that decide it. A system that generates synthetic content or deep fakes without
both screens goes to review.

## High-Risk Logic

Annex I product-safety systems are high-risk where both the safety-component
route and third-party assessment route are asserted. The reviewer names the
Annex I legislation in `annex_i_legislation`; the engine derives the Section.
Annex I is applied as amended by Art. 1(41) of Regulation (EU) 2026/1744:
Section A, point 1 (Directive 2006/42/EC) is deleted and machinery under
Regulation (EU) 2023/1230 is Section B, point 21.

1. Section A: Chapter III obligations attach, applicable from 2 August 2028
   (Art. 113, third paragraph, point (c)(ii)).
2. Section B: only Art. 6(1), Art. 60a and Arts. 102 to 112 apply (Art. 2(2)
   AIA, as replaced by Art. 1(2)(a)). The engine attaches no Chapter III
   obligations and no Art. 50 transparency obligations. Where an Art. 5 finding
   or an Annex III listing coincides, the engine keeps it and raises an open
   question.
3. Legislation not named: the engine keeps the Section A consequence and asks
   for the legislation.

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

Two transitional rules turn on `placing_on_market_date`:

1. General-purpose AI models placed on the market before 2 August 2025 comply
   by 2 August 2027 (Art. 111(3) AIA, not amended by Regulation (EU) 2026/1744).
   Later models are bound from 2 August 2025 (Art. 113, third paragraph,
   point (b)).
2. Systems generating synthetic audio, image, video or text content placed on
   the market before 2 August 2026 comply with Art. 50(2) by 2 December 2026
   (Art. 111(4) AIA, added by Art. 1(39)(b)). Other Art. 50 duties keep
   2 August 2026.

Without a placing date, the affected obligation-graph items carry
`application_date: null`, are marked `review_required`, and the report asks for
the date. Each item also carries `applies_on_assessment_date`, which compares
the application date with `assessment_date` and stays `null` when either is
unknown. "Comply by" a date is read as applying on that date.

## Interpretation Choices

The source texts leave these points open. The engine labels each one
"interpretation" in its finding or open-question text, and the fixtures name
them. They are for the reviewer to confirm.

1. Consent under Art. 5(1)(ba) is read at system level for providers: the
   point is not met where the system generates the material only with the
   depicted person's consent (Recital 12).
2. The use limb, Art. 5(1a)(b), keeps the content element and drops the
   Art. 5(1a)(a) conditions.
3. Providers and importers are tested under Art. 5(1a)(a); deployers under
   Art. 5(1a)(b). A distributor alone leaves the result open.
4. A met point with no assessment date keeps the prohibited tier; a met point
   before 2 December 2026 goes to review.
5. A generative system without the Art. 5(1)(ba) and (bb) screens goes to
   review.
6. Art. 2(2) is read literally for Section B products, including Art. 50; an
   Art. 5 finding or an Annex III listing is kept and goes to review.
7. An Art. 6(1) system without named Annex I legislation keeps the Section A
   consequence.
8. "Comply by" in Art. 111(3) and (4) includes the named date.
9. Art. 111(4) is triggered by placing on the market only, not by putting into
   service.

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
9. Application date, or `null` where it turns on a fact not given.
10. Review status.
11. Whether it applies on the assessment date (`null` if unknown).

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
