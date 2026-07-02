# Deterministic Classification Versus Legal Advice

This repository is a deterministic screening tool. It is not a legal-advice
engine.

## What the classifier does

The classifier receives a structured `SystemProfile` and applies coded gates:
scope, prohibited practices, Annex I and Annex III high-risk routes, GPAI model
facts and Art. 50 transparency duties.

It returns a `ClassificationReport` with:

- risk tier and disposition;
- pinpoint citations;
- source status for binding, provisional and nonbinding material;
- obligations and draft evidence artifacts;
- open questions where the facts need human review.

## What the classifier does not do

It does not decide contested facts, give a legal opinion, perform a conformity
assessment, replace counsel or predict an authority decision.

For example, the code can apply Annex III once the intended purpose is
characterised. It cannot determine from an incomplete product narrative whether
the intended purpose is employment selection, creditworthiness, law enforcement or a
general analytics use.

## Source discipline

Binding logic is based on Regulation (EU) 2024/1689. Provisional dates are
shown separately. Nonbinding Commission guidance and service-desk material are
advisory overlays only and do not override the Level 1 rule path.

## Review gate

Use `requires_review`, `open_questions`, `unverified_citations` and draft
artifact notices as the handoff to a qualified reviewer. Public demos must use
synthetic profiles only.
