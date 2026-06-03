# Sample output

Real runs of `eu-ai-act-classify` against three of the example profiles, so the
output is visible without installing anything. Reproduce with
`eu-ai-act-classify examples/<file>.json`.

## High-risk provider — credit scoring

Input (`examples/credit_scoring.json`):

```json
{
  "name": "CreditSightScore",
  "description": "Generates consumer creditworthiness scores for lenders.",
  "roles": ["provider"],
  "purpose": "Credit scoring",
  "sector": "Fintech",
  "annex_iii_area": "III.5.b"
}
```

Output:

```text
==============================================================================
EU AI Act classification — CreditSightScore
==============================================================================
Risk tier:    HIGH-RISK (Art. 6 AIA)
Disposition:  DETERMINED
Roles:        provider

Findings:
  [high] Annex III(5)(b) AIA — High-risk: Creditworthiness evaluation and credit scoring
      Annex III high-risk area (Art. 6(2) AIA); no derogation asserted.

Obligations:
  - Art. 9 AIA — Risk management system: Establish, document and maintain a continuous risk management system.
  - Art. 10 AIA — Data and data governance: Apply data governance to training, validation and testing data sets.
  - Art. 11 AIA — Technical documentation: Draw up technical documentation (Annex IV) before placing on the market.
  - Art. 12 AIA — Record-keeping (logging): Enable automatic recording of events (logs) over the system's lifetime.
  - Art. 13 AIA — Transparency to deployers: Provide instructions for use enabling deployers to comply.
  - Art. 14 AIA — Human oversight: Design the system for effective oversight by natural persons.
  - Art. 15 AIA — Accuracy, robustness, cybersecurity: Achieve appropriate accuracy, robustness and cybersecurity.
  - Art. 17 AIA — Quality management system: Put a quality management system in place.
  - Art. 43 AIA — Conformity assessment: Undergo the applicable conformity assessment before market placement.
  - Art. 47 AIA — EU declaration of conformity: Draw up and keep an EU declaration of conformity.
  - Art. 48 AIA — CE marking: Affix the CE marking to indicate conformity.
  - Art. 49 AIA — Registration: Register the system in the EU database before market placement.
  - Art. 72 AIA — Post-market monitoring: Operate a post-market monitoring system.
  - Art. 73 AIA — Serious incident reporting: Report serious incidents to the market surveillance authority.

Documentation to maintain:
  - Art. 11 AIA + Annex IV — Technical documentation: Annex IV technical documentation, kept current.
  - Art. 9 AIA — Risk management file: Documented risk management system and its results.
  - Art. 13 AIA — Instructions for use: Instructions enabling deployer compliance.
  - Art. 17 AIA — QMS documentation: Written quality management system policies and procedures.
  - Art. 47 AIA — EU declaration of conformity: Signed EU declaration of conformity.

Application timeline (Art. 113 AIA):
  2025-02-02 — Chapters I-II, incl. Art. 5 (prohibited practices)
  2025-08-02 — Chapter V (general-purpose AI models)
  2026-08-02 — General application, incl. Annex III high-risk systems
  2027-08-02 — Art. 6(1) / Annex I high-risk (product-safety route)
```

## GPAI model with systemic risk

Input (`examples/foundation_model_systemic.json`) — note `training_flops` above the 10^25 presumption:

```json
{
  "name": "Atlas-70B",
  "roles": ["gpai_provider", "provider"],
  "is_gpai_model": true,
  "training_flops": 5e25
}
```

Output (abridged to the findings and obligations):

```text
Risk tier:    MINIMAL RISK
Disposition:  DETERMINED
Roles:        gpai_provider, provider
GPAI:         general-purpose AI model with systemic risk (Art. 51 AIA)

Findings:
  [high] Art. 51 AIA — General-purpose AI model with systemic risk
      Systemic risk on the basis of training compute above the 10^25 FLOP presumption (Art. 51(2) AIA).

Obligations:
  - Art. 53(1)(a) AIA — Model technical documentation: Draw up and keep technical documentation per Annex XI.
  - Art. 53(1)(b) AIA — Information to downstream providers: Provide downstream providers with information per Annex XII.
  - Art. 53(1)(c) AIA — Copyright policy: Put in place a policy to comply with Union copyright law.
  - Art. 53(1)(d) AIA — Training-content summary: Publish a sufficiently detailed summary of training content.
  - Art. 55(1)(a) AIA — Model evaluation: Perform model evaluation, including adversarial testing.
  - Art. 55(1)(b) AIA — Systemic-risk mitigation: Assess and mitigate systemic risks at Union level.
  - Art. 55(1)(c) AIA — Serious-incident tracking: Track, document and report serious incidents.
  - Art. 55(1)(d) AIA — Cybersecurity: Ensure an adequate level of cybersecurity protection.
```

The system tier is minimal — a general-purpose model is not itself an Annex III
use case — but Chapter V duties attach to the model provider regardless.

## Machine-readable output (`--json`)

Input (`examples/support_chatbot.json`) classified with `--json`:

```json
{
  "system": "HelpDesk Assistant",
  "risk_tier": "limited_risk",
  "disposition": "determined",
  "roles": ["provider"],
  "is_gpai": false,
  "gpai_systemic": false,
  "findings": [
    {
      "rule_id": "TRANSPARENCY.50",
      "citation": "Art. 50(1) AIA",
      "citation_verified": true,
      "title": "Transparency obligations apply",
      "severity": "medium",
      "tier": "limited_risk"
    }
  ],
  "transparency_obligations": [
    {
      "article": "Art. 50(1) AIA",
      "title": "Inform persons of AI interaction",
      "applies_to": "provider",
      "requirement": "Inform natural persons that they are interacting with an AI system, unless obvious."
    }
  ],
  "open_questions": [],
  "unverified_citations": []
}
```

The JSON is the surface an intake pipeline or an agent consumes (timeline and
disclaimer fields omitted here for length).
