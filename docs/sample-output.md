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
  Transitional status: No transitional limitation identified from the submitted facts.

Findings:
  [high] Annex III(5)(b) AIA: High-risk: Creditworthiness evaluation and credit scoring

Obligation graph:
  - high-risk.provider.16: Art. 16 AIA (provider), evidence: Provider compliance responsibility matrix, review: draft
  - high-risk.provider.43: Art. 43 AIA (provider), evidence: Conformity assessment file, review: review_required
  - high-risk.provider.72: Art. 72 AIA (provider), evidence: Post-market monitoring plan, review: draft

Binding application timeline:
  2025-02-02: Chapters I-II, incl. Art. 5 (prohibited practices)
  2025-08-02: Chapter V (general-purpose AI models)
  2026-08-02: General application for provisions without a later specific date
  2027-12-02: Regulation (EU) 2026/1744: Annex III high-risk systems
  2028-08-02: Regulation (EU) 2026/1744: product-embedded high-risk systems

Source manifest:
  - Regulation (EU) 2024/1689: binding_level_1, retrieved 2026-08-26
  - Regulation (EU) 2026/1744: binding_level_1, retrieved 2026-08-26
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
      "evidence_artifact": "GPAI model documentation checklist."
    }
  ]
}
```
