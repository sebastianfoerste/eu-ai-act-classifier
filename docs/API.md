# API Contracts

The Python classifier is the source of truth. The local API bridge and optional
web cockpit only expose deterministic projections for review.

Legora-inspired product pattern, no Legora integration or dependency.

## Local Commands

```bash
eu-ai-act-local-api schema
eu-ai-act-local-api inventory
echo '{"profile":{"name":"CreditSightScore"}}' | eu-ai-act-local-api classify
echo '{"profile":{"name":"CreditSightScore"}}' | eu-ai-act-local-api dossier
```

## Inventory

`eu-ai-act-local-api inventory` and `GET /api/inventory` return
`eu-ai-act-classifier.system-inventory.v1`.

Important nested contracts:

1. `eu-ai-act-classifier.system-review-table.v1`
2. `eu-ai-act-classifier.review-control-profile.v1`
3. `eu-ai-act-classifier.system-review-table-scale.v1`
4. `eu-ai-act-classifier.system-prompt-brief.v1`
5. `eu-ai-act-classifier.system-aos-review.v1`

The aOS review profile exposes:

1. `aosLayers`
2. `agentPlan`
3. `skills`
4. `tabularReview`
5. `trustedSources`
6. `editorDraft`
7. `wordExportPackage`
8. `portalRoom`
9. `monitors`
10. `lists`
11. `securityGovernance`
12. `externalActionAllowed`

`externalActionAllowed` is always `false`. Regulator, customer, deployment and
public-facing outputs remain draft-only until qualified human review is
recorded.

## Review Boundary

The system review table may restate classifier output, source status and draft
artifact references. It must not add article-level conclusions beyond the
existing deterministic classifier result.

Review rows expose `cellStatus` for the factor-level review state. Pinpoint
citations expose source id, citation label, URL, verification flag, legal status
class, source class, quote snippet and optional offsets when the source
manifest supports them.
