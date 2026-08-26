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
