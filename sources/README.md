# Source snapshots

The rules and the legal fixtures rest on the texts in this folder, not on web
pages, search results or memory. Each file is the byte-exact response of the
Publications Office to the request recorded in [`manifest.json`](manifest.json),
with its retrieval date and SHA-256 digest. `tests/test_sources.py` fails if a
file no longer matches its digest.

| File | Text | Status |
| --- | --- | --- |
| `oj/32026R1744.en.xhtml` | Regulation (EU) 2026/1744 (Digital Omnibus on AI), OJ L, 2026/1744, 24.7.2026 | Official Journal |
| `oj/32024R1689.en.xhtml` | Regulation (EU) 2024/1689 (AI Act), OJ L, 2024/1689, 12.7.2024, original wording | Official Journal |
| `consolidated/02024R1689-20260727.en.xhtml` | AI Act consolidated as at 27 July 2026 | No legal effect; cross-check only |
| `oj/32011L0093.en.xhtml` | Directive 2011/93/EU, referred to in Art. 5(1)(bb) AIA | Official Journal |

The authentic law is the Official Journal text of Regulation (EU) 2024/1689 read
with the amendments made by Regulation (EU) 2026/1744. The consolidated version
says of itself that it has no legal effect.

## Rules

- Never edit a snapshot. A changed digest means the source drifted; record a new
  retrieval as a new file and manifest entry, and have the change reviewed.
- Fixtures in `tests/legal/fixtures/` cite the `source_id` and pinpoint they were
  written from. Write the fixture from the snapshot before changing rule code.
- Interpretation choices are labelled `interpretation` in the fixture and in the
  engine's finding or open-question text. They are not statute.
