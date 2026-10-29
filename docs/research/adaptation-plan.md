# Adaptation plan

What this project takes from the [competitive landscape](2026-10-competitive-landscape.md), what it deliberately does differently, and what was built in this change. Patterns are re-implemented for the deterministic Python engine, the static Pyodide playground and the local cockpit; nothing is copied. Research date 2026-10-20, network-limited (see the landscape banner). Not legal advice.

## Baseline

Measured on `main` at `dea9675` before any change, and after the three built items.

| Measure | Before | After |
|---|---|---|
| Python tests (pytest, collected) | 230, all passing | 277, all passing |
| Playground tests (`node --test`) | 9 | 16 |
| Cockpit tests (vitest) | 3 | 6 |
| Cockpit build | passes | passes |
| axe, WCAG 2.2 AA tags, playground (5 states, 1280 and 375 px) | 1 rule each: `label-content-name-mismatch` on the brand link | unchanged; every guided page adds none |
| axe, cockpit `/` | color-contrast (17), label (1), scrollable-region-focusable (6 at 1280, 8 at 375) | unchanged (not in scope) |
| axe, cockpit `/workspace` | 0 (page unstyled) | 0 (styled) |
| axe, cockpit `/self-assessment` | label (4), page unstyled | 0 (styled) |
| Playground time to ready, CDN bytes | not reachable: cdn.jsdelivr.net returned 403 in the capture environment | not reachable |
| Playground same-origin bytes (all files in `docs/playground/`) | 309,538 | 373,644 (+64,106: intake definition 27.5 KB, interpreter and wizard 22 KB, regenerated wheel, styles) |
| Guided intake on the wire | n/a | `intake.json` 4.4 KB gzip; `intake.mjs` 2.6 KB and `wizard.mjs` 3.8 KB gzip |
| README words | 339 | 339 (README untouched) |
| `guidance_eval` agreement | 3 of 3 scored examples; 3 stored checker results echoed | unchanged |
| `--verify-sources` | every URL failed (proxy 403); logged, not updated | unchanged |
| Flaky test seen | `test_collaboration_workspace.py::test_comments_and_overrides_persist_without_changing_deterministic_baseline` failed once in about six full runs while the cockpit dev server was running, then passed; not reproduced | not investigated further |

Captures (git-ignored, not committed) cover the playground empty, example, field guide, invalid JSON and runtime-error states and the three cockpit routes; classified playground states could not be captured because Pyodide did not load. CLI transcripts for `--strict`, `--json`, `--sources`, `--artifact all`, `--dossier-dir` and `guidance_eval` were recorded locally.

## Candidates

Impact 1 to 5 on the counsel, reviewer or legal-engineer job. Fit names the non-negotiable it passes or fails. Effort S/M/L. Evidence is the strongest tag behind the pattern. Differentiation: table stakes (T) or differentiator (D).

| # | Candidate | Inspiration | Impact | Fit | Effort | Evidence | Diff. |
|---|---|---|---|---|---|---|---|
| 1 | Guided one-question intake from one Python definition (H1) | GOV.UK patterns; DanielHuette generated flow; AbdelStark (counter-example) | 5 | pass, rules 2, 5, 10 | M | Observed | D |
| 2 | One label catalog, EN now, DE after review (H2) | EuConform and AbdelStark dictionaries; IATE | 4 | pass, rule 4 (no new citations) | S | Observed | T |
| 3 | Style `/workspace` and `/self-assessment` (H4a) | baseline gap | 3 | pass, rule 9 | S | Observed | T |
| 4 | Obligation evidence state, owner, freshness (H6) | OpenComplAI (pattern), ComplianceLint, Stripe Tax (Claimed) | 4 | pass if state stays outside the binding result, rule 6 | M | Observed | D |
| 5 | Annex III synthetic benchmark scored per source (H8) | DanielHuette 207/217 | 4 | pass, rule 3 | M | Observed | D |
| 6 | Shareable profile in the URL hash (H5) | Svelte native compression; TypeScript playground | 3 | pass, rules 9 and privacy | S | Observed | T |
| 7 | Source text content hash for `--verify-sources` (Q9) | Lexbeam manifest | 3 | pass if hashes are recorded, never auto-updated, rule 8 | M | Observed | D |
| 8 | Print stylesheet PDF, then DOCX (H3) | Attestor, EuConform PDFs; npm `docx`; python-docx | 3 | pass if `DRAFT_NOTICE` in flow and DOCX optional, rules 3 and 7 | M | Observed | T |
| 9 | Dark mode on both surfaces (H4b) | EuConform, DanielHuette | 2 | pass | M | Observed | T |
| 10 | Art. 5(1)(ba)/(bb), 5(1a)/(1b), Art. 4 screens (H7) | Lexbeam, Attestor | 4 | **park**: EUR-Lex not reachable, rule 8 | M | Observed | T |
| 11 | GitHub Action and SARIF | Systima, legalithm | 2 | pass | S | Observed | T |
| 12 | Free-text or document intake drafting a profile | Luxgap, legalithm, Lexbeam | 2 | **fail** in the core, rule 3; optional only if a human confirms each field | L | Claimed | n/a |
| 13 | Readiness or compliance score | AbdelStark, EuConform, Aguardic | 1 | **fail**, rules 1 and 5: a score implies compliance | S | Observed | n/a |

