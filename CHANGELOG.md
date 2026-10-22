# Changelog

Notable changes to the classifier. Earlier releases are described in their
pull requests.

## Unreleased

Changes since 0.2.1. Main also carries #25 to #29, described in their pull
requests: the Annex III coverage matrix, JSON Schemas, CI hardening and
contributor files (#25), the Art. 113 dating of the Chapter III, Section 5 and
Chapter IX high-risk items (#26), a shorter README with the detail moved into
`docs/` (#27), absolute GitHub links in the README for PyPI (#28) and the
playground screenshot (#29).

The Added, Changed and Fixed entries below follow up the Regulation (EU) 2026/1744 dating work (#26),
checked against the consolidated AI Act of 27 July 2026 and Regulation (EU)
2026/1744. Items whose dating or scope is contested carry
"Literal reading, confirm with counsel".

### Added

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

### Changed

- A high-risk profile whose `placing_on_market_date` or
  `putting_into_service_date` precedes its Chapter III date now reports
  disposition `REQUIRES_REVIEW`, so `--strict` exits 1. Where main reported
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
  `review_required` (`determined` on main).
- The Art. 6(1) finding states Art. 6(1c) (a third-party conformity assessment
  required solely for risks other than health and safety does not meet
  Art. 6(1)(b)) and an Annex I section note: the Art. 2(13) delegated acts for
  Section A, or, with no section given, that the product is treated as
  Section A and what Art. 2(2) means for a Section B product.
- The existing Art. 49 registration items (Art. 49(1) and (2)) for Annex III
  points 6 and 7, and point 1 where used in law enforcement, migration, asylum
  or border control management, add the Art. 49(4) sentence: the registration
  in the secure non-public section includes only the Annex VIII and Annex IX
  information Art. 49(4) lists, and only the Commission and the Art. 74(8)
  authorities have access to it.
- A deployer of an Annex III point 5(a), 6, 7 or 8(a) system that leaves
  `deployer_public_authority` unset, and a deployer that answers
  `deployer_public_law_body: true` for an Annex III system other than point 2,
  now gets an Art. 49(3) open question (for points 5(a), 6 and 7 with the
  inferred item), so a profile that main reported as `DETERMINED` can become
  `REQUIRES_REVIEW` and fail `--strict`.
- A GPAI profile that gives only `placing_on_market_date` is still dated by it,
  but its Chapter V items are now `review_required` and an open question asks
  for the model's own date, so the disposition becomes `REQUIRES_REVIEW` and
  `--strict` exits 1 where main reported `DETERMINED` and exited 0.
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

### Fixed

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

### Legal mapping corrections (#14)

These entries come from #14, not from the #26 follow-ups above. The provisions
were checked against the consolidated AI Act of 27 July 2026 in a GitHub
mirror of EUR-Lex, not on EUR-Lex itself (see Honest limits in
`docs/overview.md`).

- Annex III labels as in Annex III: point 5(b) is "Creditworthiness
  evaluation and credit scoring of natural persons" and point 5(c) "Risk
  assessment and pricing for natural persons in life and health insurance".
  The 5(b) finding title and the display labels from `labels.py` (#31)
  change with it.
- `used_for_financial_fraud_detection` (default `false`): point 5(b) excepts
  AI systems used for the purpose of detecting financial fraud. On a point
  5(b) profile, `true` or `null` adds an open question and the system stays
  high-risk, so the disposition is `REQUIRES_REVIEW` and `--strict` exits 1.
  The guided intake asks it only for a point 5(b) profile; "I don't know"
  records `null`.
- For Annex III points 2 to 8 the provider graph has
  `high-risk.provider.43.2` (Art. 43(2) AIA, internal control under Annex VI
  without a notified body, `review_required`) instead of
  `high-risk.provider.44` (Art. 44 certificate). Integrations that read
  `high-risk.provider.44` for these systems will no longer find it. Where the
  Chapter III duties apply, Annex III point 1, `III.unsure` and every system
  that `annex_i_safety_component` marks as an Annex I product keep the Art. 44
  item. The new item is dated like the other Section 5 items: 2026-08-02 with
  "Literal reading, confirm with counsel".
- The profiling rule is cited as "Art. 6(3), third subparagraph, AIA"
  instead of "Art. 6(3) subpara. 2 AIA".
- Art. 50 sources: the placeholder "Transparency guidance tracker" is
  replaced by the Code of Practice on marking and labelling of AI-generated
  content (Art. 50(7) AIA, `art-50-code-of-practice`) and the Commission
  guidelines on the Art. 50 transparency obligations (Art. 96(1)(d) AIA,
  `art-50-guidelines`). Their titles, dates and URLs come from search results
  only, so both carry `[noch zu verifizieren]`. With `--advisory`, every
  Art. 50 profile gets the note `guidance.transparency-guidelines` (was
  `guidance.transparency`), and profiles under Art. 50(2) or (4) also get
  `guidance.transparency-code-of-practice`.
- The regulation named in every report ends with "as amended by Regulation
  (EU) 2026/1744".
- New example `examples/life_insurer_pricing.json` (Annex III point 5(c),
  provider and deployer, with profiling) and two worked examples in
  `docs/worked-examples/`, a bank's credit-scoring model and a life insurer's
  pricing model.
