# Example Systems

Each file is a `SystemProfile`. The 17 base examples double as fixtures in
`tests/test_examples.py`; expected classification is asserted on every run.

## Base Eval Set

`social_scoring.json`: Prohibited, determined. Social scoring under Art.
5(1)(c) AIA.

`emotion_hiring.json`: Prohibited, determined. Emotion recognition in hiring
under Art. 5(1)(f) AIA.

`cv_screening.json`: High-risk, determined. Recruitment under Annex III(4)(a)
AIA.

`credit_scoring.json`: High-risk, determined. Credit scoring under Annex
III(5)(b) AIA.

`proctoring_education.json`: High-risk, determined. Exam proctoring under Annex
III(3)(d) AIA.

`credit_scoring_deployer.json`: High-risk, determined. Deployer of Annex
III(5)(b); FRIA required under Art. 27 AIA.

`law_enforcement.json`: High-risk, determined. Reoffending risk under Annex
III(6)(d) AIA.

`ambiguous_use_case.json`: High-risk, requires_review. Annex III area
implicated, point unsettled and flagged `noch zu verifizieren`.

`employment_derogation.json`: High-risk, requires_review. Art. 6(3) derogation
asserted and documentation needed.

`support_chatbot.json`: Limited risk, determined. Chatbot disclosure under Art.
50(1) AIA.

`deepfake_generator.json`: Limited risk, determined. Deepfake disclosure under
Art. 50(4) AIA.

`spam_filter.json`: Minimal risk, determined. No regulated use case.

`foundation_model_systemic.json`: Minimal system-level risk, determined. GPAI
with systemic risk under Arts. 51, 53 and 55 AIA.

`foundation_model_unknown_compute.json`: Minimal system-level risk,
requires_review. GPAI compute undisclosed, systemic status open under Art. 51
AIA.

`gpai_non_systemic.json`: Minimal system-level risk, determined. GPAI model without systemic risk under Art. 53 AIA.

`gpai_systemic_by_flops.json`: Minimal system-level risk, determined. GPAI model with systemic risk based on FLOPs threshold under Art. 51(2) AIA.

`gpai_systemic_designated.json`: Minimal system-level risk, determined. GPAI model with systemic risk by Commission designation under Art. 51(1)(b) AIA.

## Guidance Corpus

`guidance/commission_guidance_examples.json` stores Commission-derived guidance
examples with source URL, source status, retrieval date, authority status and
expected classifier result.

`guidance/compliance_checker_comparison.json` stores beta Compliance Checker
comparisons as nonbinding evidence with manual-review notes.

## Run Examples

```bash
eu-ai-act-classify examples/cv_screening.json
eu-ai-act-classify examples/foundation_model_systemic.json --json
python -m eu_ai_act_classifier.guidance_eval
```