## Anti-patterns

Each is something this project does not do. Observed unless tagged.

| Anti-pattern | Example | Rule it breaks |
|---|---|---|
| Unknown defaults to "no" | AbdelStark boolean defaults (`classify.ts`, `ClassifierWizard.tsx`, `@fff58f6`); Attestor optional fields (`model.py`, `@cc70eec`); a NuGet classifier that defaults to Minimal (Claimed, nuget.org) | 5 |
| Unsure lowers the tier | EuConform `risk-classifier.ts` (`@011a5ad`) | 5 |
| Two question trees for one engine | AbdelStark CLI versus web | 10 |
| Pre-amendment Annex III date | AbdelStark, DanielHuette, Systima, ArkForge (code or README); Prefactor, Aguardic pages (Claimed) | 8 |
| LLM in the classification path | Luxgap (Claimed); ComplianceLint judges evidence with an LLM (`evidence.py`, `@a3fec46`) | 3 |
| Hosted keys or sign-up for core checks | legalithm `init` and `check` (Claimed in README); ComplianceLint detection logic (Claimed) | 3 |
| Readiness score implying compliance | AbdelStark `scoring.ts`; EuConform level scores; Aguardic readiness and penalty figure (Claimed) | 1, 5 |
| Uploading system descriptions to a server | Luxgap technical documents (Claimed) | privacy, "nothing you paste leaves the page" |
| Auto-applied Art. 6(3) | not found; IsHighRiskAI asks it as its own stage (Claimed) | 5 |
| Uncited one-word verdicts | not confirmed for any product | 1 |
| Keyword matching for prohibitions | legalithm `risk_map.json`; compliance kit `PROHIBITED_KEYWORDS` | 2 |
| Default-on telemetry in a compliance tool | legalithm `telemetry.ts`; ArkForge `server.py` | privacy |

## Positioning

Hypothesis tested: the only free, offline, deterministic classifier whose citations and dates are ledger-verified against the 27 July 2026 consolidation, which fails closed to lawyer review and runs one engine in browser, CLI, CI and MCP. **Modified.** "Only" cannot be supported: other open-source projects are free, offline and deterministic, and some show the amended dates (Observed). What the research supports is narrower: this project combines a claim ledger with per-claim review status, a fail-closed disposition that never maps unknown to no, never applies Art. 6(3) automatically, and, after this change, a single Python-generated intake that every surface shares and that tests prove cannot drop or reinterpret an answer. Proposed wording for the overview, without comparison: "A free, offline and deterministic first pass. Every citation and date is tracked in a review ledger, unknown facts go to a lawyer rather than to a default, and one engine and one question set run in the browser, the CLI, CI and MCP."

## Hypothesis verdicts

