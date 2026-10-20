# Design teardown

Interface patterns from eight products, then a comparison per surface of this project. Sources, commits and evidence tags as in the [landscape](2026-10-competitive-landscape.md); access date 2026-10-20. No vendor site loaded (network-limited run), so the open-source sections rest on code read at a pinned commit and the Commission checker section on snippets only. Patterns are adapted, never copied.

Baseline captures and axe results for this project are listed in the [adaptation plan](adaptation-plan.md#baseline).

## Top eight

### 1. European Commission AI Act Compliance Checker (Claimed)

- **Flow.** Role first, then system questions; the AI Act Explorer is bundled alongside (snippets of the Service Desk and a ZwillGen review).
- **Uncertainty.** Reviewers note little help when a definition is ambiguous and reliance on a self-identified role (Claimed).
- **Language.** English only (Claimed).
- **Adopt:** role-first entry and links from each question to the article. **Reject:** nothing specific; not enough was visible to judge.
- `guidance_eval.py` stores three earlier checker results as nonbinding evidence; no new runs could be stored.

### 2. AbdelStark eu-ai-act-toolkit (Observed, `@fff58f6`)

- **Flow.** 26 boolean questions in five steps from `data/questions.json`; the web wizard advances linearly with no early exit (`ClassifierWizard.tsx`). The CLI asks 15 prompts for a credit-scoring system and stops after 1 for social scoring (`classify.ts`).
- **Question anatomy.** Yes and No only; booleans default to false.
- **Results.** Tier plus per-tier checklist; a 0 to 100 score from checklist progress (`scoring.ts`).
- **Export.** Markdown with `[TODO` placeholders; no draft label.
- **Adopt:** one data file for questions. **Reject:** separate CLI prompts, unknown as no, checklist score.

### 3. Hiepler EuConform (Observed, `@011a5ad`)

- **Flow.** Intro, role choice, eight Annex III questions with Yes, No and Unsure, then a bias-test step (`useComplianceWizard.ts`). Art. 5 questions exist in core but are not referenced by the web flow (grep, Observed absence).
- **Uncertainty.** Unsure lowers the result to `limited` when nothing is yes (`risk-classifier.ts`).
- **Shell.** Dark mode toggle; EN and DE dictionaries; PDF with a no-legal-advice block.
- **Adopt:** EN/DE dictionaries, dark mode. **Reject:** unsure mapped to a tier.

### 4. DanielHuette ai-act-compliance-helper (Observed, `@88e9710`)

- **Flow.** Preliminaries, Annex I gate, area, the area's legal questions, then Art. 6(3) with the profiling counter-exception. The web flow is exported from YAML rules and parity-checked against Python (`scripts/export_question_flow.py`, `check_parity.py`).
- **Question anatomy.** Yes, No, "I don't know" on every question; unknown keeps the provision open (`question_flow.py`).
- **Shell.** Static page, no server, dark mode via `prefers-color-scheme`, DE and EN.
- **Adopt:** generated web flow with a parity check, three-answer questions, published benchmark. **Reject:** counting an unresolved conditional as agreement.

### 5. Lexbeam eu-ai-act-mcp (Observed, `@efcbae2`)

- **Surface.** MCP tools only; the calling agent supplies structured signals.
- **Uncertainty.** `insufficient_information`, `undetermined` and `missing_facts` (`assess-system.ts`).
- **Provenance.** Hashed law manifest, sealed corpus, per-finding provenance with operative date and source status.
- **Adopt:** a content hash for `--verify-sources` (parked, see the plan). **Reject:** trusting a caller-supplied domain without a human confirming it.

### 6. legalithm (Observed, `@38d46d7`)

- **Results.** Citations with `asOf` and `appliesFrom`; `matchedRules`; a fixed confidence per decision path with `reviewRequired` below 0.6 (`engine.ts`).
- **Developer surfaces.** CLI, MCP, GitHub Action, compliance record with drift detection. Telemetry on by default (`telemetry.ts`).
- **Adopt:** date on every citation (already in the obligation graph). **Reject:** keyword matching, numeric confidence, default-on telemetry.

### 7. Attestor (Observed, `@cc70eec`)

- **Flow.** Role, Annex III area and flags; versioned rule bundles per law version.
- **Trust.** Canonical-JSON hash per bundle, signed ledger, optional timestamps; a persistent honesty banner (`HonestyBanner.tsx`).
- **Export.** Annex IV PDF with fill-in placeholders, no draft label.
- **Adopt:** a banner that stays on every view. **Reject:** optional fields that behave as no.

### 8. OpenComplAI (Observed, `@ed65bc9`; AGPL-3.0, pattern only)

- **Evidence model.** Control state, owner, evidence references, TTL, waivers; staleness on manifest change; human-attached evidence cannot be downgraded by heuristics.
- **Placeholders.** A literal fill-in marker makes a scaffold non-content-bearing.
- **Adopt (pattern):** state, owner and freshness per obligation graph item (spec H6). **Reject:** any code reuse (licence).

## Comparison per surface

### Playground input

| Aspect | Peers | This project before | After this change |
|---|---|---|---|
| Entry | Quiz or form (AbdelStark, EuConform, DanielHuette) | JSON textarea plus 17 examples | Guided questions by default, JSON as a second mode |
| Example picker | Rare | Grouped `<select>` | Unchanged; in guided mode an example opens on the check-answers page |
| Validation | Mostly client-side forms | Pydantic errors by field, no input echo | Unchanged for JSON; guided pages validate dates and numbers before Continue |

### Guided intake

| Aspect | Peers | Before | After |
|---|---|---|---|
| Source of questions | Separate per surface (AbdelStark), generated with parity check (DanielHuette) | Cockpit toggles and `/self-assessment` text fields, neither mapped to `SystemProfile` | `intake.py` generates `intake.json`; browser interprets; fixtures hold it to Python |
| Unknown | No, lower tier, open, or threshold | Cockpit `TriStateControl` writes null for nullable fields | Per question: null routed to review, `III.unsure`, or block for counsel; never false |
| Skip rules | Linear (AbdelStark), early exit (CLI) | n/a | Declarative conditions, each proven not to change the report over a grid |
| Check answers | GOV.UK pattern | n/a | Change links, blocked and missing answers marked, every defaulted value listed |

Wireframe, 1280 px (input panel, left column of the existing two-panel layout):

```text
+--------------------------------------------+
| INPUT  System profile               GUIDED |
| Start with a synthetic example [v] [Load]  |
| [ Guided questions ][ JSON editor ]        |
|--------------------------------------------|
| Question 9 of 15                      Back |
| Is the system intended for a use listed    |
| in Annex III?                               |
| Art. 6(2) and Annex III AIA                 |
| Choose the point that applies...            |
| ( ) Annex III(1)(a): Remote biometric ...   |
| (o) Annex III(5)(b): Creditworthiness ...   |
| ( ) None of these                           |
| or                                          |
| ( ) I don't know                            |
| I don't know is recorded and routed to      |
| review.                                     |
| [Continue]                                  |
+--------------------------------------------+
```

Wireframe, 375 px (single column, results below):

```text
+-----------------------------+
| Question 9 of 15       Back |
| Is the system intended for  |
| a use listed in Annex III?  |
| Art. 6(2) and Annex III AIA |
| [ ] option rows, full width |
| or                          |
| [ ] I don't know            |
| [Continue]                  |
+-----------------------------+
| OUTPUT  Classification      |
+-----------------------------+
```

### Results

Unchanged in this change. Peers show a tier word plus checklist (AbdelStark), a score (AbdelStark, EuConform, Aguardic Claimed), or a confidence number (legalithm). This project keeps the tier card with its basis, the disposition badge, four metric tiles and cited sections; no score is added (anti-pattern, see the plan). Follow-ups specified in the plan: an application-date timeline with contested-reading markers, and binding result visibly apart from the advisory overlay.

### Cockpit

| Page | Before | After |
|---|---|---|
| `/` | Styled; labels such as "III 5 B" | Labels from the shared catalog ("Annex III(5)(b): Creditworthiness ...") |
| `/workspace` | Tailwind classes without Tailwind: unstyled | Plain classes on cockpit tokens; scrollable table region; 375 px without page overflow |
| `/self-assessment` | Unstyled; 4 inputs without labels | Styled; each input has a label and hint |

### Exports

No inspected peer keeps a draft status on exported documents. This project's seven artifacts and dossier already carry `DRAFT_NOTICE`. The DOCX/PDF route is specified (H3) and not built; the print-stylesheet route must put the banner in the page flow because running page headers work only in Chrome 131+ (MDN browser-compat-data, Observed).

### Tokens

| Token | Playground | Cockpit |
|---|---|---|
| Ink / text | `#172b35` | `#17202a` |
| Accent / links | `#2c4f7c` (also used for the limited tier) | `#1f5eff` |
| Background | `#f4f5f2` | `#f6f7f8` |
| Muted | `#5d6a70` | `#64717f`; new `--muted-on-tint #525e6b` for text on tinted surfaces (4.47:1 was below AA) |
| Type | Georgia headings, system sans | Inter stack |
| Theme | light only | light only |

### CLI and MCP developer experience

Unchanged. `--strict` exits 1 for prohibited or review results; Pydantic errors name fields; MCP tools `classify_ai_system` and `classify_ai_system_text`. Peers add a GitHub Action and SARIF (Systima, legalithm); parked as a follow-up.

### Accessibility and i18n

All new wizard pages pass axe with WCAG 2.2 AA tags at 1280 and 375 px; the only finding is the pre-existing `label-content-name-mismatch` on the brand link. Focus moves to the question heading on each page and to the error summary on a validation error. `lang="en"` throughout; German labels wait for review of their terms (H2).
