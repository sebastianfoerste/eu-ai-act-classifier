# Reviewer Notes

This classifier is intentionally conservative. It is designed to screen AI-system profiles, surface obligations and route open questions to a qualified reviewer. It does not replace legal judgment, conformity assessment work or organisation-specific advice.

## Cases where the classifier should refuse to be overconfident

### 1. Article 6(3) derogation claims

If a system is in an Annex III area but the user asserts that it does not pose a significant risk, the classifier should flag the claim for review. Whether the derogation is available turns on product facts, actual use, safeguards and documentation that a static profile cannot settle alone.

### 2. Profiling carve-out

Where profiling is involved, the classifier should not silently apply a lower-risk path. The profiling carve-out can close off the Article 6(3) route and should be reviewed explicitly.

### 3. GPAI systemic-risk threshold

If training compute, model capability, provider role or downstream integration facts are incomplete, the classifier should return an open question rather than infer whether the systemic-risk presumption applies.

### 4. Deployer obligations and FRIA

Some obligations depend on whether the organisation is a provider, deployer, importer, distributor, public body or other relevant actor. Where that role is unclear, the classifier should route the matter for legal review.

### 5. Mixed product surfaces

AI products often combine several features, such as search, summarisation, scoring, recommendations and workflow automation. The classifier should treat the highest-risk relevant feature as the review driver and disclose the basis for that routing.

## Practical review rule

A green or minimal-risk classification is only useful if the input facts are complete and stable. If the product, user group, data category, deployment context or customer sector changes, the classification should be rerun and reviewed.

## Data boundary

Examples in this repository are synthetic and public-safe. They should not be replaced with client data, privileged material, confidential information or personal data.