| | Verdict | Evidence |
|---|---|---|
| H1 Guided questionnaire | **Confirmed, built.** Modified: three unknown policies (null routed to review, `III.unsure`, block); `significant_change_after_application_date` blocks on "I don't know", and its model-default null opens unanswered | GOV.UK (Observed); peers' unknown handling (Observed); checks in `tests/test_intake.py` |
| H2 Label catalog EN/DE | **Confirmed; EN built.** DE parked: German legal terms cannot be checked against the DE Official Journal text from this environment | EuConform, AbdelStark DE terms (Observed); IATE and EUR-Lex not reachable |
| H3 DOCX/PDF export | **Modified, specified.** Print stylesheet first (no dependency); DOCX as an optional Python extra; rename `wordExportPackage` until real DOCX exists | No peer keeps draft status (Observed); `@page` margin boxes Chrome only (Observed) |
| H4 Cockpit styling, then dark mode | **Styling confirmed and built** without Tailwind ([ADR 0004](../adr/0004-cockpit-styling-without-tailwind.md)). Dark mode specified, not built | Baseline captures |
| H5 Shareable URL hash | **Confirmed, specified.** Native `deflate-raw` plus base64url, written only on "Create share link"; no dependency | Svelte, TypeScript playground (Observed); 160 to 316 characters per example (Observed) |
| H6 Evidence tracker | **Confirmed, specified.** Minimal state, owner and reviewed-on date on the cockpit side only | OpenComplAI, ComplianceLint (Observed) |
| H7 Legal coverage gaps | **Parked.** Every change needs the EUR-Lex check this run could not make | Network |
| H8 Annex III synthetic benchmark | **Confirmed, specified.** Report tier and disposition separately per source; never count an unresolved result as agreement | DanielHuette `showcase.py` (Observed) |

## Specs

### S1. Guided intake (built)

- **User story.** As counsel without the schema in my head, I answer one plain question at a time and see every answer, and every value I was not asked about, before I classify.
- **References.** GOV.UK question pages and check answers (`alphagov/govuk-design-system@2508866a`); DanielHuette generated flow and parity script; AbdelStark as the counter-example of drifting trees.
- **Adapted versus different.** One question per page, question as heading, article under it, error summary with focus, check-answers page with Change links. Different: questions, order and skip rules are Python data; the browser only interprets them; "I don't know" never becomes false and can block the run.
- **Acceptance.** All 19 examples round-trip; every fail-closed unknown yields `requires_review`; every answer to each skipped question is tried over two grids of intake-reachable states (1,041 and 1,656 distinct states) without changing the classification report, apart from the engine's own "not used" statements, and, in scope, without changing the advisory notes; the browser interpreter matches Python on the generated fixtures, including padded text and unanswered questions; every question article is a pinpoint the engine already cites; a profile whose values the questions would drop is refused; no new axe violations.
- **Files.** `src/eu_ai_act_classifier/intake.py`, `scripts/build_playground.py`, `docs/playground/{intake.json,intake.mjs,wizard.mjs,app.mjs,index.html,styles.css}`, `tests/test_intake.py`, `tests/playground/{intake.test.mjs,intake-fixtures.json}`.
- **Risk.** Rule 10 (no legal logic outside Python): the conditions are data and their effect is tested in Python. Rule 5: covered by tests. Follow-ups: split the 26-option Annex III page into area then point; map `/self-assessment` and the cockpit toggles onto the same definition; update `document.title` per page.

### S2. Label catalog (built, EN)

- **Story.** As a reviewer I read "Annex III(5)(b): Creditworthiness evaluation and credit scoring of natural persons", not "III 5 B".
- **References.** EuConform and AbdelStark dictionaries (Observed); IATE (not reachable).
- **Adapted.** One generated catalog (`labels.py` to `web/lib/labels.json` and `fields.json`) with titles taken from `catalog.py`. Different: no new citation is introduced by a label.
- **Acceptance.** Every enum value labelled; generated file current; no raw value as a label. DE: add `locale: "de"` entries only after each term has a `PENDING` ledger row and a lawyer confirms it.
- **Files.** `labels.py`, `scripts/build_playground.py`, `web/lib/labels.{ts,json,test.ts}`, `web/components/cockpit.tsx`, `tests/test_labels.py`.

### S3. Cockpit page styling (built)

- **Story.** As a reviewer on the portfolio and self-assessment pages I get the same readable layout as the cockpit home.
- **Acceptance.** No Tailwind class left; axe clean at 1280 and 375 px; no page overflow at 375 px; labelled inputs.
- **Files.** `web/app/globals.css`, `web/app/workspace/page.tsx`, `web/app/self-assessment/*`. See [ADR 0004](../adr/0004-cockpit-styling-without-tailwind.md).

