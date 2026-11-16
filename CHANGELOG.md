# Changelog

Notable changes to the classifier. Earlier releases are described in their
pull requests.

## Unreleased

### Print a draft artifact as PDF (S8)

- The cockpit's Export Pack has a print button. The printed page, or a PDF saved
  from the print dialog, shows only the draft notice, first, and the selected
  artifact; the document title starts with "DRAFT" while printing, also when
  printing starts from the browser menu. No dependency is added
  ([ADR 0003](docs/adr/0003-export-route.md), parts 1 and 3).
- The inventory tile "Word package" reads "Draft package". The inventory JSON
  field `wordExportPackage` keeps its name.

## 0.3.0 (2026-11-16)

#### Upgrade notes

Profiles and CI jobs that pass on 0.2.2 can fail or change on 0.3.0. Pinning
`eu-ai-act-classifier==0.2.2` keeps the 0.2.2 behaviour while you update them.

- `application_date` on an obligation-graph item can be null where the date
  turns on a placing date the profile does not give: the Chapter V items of a
  general-purpose AI model without `gpai_model_placing_on_market_date` or
  `placing_on_market_date` (Art. 111(3)), and `transparency.1` for a provider
  with `generates_synthetic_content` and no `placing_on_market_date`
  (Art. 111(4)). It can be null while `applies_on_assessment_date` is true.
  The Python model types it `str | None`, and the 0.2.2 report schema rejects
  such a report.
- The JSON report and its models have two new keys, both null by default:
  `applies_on_assessment_date` on every obligation-graph item (true, false or
  null; null without an `assessment_date`) and `scope.assessment_date`. The
  report schema allows extra keys, so the 0.2.2 schema accepts them; key-set
  and snapshot comparisons change.
- Every report in scope lists an Art. 4 AI literacy obligation (`Art. 4 AIA`)
  and a graph item `literacy.provider.4` or `literacy.deployer.4`, dated
  2025-02-02, once per provider or deployer role, whatever the tier.
  Minimal-risk and prohibited reports, whose `obligations` and
  `obligation_graph` were empty on 0.2.2, now hold these entries; for a
  prohibited system the item is `review_required`. A profile whose only role
  is `gpai_provider` gets none.
- `--strict` now exits 1 for five kinds of profile that 0.2.2 reported as
  `determined` (exit 0). Each now has an open question, so the disposition is
  `requires_review`:
  - `generates_synthetic_content` or `generates_deepfakes` with neither
    `5.1.ba` nor `5.1.bb` declared and no element facts, as in
    `examples/deepfake_generator.json`. Element facts in `intimate_imagery`
    and `child_sexual_abuse_material` that settle both points close the
    question.
  - a provider with `generates_synthetic_content` and no
    `placing_on_market_date` (the Art. 111(4) question).
  - a general-purpose AI model with neither
    `gpai_model_placing_on_market_date` nor `placing_on_market_date`
    (Art. 111(3)). The bundled GPAI examples now give
    `gpai_model_placing_on_market_date`.
  - an Art. 6(1) product with neither `annex_i_legislation` nor
    `annex_i_section`, which 0.2.2 treated as Section A.
  - an Annex I, Section B product with an Art. 50 trigger.
- A declared `5.1.ba` or `5.1.bb` without `assessment_date` keeps the tier
  `prohibited` and now goes to review. With an `assessment_date` before
  2026-12-02 the point no longer sets the tier to `prohibited`: the finding is
  `PROHIBITED.5.1.ba.not_yet_applicable` or its `5.1.bb` counterpart, and the
  report goes to review.
- A consumer that matches the text of the Art. 5(1)(ba)/(bb) screen question
  (`LATER_SCREEN_QUESTION`) must match the new wording quoting Art. 5(1a) and
  (1b); when the question is asked is unchanged.
- For an Annex III point 2 to 8 provider the graph lists
  `high-risk.provider.43.2` (Art. 43(2) internal control) in place of
  `high-risk.provider.44`.
- An Annex I report has one or two more findings: `HIGHRISK.6.1c` on every
  Annex I route and `HIGHRISK.2.13` for Section A.
- New optional profile fields: `assessment_date`, `annex_i_legislation`,
  `intimate_imagery`, `child_sexual_abuse_material` and
  `used_for_financial_fraud_detection` (default false; true or null on a
  `III.5.b` profile raises a review question). No field or value was removed,
  so a profile valid on 0.2.2 stays valid. `annex_i_legislation` takes
  `I.A.2` to `I.A.12` and `I.B.13` to `I.B.21`; `I.A.1`, and an
  `annex_i_section` that contradicts the legislation, exit 2. 0.2.2 and its
  profile schema reject any profile that uses a new field. The new models are
  in `eu_ai_act_classifier.models`; the package root does not export them.
- Both schema files keep their names and `$id`s, which point at `main`, and
  `main` already serves the 0.3.0 versions. A kept copy of the 0.2.2 report
  schema rejects a report with a null `application_date`. Reports from 0.2.2
  validate against the 0.3.0 schema.
- The CLI prints an invalid profile as one `field: message` line per error
  after `error: invalid SystemProfile:`, without pydantic's report and its
  `errors.pydantic.dev` links. The exit code stays 2.
- The MCP tools type `profile` as `SystemProfile`: `list_tools` returns its
  schema, and a validation error names the model
  `classify_ai_systemArguments` and the field as `profile.<field>`. The
  `[mcp]` extra needs `mcp>=1.21.1`.
- `--update` without `--verify-sources` exits 2; 0.2.2 ignored it. From an
  installed package, `--verify-sources --update` exits 2 before any request.
  `python -m eu_ai_act_classifier.verify_sources` exits 1 when a URL fails;
  0.2.2 exited 0.
- Changed text and ids: the limited-risk label reads "transparency duties
  (Art. 50 AIA)"; `regulation` ends with ", as amended by Regulation (EU)
  2026/1744"; the `HIGHRISK.III.5.b` and `HIGHRISK.III.5.c` titles name
  natural persons; with `--advisory`, `guidance.transparency` is
  `guidance.transparency-guidelines`, and Art. 50(2) and (4) profiles also get
  `guidance.transparency-code-of-practice`; the source manifest replaces
  `transparency-guidance` with `art-50-code-of-practice` and
  `art-50-guidelines`.
- `deployer_public_authority` counts only for a profile with the `deployer`
  role, and `significant_change_after_application_date` only where
  Art. 111(2) uses it. Elsewhere the scope notes say the answer "is given, but
  it is not used". Tier, disposition and obligations stay the same.
- `eu-ai-act-local-api` names artifact files with the CLI's slug, for example
  `provider-a-cv-screening.annex-iv-checklist.md`.
- 0.3.0 needs `pydantic>=2.11`; 0.2.2 accepted `>=2.6`.

Changes since 0.2.2.

### Claim ledger checked again in the pinned texts

#### Changed

