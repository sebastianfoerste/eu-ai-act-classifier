# Worked example: a life insurer's term-life pricing model (provider and deployer)

> Synthetic profile, not legal advice. The classifier is a first-pass screening tool: it applies encoded rules to facts a lawyer has already characterised. A qualified lawyer confirms the characterisation and the result before anyone relies on them.

## The case

A German life insurer builds a gradient-boosted model in house and uses it in its own underwriting to price term-life premiums from applicant health questionnaires. The insurer and its model are synthetic. The profile is [`examples/life_insurer_pricing.json`](../../examples/life_insurer_pricing.json):

```json
{
  "name": "Musterversicherung term-life pricing model",
  "description": "A synthetic German life insurer's gradient-boosted model that sets term-life premiums from applicant health questionnaires. The insurer builds the model and uses it in its own underwriting.",
  "roles": ["provider", "deployer"],
  "purpose": "Risk assessment and pricing of term-life insurance for natural persons",
  "sector": "Life insurance",
  "annex_iii_area": "III.5.c",
  "derogation": {
    "performs_profiling": true
  }
}
```

## Run it

```bash
uv run eu-ai-act-classify examples/life_insurer_pricing.json
```

Output (97 lines; the cuts are marked):

```text
EU AI Act classification: Musterversicherung term-life pricing model
Risk tier: HIGH-RISK (Art. 6 AIA)
Disposition: DETERMINED
Scope status: in_scope
Roles: provider, deployer

Scope and intake:
  AI system: True
  EU nexus: True
  Transitional status: No transitional limitation identified from the submitted facts.

Findings:
  [high] Annex III(5)(c) AIA: High-risk: Risk assessment and pricing for natural persons in life and health insurance
      Annex III high-risk area. Profiling of natural persons keeps the system high-risk despite any derogation (Art. 6(3), third subparagraph, AIA).

Obligations:
  - Art. 9 AIA: Risk management system. Establish, document and maintain a continuous risk management system.
[... 13 lines omitted]
  - Art. 26 AIA: Deployer obligations. Use per instructions, assign human oversight, monitor use, keep logs.
  - Art. 27 AIA: Fundamental rights impact assessment. Conduct a fundamental rights impact assessment before deployment.

[... 7 lines omitted]
Obligation graph:
[... 12 lines omitted]
  - high-risk.provider.43: Art. 43 AIA (provider), evidence: Conformity assessment file., review: review_required
      Literal reading, confirm with counsel: Art. 113, third paragraph, point (c) AIA defers only Chapter III, Sections 1, 2 and 3, so this Chapter III, Section 5 duty applies from 2026-08-02 (Art. 113, second paragraph). If it is read as following that deferral, 2027-12-02 applies.
  - high-risk.provider.43.2: Art. 43(2) AIA (provider), evidence: Annex VI internal-control assessment record., review: review_required
      Literal reading, confirm with counsel: Art. 113, third paragraph, point (c) AIA defers only Chapter III, Sections 1, 2 and 3, so this Chapter III, Section 5 duty applies from 2026-08-02 (Art. 113, second paragraph). If it is read as following that deferral, 2027-12-02 applies.
[... 10 lines omitted]
  - high-risk.deployer.26: Art. 26 AIA (deployer), evidence: Deployer operating procedure and monitoring log., review: determined
  - high-risk.deployer.27: Art. 27 AIA (deployer), evidence: Draft FRIA and notification record., review: review_required

Binding application timeline:
  2025-02-02: Chapters I-II, incl. Art. 5 (prohibited practices)
  2025-08-02: Chapter V (general-purpose AI models)
  2025-08-02: Chapter III Section 4, Chapter VII, Chapter XII (except Art. 101) and Art. 78
  2026-07-27: Regulation (EU) 2026/1744: Arts. 102-110 AIA (amendments to other Union acts)
  2026-08-02: General application for provisions without a later specific date
  2026-12-02: Regulation (EU) 2026/1744: Art. 5(1)(ba) and (bb), Art. 5(1a) and (1b) AIA
  2026-12-02: Regulation (EU) 2026/1744: Art. 50(2) AIA for generative systems already on the market
  2027-08-02: Art. 111(3) AIA: general-purpose AI models already on the market before 2 August 2025
  2027-12-02: Regulation (EU) 2026/1744: Chapter III Sections 1-3, Annex III high-risk systems
  2028-08-02: Regulation (EU) 2026/1744: Chapter III Sections 1-3, product-embedded high-risk systems
  2030-08-02: Regulation (EU) 2026/1744: Art. 111(2) AIA, high-risk systems for public authorities

Source manifest:
  - Regulation (EU) 2024/1689: binding_level_1, retrieved 2026-10-18
  - Regulation (EU) 2026/1744: binding_level_1, retrieved 2026-10-18
[... 8 lines omitted]

Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024, as amended by Regulation (EU) 2026/1744
This is a screening tool, not legal advice. It does not produce a conformity assessment and it does not replace review by a qualified lawyer. Determinations marked 'requires_review' turn on facts the engine cannot settle.
```

