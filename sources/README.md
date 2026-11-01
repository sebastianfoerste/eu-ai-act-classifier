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
| `oj/32026D2274.en.xhtml` | Commission Implementing Decision (EU) 2026/2274 (EN 18286:2026), OJ L, 2026/2274, 14.10.2026 | Official Journal |

The authentic law is the Official Journal text of Regulation (EU) 2024/1689 read
with the amendments made by Regulation (EU) 2026/1744. The consolidated version
says of itself that it has no legal effect.

## Authenticity

The digests in `manifest.json` were recorded when the files were retrieved
(14 October 2026; Decision (EU) 2026/2274 on 21 October 2026). They have not
been recomputed against a fresh download since: the environment that added this
folder could not reach publications.europa.eu. Until someone reruns the
retrieval command for each `request_url` and gets the same SHA-256, treat the
files as unconfirmed copies, and do not cite them as the checked source in the
claim ledger. The `relied_on_for` lists name the provisions that the rules in
pull request #34 rest on; the classifier on this branch does not read these
files.

## Rules

- Never edit a snapshot. A changed digest means the source drifted; record a new
  retrieval as a new file and manifest entry, and have the change reviewed.
- Legal fixtures cite the `source_id` and pinpoint they were written from. Write
  the fixture from the snapshot before changing rule code.
- Interpretation choices are labelled `interpretation` in the fixture and in the
  engine's finding or open-question text. They are not statute.
