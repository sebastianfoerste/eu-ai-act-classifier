# Case Study: EU AI Act Classifier

## Legal problem

EU AI Act analysis requires classification of AI systems, identification of risk tiers, mapping of obligations and careful documentation of assumptions.

In practice, early classification work can become unclear when the reasoning, source basis and review status are not visible.

## Product problem

A regulatory workflow tool should not merely produce an answer. It should create a review packet that separates classification, obligations, timelines, sources, assumptions and review status.

The product challenge is to support first pass analysis while making clear that final legal assessment remains subject to human review.

## Workflow design

The classifier models a deterministic first pass review workflow:

1. Capture facts about the AI system
2. Identify potentially relevant risk tiers
3. Map obligations and timelines
4. Attach source references
5. Flag assumptions and gaps
6. Produce a reviewable output packet

## AI risk addressed

The project addresses:

1. Overconfident classification
2. Hidden assumptions
3. Unsupported regulatory conclusions
4. Confusion between first pass analysis and legal advice
5. Missing review status
6. Poor traceability between facts, sources and obligations

## Human review model

The output is designed as a review packet, not legal advice.

A human lawyer or compliance reviewer remains responsible for final interpretation, classification and advice.

## Evaluation or quality control

The project uses deterministic logic, structured outputs, source references and tests to keep the classification workflow auditable and predictable.

The quality focus is traceability, not autonomous legal judgment.

## What I would improve next

1. Add richer source references by obligation
2. Add more synthetic AI system scenarios
3. Add a web based review view
4. Add a gap analysis export
5. Add versioned regulatory source tracking
6. Add comparison tests for borderline classification cases

## Relevance for Legal Engineer / Product Specialist roles

This project demonstrates how legal classification can be translated into a structured, source aware product workflow.

It is relevant for roles involving regulated AI, product counsel workflows, compliance tooling, explainability, review states and professional services AI.
