# Design teardown

Interface patterns from eight products, then a comparison per surface of this project with wireframes at 1280 and 375 px. Access date 2026-10-20. Every claim carries its own tag: **Observed** (code or docs read at the commit named in the section heading, or measured), **Claimed** (README, marketing copy or search snippet), **Inferred** (reasoning). No vendor site loaded (network-limited run; see the [landscape](2026-10-competitive-landscape.md)). Patterns are adapted, never copied.

Baseline captures and axe results for this project are listed in the [adaptation plan](adaptation-plan.md#baseline).

## Top eight

### 1. European Commission AI Act Compliance Checker (not loaded)

Source: search snippets and a review at https://www.zwillgen.com/artificial-intelligence/the-eus-ai-act-compliance-checker-explorer-whats-useful-today-whats-still-come/.

- **Flow.** Role first, then system questions, with the AI Act Explorer alongside (Claimed).
- **Uncertainty.** Reviewers note little help when a definition is ambiguous and reliance on a self-identified role (Claimed).
- **Language.** English only (Claimed).
- **Adopt:** role-first entry and links from each question to the article (Inferred from the above). **Reject:** nothing specific; not enough was visible to judge.
- `guidance_eval.py` stores three earlier checker results as nonbinding evidence; no new runs could be stored (Observed in this repository).

### 2. AbdelStark eu-ai-act-toolkit (code read at `@fff58f6`)

- **Flow.** 26 boolean questions in five steps from `data/questions.json`; the web wizard advances linearly with no early exit (`ClassifierWizard.tsx`) (Observed). The CLI asks 15 prompts for a credit-scoring system and stops after 1 for social scoring (`classify.ts`) (Observed in code, not executed).
- **Question anatomy.** Yes and No only; booleans default to false (Observed).
- **Results.** Tier plus per-tier checklist; a 0 to 100 score from checklist progress (`scoring.ts`) (Observed).
- **Export.** Markdown with `[TODO` placeholders; no draft label (Observed in `renderer.ts`, `ExportButton.tsx`).
- **Adopt:** one data file for questions. **Reject:** separate CLI prompts, unknown as no, checklist score.

### 3. Hiepler EuConform (code read at `@011a5ad`)

- **Flow.** Intro, role choice, eight Annex III questions with Yes, No and Unsure, then a bias-test step (`useComplianceWizard.ts`) (Observed). Art. 5 questions exist in core but nothing under `apps/` references them (grep; Observed absence).
- **Uncertainty.** Unsure lowers the result to `limited` when nothing is yes (`risk-classifier.ts`) (Observed).
- **Shell.** Dark mode toggle (`ThemeToggle.tsx`) and EN and DE dictionaries (Observed); WCAG 2.2 AA conformance (Claimed in README).
- **Export.** PDF with a no-legal-advice block (Observed); no draft watermark seen (Observed absence in the hook).
- **Adopt:** EN/DE dictionaries, dark mode. **Reject:** unsure mapped to a tier.

### 4. DanielHuette ai-act-compliance-helper (code read at `@88e9710`)

- **Flow.** Preliminaries, Annex I gate, area, the area's legal questions, then Art. 6(3) with the profiling counter-exception (Observed in `data/rules/question_flow/*.yaml`). The web flow is exported from the YAML rules (`scripts/export_question_flow.py`, Observed) and parity-checked (`check_parity.py` exists, Observed; "400 of 400" Claimed).
- **Question anatomy.** Yes, No, "I don't know" on every question; unknown keeps the provision open (`question_flow.py`) (Observed).
- **Shell.** Static page with no server, dark mode via `prefers-color-scheme`, DE and EN (Observed in `web/index.html`).
- **Adopt:** generated web flow with a parity check, three-answer questions. **Reject:** counting an unresolved conditional result as agreement (mapping Observed in `showcase.py`; leniency Inferred).

### 5. Lexbeam eu-ai-act-mcp (code read at `@efcbae2`)

- **Surface.** MCP tools only (Observed); a hosted endpoint without key (Claimed in README).
- **Uncertainty.** `insufficient_information`, `undetermined` and `missing_facts` (`classify.ts`, `assess-system.ts`) (Observed).
- **Provenance.** Hashed law manifest and sealed corpus; per-finding provenance with operative date and source status (Observed; hashes recomputed).
- **Input trust.** The README states the classifier trusts a caller-supplied domain signal (Claimed).
- **Adopt:** a content hash for `--verify-sources` (spec S7). **Reject:** acting on caller-supplied signals without a human confirming them.

### 6. legalithm (code read at `@38d46d7`)

- **Results.** Citations with `asOf` and `appliesFrom`; `matchedRules`; a fixed confidence per decision path with `reviewRequired` below 0.6 (`engine.ts`) (Observed).
- **Developer surfaces.** CLI, MCP, GitHub Action (Observed); record service with a free API key (Claimed). Telemetry on by default (`telemetry.ts`) (Observed).
- **Adopt:** a date on every citation (this project's obligation graph already carries one). **Reject:** keyword matching, numeric confidence, default-on telemetry.

### 7. Attestor (code read at `@cc70eec`)

- **Flow.** Role, Annex III area and flags; versioned rule bundles per law version (Observed in `classifier/rules/`).
- **Trust.** Canonical-JSON hash per bundle and a signed ledger (Observed); 27 anchored digests (Claimed in README). A persistent honesty banner (`HonestyBanner.tsx`) (Observed).
- **Export.** Annex IV PDF with fill-in placeholders, no draft label (Observed).
- **Adopt:** a banner that stays on every view. **Reject:** optional fields that behave as no (Observed defaults; effect Inferred).

### 8. OpenComplAI (code read at `@ed65bc9`; AGPL-3.0, pattern only)

- **Evidence model.** Control state, owner, evidence references, TTL and waivers; staleness on manifest change; human-attached evidence not downgraded by heuristics (Observed in `models.py`, `control_freshness.py`, `control_assessment.py`).
- **Placeholders.** A literal fill-in marker makes a scaffold non-content-bearing (Observed in `gap_probes.py`).
- **LLM.** An optional plugin classifies call sites with a local model (Claimed in its README).
- **Adopt (pattern):** state, owner and freshness per obligation graph item (spec S4). **Reject:** any code reuse (licence).

## Comparison per surface

### Playground input

| Aspect | Peers | This project before | After this change |
|---|---|---|---|
| Entry | Quiz or form (AbdelStark, EuConform, DanielHuette; Observed) | JSON textarea plus 17 examples | Guided questions by default, JSON as a second mode |
| Example picker | Rare (Inferred from the eight above) | Grouped `<select>` | Unchanged; in guided mode an example opens on the check-answers page |
| Validation | Mostly client-side forms (Observed) | Pydantic errors by field, no input echo | Unchanged for JSON; guided pages validate dates and numbers before Continue |

```text
1280 px                                        375 px
+------------------------------+------------+  +---------------------------+
| INPUT  System profile  GUIDED| OUTPUT     |  | INPUT System profile      |
| Example [v]  [Load]          | Classific. |  | Example [v] [Load]        |
| Import JSON  local, 1 MB     |            |  | Import JSON               |
| [Guided questions][JSON]     | empty      |  | [Guided][JSON]            |
| ...question or JSON editor...| state      |  | ...question or editor...  |
| [ ] Include guidance notes   |            |  | Runtime status            |
| Runtime status               |            |  +---------------------------+
+------------------------------+------------+  | OUTPUT (below)            |
```

### Guided intake

| Aspect | Peers | Before | After |
|---|---|---|---|
| Source of questions | Separate per surface (AbdelStark, Observed); generated with parity check (DanielHuette, Observed) | Cockpit toggles and `/self-assessment` text fields, neither mapped to `SystemProfile` | `intake.py` generates `intake.json`; the browser interprets it; fixtures hold it to Python |
| Unknown | No, lower tier, open, or threshold (Observed, see landscape) | Cockpit `TriStateControl` writes null for nullable fields | Per question: null routed to review, `III.unsure`, or block for counsel; never false, never the omitted default |
| Skip rules | Linear (AbdelStark web) or early exit (AbdelStark CLI) (Observed) | n/a | Declarative conditions; every answer tried over a grid without changing the report |
| Check answers | GOV.UK pattern (Observed in `alphagov/govuk-design-system@2508866a`) | n/a | Change links, blocked and missing answers marked, every defaulted value listed |

```text
1280 px (left panel)                           375 px
+--------------------------------------------+ +-----------------------------+
| Question 9 of 15                      Back | | Question 9 of 15       Back |
| Is the system intended for a use listed    | | Is the system intended for  |
| in Annex III?                               | | a use listed in Annex III?  |
| Art. 6(2) AIA                               | | Art. 6(2) AIA               |
| Choose the point that applies...            | | ( ) option rows, full width |
| ( ) Annex III(1)(a): Remote biometric ...   | | ( ) None of these           |
| (o) Annex III(5)(b): Creditworthiness ...   | | or                          |
| ( ) None of these                           | | ( ) I don't know            |
| or                                          | | I don't know is recorded    |
| ( ) I don't know                            | | and routed to review.       |
| I don't know is recorded and routed to      | | [Continue]                  |
| review.                                     | +-----------------------------+
| [Continue]                                  |
+--------------------------------------------+
```

### Results

Unchanged in this change. Peers show a tier word plus checklist (AbdelStark, Observed), a score (AbdelStark and EuConform Observed; Aguardic Claimed), or a confidence number (legalithm, Observed). This project keeps the tier card with its basis, the disposition badge, four metric tiles and cited sections; no score is added (anti-pattern, see the plan). Proposed upgrades D3 and D4 in the plan:

```text
1280 px (right panel)                          375 px
+--------------------------------------------+ +-----------------------------+
| CreditSightScore   Provider, In scope      | | CreditSightScore            |
| RISK TIER  High-risk   Art. 6 AIA [Review] | | RISK TIER High-risk         |
| Review required: open questions below      | | Art. 6 AIA   [Requires rev.]|
| [Findings 1][Obligations 19][Open 0][Cit 0]| | [Find 1][Obl 19]            |
| BINDING RESULT                              | | [Open 0][Cit 0]             |
|  Findings / Open questions / Obligations    | | BINDING RESULT  (sections)  |
| Timeline  2026-08 | 2026-12 | 2027-12 | ... | | Timeline as a list with     |
|   contested reading marked, text list below | | contested items marked      |
| ADVISORY OVERLAY (nonbinding, separate box) | | ADVISORY (separate box)     |
| [JSON report] [Text report]                 | | [JSON] [Text]               |
+--------------------------------------------+ +-----------------------------+
```

### Cockpit

| Page | Before | After |
|---|---|---|
| `/` | Styled; labels such as "III 5 B" | Labels from the shared catalog ("Annex III(5)(b): Creditworthiness ...") |
| `/workspace` | Tailwind classes without Tailwind: unstyled | Plain classes on cockpit tokens; scrollable table region; 375 px without page overflow |
| `/self-assessment` | Unstyled; 4 inputs without labels | Styled; each input has a label and hint |

```text
/workspace, 1280 px                            375 px
+--------------------------------------------+ +-----------------------------+
| AI SYSTEM PORTFOLIO                         | | AI SYSTEM PORTFOLIO         |
| System vault and fleet command center       | | System vault and fleet ...  |
| [Systems 17][Blocked 2][Review 3][High 7]   | | [Systems][Blocked]          |
| Fleet command center                        | | [Review ][High   ]          |
| System | Risk | Review | Priority | Next    | | Fleet table: scrolls inside |
| ...rows...                                  | | its own region <-->         |
| [Vault card]          [Workflows card]      | | [Vault card]                |
|                                             | | [Workflows card]            |
+--------------------------------------------+ +-----------------------------+
```

### Exports

No inspected peer keeps a draft status on exported documents (Observed absence in the files read). This project's seven artifacts and dossier already carry `DRAFT_NOTICE`. The DOCX/PDF route is specified (S8) and not built. Running page headers work only in Chrome 131+ (MDN browser-compat-data, Observed), so the banner must be in the page flow:

```text
Print / PDF, A4 (same at 375 px preview)
+--------------------------------------------+
| DRAFT. Not legal advice, not a conformity  |
| assessment, not a final filing. Requires   |
| human legal review before use.             |
| Art. 27 FRIA: CreditSightScore             |
| Source manifest | Open questions | Status  |
| ...checklist with [fill in] placeholders...|
| Generated <date>, classifier <version>     |
+--------------------------------------------+
```

### Tokens

| Token | Playground | Cockpit |
|---|---|---|
| Ink / text | `#172b35` | `#17202a` |
| Accent / links | `#2c4f7c` (also used for the limited tier) | `#1f5eff` |
| Background | `#f4f5f2` | `#f6f7f8` |
| Muted | `#5d6a70` | `#64717f`; new `--muted-on-tint #525e6b` for text on tinted surfaces (4.47:1 was below AA; measured) |
| Type | Georgia headings, system sans | Inter stack |
| Theme | light only | light only |

```text
Token sheet (proposed D1 and D2), 1280 px; stacks to one column at 375 px
+--------------------+--------------------+
| LIGHT              | DARK               |
| ink    #172b35     | ink    (>=4.5:1)   |
| accent #2c4f7c     | accent (>=4.5:1)   |
| tier-limited (own) | tier-limited (own) |
| focus ring >=3:1   | focus ring >=3:1   |
+--------------------+--------------------+
```

### CLI and MCP developer experience

Unchanged. `--strict` exits 1 for prohibited or review results; Pydantic errors name fields; MCP tools `classify_ai_system` and `classify_ai_system_text` (Observed in this repository). Peers add a GitHub Action and SARIF (Systima and legalithm, Observed); parked as a follow-up.

```text
Terminal, 120 columns (wraps at 40 on a phone-width terminal)
$ eu-ai-act-classify profile.json --strict
EU AI Act classification: CreditSightScore
Risk tier: HIGH-RISK (Art. 6 AIA)
Disposition: DETERMINED
...
exit 0 (1 if prohibited or requires_review)
```

### Accessibility and i18n

All new wizard pages pass axe with WCAG 2.2 AA tags at 1280 and 375 px; the only finding is the pre-existing `label-content-name-mismatch` on the brand link (Observed, measured). Focus moves to the question heading on each page and to the error summary on a validation error. `lang="en"` throughout; German labels wait for review of their terms (H2).

```text
Focus order on a question page (both widths)
skip link -> brand -> view source -> example select -> Load -> Import
-> [Guided][JSON] -> Back -> question heading (focused on page change)
-> options in order -> "I don't know" -> Continue -> guidance toggle
Error: focus moves to "There is a problem" summary above the heading
```
