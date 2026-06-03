# Example systems (eval set)

Each file is a `SystemProfile`. They double as the test fixtures in
`tests/test_examples.py`: the expected classification below is asserted on every
run, so a rule change that moves any of these is caught immediately.

| Profile | Expected tier | Disposition | Why |
| --- | --- | --- | --- |
| `social_scoring.json` | Prohibited | determined | Social scoring — Art. 5(1)(c) AIA |
| `emotion_hiring.json` | Prohibited | determined | Emotion recognition in hiring — Art. 5(1)(f) AIA |
| `cv_screening.json` | High-risk | determined | Recruitment — Annex III(4)(a) AIA |
| `credit_scoring.json` | High-risk | determined | Credit scoring — Annex III(5)(b) AIA |
| `proctoring_education.json` | High-risk | determined | Exam proctoring — Annex III(3)(d) AIA |
| `credit_scoring_deployer.json` | High-risk | determined | Deployer of Annex III(5)(b); FRIA required — Art. 27 AIA |
| `law_enforcement.json` | High-risk | determined | Reoffending risk — Annex III(6)(d) AIA |
| `ambiguous_use_case.json` | High-risk | requires_review | Annex III area implicated, point unsettled — flagged `noch zu verifizieren` |
| `employment_derogation.json` | High-risk | requires_review | Art. 6(3) derogation asserted — needs documented assessment |
| `support_chatbot.json` | Limited risk | determined | Chatbot disclosure — Art. 50(1) AIA |
| `deepfake_generator.json` | Limited risk | determined | Deepfake disclosure — Art. 50(4) AIA |
| `spam_filter.json` | Minimal risk | determined | No regulated use case |
| `foundation_model_systemic.json` | Minimal risk* | determined | GPAI with systemic risk — Art. 51, 53, 55 AIA |
| `foundation_model_unknown_compute.json` | Minimal risk* | requires_review | GPAI; compute undisclosed, systemic status open — Art. 51 AIA |

\* System-level tier. A general-purpose model carries Chapter V obligations
regardless of the downstream system's tier.

Run one:

```bash
eu-ai-act-classify examples/cv_screening.json
eu-ai-act-classify examples/foundation_model_systemic.json --json
```
