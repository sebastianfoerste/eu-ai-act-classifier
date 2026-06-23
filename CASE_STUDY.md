# Case study — eu-ai-act-classifier

> EU AI Act classification should be cited and reviewable, with the judgment calls flagged — not a confident one-word answer. Synthetic data only; not legal advice.

## Problem
"Is our AI system high-risk under the EU AI Act?" is asked constantly and answered badly — either with hand-waving or with an over-confident label that hides the parts that actually carry exposure (is the human oversight real? is a fundamental-rights assessment owed?). Teams need a structured first pass that is honest about what needs a lawyer.

## Users
A GC, AI governance lead, or product counsel doing a first-pass classification of an AI system before deeper legal review.

## Workflow
1. A structured description of the system is provided (purpose, deployment, users, autonomy, biometric/emotion features).
2. The classifier runs a prohibited-practice screen (Art. 5) and a risk-tier assessment (Annex III).
3. It outputs the **risk tier**, the **obligations triggered** (each cited to an Article), an indicative **timeline**, and an explicit **review status**.

## Controls
Every tier and obligation is cited to a specific Article or Annex point. The output marks itself **NEEDS LEGAL REVIEW** and flags the genuine judgment calls (e.g. whether the recruiter's "final decision" is real Art. 14 oversight or a rubber stamp) rather than asserting a clean answer.

## Evaluation
The bundled run (`examples/classification-packet.md`) classifies a synthetic CV-screening system as **HIGH-RISK** under Annex III 4(a), lists the Art. 9–15, 26, 27, 49 obligations, and flags two open questions for a lawyer.

## Limitations
A first-pass classifier over a structured description; it does not read product documentation, does not resolve the flagged judgment calls, and the Annex/Article mapping is illustrative and must be confirmed against the current text and guidance.

## Next steps
Add a conformity-assessment checklist for confirmed high-risk systems; link obligations to evidence/templates; track the system through to a documented governance decision.
