# Case study — eu-ai-act-classifier

> EU AI Act classification should be cited and reviewable, with the judgment calls flagged — not a confident one-word answer. Synthetic data only; not legal advice.

## Problem
"Is our AI system high-risk under the EU AI Act?" is asked constantly and answered badly — either with hand-waving or with an over-confident label that hides the parts that actually carry exposure (is the human oversight real? is a fundamental-rights assessment owed?). Teams need a structured first pass that is honest about what needs a lawyer.

## Users
A GC, AI governance lead, or product counsel doing a first-pass classification of an AI system before deeper legal review.

## Workflow
1. A structured `SystemProfile` is provided: name, description, purpose, sector and operator roles, plus optional facts such as the Annex III area, Art. 5 practices, Art. 6(3) derogation facts, GPAI status and Art. 50 transparency features.
2. The classifier runs a prohibited-practice screen (Art. 5) and a risk-tier assessment (Annex III).
3. It outputs the **risk tier**, the **obligations triggered** (each cited to an Article), an indicative **timeline**, and an explicit **review status**.

## Controls
Every tier and obligation is cited to a specific Article or Annex point, and every report states a disposition. The disposition is `DETERMINED` unless a rule raises an open question. Then it is `REQUIRES_REVIEW`: the report prints `This classification requires lawyer review before it is relied upon.`, lists the questions under `Open questions for review:`, and `--strict` exits 1. Three of the 17 bundled examples take that path: `ambiguous_use_case.json`, `employment_derogation.json` and `foundation_model_unknown_compute.json`.

The obligation graph also gives each item its own review status, `review: determined` or `review: review_required`.

The engine does not test whether human oversight works in practice. Art. 14 appears as a provider design obligation, `Art. 14 AIA: Human oversight. Design the system for effective oversight by natural persons.` Whether a reviewer's final decision is real oversight or a rubber stamp is not flagged in the output; it is left to the reviewing lawyer.

## Evaluation
The bundled CV-screening example is `examples/cv_screening.json` (TalentRank CV Screener, provider role). The first lines of `uv run eu-ai-act-classify examples/cv_screening.json` are:

```text
EU AI Act classification: TalentRank CV Screener
Risk tier: HIGH-RISK (Art. 6 AIA)
Disposition: DETERMINED
Scope status: in_scope
Roles: provider

Scope and intake:
  AI system: True
  EU nexus: True
  Transitional status: No transitional limitation identified from the submitted facts.

Findings:
  [high] Annex III(4)(a) AIA: High-risk: Employment selection and worker management
      Annex III high-risk area (Art. 6(2) AIA); no derogation asserted.
```

The report then lists 14 provider obligations (Art. 9 to 15, 17, 43, 47, 48, 49, 72 and 73 AIA) and five documentation items. It raises no open questions, so it has no `Open questions for review:` block, and `--strict` exits 0. Its obligation graph marks 9 of 16 items `review: review_required` (Art. 20, 21, 40 to 44, 49 and 73 AIA). No deployer obligations, such as Art. 26 AIA, are listed because the profile names only the provider role.

The committed sample packet, `examples/classification-packet.md`, is a different system: CreditSightScore, classified high-risk under Annex III(5)(b). The expected tier and disposition of all 17 bundled examples are asserted in `tests/test_examples.py`.

## Limitations
A first-pass classifier over a structured description. It does not read product documentation and does not resolve the open questions it raises. It encodes Regulation (EU) 2026/1744 only in part; see the [claim ledger](docs/REGULATORY_CLAIM_LEDGER.md). The Annex/Article mapping is illustrative and must be confirmed against the current text and guidance.

## Next steps
Add a conformity-assessment checklist for confirmed high-risk systems; link obligations to evidence/templates; track the system through to a documented governance decision.
