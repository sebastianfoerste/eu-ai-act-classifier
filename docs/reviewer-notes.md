# Reviewer Notes

The classifier is intentionally conservative. It screens AI-system profiles,
surfaces obligations and routes open questions to a qualified reviewer.

It does not replace legal judgment, conformity assessment work or
organisation-specific advice.

## Review Triggers

### Scope

If AI-system status, EU nexus, intended purpose, excluded-use flags or Article
111 transition facts are incomplete, the classifier records a scope review
question.

### Article 6(3) Derogation Claims

If a system is in an Annex III area and the user asserts that it does not pose a
significant risk, the classifier keeps the tier high-risk and flags the claim
for review. The Art. 6(4) work product can then document the assessment.

### Profiling

Where profiling of natural persons is involved, the classifier should not apply
the Art. 6(3) path. The profiling carve-out closes that route.

### GPAI Systemic Risk

If training compute, provider role or Commission designation facts are
incomplete, the classifier returns an open question rather than inferring
systemic-risk status.

### FRIA

Creditworthiness and life and health insurance deployer cases receive an
automatic Art. 27 FRIA obligation.

Critical infrastructure deployer cases do not receive the generic FRIA review
question because Annex III point 2 is excluded from the Art. 27 trigger.

For other high-risk deployer cases, review public-law body status and private
public-service status.

### Mixed Product Surfaces

AI products often combine search, summarisation, scoring, recommendations and
workflow automation. The classifier should route the highest-risk relevant
feature and disclose the basis.

## Practical Review Rule

A minimal-risk or determined classification is only useful if the input facts
are complete and stable. If the product, user group, data category, deployment
context or customer sector changes, rerun and review the classification.

## Data Boundary

Examples in this repository are synthetic and public-safe. Do not replace them
with client data, privileged material, confidential information or personal data.
