# Sample Output

This page shows the shape of the v0.2 output. The exact obligation list may grow
as the source registry and obligation graph are extended.

## CLI Report

Command:

```bash
eu-ai-act-classify examples/credit_scoring.json --advisory
```

Selected output:

```text
EU AI Act classification: CreditSightScore
Risk tier: HIGH-RISK (Art. 6 AIA)
Disposition: DETERMINED
Scope status: in_scope
Roles: provider

Scope and intake:
  AI system: True
  EU nexus: True
  Assessment date: not given
  Transitional status: No transitional limitation identified from the submitted facts.

Findings:
  [high] Annex III(5)(b) AIA: High-risk: Creditworthiness evaluation and credit scoring

Obligation graph:
  - high-risk.provider.16: Art. 16 AIA (provider), evidence: Provider compliance responsibility matrix, review: draft
  - high-risk.provider.43: Art. 43 AIA (provider), evidence: Conformity assessment file, review: review_required
  - high-risk.provider.72: Art. 72 AIA (provider), evidence: Post-market monitoring plan, review: draft

Binding application timeline:
  2025-02-02: Chapters I-II, incl. Art. 5 (prohibited practices), with 2026/1744 exceptions
  2025-08-02: Chapter V (general-purpose AI models)
  2026-07-27: Art. 2(2) and Annex I as amended: machinery moved to Annex I, Section B
  2026-07-27: Arts. 102 to 110 (amendments to other Union acts)
  2026-08-02: General application for provisions without a later specific date
  2026-12-02: Art. 5(1)(ba), (bb), (1a), (1b) (prohibitions added by Reg. (EU) 2026/1744)
  2026-12-02: Art. 50(2) for generative AI systems placed on the market before 2026-08-02
  2027-08-02: Art. 111(3): GPAI models placed on the market before 2025-08-02
  2027-12-02: Chapter III, Sections 1 to 3: Art. 6(2) and Annex III high-risk systems
  2028-08-02: Chapter III, Sections 1 to 3: Art. 6(1) and Annex I high-risk systems

Source manifest:
  - Regulation (EU) 2024/1689: binding_level_1, retrieved 2026-08-26
  - Regulation (EU) 2026/1744: binding_level_1, retrieved 2026-08-26
  - Directive 2011/93/EU: binding_level_1, retrieved 2026-10-14
```

## Artifact Draft

Command:

```bash
eu-ai-act-classify examples/credit_scoring.json --artifact fria --artifacts-dir ./draft-artifacts
```

The generated Markdown draft includes:

1. Draft-only notice.
2. System, risk tier, disposition and scope status.
3. Review status.
4. Checklist.
5. Relevant obligation graph items.
6. Open questions.
7. Source manifest.

## GPAI JSON

Command:

```bash
eu-ai-act-classify examples/foundation_model_systemic.json --json
```

Selected fields:

```json
{
  "risk_tier": "minimal_risk",
  "is_gpai": true,
  "gpai_systemic": true,
  "obligation_graph": [
    {
      "obligation_id": "gpai.provider.53.a",
      "article": "Art. 53(1)(a) AIA",
      "actor": "gpai_provider",
      "evidence_artifact": "GPAI model documentation checklist.",
      "application_date": "2027-08-02",
      "applies_on_assessment_date": null
    }
  ]
}
```

The model was placed on the market on 2025-06-16, before 2 August 2025, so its
Chapter V obligations apply from 2 August 2027 (Art. 111(3) AIA). Without a
`placing_on_market_date` the application date is `null` and the report asks for
it; without an `assessment_date`, `applies_on_assessment_date` stays `null`.