- The Art. 5(1)(ba) and (bb) screen question (`LATER_SCREEN_QUESTION`,
  #63) quotes Art. 5(1a) and Art. 5(1b) as the findings for those points
  do. It paraphrased Art. 5(1a)(a), leaving out "without requiring
  significant technical modification" and what the safeguards must do,
  and did not name Art. 5(1b). The question asked where only one point
  is unscreened (#66) quotes Art. 5(1a), and for point (ba) Art. 5(1b),
  too. `docs/methodology.md` states Art. 5(1a)(a)(ii) with all its
  elements, and point (7) of `docs/omnibus-coverage.md` names the element
  the question left out. The playground wheel is rebuilt.
- `docs/REGULATORY_CLAIM_LEDGER.md`: the rows whose access date was before
  11 November 2026 were checked again on 16 November 2026 in the Official
  Journal texts pinned in `sources/` and against the code. Each re-checked
  row names the snapshot files and the amending point, and its access date
  moves to 16 November 2026; the row on the GPAI provider guidelines page
  (a Commission page) and the row on fact-specific classification (no
  provision) keep theirs. The rows on Art. 2(2), the machinery move, the
  Art. 2(13) note and the partial encoding describe `annex_i_legislation`
  (#66). The VERIFIED row on the consolidated text no longer calls it the
  current one, since the pinned files cannot show a later consolidation.
  The corrigendum row quotes the English Art. 6(1b) from the pinned text;
  that no English correction exists rests on the HTTP 404 of 14 November
  2026.
  The Stand date moves to 16 November 2026.
- `docs/research/adaptation-plan.md` unparks H7: the Art. 5(1)(ba)/(bb),
  Art. 5(1a)/(1b) and Art. 4 items are built, and their wording was
  checked in the pinned texts.
- The entry for #63 below was missing and is added.

#### Added

- `tests/test_sources.py` checks the quotations in the provision column
  of every CORRECTED and PENDING ledger row that cites a snapshot, as it
  already checked every column of the VERIFIED rows. It also checks that
  `ART_5_1A`, `ART_5_1B` and the two point texts in `LATER_PROHIBITIONS`
  are the Official Journal's words, straight quotation marks aside.
- `tests/test_prohibited.py` checks that both screen questions quote the
  paragraphs.

#### Upgrade notes

- A consumer that matches the text of the screen question must match the
  new wording. When the question is asked is unchanged.

### Omnibus coverage map

#### Added

- `docs/omnibus-coverage.md` lists every amending point of Art. 1 of
  Regulation (EU) 2026/1744 (points (1) to (43)) and its Arts. 2 to 4 with
  the classifier's status for each (encoded, flagged for review, outside the
  classifier's scope, or not encoded) and where the code or the claim ledger
  handles it. Written on 31 October 2026 and checked again row by row
  against the Official Journal text pinned in `sources/` and against the
  code after #14, #59, #55 and #66. `tests/test_omnibus_coverage.py` checks
  that every point has one row, that every file, symbol and id the map's
  last column names exists and that every ledger row it names is in the
  claim ledger. The claim ledger's "in part" row points to the map.
- The corrigendum to Regulation (EU) 2026/1744 (CELEX 32026R1744R(01), OJ L
  2026/90810, 29.9.2026) was read on 14 November 2026. It exists in German
  only and changes one phrase of the German text of Art. 6(1b); the English
  text the classifier relies on is unaffected. A CORRECTED row in the claim
  ledger records it.

### Research notes brought up to date

#### Changed

- `docs/research/2026-10-competitive-landscape.md` marks the Art. 50(2)
  grace-period conflict as resolved (Art. 111(4) AIA: "by 2 December 2026";
  recital (38): a transitional period of four months), and
  `docs/research/adaptation-plan.md` records the same Art. 50(2) check
  and notes that the Art. 5(1)(ba)/(bb) screens are encoded since #30 and
  that #66 tests them element by element, each as a dated update line next
  to the original text.

### MCP tools: typed input schema and read-only annotations

#### Changed

- `classify_ai_system` and `classify_ai_system_text` type their `profile`
  parameter as the `SystemProfile` model instead of `dict`, so `list_tools`
  returns the profile's JSON Schema (field names, the `prohibited_practices`
  and `annex_iii_area` codes, date patterns) and the SDK validates the
  argument before the tool runs; an invalid profile is still a `ToolError`
  naming the field, now as `profile.<field>`. Both tools carry
  `readOnlyHint`/`idempotentHint` true and `destructiveHint`/`openWorldHint`
  false. Verified on the locked mcp (1.30.0) and on the 1.21.1 floor. The
  MCP guide notes that SDK v2 renamed `FastMCP` to `MCPServer` and that v1
  receives critical bug fixes and security patches only; the migration is the
  owner's call.

### Readable CLI validation errors

#### Fixed

- An invalid profile no longer prints pydantic's raw report with
  `errors.pydantic.dev` links. The CLI prints one line per error as
  `field: message`: an enum error lists the allowed values and the value
  given, an unknown field says so and points at `--schema profile`, and a
  date error shows the validator's own message. Exit code stays 2.
  `tests/test_cli.py` covers every error path and the `--strict` exit codes.

### Precision notes from Regulation (EU) 2026/1744

#### Changed

- `placing_on_market_date` and `putting_into_service_date` carry a
  description in the JSON Schema, the field guide and the guided intake: ISO
  dates, and for Art. 111(2) AIA the date the first unit of that type and
  model was placed on the Union market or put into service decides
  (recital 39 of Regulation (EU) 2026/1744).
- The Art. 73 obligation and graph item name both reporting routes: the
  market surveillance authorities of the Member States where the incident
  occurred (Art. 73(1)), or the AI Office where it is exclusively competent
  for the system under Art. 75(1) (Art. 75(1a), inserted by Art. 1,
  point (31)).
- The Art. 72 obligation and graph item say that the post-market monitoring
  plan is part of the Annex IV technical documentation and that the
  Commission's guidance and template are due by 2 September 2027
  (Art. 72(3) as replaced by Art. 1, point (30)).
- The playground footer links the consolidated text of 27 July 2026 instead
  of the 2024 text.
- The provisions above were checked on 14 November 2026 in the Official
  Journal texts pinned in `sources/` (VERIFIED rows of that date in the claim
  ledger).

### Art. 50 Commission documents read

#### Changed

- The two Art. 50 sources that #14 added from search results were read on
  the Commission's site: the pages on 12 and 14 November 2026, the documents
  on 14 November 2026. Both lose `[noch zu verifizieren]` and carry the
  retrieval date 2026-11-14 (`ART_50_SOURCES_RETRIEVED_ON`). The code is
  named as on the Commission's policy page, "Code of Practice on
  Transparency of AI-generated Content" (final text of 10 June 2026;
  Art. 50(2), (4) and (5)). The
  guidelines are the Communication C(2026) 7702 final of 5 November 2026,
  issued under Art. 96(1)(d), and the source links the Commission's library
  page that holds them. The code does not cite Art. 50(7); the guidelines
  refer to it, in points (146) and (147), as a code of practice assessed as
  adequate pursuant to Art. 50(7), and the source note says so. The advisory
  notes drop
  "reported as" and "Not primary-verified". The claim ledger has a CORRECTED
  row of 14 November 2026 with the documents' SHA-256 digests.
- The GPAI provider guidelines source points to the Commission's library page
  for the guidelines instead of an on-the-fly printable PDF link and carries
  the page's title; its retrieval date is unchanged, as the page's last update
  (20 April 2026) predates it.
- `--verify-sources --update` moves all three retrieval dates together, still
  only when every URL is verified.

### Art. 4 AI literacy duty

#### Added

- Every report whose scope is not outside the AI Act lists an Art. 4 AIA
  obligation and a graph item (`literacy.provider.4`, `literacy.deployer.4`,
  dated 2025-02-02) once per provider or deployer role the profile holds,
  whatever the tier: take measures to support the AI literacy of staff and
  other persons operating or using the system on the operator's behalf, in the
  words of Art. 4(1) as replaced by Art. 1, point (5) of Regulation (EU)
  2026/1744 (in force 27 July 2026). A minimal-risk run, such as
  `examples/spam_filter.json`, listed no obligation at all. Importers,
  distributors, authorised representatives and a general-purpose AI model
  provider as such get none. For a Section B product and for a legacy
  high-risk system the item is kept, flagged "Literal reading, confirm with
  counsel" and sent to review, as the Art. 50 items are. So it is for a system
  classified as prohibited: Art. 4 names no exception for it, and a
  prohibition can apply from a later date or be subject to an exception. The
  claim ledger has a VERIFIED row
  (Art. 4(1) and its date, checked on 14 November 2026 in the Official Journal
  texts pinned in `sources/`) and PENDING rows for the Section B reading and
  for a prohibited system.

#### Changed

- The limited-risk tier label reads "transparency duties (Art. 50 AIA)"
  instead of "transparency only", in the text report and the playground,
  since a limited-risk report also lists the Art. 4 duty.
- The system inventory's next action for a system whose only obligation is
  the Art. 4 duty reads "Record the determination, keep the Art. 4 AI
  literacy measures record and monitor source updates." No draft artifact
  covers Art. 4, so such a system is not sent to prepare draft artifacts.

### Pinned source texts

#### Added

- `sources/` holds byte-exact copies of Regulation (EU) 2026/1744, Regulation
  (EU) 2024/1689 (original and the consolidated version of 27 July 2026),
  Directive 2011/93/EU and Implementing Decision (EU) 2026/2274, with each
  file's request URL, retrieval date and SHA-256 in `sources/manifest.json`.
  `tests/test_sources.py` fails if a file no longer matches its digest. The
  classifier does not read these files.
- Each snapshot was compared with its EUR-Lex rendition on 10 November 2026.
  The renditions differ in presentation only (meta tags, scripts, link and
  image targets, a table class); the body text and the element structure are
  identical. The manifest records the EUR-Lex URL, the date, the digest of
  the EUR-Lex response and SHA-256 digests of the text and the structure,
  which the test recomputes offline. `scripts/compare_sources.py` repeats the
  comparison on request: it exits 1 when a text or structure differs and 2
  when a source could not be compared, for example when EUR-Lex answers with
  a bot challenge. The byte digests of the Publications Office responses have
  not been recomputed against a fresh download (see `sources/README.md`).

### Art. 5(1)(ba) and (bb) screen question for generators (#63)

#### Changed

- A profile that records synthetic content or deep fakes
  (`generates_synthetic_content` or `generates_deepfakes`) and declares
  neither `5.1.ba` nor `5.1.bb` raises an open question and goes to review
  instead of being determined; `--strict` exits 1. From 2 December 2026
  (Art. 113, third paragraph, point (a) AIA, as replaced by Art. 1, point
  (40)(a) of Regulation (EU) 2026/1744) Art. 5(1a)(a)(ii) can reach a
  general generator whose purpose is not generating such material, so the
  report asks rather than clears. The risk tier does not change.
- `examples/deepfake_generator.json` ends in `REQUIRES_REVIEW`
  (CASE_STUDY.md); `tests/test_prohibited.py` covers the question and its
  absence where a point is declared or nothing is generated.
- Since #66 the question also offers the element facts in
  `intimate_imagery` and `child_sexual_abuse_material`, is not asked of a
  system already classified as prohibited, and asks about one point where
  the profile screens only the other. Its wording is corrected in the
  entry on the claim ledger re-check above.

#### Upgrade notes

- A consumer that expected `deepfake_generator.json`, or any generator
  profile without the two codes, to be `DETERMINED` gets `REQUIRES_REVIEW`
  until the profile declares a point or records the element facts.

### Art. 5(1)(ba) and (bb) element by element, assessment date, Annex I acts

Ported from #34 onto the models on `main`; the cases in `tests/legal/fixtures/`
were written from the snapshots in `sources/` before the rules.

#### Added

- `intimate_imagery` and `child_sexual_abuse_material` take the element facts of
  Art. 5(1)(ba) and (bb) AIA (true, false or null each). The classifier applies
  Art. 5(1a)(a)(i) and (ii) to placing on the market and putting into service,
  Art. 5(1a)(b) to use and, for point (ba), Art. 5(1b), and reports a point as
  met, not met or UNKNOWN with the facts it turns on. A declared `5.1.ba` or
  `5.1.bb` still stands for the elements; a distributor-only profile stays
  UNKNOWN with review. The interim screen question of #63 stays for generators
  that give neither a code nor the facts.
- `assessment_date` decides whether a rule with a later date applies. Before
  2 December 2026 a met point (ba) or (bb) reads "prohibited from 2 December
  2026" and goes to review; with no date the prohibited tier is kept, with
  review. Each obligation-graph item carries `applies_on_assessment_date`.
- `annex_i_legislation` names the Annex I act (`I.B.21` is machinery under
  Regulation (EU) 2023/1230, Section B, point 21 since Regulation (EU)
  2026/1744) and decides the section. The guided intake asks it and the
  assessment date.
- The Art. 40 graph item names EN 18286:2026, published by Implementing
  Decision (EU) 2026/2274; for an Annex III, point 1 system the Art. 43 item
  states the Art. 43(1) choice between Annex VI and Annex VII. Both readings
  are labelled interpretations (S1, S2) and the items stay review_required.

#### Changed

- An obligation-graph item's `application_date` is null where it turns on an
  unknown placing date (Art. 111(3) and (4)); an open question asks for the
  date unless the assessment date falls on or after both possible dates. An
  assessment date before both still asks, because the day the duty starts
  turns on the missing date.
- An Art. 6(1) product with neither the Annex I act nor the section keeps the
  Section A duties and goes to review instead of being treated as Section A.
- Art. 50 for a Section B product raises an open question, as Art. 5 does.

#### Fixed (review of the port)

- A screened point (ba) or (bb) whose facts affirm the generation as a
  reasonably foreseeable and reproducible outcome or as the deployer's purpose
  but deny that the system generates the material was reported "not met",
  determined. A general generator whose reviewer answered `generates_material`
  false because generating such material is not its purpose passed the screen.
  Where that denial decides the result, the point is now UNKNOWN with an open
  question (Recital 12 of Regulation (EU) 2026/1744), and the field
  descriptions say that a foreseeable outcome or a deployer's purpose counts.
- `applies_on_assessment_date` was true for an unchanged legacy high-risk
  system's Chapter III and Art. 50 items once their date had passed, although
  the scope text and each item's note say that under Art. 111(2) the duties
  attach only after a significant change in design; it is now null there. For
  Chapter III, Section 5 and Chapter IX items it no longer takes the literal
  date's side between 2 August 2026 and the point (c) date.

### Audit fixes on commits merged after verification

#### Fixed

- Art. 6(1c) and Art. 2(13) AIA, which #30 added to the Art. 6(1) finding,
  were shown as verified although no primary source was recorded for them.
  They were read on 11 November 2026 in the Official Journal text of
  Regulation (EU) 2026/1744 (Art. 1, points (8) and (3)), in the snapshot
  pinned with its SHA-256 digest in #40, and the claim ledger now records
  that source. Each is now an `info` finding of its own, `HIGHRISK.6.1c` on
  every Annex I route and `HIGHRISK.2.13` for Section A, with
  `citation_verified` true. Their wording is unchanged; the `HIGHRISK.6.1`
  detail no longer states them, so an Annex I profile has one more finding
  (two for Section A).
- The Art. 111(1) carve-out for Annex X components and its two dates
  (placed on the market or put into service before 2 August 2027, brought
  into compliance by 31 December 2030) had no recorded source either. They
  were read on 11 November 2026 in the Official Journal text of Regulation
  (EU) 2024/1689; Regulation (EU) 2026/1744 amends Art. 111 only in
  paragraphs 2 and 4. The text and the dates are unchanged. Should one of
  the three citations be set back to `verified=False` in `citations.py`, the
  output flags it again: its finding's `citation_verified` turns false, and
  for Art. 111(1) the scope text, the Art. 111(2) graph notes and the
  timeline carry "[noch zu verifizieren]" and `unverified_citations` lists it
  where the scope text or a graph note states the carve-out.
  `tests/test_reread_pinpoints.py` checks this on a copy of the package with
  the three citations set to `verified=False`.
- The claim ledger has a VERIFIED row for each of the three, with the
  Official Journal text, the pinpoint, the access date (11 November 2026)
  and what was read. Each row points to the ledger's list "Sources read on
  11 November 2026", which gives each snapshot's file, request URL,
  retrieval date and SHA-256 digest. EUR-Lex itself could not be read
  from the session (2 and 11 November 2026), so the snapshot is the source;
  the "Stand" date stays 18 October 2026 with a dated note. Before that
  reading this branch showed all three as unverified (PENDING); that state
  was never released.
- Guided intake, playground field guide and the system-profile schema
  (`annex_i_section` and `AnnexISection` descriptions): the Annex I section
  text no longer states the contested literal reading of Art. 2(2) as
  settled. It says that the report keeps Art. 5, Art. 50 and any Annex III
  duties of a Section B product for review, as the PENDING ledger rows on
  Art. 2(2) record.
- The #31 entry below said "I don't know" pauses the run on all three new
  intake questions; the model-date question offers no "I don't know", and a
  blank model date means "not given".
- Guided intake: the number answer (training compute) takes the same inputs
  in the Python and the browser interpreter. Both accept ASCII digits only
  and trim only ASCII whitespace; before, Python also took Arabic-Indic or
  fullwidth digits, each side trimmed characters the other kept (a byte
  order mark in the browser, `\x1c` to `\x1f` and `\x85` in Python), and
  Python raised `ValueError` on `"\x1c5"` instead of reporting the answer as
  missing. The generated fixtures cover these inputs. An answer padded with
  a no-break space (`"\xa05"`), which both accepted before, is now invalid:
  the browser asks for a number again and the Python intake lists the
  question as missing. The question's hint and `docs/FEATURES.md` say so.
- Guided intake in the browser: the wizard passed a typed number through
  `String.prototype.trim()` before the interpreter saw it. An answer padded
  with a no-break space was therefore still accepted there, and one of
  whitespace only was read as blank, although the entry above and
  `docs/FEATURES.md` say that the browser asks for a number again. The
  wizard now hands the text over as typed, so the one grammar decides.
  `tests/playground/wizard.test.mjs` drives the wizard's number page.
- Guided intake: a long text that is not a number was refused in time that
  grew with the square of its length, in the browser's whitespace trim
  (added by the number-grammar entry, two above) and in the number pattern
  of both interpreters (already so on `main`). A share link can hold such a
  text: one of 200 characters kept the playground busy for about two
  seconds on opening, and the limit is 8,000 characters. The trim now scans
  from each end and the pattern reads a run of digits in one way only; it
  takes and refuses the same texts as before. Each interpreter has a test
  with a long text.
- Guided intake in Python: a number answer given as an integer beyond the
  float range (above about 1.8e308, which a JSON integer literal can be)
  raised `OverflowError`. It is now reported as missing, as in the browser,
  where `JSON.parse` reads the literal as Infinity.

#### Decisions

Taken in a Claude Code session on the owner's instruction of 10 November
2026 to answer the open decisions, and applied on 11 November 2026; the
owner has not reviewed the detail. The claim ledger records them too.

- Art. 6(1c), Art. 2(13) and Art. 111(1) are verified on the Official
  Journal snapshots pinned in #40, read on 11 November 2026.
- While Art. 111(1) is unverified, the binding timeline flags it in its note
  but does not add it to `unverified_citations`, which would send every
  report's source status to review. With the citation verified, neither
  applies.
- Number answers stay strict in both interpreters: digits 0 to 9, ASCII
  whitespace trimmed, anything else invalid.
- `HIGHRISK.6.1c` and `HIGHRISK.2.13` stay findings of their own.
- The ledger's "Stand" date stays 18 October 2026, with a dated note for
  the reading of 11 November 2026.

### Art. 49(3) public-authority status asked only of deployers (#54)

#### Changed

- The guided intake asks whether the deployer is, or acts on behalf of, a
  public authority (`deployer_public_authority`, Art. 49(3) AIA) only where
  the profile holds the deployer role on a high-risk route. The six bundled
  high-risk examples that name only a provider no longer open with the
  question unanswered. It still stops the run on "I don't know": for a
  deployer of an Annex III point 5(b) system with no public-authority use
  and no public law body, for one, a missing status reads like "no" and
  raises no review question, so `credit_scoring_deployer.json` still opens
  with it unanswered, and so does `life_insurer_pricing.json` (#14), a
  point 5(c) provider and deployer.
- The engine reads `deployer_public_authority` only for a profile that holds
  the deployer role. For any other profile, the Art. 111(2) caveat on
  systems intended to be used by public authorities turns on
  `public_authority_use` alone. Where a profile in scope gives a status that
  is not used (no deployer role, or a deployer with no high-risk route or
  with a prohibited practice screened), the scope check now says so:
  "deployer_public_authority is given, but it is not used".
- For a profile without the deployer role that gave `true` and does not
  assert public-authority use, the report no longer shows the text the
  status triggered, as for a profile that leaves it unset:
  - with a date before the Chapter III date, the caveat "A public-authority
    deployer is asserted: confirm whether the system is intended to be used
    by public authorities", with the conditional Art. 111(2)
    public-authority deadline that follows it, in the transitional status,
    the Art. 111(2) open question and the Art. 111(2) graph items, and,
    with an Art. 50 trigger, in the `TRANSPARENCY.50` finding and the
    Art. 50 item notes; the legacy notes on the other high-risk items lose
    their clause on that deadline ("as the public-authority deployer
    suggests");
  - with no date, the whole Art. 111(2) paragraph of the transitional
    status: the Chapter III date to compare with, the significant-change
    condition and the "Literal reading, confirm with counsel" flag, or, for
    an Annex I, Section B product without an Annex III area, the Section B
    Art. 111(2) statement.

  No profile's tier, disposition, obligations, finding rule ids or
  severities, graph item ids, dates or review statuses, or number of open
  questions changes (compared over 221,184 synthetic profiles).
- A high-risk profile without the deployer role that gives the status, as
  share links and drafts saved from the guided mode before this change do
  (the guided mode required an answer), now opens only in the JSON editor:
  the guided mode would drop the answer. There it classifies as described
  above.

### CI trust signals and dependency floors

#### Changed

- CI runs the Python suite on 3.13 and 3.14, gates statement coverage at 94 %
  (the integer part of the measured total; `pytest-cov` joins the `dev`
  extra), runs the suite at the lowest declared dependency versions
  (`uv run --isolated --resolution lowest-direct`) and installs the built
  wheel into a clean environment to run the CLI, expecting exit 1 for
  `examples/social_scoring.json --strict`. Each job has a timeout, checkouts
  do not persist credentials, and a new push cancels the superseded run of a
  pull request.
- The declared `pydantic` floor rises from `>=2.6` to `>=2.11`, the lowest
  version the lowest-direct job passes with on Python 3.13; the `mcp` extra
  floor (1.21.1) passes there too. The package classifiers add Python 3.14.

### Art. 111(2) change answer asked only where it is used (#43)

#### Changed

- The guided intake asks whether the system changed significantly
  (`significant_change_after_application_date`) only for a high-risk system,
  with no prohibited practice, placed on the market or put into service
  before its Chapter III date. There "I don't know" records `null`, which
  raises the Art. 111(2) open question, so the run goes to review instead of
  stopping. Profiles without such a date, the bundled examples among them, no
  longer open with the question unanswered.
- Where Art. 111(2) cannot use a given change answer (no date before the
  Chapter III date, no high-risk route, a Section B product without an
  Annex III area, or a prohibited practice), the scope check states that the
  answer is not used instead of echoing it. For a prohibited practice, the
  Art. 111(2) "not applied" sentence now appears only when a date or
  public-authority use is given.
- A profile that gives a change answer without such a date, as share links
  and drafts saved from the guided mode before this change do, now opens
  only in the JSON editor: the guided mode would drop the answer. It
  classifies the same there.

### Binding result apart from guidance notes in the playground (#38)

#### Changed

- The playground groups findings, open questions, obligations, the graph, the
  timeline, scope and sources under "Binding result". Commission guidance
  notes, when the toggle was on for the run, follow in a separate box headed
  "Nonbinding guidance notes" that says they change no tier, disposition or
  obligation.
- Links and primary actions use their own accent colour (`#5a3e85`); the
  limited-risk tier keeps `#2c4f7c`, and nonbinding source badges are grey.

### Share links in the playground (#39)

#### Added

- "Create share link" writes the profile, compressed with `deflate-raw` and
  base64url-encoded, into the address after `#p1.` (`#j1.` without
  compression). The fragment is not sent to a server. Opening a link
  validates the profile, opens it on the check-answers page and never
  classifies it on its own. Links above 8,000 characters are refused in favour
  of the JSON download, and a decoded profile above 1 MB is refused. A note
  next to the button says the link is not encrypted and that history sync
  and chat services keep it. In guided mode the link carries the answers
  once every question is answered.

### Source retrieval dates move only after every URL passes

#### Fixed

- `--verify-sources --update` set both source retrieval dates in
  `citations.py` to today even when source URLs failed, and those dates reach
  every report's source manifest. It now changes nothing unless every URL
  answers with a 2xx status; otherwise it names the failed URLs and exits 1.
  A 4xx or 5xx answer and a network error both count as failures.
- `--update` runs only in a source checkout: a `pyproject.toml` naming
  `eu-ai-act-classifier` next to `src/eu_ai_act_classifier/citations.py`.
  From an installed package it exits 2 before any request, where it used to
  rewrite the installed `citations.py` and write `dist/verified_sources.json`
  three directories above it.
- `--update` without `--verify-sources` is a usage error (exit 2); it was
  ignored.
- `python -m eu_ai_act_classifier.verify_sources` exits 1 when a URL fails and
  2 outside a source checkout; it always exited 0.

### Source URL check names itself

#### Changed

- `--verify-sources` and `python -m eu_ai_act_classifier.verify_sources` sent
  the User-Agent of desktop Chrome. They now send
  `eu-ai-act-classifier/<version> (+https://github.com/sebastianfoerste/eu-ai-act-classifier)`,
  with the version of the installed package.

### Source check reports bot challenges as unverified

#### Fixed

- `--verify-sources` counted every 2xx answer as a pass. EUR-Lex, which
  serves both binding sources, answers the check with 202 and an AWS WAF
  challenge page (`x-amzn-waf-action: challenge`), so both URLs passed
  although the document was never reached, and `--update` would have dated
  both binding sources from that page. A 202 answer, or a 2xx answer with AWS
  WAF's challenge header or script names, is now unverified: its line reads
  `[202 unverified]` with the reason, a closing line counts the outcomes (for
  example `7 verified, 2 unverified, 0 failed of 9 source URLs`), and a
  `warning:` line on stderr names the unverified URLs. Unverified URLs alone
  do not change the exit code: `--verify-sources` exits 0 unless a URL
  failed. `--update` moves no date unless every URL is verified, and exits 1
  otherwise. 4xx and 5xx answers and network errors still fail.

### Web cockpit dependencies pinned

#### Changed

- `web/package.json` names the versions `web/package-lock.json` already
  resolved (for example `next` 16.2.7 and `react` 19.2.7) instead of
  `"latest"`, so `npm install` outside the lockfile cannot pull a new major
  version. Dependabot proposes weekly npm updates for `web/`, minor and patch
  grouped.

### Web cockpit audit fixes within the pinned versions

#### Fixed

- `npm audit fix`, without `--force`, updated `web/package-lock.json` only,
  on top of the Dependabot updates to `next` 16.4.3 and `vitest` 5.0.5: as
  dependencies of other packages, `nanoid` 3.3.20, `source-map-js` 1.2.2 and
  `baseline-browser-mapping` 2.11.34. `npm audit` reports 3 vulnerabilities
  instead of 6. The `postcss` advisories remain: they need a `postcss`
  override above 8.5.22, and `next` and `vite` are listed only because they
  use that `postcss`.

### Web cockpit postcss override removed

#### Fixed

- `web/package.json` forced every `postcss` in the cockpit to 8.5.10 through
  `overrides`. The override dates from the first commit, when `next` 16.2.7
  pinned `postcss` 8.4.31. `next` 16.4.3 pins `postcss` 8.5.23 and `vite`
  8.3.5 asks for `^8.5.30`, so the override held both below their own
  versions and inside the three `postcss` advisories up to 8.5.22. Without
  it, `next` uses 8.5.23 and `vite` 8.5.32, and `npm audit` reports 0
  vulnerabilities instead of 3.

### Web cockpit stops tracking next-env.d.ts

#### Changed

- `web/next-env.d.ts` is no longer in Git, and `.gitignore` lists it. Next.js
  writes the file on `next dev`, `next build` and `next typegen`; `next build`
  with Next.js 16.4.3 added a line to the committed copy, so every build left
  the working tree changed. The Next.js TypeScript docs say to add the file to
  `.gitignore` and remove it from Git, and the `create-next-app` templates
  ignore it. `npm run build` writes it before its type check, and `npm test`
  does not need it.

### Web cockpit errors and artifact filenames

#### Fixed

- The cockpit's classify, artifacts, dossier and collaboration routes answered
  HTTP 400 for every failure of the Python bridge, including timeouts and
  crashes. They now answer 400 only when `local_api` rejects the input (exit 2
  with a JSON error line) and 500 otherwise; a stale write to the
  collaboration workspace still answers 409, and a request body that is not
  JSON still answers 400.
- The local API named artifact files after the raw system name, so a name such
  as "Provider A / CV screening" went into the download name unchanged. It
  now uses the slug the CLI's `--artifacts-dir` files use, for example
  `provider-a-cv-screening.fria.md`.

### MCP extra requires mcp 1.21.1

#### Fixed

- The `[mcp]` extra allowed `mcp>=1.2,<2`, but every `mcp` release from 1.2.0
  to 1.21.0 imports `eval_type_backport` from pydantic's internals, which
  pydantic 2.14 removed. With such an `mcp` and pydantic 2.14 or later,
  `mcp.server.fastmcp` does not import and the server exits with the install
  hint. The extra now requires `mcp>=1.21.1,<2`, and the hint names that
  range. `tests/test_mcp_server.py` passes with `mcp` 1.21.1 and with 1.30.0,
  the version `uv.lock` pins.
- `tests/test_docs.py` finds the server's tools by their `@server.tool(...)`
  decorator with or without arguments; it matched only `@server.tool()`. A new
  test checks that it finds the same tools as the server registers.

### eu-reg-mcp recommendation (#13)

#### Changed

- When `mcp.server.fastmcp` does not import, the MCP server's exit message
  still gives the pip, uvx and clone commands, and now ends by recommending
  eu-reg-mcp for Claude Code and Claude Desktop:
  `uvx --python 3.13 --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp`.
- The README, `docs/surfaces.md` and `docs/mcp-configuration-guide.md`
  recommend eu-reg-mcp ahead of this package's own server. The guide and
  `docs/surfaces.md` also give the clone command
  `uv run --extra mcp eu-ai-act-classifier-mcp`.
- Every uvx command for eu-reg-mcp, and the exit message's uvx command for
  this package's server, passes `--python 3.13`, as the README and the
  guides already did for this package's server. eu-reg-mcp, the linter and
  this classifier require Python 3.13 or later; without the flag, uvx fails
  with `No solution found` when the default Python is older.

### Legal mapping corrections (#14)

These entries come from #14. After a first check in a GitHub mirror of
EUR-Lex, these provisions were checked on 11 November 2026 against the
Official Journal texts pinned in `sources/`, each in a VERIFIED row of the
claim ledger of that date: Art. 6(3), third subparagraph; Annex III, point
5(b) and (c); Art. 43(2) and Art. 43(3), last subparagraph; Art. 50(7); Art. 96(1)(d); and the titles
and dates in the regulation string. The check confirms wording and pinpoints.
The 2026-08-02 dating of the new Art. 43(2) item rests on the reading of
Art. 113 of 18 October 2026 (the CORRECTED and PENDING Section 5 rows). No
lawyer has adopted the conclusions, so confirm them with counsel before
reliance. The two Art. 50 Commission sources could not be opened then and
kept `[noch zu verifizieren]` until their documents were read on 14 November
2026 ("Art. 50 Commission documents read", above).

#### Added

- `used_for_financial_fraud_detection` (default `false`): point 5(b) excepts
  AI systems used for the purpose of detecting financial fraud. On a point
  5(b) profile, `true` or `null` adds an open question and the system stays
  high-risk, so the disposition is `REQUIRES_REVIEW` and `--strict` exits 1.
  The guided intake asks it only for a point 5(b) profile; "I don't know"
  records `null`.
- New example `examples/life_insurer_pricing.json` (Annex III point 5(c),
  provider and deployer, with profiling) and two worked examples in
  `docs/worked-examples/`, a bank's credit-scoring model and a life insurer's
  pricing model.

#### Changed

- Annex III labels as in Annex III: point 5(b) is "Creditworthiness
  evaluation and credit scoring of natural persons" and point 5(c) "Risk
  assessment and pricing for natural persons in life and health insurance".
  The 5(b) and 5(c) finding titles and the display labels from `labels.py`
  (#31) change with them.
- For Annex III points 2 to 8 the provider graph has
  `high-risk.provider.43.2` (Art. 43(2) AIA, internal control under Annex VI
  without a notified body, `review_required`) instead of
  `high-risk.provider.44` (Art. 44 certificate). Integrations that read
  `high-risk.provider.44` for these systems will no longer find it. Where the
  Chapter III duties apply, Annex III point 1, `III.unsure` and an Annex I
  product in Section A, or whose section is not given (also an Annex I
  safety component off the Art. 6(1) route, where the section is not asked),
  keep the Art. 44 item:
  the last subparagraph of Art. 43(3), as replaced by Regulation (EU)
  2026/1744, sends a system covered by Section A legislation that also falls
  under Annex III to that legislation's procedure. It names Section A only, so
  a Section B product on the Art. 6(1) route in points 2 to 8 gets the
  Art. 43(2) item. The new item is dated like the other Section 5 items: 2026-08-02 with
  "Literal reading, confirm with counsel".
- CI's coverage floor rises from 94 % to 95 % (`--cov-fail-under=95`), the
  integer part of the measured total of 95.02 %.
- The profiling rule is cited as "Art. 6(3), third subparagraph, AIA"
  instead of "Art. 6(3) subpara. 2 AIA".
- Art. 50 sources: the placeholder "Transparency guidance tracker" is
  replaced by the Code of Practice on marking and labelling of AI-generated
  content (Art. 50(7) AIA, `art-50-code-of-practice`) and the Commission
  guidelines on the Art. 50 transparency obligations (Art. 96(1)(d) AIA,
  `art-50-guidelines`). Their titles, dates and URLs came from search results
  only, so both carried `[noch zu verifizieren]` until the entry "Art. 50
  Commission documents read", above. With `--advisory`, every
  Art. 50 profile gets the note `guidance.transparency-guidelines` (was
  `guidance.transparency`), and profiles under Art. 50(2) or (4) also get
  `guidance.transparency-code-of-practice`.
- The regulation named in every report ends with "as amended by Regulation
  (EU) 2026/1744".

## 0.2.2 (2026-10-23)

#### Upgrade notes

Profiles and CI jobs that pass on 0.2.1 can fail on 0.2.2. Pinning
`eu-ai-act-classifier==0.2.1` keeps the 0.2.1 behaviour while you update them.

- Dates must be ISO dates (YYYY-MM-DD). A `placing_on_market_date` or
  `putting_into_service_date` such as "March 2026" is now rejected: the CLI
  exits 2, and `SystemProfile` and the MCP tools raise a pydantic
  `ValidationError`. 0.2.1 accepted any string.
- `--strict` now exits 1 for three kinds of profile that 0.2.1 reported as
  `DETERMINED` (exit 0). Each now has an open question, so the disposition is
  `REQUIRES_REVIEW`:
  - a high-risk system whose `placing_on_market_date` or
    `putting_into_service_date` is before its Chapter III date (2 December 2027
    with an Annex III area, 2 August 2028 for an Annex I product without one).
    Answering `significant_change_after_application_date` closes the question.
  - a deployer of an Annex III system other than point 2 that sets
    `public_authority_use` or `deployer_public_law_body: true`, or that deploys
    a point 5(a), 6, 7 or 8(a) system (Art. 49(3)). Setting the new
    `deployer_public_authority` field closes the question.
  - a general-purpose AI model dated only by `placing_on_market_date`. Giving
    the new `gpai_model_placing_on_market_date` closes the question.
- The high-risk graph items for Arts. 40 to 44, 47 and 48, Art. 49 where it
  applies, and Arts. 72 and 73 now carry `application_date` 2026-08-02 instead
  of 2027-12-02 (Annex III) or 2028-08-02 (Annex I), and all of them are
  `review_required`.
- Art. 49 registration, as an obligation and a graph item, is no longer listed
  for a system that is high-risk only as an Annex I product, or for an
  Annex III point 2 (critical infrastructure) system. 0.2.1 listed it for every
  high-risk provider.

Changes since 0.2.1. The release also carries #25 and #27 to #29, described
in their pull requests: the Annex III coverage matrix, JSON Schemas (printed by
`eu-ai-act-classify --schema profile` or `--schema report`; the classifier
ignores a `"$schema"` key in a profile), CI hardening and contributor files
(#25), a shorter README with the detail moved into `docs/` (#27), absolute
GitHub links in the README for PyPI (#28) and the playground screenshot (#29).

### Regulation (EU) 2026/1744 dating of the high-risk items (#26)

Checked on 18 October 2026 against Art. 113 and Art. 111 in the consolidated AI
Act of 27 July 2026 and Art. 1, points (39) and (40) of Regulation (EU)
2026/1744. Items whose dating is contested carry
"Literal reading, confirm with counsel".

#### Changed

- Corrected dating under Regulation (EU) 2026/1744. 0.2.1 gave every
  high-risk graph item the deferred date: 2 December 2027 for Annex III,
  2 August 2028 for Annex I. Art. 113, third paragraph, point (c), as replaced
  by Art. 1, point (40) of Regulation (EU) 2026/1744, defers only Chapter III,
  Sections 1, 2 and 3, which keep those dates. The Chapter III, Section 5
  items (Arts. 40 to 44, 47 and 48, and Art. 49 where it applies) and the
  Chapter IX items (Arts. 72 and 73) now carry 2 August 2026, the general date
  (Art. 113, second paragraph). Each is `review_required`, and its
  `application_date_note`, flagged "Literal reading, confirm with counsel",
  names the deferred date that applies if the duty is read as following the
  deferral.
- A system that is an Annex I product and also falls in an Annex III area is
  classified under Art. 6(2) and Annex III, so its Sections 1 to 3 items take
  2 December 2027 (point (c)(i)) instead of 2 August 2028.
- Art. 49(1) registration, as an obligation and a graph item, covers only
  Annex III systems other than point 2 (and where the Annex III point is not
  settled); 0.2.1 listed it for every high-risk provider. A point 2 system gets
  a `review_required` Art. 49(5) item (registration at national level)
  instead, and a provider of an Annex III system asserting an Art. 6(3)
  derogation condition without profiling gets a `review_required` Art. 49(2)
  item.
- The Art. 6(4) assessment work product (`art-6-4-assessment`) draws on the
  Art. 49(2) graph items instead of the Art. 49 item: under Art. 6(4), a
  provider relying on Art. 6(3) registers under Art. 49(2).
- The binding timeline is sorted by date and cites Art. 113 by paragraph and
  point ("Art. 113, third paragraph, point (a) AIA" instead of
  "Art. 113(a) AIA"). The 2 December 2027 and 2 August 2028 entries name
  Chapter III, Sections 1, 2 and 3 (except Art. 6(5)) instead of "the
  relevant" high-risk provisions, and the general-date entry names the
  contested Section 5 and Chapter IX reading. The binding sources record
  `retrieved_on` 2026-10-18 instead of 2026-08-26.
- The proof contract (`contracts/eu-ai-act-classifier.proof.v1.json`) records
  `sourceCurrencyDate` 2026-10-18 instead of 2026-08-26.

#### Added

- A binding timeline entry dated 2 December 2026 under Art. 113, third
  paragraph, point (a) AIA, as replaced by Art. 1, point (40) of Regulation
  (EU) 2026/1744: Art. 5(1), first subparagraph, points (ba) and (bb), and
  Art. 5(1a) and (1b) apply from that date, not from 2 February 2025. The
  2 February 2025 entry for Chapters I and II names the exception.
- Binding timeline entries for Arts. 102 to 110 (27 July 2026, point (d)),
  Art. 50(2) for generative systems placed on the market before 2 August 2026
  (2 December 2026, Art. 111(4)), general-purpose AI models placed on the
  market before 2 August 2025 (2 August 2027, Art. 111(3)) and Chapter III,
  Section 4, Chapter VII, Chapter XII (except Art. 101) and Art. 78
  (2 August 2025, point (b)).
- Art. 111(3) and (4) on the graph: the GPAI items take 2 August 2027 where
  the model was placed on the market before 2 August 2025 (#30 adds the
  model's own date, below), and the Art. 50(2) item takes 2 December 2026
  where `placing_on_market_date` precedes 2 August 2026, each with a note.
- `application_date_note` on obligation graph items, also in the report JSON
  Schema.
- The text report and the review dossier print an item's
  `application_date_note` on the line under the graph item, and the draft work
  products add it to the item's line, so text output and goldens made with
  0.2.1 differ.

#### Fixed

- `placing_on_market_date` and `putting_into_service_date` must be ISO dates
  (YYYY-MM-DD). 0.2.1 accepted any string, such as "March 2026", which the
  Art. 111 checks cannot compare with a cut-off date.
- The example inventory (`eu-ai-act-local-api inventory`) warns about an
  example profile that fails validation, such as one with a non-ISO date,
  naming the file and the invalid fields. 0.2.1 dropped such a profile
  silently.

### Digital Omnibus follow-ups to #26 (#30)

The entries below follow up the Regulation (EU) 2026/1744 dating work (#26),
checked against the consolidated AI Act of 27 July 2026 and Regulation (EU)
2026/1744. Items whose dating or scope is contested carry
"Literal reading, confirm with counsel".

#### Added

- Art. 111(2) AIA: a high-risk system whose `placing_on_market_date` or
  `putting_into_service_date` precedes its Chapter III date (2 December 2027
  for Annex III, 2 August 2028 for an Annex I product without an Annex III
  area) gets an Art. 111(2) graph item for
  each operator role, as Art. 111(2) applies to "operators". A role listed
  twice gives one item. Only the provider and deployer items carry the second
  sentence of Art. 111(2): with `public_authority_use` they take the necessary
  steps to comply by 2 August 2030 and, unless a significant change is
  asserted, are dated then; with `deployer_public_authority` alone they ask to
  confirm that use. 2 August 2030 is a new entry in the binding timeline.
- Art. 111(2) uses the Chapter III date twice: the system must be placed on
  the market or put into service before it, and a significant change in design
  counts "as from that date". Which date is meant is contested, so every legacy
  result and every Art. 111(2) check without a date, open question included,
  carries "Literal reading, confirm with counsel". An asserted significant
  change is not dated; the flag says that on the date used here it counts only
  if it was made on or after that date. The legacy note on an item dated
  2 August 2026 says that the duty does not bind the unchanged system from that
  date either.
- Art. 6(3) AIA: for an Annex I product (not Section B) also in an Annex III
  area with an asserted derogation, the Art. 111(2) check states that the
  Chapter III date is 2 August 2028 if the derogation is established. Where
  only that date would make the system a legacy system, the statement carries
  "Literal reading, confirm with counsel" (on the general date it is no legacy
  system on either route) and an open question asks to confirm the
  derogation.
- `annex_i_section` (`A` or `B`): a Section B product with no Annex III area
  stays high-risk under Art. 6(1) but gets the Art. 2(2) provisions (Art. 6(1),
  Art. 60a and Arts. 102 to 112) instead of the Chapter III duties, and its
  high-risk draft work products (Annex IV checklist, FRIA, post-market
  monitoring plan and serious-incident register) say that Art. 2(2) does not
  require them.
  Machinery (Regulation (EU) 2023/1230) is now a Section B product. A section
  given without the Art. 6(1) route is reported as unused.
- `AnnexISection` is exported from the package root.
- The local API `schema` payload (`eu-ai-act-local-api schema`) lists the
  Annex I sections as `annex_i_sections`.
- Art. 2(2) lists neither Art. 5 nor Art. 50, so for every Section B product,
  Annex III area or not, the report keeps both as the conservative reading,
  flagged "Literal reading, confirm with counsel": Art. 5 in the finding and an
  open question, Art. 50 in the `TRANSPARENCY.50` finding and on
  `review_required` graph items. A Section B product also in an Annex III area
  keeps the Annex III duties; the Art. 6(1) finding and the `review_required`
  Art. 2(2) item carry "Literal reading, confirm with counsel".
- Art. 49(3) AIA: registration of use by deployers that are, or act on behalf
  of, public authorities or Union institutions, bodies, offices or agencies,
  for Annex III systems other than point 2, as an obligation and a flagged
  graph item. The new `deployer_public_authority` field records the deployer's
  own status. Where it is unset, the item is inferred for review, with an open
  question, if `public_authority_use` is set or the Annex III point describes
  use by or on behalf of public authorities (points 5(a), 6 and 7). Point 8(a),
  whose alternative dispute resolution limb may be private, and a
  `deployer_public_law_body: true` answer raise the question only.
- Art. 49(5) AIA: a point 2 deployer that is a public authority
  (`deployer_public_authority`) or, with that status unset, of a system
  intended to be used by public authorities gets an item saying that point 2
  systems are registered at national level.
- Art. 26(8) AIA: where the Art. 49(3) item applies, the Art. 26 item adds that
  a public-authority deployer does not use an unregistered system and informs
  the provider or the distributor. It takes the Art. 26 date, as a Chapter III,
  Section 3 duty.
- `gpai_model_placing_on_market_date`: the model's own date for Art. 111(3).
  `placing_on_market_date` stays the AI system's date for Art. 111(2) and (4).
  A model date later than the system date raises an open question.
- Prohibited-practice codes `5.1.ba` and `5.1.bb` (Art. 5(1)(ba) and (bb)),
  with findings that quote the point and say the ban applies from
  2 December 2026, and the example `examples/intimate_imagery_generator.json`.
  The advisory note on the Commission prohibited-practices guidance works out
  from its retrieval date whether the guidance predates the new points.
- A test that keeps the adapter manifest's `sourceCurrencyDate` equal to the
  proof contract's.

#### Changed

- A high-risk profile whose `placing_on_market_date` or
  `putting_into_service_date` precedes its Chapter III date now reports
  disposition `REQUIRES_REVIEW`, so `--strict` exits 1. Where 0.2.1 reported
  `DETERMINED` and exited 0, CI runs that gate such profiles with `--strict`
  will start failing. Answering
  `significant_change_after_application_date` (true or false) removes the open
  question, so `--strict` passes again unless another question is open, but
  the flagged graph items stay `review_required`.
- Every high-risk graph item of such a legacy system carries an Art. 111(2)
  note (the duty attaches only once the design changes significantly, and for
  providers and deployers of a system intended to be used by public
  authorities by 2 August 2030 in any case), flagged
  "Literal reading, confirm with counsel" and set to `review_required`. An
  asserted significant change removes the note.
- Unless a significant change is asserted, the `TRANSPARENCY.50` finding and
  the Art. 50 graph items of such a legacy system are flagged
  "Literal reading, confirm with counsel": on its wording Art. 111(2) would
  apply Art. 50 only after a significant change, and the report keeps the
  Art. 50 dating as the conservative reading. The flagged items are
  `review_required` (`determined` in 0.2.1).
- The Art. 6(1) finding states Art. 6(1c) (a third-party conformity assessment
  required solely for risks other than health and safety does not meet
  Art. 6(1)(b)) and an Annex I section note: the Art. 2(13) delegated acts for
  Section A, or, with no section given, that the product is treated as
  Section A and what Art. 2(2) means for a Section B product.
- The Art. 49(1) and (2) registration items (#26, above) for Annex III
  points 6 and 7, and point 1 where used in law enforcement, migration, asylum
  or border control management, add the Art. 49(4) sentence: the registration
  in the secure non-public section includes only the Annex VIII and Annex IX
  information Art. 49(4) lists, and only the Commission and the Art. 74(8)
  authorities have access to it.
- A deployer of an Annex III point 5(a), 6, 7 or 8(a) system that leaves
  `deployer_public_authority` unset, and a deployer that answers
  `deployer_public_law_body: true` for an Annex III system other than point 2,
  now gets an Art. 49(3) open question (for points 5(a), 6 and 7 with the
  inferred item), so a profile that 0.2.1 reported as `DETERMINED` can become
  `REQUIRES_REVIEW` and fail `--strict`.
- A GPAI profile that gives only `placing_on_market_date` is still dated by it,
  as in #26, but its Chapter V items are now `review_required` and an open
  question asks for the model's own date, so the disposition becomes
  `REQUIRES_REVIEW` and `--strict` exits 1 where 0.2.1 reported `DETERMINED`
  and exited 0.
- The scope transitional status reports the Art. 111 checks the facts touch
  instead of generic wording: the placing-on-market and putting-into-service
  dates against the system's Chapter III date (Art. 111(2), naming the
  Art. 111(1) carve-out for Annex X components), the model date (Art. 111(3))
  and, for a system generating synthetic content, the placing-on-market date
  for Art. 50(2) (Art. 111(4)). A profile that gives only the model date gets
  the Art. 111(3) check.
- `docs/integrations/eu-ai-act-classifier.adapter.v1.json`: `sourceCurrencyDate`
  is 2026-10-18, as in the proof contract.
- `docs/demo.png` is rendered from real CLI output by the new
  `scripts/render_demo.py`; it used to be a copy of the cockpit screenshot.
  `docs/cockpit.png` is a full-page headless capture of the production build,
  with the scroll bars of the scrolling lists visible and reduced to 256
  colours. Both recipes are in `docs/TESTING.md`.

#### Fixed

- JSON Schema: date fields carry the pattern `^[0-9]{4}-[0-9]{2}-[0-9]{2}$`
  next to `format: date`, which many validators skip, so schema validation
  also rejects forms such as "March 2026". The new fields and
  `significant_change_after_application_date` have descriptions; the latter
  names both candidate Chapter III dates.

### Guided intake, label catalog and cockpit styling (#31)

#### Added

- Guided intake in the browser playground: one question per page, an "I don't know" answer that routes to review or pauses the run for counsel, and a check-answers page listing every defaulted value. Questions, order and skip conditions come from `src/eu_ai_act_classifier/intake.py`; the JSON editor remains as a second mode.
- The guided intake also asks the fields the entries above add: the Annex I section on the Art. 6(1) route, the general-purpose AI model's own date, and the deployer's public-authority status (Art. 49(3)) on a high-risk route. "I don't know" pauses the run on the Annex I section and the deployer's status; a blank model date means "not given" (dated by the system's date for review, or noting the Art. 111(3) transition).
- `labels.py`: one display-label catalog for the playground field guide and the cockpit, using the pinpoints and titles in `catalog.py`.
- Competitive research, a feature matrix, a design teardown and an adaptation plan in `docs/research/`, and architecture decision records in `docs/adr/`.

#### Changed

- The cockpit shows catalog labels (for example "Annex III(5)(b): Creditworthiness evaluation and credit scoring") instead of mechanically formatted values.
- The cockpit portfolio (`/workspace`) and self-assessment pages use plain CSS classes instead of Tailwind classes, which were not installed; self-assessment inputs have labels.

#### Unchanged

- Classification rules, citations, application dates, examples and goldens. No new legal claim was added: the article shown under each guided question is one the engine already cites, and `tests/test_intake.py` enforces that.

### Collaboration workspace digest (#33, #36)

#### Fixed

- The cockpit's collaboration workspace no longer reads as stale when the next action comes in a later second: the inventory digest leaves out the `generatedAt` stamps the inventory takes from the clock on every rebuild (#33). `tests/test_collaboration_workspace.py` checks that a saved workspace still loads against the same inventory rebuilt a second later (#33), and `tests/test_local_api.py` runs two collaboration actions through `local_api.main` across a clock tick (#36).
