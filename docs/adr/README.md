# Architecture decision records

Each record states a decision, its context and its consequences. Status is Accepted for decisions implemented in the code and Proposed for those only specified.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-guided-intake-source-of-truth.md) | Guided intake questions come from one Python definition | Accepted |
| [0002](0002-labels-and-i18n.md) | One generated label catalog; English first, German after review | Accepted (EN) |
| [0003](0003-export-route.md) | Print stylesheet PDF, DOCX only as an optional extra | Proposed |
| [0004](0004-cockpit-styling-without-tailwind.md) | Cockpit pages use plain CSS classes, not Tailwind | Accepted |
| [0005](0005-url-state-encoding.md) | Share links encode the profile in the URL hash with native compression | Proposed |
| [0006](0006-evidence-model.md) | Evidence state lives in the cockpit workspace, not in the report | Proposed |
| [0007](0007-systemprofile-change-proposals.md) | SystemProfile changes that would let fewer intake runs block | Proposed |
