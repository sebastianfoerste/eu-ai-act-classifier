# Changelog

Notable changes to the classifier. Earlier releases are described in their
pull requests.

## Unreleased

Follow-ups to the Regulation (EU) 2026/1744 dating work (#26), checked against
the consolidated AI Act of 27 July 2026 and Regulation (EU) 2026/1744. Items
whose dating or scope is contested carry "Literal reading, confirm with
counsel".

### Added

- Art. 111(2) AIA: a high-risk system whose `placing_on_market_date` or
  `putting_into_service_date` precedes its Chapter III date (2 December 2027
  for Annex III, 2 August 2028 for Annex I) gets an Art. 111(2) graph item for
  each provider and deployer role. With `public_authority_use` the item adds
  the 2 August 2030 deadline, which also joins the binding timeline. The
  cut-off is flagged where the reading of "the date of application of
  Chapter III" decides the result.
- `annex_i_section` (`A` or `B`): a Section B product with no Annex III area
  stays high-risk under Art. 6(1) but gets only the Art. 2(2) provisions
  (Art. 6(1), Art. 60a and Arts. 102 to 112) instead of the Chapter III
  duties. Machinery (Regulation (EU) 2023/1230) is now a Section B product.
- Art. 49(3) AIA: registration of use by public-authority deployers of Annex
  III systems other than point 2, as an obligation and a flagged graph item.
- `gpai_model_placing_on_market_date`: the model's own date for Art. 111(3).
  `placing_on_market_date` stays the AI system's date for Art. 111(2) and (4).
- Prohibited-practice codes `5.1.ba` and `5.1.bb` (Art. 5(1)(ba) and (bb)),
  with findings that quote the point and say the ban applies from
  2 December 2026, and the example `examples/intimate_imagery_generator.json`.
- A test that keeps the adapter manifest's `sourceCurrencyDate` equal to the
  proof contract's.

### Changed

- The scope transitional status compares the placing-on-market and
  putting-into-service dates with the system's Chapter III date instead of
  generic wording.
- A GPAI profile that gives only `placing_on_market_date` is dated by it as
  before, with a note asking for the model's own date.
- `docs/integrations/eu-ai-act-classifier.adapter.v1.json`: `sourceCurrencyDate`
  is 2026-10-18, as in the proof contract.
- `docs/demo.png` is rendered from real CLI output by the new
  `scripts/render_demo.py`; it used to be a copy of the cockpit screenshot.
  `docs/cockpit.png` is a full-page headless capture of the production build.
  Both recipes are in `docs/TESTING.md`.
