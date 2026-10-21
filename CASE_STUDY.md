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
Every tier and obligation is cited to a specific Article or Annex point. The output marks itself **NEEDS LEGAL REVIEW** and flags the genuine judgment calls (e.g. whether the human reviewer's "final decision" is real Art. 14 oversight or a rubber stamp) rather than asserting a clean answer.

## Evaluation
The bundled run (`examples/classification-packet.md`) classifies a synthetic credit-scoring system as **HIGH-RISK** under Annex III 5(b), lists the Art. 9-15, 17, 43, 47-49, 72 and 73 obligations, and marks the Art. 40-44, 47-49, 72 and 73 graph items as applying from 2026-08-02 on a literal reading, confirm with counsel, or from 2027-12-02 if they follow the Sections 1 to 3 deferral.

## Limitations
A first-pass classifier over a structured description; it does not read product documentation, does not resolve the flagged judgment calls, and the Annex/Article mapping is illustrative and must be confirmed against the current text and guidance.

## Guided intake and competitive research
A research pass across 39 other classifiers and governance tools and 19 design pattern sources ([docs/research/](docs/research/adaptation-plan.md)) found that wizards often keep a separate question tree per surface and map "I don't know" to "no" or to a lower tier. The playground now opens on guided questions defined once in Python: unknown facts route the result to review or pause the run for counsel, and tests check, over a grid of earlier answers, that no answer to a skipped question changes the result. Labels for Annex III points and Art. 5 practices come from one catalog, and the cockpit's portfolio and self-assessment pages are styled.

## Next steps
Add a conformity-assessment checklist for confirmed high-risk systems; link obligations to evidence/templates; track the system through to a documented governance decision.
