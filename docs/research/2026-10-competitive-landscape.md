# Competitive landscape, October 2026

> **Network-limited run.** This research ran in a cloud container on 2026-10-20 with restricted egress. GitHub (clone and raw files), PyPI, the npm registry and web search worked. The following hosts failed (DNS error or proxy 403) and could not be opened: eur-lex.europa.eu, ai-act-service-desk.ec.europa.eu, digital-strategy.ec.europa.eu, futurium.ec.europa.eu, design-system.service.gov.uk, iate.europa.eu, w3.org, cdn.jsdelivr.net (Pyodide), and every commercial vendor site listed under [Not reachable](#not-reachable). Facts about those products come only from search-engine snippets and are tagged **Claimed**. Nothing was filled in from memory.

Research only. Not legal advice. Every product fact carries its source and an evidence tag; see the [feature matrix](feature-matrix.csv) for the per-capability view and the [design teardown](design-teardown.md) for interface patterns. The resulting plan is in [adaptation-plan.md](adaptation-plan.md).

## Method

- **Evidence tags.** **Observed**: seen in source code at a pinned commit, in package metadata, or measured. **Claimed**: README, marketing copy or a search snippet only. **Inferred**: reasoning from tagged facts. No tag was upgraded. Access date for every source: 2026-10-20.
- **Rings.** Direct competitors (EU AI Act classifiers and checkers), adjacent products (AI governance platforms, scanners, benchmarks) and pattern donors (guided interviews, playgrounds, document export, accessibility rules).
- **Code reading.** 15 open-source repositories were shallow-cloned outside this repository (`/tmp/oss/`) and read at a pinned commit. Citations use `owner/repo@SHA7:path`. The GitHub REST API returned 403 for unattached repositories, so stars, archive flags and releases were not read.
- **Clean room.** No code, question bank, rule text, label set or marketing copy was copied. Quotes are at most one phrase of ten words per source. Competitor screenshots were not taken (no vendor site loaded).
- **No external actions.** No accounts, trials, forms, messages, issues, stars or forks. No live questionnaire could be run, so no checker results were stored and `checker-runs.json` was not produced.

## Coverage against the brief

| Target | Result |
|---|---|
| Searches, EN/DE/FR, at least 12 | More than 60 web searches across three research tracks, including the German and French queries listed below |
| Products in the matrix, at least 15 | 59 rows: 25 direct, 15 adjacent, 19 pattern donors (including this repository for reference) |
| Deep teardowns, at least 8, incl. the Commission checker and 3 OSS peers | 8 in [design-teardown.md](design-teardown.md). The Commission checker section rests on snippets only (**shortfall**: not reachable) |
| Code read for at least 3 OSS projects | 15 repositories read at pinned commits |
| Review mining for at least 3 products | 5 products (Commission checker, OneTrust, Credo AI, IBM watsonx, Holistic AI), all from third-party pages tagged Claimed. No Reddit, Hacker News, Artificial Lawyer, LawSites or Legal Geek items surfaced |

Shortfalls: no vendor product was loaded, so no **Observed** fact exists for any commercial checker, and the synthetic credit-scoring and social-scoring walkthroughs could only be run (by reading code) for open-source tools.

## Searches

A selection of the queries; per-product sources are in the `sources` column of the matrix:

| Language | Query | What it surfaced |
|---|---|---|
| EN | EU AI Act compliance checker alternative | checker listings, an offline OSS quiz, subscription tools, a TUM thesis on checkers |
| EN | EU AI Act risk classification tool | Commission checker, TUV SUD Risk Navigator press, JUN Legal CAILEE, Aguardic, RiskLine |
| EN | site:github.com eu ai act classifier | compliance kit, a NuGet classifier, several MCP servers, ActTrace |
| EN | EU AI Act MCP server | Lexbeam MCP, a G2 marketplace MCP listing, other hosted MCP servers |
| EN | AI governance platform EU AI Act | FairNow, SimpleAct, Commugen and others |
| EN | guided legal interview software | A2J Author, Gavel (pattern references) |
| DE | KI-Verordnung Risikoklassifizierung Tool | TUV SUD (DE), Bitkom mention, a 12-question decision tree, appliedAI study |
| DE | KI-VO Hochrisiko Check online | blog posts on the Commission consultation; many pages still citing 2 August 2026 |
| DE | Bundesnetzagentur KI-Service-Desk KI-Compliance-Kompass | Compliance Kompass with per-question article links (Claimed) |
| FR | outil classification AI Act | regulation-ai.eu, Luxgap (LLM agent reading documents), Aguardic |
| FR | conformite AI Act questionnaire gratuit | AiActo diagnostic (role and tier, short and full versions) |
| FR | AiActo diagnostic AI Act role fournisseur deployeur niveau de risque | AiActo roles, tiers, PDF report, 2 Dec 2027 date (Claimed) |
| EN | EU AI Act digital omnibus 2026/1744 high-risk delay 2 December 2027 | secondary sources on the amended dates |
| EN | Collibra acquires trail ML October 2026 | acquisition announced 2026-10-05, https://www.collibra.com/company/newsroom/press-releases/collibra-acquires-trail-ml-to-automate-ai-governance-from-policy-to-production (Claimed) |

## Owner's awesome lists

Checked through raw.githubusercontent.com on 2026-10-20 (all returned the README; Observed). Entries were listed, not visited or verified.

| List | Commit | EU AI Act entries |
|---|---|---|
| [awesome-eu-fintech-regulation](https://github.com/sebastianfoerste/awesome-eu-fintech-regulation) | `c77ef2f` | AI Act Explorer (guide); AegisAI; AI Act Implementation Tool (questionnaire-based classification); AI Assessment Tool (ALTAI); EuConform; this repository and eu-reg-mcp (curator-maintained, disclosed); a related awesome-eu-ai-act list |
| [awesome-legal-tech](https://github.com/sebastianfoerste/awesome-legal-tech) | `7614f25` | EU AI Act Dataset; Regulus; Regula (Apache-2.0); an EU AI Act legal RAG prototype; EuConform; Pinpoint (MIT); two EU AI Act MCP servers (SonnyLabs, Lexbeam); Awesome EU AI Act (CC0-1.0) |
| [awesome-in-house-legal](https://github.com/sebastianfoerste/awesome-in-house-legal) | `43b145e` | none (compliance section lists CISO Assistant and Giskard) |
| [awesome-legal-nlp](https://github.com/sebastianfoerste/awesome-legal-nlp) | `397ef5e` (master) | none |
| [Awesome-LegalAI-Resources](https://github.com/sebastianfoerste/Awesome-LegalAI-Resources) | `97fec0d` | none |

EuConform and Lexbeam from these lists are in the matrix. AegisAI, the AI Act Implementation Tool, Regula, Regulus and Pinpoint were not researched in this run (coverage gap).

## Products

Full rows, capability cells and sources are in [feature-matrix.csv](feature-matrix.csv). Summary by ring:

**Direct (25).** European Commission AI Act Service Desk Compliance Checker; FLI Compliance Checker; TUV SUD Risk Navigator; Aguardic; Pinsent Masons EUaiN; AiActo; Holistic AI risk calculator; JUN Legal CAILEE; Bundesnetzagentur Compliance Kompass; Prefactor; Fluxforce; IsHighRiskAI; Luxgap; VerifyWise; AbdelStark eu-ai-act-toolkit; Hiepler EuConform; DanielHuette ai-act-compliance-helper; Lexbeam eu-ai-act-mcp; legalithm; Attestor; EU AI Act Compliance Kit; RiskLine; disclos-eu-ai-act; @artale/pi-comply (repository not reachable); this repository.

**Adjacent (15).** Credo AI; OneTrust AI Governance; IBM watsonx.governance; Modulos; Saidot; trail ML (acquired by Collibra, `still_exists=acquired`); appliedAI risk classification database; Legiscope; Enzai; FairNow; ValidMind; Systima Comply; COMPL-AI; ActTrace; ArkForge mcp-eu-ai-act.

**Pattern donors (19).** GOV.UK Design System question pages, check answers and error summary (read from the `alphagov/govuk-design-system` source); Typeform Logic Jumps; Stripe Tax monitoring; Ruff, TypeScript, Svelte, JupyterLite and Rust playgrounds; docassemble; react-jsonschema-form; Catala; CNIL PIA (GPL-3.0, pattern only); IATE; npm `docx`; python-docx; print-stylesheet PDF; WCAG 2.2; OpenComplAI and ComplianceLint (AGPL and BSL, pattern only).

Seed items checked and dropped or changed: trail ML is listed as acquired; `mcp-eu-ai-act` does not exist on npm (the PyPI package of that name is an ArkForge alias); `@artale/pi-comply` points at a repository that asked for credentials. The "EU AI Act Compliance Kit" seed resolved to `ogulcanaydogan/eu-ai-act-compliance-kit` (Apache-2.0, Observed).

## Key findings

Each finding names its source and tag. Paths are at the commits listed in the matrix.

1. **Several open-source wizards keep separate question trees per surface.** In `AbdelStark/eu-ai-act-toolkit@fff58f6` the web wizard reads `data/questions.json` while the CLI hardcodes its own prompts and order (`packages/cli/src/commands/classify.ts`); only the classify function is shared (Observed). The web wizard's answer map has no entry for the Annex III question IDs (`ClassifierWizard.tsx`), so an Annex III answer would not reach the engine (mapping Observed, effect Inferred).
2. **"I don't know" is handled in four different ways.** As "no" (AbdelStark boolean defaults; Attestor optional fields, Observed), as a lower tier (EuConform maps unsure to `limited`, `risk-classifier.ts`, Observed), as an open or conditional result (DanielHuette `question_flow.py`; Lexbeam `insufficient_information` and `missing_facts`, Observed), or as a confidence threshold (legalithm `reviewRequired` below 0.6, `engine.ts`, Observed).
3. **Annex III dates diverge.** 2 August 2026 is still shown by AbdelStark, DanielHuette, Systima and ArkForge (Observed in code or README). Lexbeam, legalithm, Attestor and disclos show 2 December 2027 (Observed). EuConform shows 2026 with a "proposed" December 2027 overlay (Observed). Aguardic, Prefactor and Legiscope pages show the 2026 date or both (Claimed).
4. **Source pinning.** Lexbeam ships a manifest of the consolidated text 02024R1689-20260727 and Reg. (EU) 2026/1744 with sha256 per file and a fail-closed freshness monitor; all 8 hashes were recomputed and match (Observed). legalithm stamps an `asOf` date without hashing the text (Observed).
5. **Benchmarks against Commission material.** DanielHuette reports agreement on 207 of 217 examples from the draft Art. 6 guidelines; the match counts tier plus disposition (high-risk, not high-risk, Art. 6(3) exemption), and an unresolved conditional result counts as agreeing with high-risk (`showcase.py`, Observed; leniency Inferred).
6. **Evidence tracking.** OpenComplAI models control state (satisfied, evidence missing, evidence stale, pending review, waived), owner and a TTL, and stales a control when its manifest changes (`models.py`, `control_freshness.py`, Observed; AGPL, pattern only). ComplianceLint binds evidence to git commits but lets an LLM judge adequacy (`evidence.py`, Observed; BSL).
7. **Exports rarely say "draft".** No inspected project exports DOCX. EuConform (PDF) and Attestor (Annex IV PDF) carry disclaimers or placeholders but no persistent draft status (Observed absence in the files read).
8. **Guided-question conventions.** GOV.UK patterns call for one question per page, the question as the page heading, an "I do not know" answer where valid, an error summary that takes focus, and a check-answers page with Change links (`alphagov/govuk-design-system@2508866a`, Observed).
9. **URL sharing without a server is practical.** Svelte compresses with the browser's native `CompressionStream` and base64url (Observed); our example profiles come to 160 to 316 characters that way (Observed measurement). Ruff's playground now stores shares server-side (Observed), which this project must not do.
10. **Commission checker.** Reviewers describe it as role-first, English only and light on help with ambiguity (review at https://www.zwillgen.com/artificial-intelligence/the-eus-ai-act-compliance-checker-explorer-whats-useful-today-whats-still-come/, Claimed). Its per-article Service Desk pages were indexed as not yet updated for the amendment (Claimed).

## Context (verify against the Official Journal)

All Claimed: EUR-Lex was not reachable, so none of these could be checked against the official text. The repository's own dates remain those in the [claim ledger](../REGULATORY_CLAIM_LEDGER.md), which this research did not change.

- Reg. (EU) 2026/1744 published in the OJ on 24 July 2026, in force 27 July 2026; Annex III high-risk from 2 December 2027 and Annex I from 2 August 2028 (secondary sources: https://pasqualepillitteri.it/en/news/8951/eu-regulation-2026-1744-digital-omnibus-ai-act, https://www.hunton.com/privacy-and-cybersecurity-law-blog/eu-digital-omnibus-on-ai-enters-into-force, https://cdp.cooley.com/digital-ai-omnibus-delays-key-deadlines-introduces-new-rules/).
- Draft Art. 6 high-risk guidelines published 19 May 2026, consultation to 23 June 2026 (https://www.hunton.com/privacy-and-cybersecurity-law-blog/european-commission-releases-draft-guidelines-on-high-risk-ai-under-the-eu-ai-act, https://www.williamfry.com/knowledge/eu-publishes-draft-guidelines-on-classification-of-high-risk-ai-systems/, https://www.skadden.com/insights/publications/2026/05/ai-act-update).
- Final Art. 50 guidelines 20 July 2026 and GPAI scope guidelines 18 July 2026 (https://www.mayerbrown.com/en/insights/publications/2026/07/eu-ai-act-news-digital-omnibus-on-ai-new-guidance-on-risk-classification-gpai-and-transparency-obligations).
- AI Act Explorer per-article URL pattern on the new consolidation: **not verified**. An indexed Service Desk URL followed `/{lang}/ai-act/article-{n}` and said it was not yet updated.
- **Conflict to review:** secondary sources disagree on when the Art. 50(2) grace period ends (2 December 2026 at https://pasqualepillitteri.it/en/news/8951/eu-regulation-2026-1744-digital-omnibus-ai-act versus 2 December 2027 at https://www.gornitzky.com/eu-ai-omnibus-enters-into-force/). The engine uses 2026-12-02 (Art. 111(4)) per the ledger. This is flagged for the confirming lawyer in the [adaptation plan](adaptation-plan.md#needs-owner-decision); no date was changed. Update 2026-10-31: resolved. Art. 111(4) AIA, added by Art. 1, point (39)(b) of Regulation (EU) 2026/1744, reads "by 2 December 2026", and recital (38) calls it a "transitional period of four months" for providers who placed their systems on the market before 2 August 2026; read in the Publications Office snapshot of the OJ text on the `feat/source-snapshots` branch (`sources/oj/32026R1744.en.xhtml`). 2026-12-02 stands; the 2027 date in the second source is wrong.

## Not reachable

DNS failure or proxy 403 on 2026-10-20, one attempt each:

- Official: eur-lex.europa.eu, ai-act-service-desk.ec.europa.eu, digital-strategy.ec.europa.eu (also every `--verify-sources` URL), futurium.ec.europa.eu, iate.europa.eu, bundesnetzagentur.de, ctu.gov.cz, design-system.service.gov.uk, w3.org.
- Vendors and publishers: artificialintelligenceact.eu, tuv-sud.risk-navigator.ai, aiacto.eu, aguardic.com, holisticai.com, jun.legal, pinsentmasons.com, credo.ai, onetrust.com, ibm.com, modulos.ai, saidot.ai, collibra.com, appliedai.de, legiscope.com, prefactor.tech, enz.ai, fairnow.ai, validmind.com, zwillgen.com, ai-regulation.com, docassemble.org, typeform.com, docs.stripe.com, eu-ai-act-compliance-kit.readthedocs.io (snippet only).
- Runtime: cdn.jsdelivr.net (Pyodide 0.28.2), so the playground could not classify in the capture browser.
- Repositories: the GitHub REST API for unattached repositories (403); `artale93/pi-comply` (credential prompt). `sebastianfoerste/legal-ai-design-system` was not attached and was not read.
