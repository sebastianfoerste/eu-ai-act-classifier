# Reviewer Notes

The classifier is intentionally conservative. It screens AI-system profiles,
surfaces obligations and routes open questions to a qualified reviewer.

It does not replace legal judgment, conformity assessment work or
organisation-specific advice.

## Review Triggers

### Scope

If AI-system status, EU nexus, intended purpose or excluded-use flags are
incomplete, the classifier records a scope review question.

### Systems Already On The Market

The transitional status compares the placing-on-market and putting-into-service
dates with the system's Chapter III date (Art. 111(2) AIA). A high-risk system
that predates it gets a `review_required` Art. 111(2) item for each operator
role, a note on every high-risk item and an open question: confirm whether its
design has changed significantly (`significant_change_after_application_date`).
Until that is answered the disposition is `requires_review` and `--strict`
fails. Providers and deployers of a system intended to be used by public
authorities plan for 2 August 2030 in any case.

Art. 111(2) uses the Chapter III date both as the date the system must precede
and as the date from which a significant change counts. Which date is meant is
contested, so every legacy result and every Art. 111(2) check without a date
says "Literal reading, confirm with counsel", and the flagged items stay
`review_required` after the question is answered.

### Public-Authority Deployers

Art. 49(3) AIA turns on whether the deployer is, or acts on behalf of, a public
authority or Union institution, body, office or agency
(`deployer_public_authority`). Where that is unset, the registration
item is inferred for review if the system is intended to be used by public
authorities or its Annex III point is 5(a), 6 or 7. Point 8(a) and a
`deployer_public_law_body: true` answer raise the question without the item. Point 2
is excepted: a public-authority deployer there gets an Art. 49(5) pointer to
national registration.

### Annex I, Section B Products

Art. 2(2) AIA lists neither Art. 5 nor Art. 50 for a Section B product. The
report keeps both as the conservative reading, and a Section B product also in
an Annex III area keeps the Annex III duties. Each kept position is flagged
"Literal reading, confirm with counsel" for the reviewer to confirm: Art. 5 on
its finding and an open question, Art. 50 on its finding and items, and the
Annex III duties on the Art. 6(1) finding and the Art. 2(2) item.

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

Where a GPAI profile gives the AI system's `placing_on_market_date` but not the
model's own `gpai_model_placing_on_market_date`, the model is dated by the
system's date for Art. 111(3) AIA, and its items go to review with an open
question until the model's date is given.

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
