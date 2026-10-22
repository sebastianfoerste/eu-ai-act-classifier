# 0002 Labels and i18n

Status: Accepted for English; German proposed

## Context

The cockpit formatted values mechanically ("III.5.b" became "III 5 B") and the playground field guide derived labels from enum names ("Biometrics remote id"). `catalog.py` already holds the titles the engine cites.

## Decision

`src/eu_ai_act_classifier/labels.py` is the one label catalog. Annex III and Art. 5 labels combine the catalog's pinpoint with its title, so a label never introduces a citation the engine does not already carry. The build writes the labels into `docs/playground/fields.json` and `web/lib/labels.json`; tests fail if either drifts.

German is added as a second locale in the same catalog only after each legal term has a `PENDING` row in the claim ledger and a lawyer confirms it against the German text of Regulation (EU) 2024/1689.

## Consequences

- One place to correct a label for every surface.
- Workflow values the classifier does not define (inventory statuses) still use the generic formatter.
- No German text ships until it is reviewed.