### S4. Obligation evidence state (next)

- **Story.** As a governance lead I mark each obligation graph item with an evidence state, an owner and the date it was last reviewed, grouped in applies-now, upcoming and contested lanes.
- **References.** OpenComplAI control states and TTL (pattern only, AGPL); ComplianceLint commit-bound evidence (pattern only, BSL); Stripe Tax status chips (Claimed).
- **Different.** State lives in the cockpit's local workspace, keyed by `obligation_id`; the engine's `ObligationGraphItem` stays unchanged, so the binding result never depends on tracker state (rule 6). States: `not_started`, `in_progress`, `evidence_attached`, `reviewed`, `stale` (reviewed-on older than the source manifest's retrieval date). No LLM judges evidence.
- **Acceptance.** Lanes derive from `application_date` and `application_date_note`; a changed report marks affected items stale; export carries `DRAFT_NOTICE`.
- **Files.** `web/components/cockpit.tsx`, `web/lib/types.ts`, `collaboration_workspace.py` (local persistence), tests. [ADR 0006](../adr/0006-evidence-model.md).

### S5. Annex III synthetic benchmark (next)

- **Story.** As a legal engineer I see per-source agreement on synthetic profiles for each of the 21 Annex III rows that have no example today.
- **References.** DanielHuette benchmark, `@88e9710:data/evaluation/*` and `showcase.py` (Observed).
- **Different.** `examples/guidance/annex_iii_synthetic_benchmark.json` with `source_status: "synthetic"`; `expected` written from the legal text by a lawyer, never from the engine; `guidance_eval.py` reports tier and disposition separately per source; an unresolved result never counts as agreement.
- **Acceptance.** One profile per uncovered Annex III row; each `expected` cites its Annex III point; `guidance_eval` prints agreement per source and per field; `docs/coverage.md` shows the new examples.
- **Files.** `examples/guidance/annex_iii_synthetic_benchmark.json`, `src/eu_ai_act_classifier/guidance_eval.py`, `scripts/build_coverage.py` output, `docs/coverage.md`.
- **Tests.** `tests/test_guidance_eval.py`: the file loads, every row has a lawyer-written `expected`, scoring separates tier from disposition, and a `requires_review` result never counts as a match for `determined`.
- **Risk.** Rule 8: each expectation rests on the legal text, so drafting waits for EUR-Lex access and review; until then rows stay `PENDING`. No existing golden, expectation or example outcome changes.

### S6. Share link in the URL hash (built)

- **Story.** As a user I share a synthetic profile with a colleague without a server.
- **References.** Svelte playground native compression; TypeScript playground hash (Observed); Ruff stores shares on a server (Observed), which this project rejects.
- **Different.** Only on "Create share link": compact profile, `deflate-raw` via `CompressionStream`, base64url, prefix `#p1.`; plain base64url fallback (`#j1.`); refuse above 8,000 characters and offer download; validate before loading; never auto-classify; warn that history sync and chat services keep links. No dependency. [ADR 0005](../adr/0005-url-state-encoding.md).
- **Acceptance.** All bundled examples encode below 400 characters and decode to the same compact profile; a corrupted or oversized hash shows an error summary and loads nothing; the hash is written only by the button; no network request carries the profile.
- **Files.** `docs/playground/share.mjs` (pure encode and decode), `docs/playground/app.mjs`, `docs/playground/index.html`, `docs/playground/styles.css`.
- **Tests.** `tests/playground/share.test.mjs`: round trip for every example, version prefix, size cap, invalid input; Playwright check that loading a share link does not classify automatically.
- **Risk.** Privacy: links persist in history and chat logs, so the warning is required and the feature stays opt-in. Rule 9: no server, no build step.

### S7. Source content hash (next)

- **Story.** As a legal engineer I can tell whether the consolidated text changed since the ledger was reviewed.
- **References.** Lexbeam `@efcbae2:law/manifest.json` (Observed).
- **Different.** Record sha256 of the retrieved HTML alongside each source in the manifest; `--verify-sources` reports a mismatch as review needed and never updates on its own (rule 8).
- **Acceptance.** Each binding source in `citations.py` carries a recorded hash and retrieval date; a changed page prints "content changed, review required" and exits non-zero under `--strict`; `--update` is never run by CI.
- **Files.** `src/eu_ai_act_classifier/citations.py`, `src/eu_ai_act_classifier/verify_sources.py`, `docs/REGULATORY_CLAIM_LEDGER.md` (a `PENDING` row per recorded hash).
- **Tests.** `tests/test_verify_sources.py` with a stubbed fetch: same content passes, changed content flags review, network failure is reported and does not pass.
- **Risk.** Rule 3: the check stays outside the classification path and is never required for a result. Recording the first hashes needs EUR-Lex access.

### S8. Draft PDF via print stylesheet, then DOCX (next)

- **Story.** As counsel I send a draft artifact to a colleague as PDF or Word without losing the draft notice.
- **References.** Attestor and EuConform PDFs (Observed); npm `docx` and python-docx licences and sizes (Observed); MDN data on `@page` margin boxes (Observed).
- **Different.** PDF: a print stylesheet on the artifact preview with `DRAFT_NOTICE` as the first block of the page flow (not a running header). DOCX: `python-docx` in an optional `[docx]` extra, outside the core; rename the cockpit's "Word package" to "Draft package" until then. [ADR 0003](../adr/0003-export-route.md).
- **Acceptance.** The printed preview shows `DRAFT_NOTICE` first and "DRAFT" in the title in Chromium, Firefox and WebKit; the DOCX has the notice as its first paragraph and in its core title; the core install stays Pydantic-only.
- **Files.** `web/app/globals.css` (print rules), `web/components/cockpit.tsx`, `src/eu_ai_act_classifier/docx_export.py` (extra only), `pyproject.toml` (`[docx]` extra), an ADR update.
- **Tests.** A test that every artifact rendered for print or DOCX contains `DRAFT_NOTICE`; a test that importing the core package does not import `docx`.
- **Risk.** Rule 7: the notice must survive every format, so the test covers each. Rule 3: the new dependency sits in an extra, with an ADR.

## Design upgrades

D2 and D4 are built; the others are specified.

### D1. Dark mode on both surfaces

- **Story.** As a reviewer working at night I read results without glare, with the same tier colours and labels.
- **References.** EuConform `ThemeToggle.tsx`; DanielHuette `prefers-color-scheme` (Observed).
- **Spec.** Replace `color-scheme: light` with token sets under `prefers-color-scheme: dark`, plus a manual override stored per viewer. Text at least 4.5:1, borders and focus rings at least 3:1, tier colours always paired with a text label.
- **Acceptance.** axe clean in both schemes at 1280 and 375 px; contrast checked per token pair.
- **Files.** `docs/playground/styles.css`, `web/app/globals.css`, a small toggle in each header.
- **Risk.** None to the non-negotiables; no web fonts or dependencies.

### D2. Separate tier and link colours (built)

- **Story.** As a reader I do not mistake a link for a limited-risk badge.
- **Spec.** Split `--blue` (limited tier) from `--accent` (links and primary actions); both were `#2c4f7c`. Built: `--accent` is `#5a3e85` (8.5:1 on white), `--blue` stays `#2c4f7c`, and nonbinding source badges use the grey tone instead of the tier blue.
- **Acceptance.** No element uses the tier token for interaction; badges keep their text labels.
- **Files.** `docs/playground/styles.css`.
- **Risk.** None.

### D3. Application-date timeline

- **Story.** As counsel I see which obligations apply now, which are upcoming and which rest on a contested reading.
- **References.** legalithm `appliesFrom` (Observed); Stripe Tax status chips (Claimed).
- **Spec.** A horizontal timeline from the report's `timeline` and graph dates, with contested readings marked and a text list as the accessible alternative; a vertical list at 375 px.
- **Acceptance.** Every date shown is one the report already carries; the text list states the same content; axe clean.
- **Files.** `docs/playground/app.mjs`, `docs/playground/styles.css`.
- **Risk.** Rule 4 and 8: no date is computed in the browser; the view only displays report data.

### D4. Binding result apart from the advisory overlay (built)

- **Story.** As a reviewer I never confuse nonbinding guidance notes with the binding classification.
- **Spec.** Group findings, open questions and obligations under "Binding result"; show advisory notes in a separate, visibly nonbinding box after them.
- **Acceptance.** The advisory box appears only when the toggle is on, carries "Nonbinding" in its heading, and sits after the binding sections in DOM and visual order.
- **Files.** `docs/playground/app.mjs`, `docs/playground/styles.css`.
- **Risk.** Supports rule 6.

### D5. Annex III in two steps

- **Story.** As counsel on a phone I choose the Annex III area first, then the point, instead of scanning 26 options.
- **Spec.** Split the Annex III question into area then point in `intake.py`; "I don't know" on either step writes `III.unsure`.
- **Acceptance.** The skip-rule and round-trip tests still pass; the point page lists only the chosen area's points.
- **Files.** `src/eu_ai_act_classifier/intake.py`, generated `intake.json`, tests.
- **Risk.** Rule 10: the split lives in Python; the area step must not become a profile field of its own.

## Design direction

- **Tokens.** Keep the playground palette and tier colours, always with a text label. `--blue` (limited tier) and `--accent` (links and primary actions) are separate colours since D2. The cockpit keeps its own tokens for now; convergence is an owner decision.
- **Type and layout.** Georgia headings with system sans; tabular numerals for counts and dates (already on metric tiles and wizard progress); single-column wizard inside the existing two-panel layout and its 1050/800/520 breakpoints.
- **Dark mode.** Replace the hard-coded `color-scheme: light` with tokens redefined under `prefers-color-scheme: dark`, text at least 4.5:1 and borders and focus rings at least 3:1, on both surfaces.
- **States.** Empty, loading, runtime error and stale states exist; the guided mode adds blocked ("Counsel must answer before classification") and missing states on the check-answers page.
- **Microcopy.** Plain and hedged; "A cited first pass. A lawyer confirms." stays.
- **Shared design system.** `sebastianfoerste/legal-ai-design-system` was not attached and was not read.

## ADRs

- [0001 Guided intake source of truth](../adr/0001-guided-intake-source-of-truth.md)
- [0002 Labels and i18n](../adr/0002-labels-and-i18n.md)
- [0003 Export route](../adr/0003-export-route.md)
- [0004 Cockpit styling without Tailwind](../adr/0004-cockpit-styling-without-tailwind.md)
- [0005 URL state encoding](../adr/0005-url-state-encoding.md)
- [0006 Evidence model](../adr/0006-evidence-model.md)
- [0007 SystemProfile change proposals](../adr/0007-systemprofile-change-proposals.md)

## Needs owner decision

1. **Unknown on `significant_change_after_application_date`.** Resolved in the audit follow-up: "I don't know" now blocks, and a profile that leaves the field at its default opens with the question unanswered. Open: whether the engine should raise a review question for a null value instead, which would let the run proceed.
2. **Nullable screens.** Most screens are non-nullable booleans, so the intake blocks on "I don't know". Making more fields nullable with engine-side review questions would let more runs proceed ([ADR 0007](../adr/0007-systemprofile-change-proposals.md)).
3. **Art. 50(2) grace period.** Secondary sources disagree (2 December 2026 versus 2 December 2027, both Claimed). The engine and ledger use 2026-12-02; please re-check against the consolidated text. Nothing was changed.
4. **Art. 5(1)(ba)/(bb), Art. 5(1a)/(1b) and Art. 4 screens (H7).** Parked until the wording can be checked on EUR-Lex; each needs a `PENDING` ledger row and a test.
5. **German labels.** Proposed terms (Anbieter, Betreiber, Hochrisiko-KI-System) match what two peers use (Observed) but were not checked against the DE Official Journal text.
6. **Positioning wording** for the overview (see above).
7. **Token convergence** between playground and cockpit.
8. **Optional natural-language intake.** Rejected for the core; acceptable only as an optional extra that drafts a profile a human confirms field by field.

## Rejected

- Readiness or compliance scores (implies compliance; rules 1 and 5).
- Confidence numbers for a deterministic result.
- LLM or keyword classification in the core path (rule 3).
- Server-side share storage (the playground stays static).
- Hosted keys or sign-up for core checks; telemetry.
- Code reuse from AGPL (OpenComplAI), BSL (ComplianceLint), GPL (CNIL PIA) or EUPL sources; patterns only. No third-party code was reused, so no `THIRD_PARTY_NOTICES.md` is needed.