## What the classifier decided

- **Tier:** high-risk under Art. 6(2) AIA and Annex III(5)(c), risk assessment and pricing for natural persons in life and health insurance. Because the profile asserts profiling, the finding notes that the Art. 6(3) derogation is unavailable (Art. 6(3), third subparagraph).
- **Disposition:** `DETERMINED`, so `--strict` exits 0.
- **Duties:** as provider, 14 obligations (Art. 9 to 15, 17, 43, 47, 48, 49, 72 and 73) and five documentation items; as deployer, Art. 26 and the Art. 27 FRIA, which Art. 27(1) and (2) require of point 5(c) deployers before first use.
- **Conformity route:** item `high-risk.provider.43.2`, internal control under Art. 43(2) and Annex VI, without a notified body, as for every Annex III point from 2 to 8 unless the system is also an Annex I product (Art. 43(3), last subparagraph).
- **Date and review:** in the JSON report (`--json`), 8 of the 18 graph items carry `"application_date": "2027-12-02"`: the provider's Arts. 16 to 21 and the deployer's Arts. 26 and 27, all in Chapter III, Section 3. Art. 113, third paragraph, point (c)(i), as amended by Regulation (EU) 2026/1744, sets that date for Chapter III, Sections 1 to 3. The other 10 items are the provider's Section 5 items (Arts. 40 to 43, the Art. 43(2) item and Arts. 47 to 49) and its Chapter IX items (Arts. 72 and 73). Point (c) does not defer them, so they carry `"application_date": "2026-08-02"`, the general date in Art. 113, second paragraph, on a literal reading. Each of them says so in a note, gives 2027-12-02 if it is read as following the deferral, and is `review_required`. In all, 13 of the 18 items are `review_required`.

## What a lawyer still has to decide

1. **The Annex III characterisation.** Point 5(c) covers natural persons in life and health insurance only. Term life fits; a non-life line such as motor or property insurance does not. The engine takes `annex_iii_area` as given.
2. **Profiling.** The profile sets `performs_profiling` to `true`. The AI Act uses the GDPR definition of profiling (Art. 3(52) AIA, Art. 4(4) GDPR). If the lawyer confirms it, no Art. 6(3) derogation is open.
3. **The roles.** Building the model and putting it into service for its own use makes the insurer the provider (Art. 3(3) and (11)) as well as the deployer. A licensed vendor model would change that analysis (Art. 25).
4. **The internal-control file.** The engine names the route; the Annex VI assessment, the EU declaration of conformity (Art. 47), CE marking (Art. 48) and registration before putting into service (Art. 49(1)) remain the provider's work and the lawyer's review.
5. **The FRIA.** The lawyer settles its content under Art. 27(1), the notification to the market surveillance authority (Art. 27(3)) and any cross-references to the GDPR data protection impact assessment (Art. 27(4)).
6. **Financial-institution rules the engine does not encode.** Whether the insurer is a financial institution subject to internal-governance requirements under Union financial services law decides whether its quality management system is deemed fulfilled through those rules, except Art. 17(1)(g) to (i) (Art. 17(4)); whether documentation and logs are kept within the financial-services documentation (Arts. 18(3), 19(2) and 26(6), second subparagraph); whether deployer monitoring is deemed fulfilled (Art. 26(5), second subparagraph); and whether post-market monitoring can be integrated into the systems kept under financial-services law (Art. 72(4), second subparagraph). Art. 26(11) and Art. 86 (information and explanation for affected persons) and Art. 74(6) and (7) (which authority supervises) also need an answer. None of this appears in the output.
7. **Other law.** Health questionnaire answers are data concerning health under Art. 9 GDPR. Data protection, insurance supervisory and anti-discrimination law are outside the classifier.

## Boundaries

The profile and the insurer are synthetic. This page is not legal advice. Drafted with AI assistance (Claude); sources verified and conclusions adopted by the author on [date]. The AI Act provisions named above were checked on 14 October 2026 against the consolidated version of Regulation (EU) 2024/1689 dated 27 July 2026, in the [legalize-dev/legalize-eu](https://github.com/legalize-dev/legalize-eu) GitHub mirror of EUR-Lex/CELLAR (`eu/e0/32024R1689.md`, mirror commit `3709ccf`); EUR-Lex itself was unreachable. The Art. 113 dating of the Section 5 and Chapter IX items follows the repository's literal reading, which was checked on EUR-Lex on 18 October 2026 (see [Application Dates](../methodology.md#application-dates) and the [regulatory claim ledger](../REGULATORY_CLAIM_LEDGER.md)). The GDPR references (Art. 4(4) and Art. 9 GDPR) were checked against Regulation (EU) 2016/679 in the same mirror and commit (`eu/6e/32016R0679.md`). Recheck on EUR-Lex before relying on them. The quoted output is the CLI's own; `tests/test_docs.py` fails if it drifts from what the CLI prints.
