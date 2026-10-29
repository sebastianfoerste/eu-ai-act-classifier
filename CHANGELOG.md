# Changelog

Notable changes to the classifier. Earlier releases are described in their
pull requests.

## Unreleased

Changes since 0.2.2.

### Art. 111(2) change answer asked only where it is used

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
- The guided intake also asks the fields the entries above add: the Annex I section on the Art. 6(1) route, the general-purpose AI model's own date, and the deployer's public-authority status (Art. 49(3)) on a high-risk route. "I don't know" pauses the run on all three.
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
