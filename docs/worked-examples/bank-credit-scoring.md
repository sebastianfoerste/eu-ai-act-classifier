# Worked example: a bank's credit-scoring model (deployer)

> Synthetic profile, not legal advice. The classifier is a first-pass screening tool: it applies encoded rules to facts a lawyer has already characterised. A qualified lawyer confirms the characterisation and the result before anyone relies on them.

## The case

A bank uses a credit-scoring model bought from a third party to decide consumer loan applications. It does not build, modify or rebrand the model. The profile is [`examples/credit_scoring_deployer.json`](../../examples/credit_scoring_deployer.json):

```json
{
  "name": "BankCo loan underwriting",
  "description": "A bank deploying a third-party credit scoring model for consumer loan decisions.",
  "roles": ["deployer"],
  "purpose": "Loan underwriting",
  "sector": "Banking",
  "annex_iii_area": "III.5.b"
}
```

## Run it

```bash
uv run eu-ai-act-classify examples/credit_scoring_deployer.json
```

Output (44 lines; only the nonbinding entries of the source manifest are cut):

```text
EU AI Act classification: BankCo loan underwriting
Risk tier: HIGH-RISK (Art. 6 AIA)
Disposition: DETERMINED
Scope status: in_scope
Roles: deployer

Scope and intake:
  AI system: True
  EU nexus: True
  Transitional status: No transitional limitation identified from the submitted facts.

Findings:
  [high] Annex III(5)(b) AIA: High-risk: Creditworthiness evaluation and credit scoring of natural persons
      Annex III high-risk area (Art. 6(2) AIA); no derogation asserted.

Obligations:
  - Art. 26 AIA: Deployer obligations. Use per instructions, assign human oversight, monitor use, keep logs.
  - Art. 27 AIA: Fundamental rights impact assessment. Conduct a fundamental rights impact assessment before deployment.

Obligation graph:
  - high-risk.deployer.26: Art. 26 AIA (deployer), evidence: Deployer operating procedure and monitoring log., review: determined
  - high-risk.deployer.27: Art. 27 AIA (deployer), evidence: Draft FRIA and notification record., review: review_required

Binding application timeline:
  2025-02-02: Chapters I-II, incl. Art. 5 (prohibited practices)
  2025-08-02: Chapter V (general-purpose AI models)
  2026-08-02: General application for provisions without a later specific date
  2027-12-02: Regulation (EU) 2026/1744: Annex III high-risk systems
  2028-08-02: Regulation (EU) 2026/1744: product-embedded high-risk systems

Source manifest:
  - Regulation (EU) 2024/1689: binding_level_1, retrieved 2026-08-26
  - Regulation (EU) 2026/1744: binding_level_1, retrieved 2026-08-26
[... 8 lines omitted]

Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024, as amended by Regulation (EU) 2026/1744
This is a screening tool, not legal advice. It does not produce a conformity assessment and it does not replace review by a qualified lawyer. Determinations marked 'requires_review' turn on facts the engine cannot settle.
```

## What the classifier decided

- **Tier:** high-risk under Art. 6(2) AIA and Annex III(5)(b), creditworthiness evaluation and credit scoring of natural persons.
- **Disposition:** `DETERMINED`. No rule raised an open question, so `--strict` exits 0.
- **Duties:** the profile names only the deployer role, so the bank gets Art. 26 (use per instructions, human oversight, monitoring, logs) and the Art. 27 fundamental rights impact assessment (FRIA). Art. 27(1) requires a FRIA from deployers of point 5(b) systems before first use. No provider duties attach on these facts.
- **Date:** in the JSON report (`--json`) both obligation-graph items carry `"application_date": "2027-12-02"`. Art. 113, third paragraph, point (c)(i), as amended by Regulation (EU) 2026/1744, sets that date for Chapter III, Sections 1 to 3, for Annex III systems; Arts. 26 and 27 sit in Section 3.

## What a lawyer still has to decide

1. **The Annex III characterisation.** Point 5(b) covers natural persons only. Consumer loans fit; lending to companies does not. A mixed portfolio has to be split. The engine takes `annex_iii_area` as given.
2. **The fraud-detection exception.** Point 5(b) excepts "AI systems used for the purpose of detecting financial fraud". The profile leaves `used_for_financial_fraud_detection` at its default, `false`. If the model also serves fraud detection, set it to `true` (or `null` while unknown): the system stays high-risk and the report raises an open question instead of applying the exception.
3. **The role.** The bank stays a deployer only while it does not put its name or trademark on the model, substantially modify it, or change its intended purpose (Art. 25(1)). Any of these makes it the provider. The profile flags `substantially_modifies_system` and `puts_name_or_trademark_on_system` cover the first two.
4. **The FRIA itself.** The engine flags the duty (`review_required`); `--artifact fria` writes a draft. The lawyer settles its content under Art. 27(1), the notification of the results to the market surveillance authority (Art. 27(3)), and any cross-references to the GDPR data protection impact assessment (Art. 27(4)).
5. **Financial-institution rules the engine does not encode.** For a deployer that is a financial institution subject to internal-governance requirements under Union financial services law, the Art. 26(5) monitoring duty is deemed fulfilled through those governance rules, and logs are kept within the financial-services documentation (Art. 26(5) and (6), second subparagraphs). Art. 26(11) requires telling natural persons that they are subject to the system, and Art. 86 gives affected persons a right to an explanation. The market surveillance authority is the financial supervisor where the use is in direct connection with financial services (Art. 74(6)), unless the Member State designates another authority (Art. 74(7)). None of this appears in the output.
6. **Other law.** Data protection, consumer-credit and banking supervisory law are outside the classifier.

## Boundaries

The profile and the bank are synthetic. This page is not legal advice. The provisions named above were checked on 14 October 2026 against the consolidated text of Regulation (EU) 2024/1689 as amended on 27 July 2026, in the [legalize-dev/legalize-eu](https://github.com/legalize-dev/legalize-eu) GitHub mirror of EUR-Lex/CELLAR (`eu/e0/32024R1689.md`, mirror commit `3709ccf`); EUR-Lex itself was unreachable. Recheck on EUR-Lex before relying on them. The quoted output is the CLI's own; `tests/test_docs.py` fails if it drifts from what the CLI prints.
