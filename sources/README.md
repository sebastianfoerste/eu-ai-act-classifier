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

Two checks back each file, and `manifest.json` records both.

- **The text, confirmed against EUR-Lex on 10 November 2026.** Each snapshot
  was compared with the EUR-Lex rendition of the same document
  (`eurlex_check.url`). The two differ only in the `<head>`: EUR-Lex adds meta
  tags and a different stylesheet path. With the `<head>`, scripts, styles and
  markup removed, character references resolved and whitespace collapsed, the
  texts are identical, character for character. `eurlex_check.text_sha256` is
  the SHA-256 of that text, and `tests/test_sources.py` recomputes it from the
  committed file. So the claim ledger may cite a snapshot and pinpoint as the
  checked source.
- **The bytes, as retrieved.** `sha256` is the digest of the Publications
  Office response, recorded at retrieval (14 October 2026; Decision (EU)
  2026/2274 on 21 October 2026). It has not been recomputed against a fresh
  download: publications.europa.eu was not reachable when the text was
  confirmed. Rerunning the retrieval command for a `request_url` and getting
  the same SHA-256 would confirm the bytes too.

To repeat the text comparison:

```bash
uv run python scripts/compare_sources.py            # fetches each eurlex_check.url
uv run python scripts/compare_sources.py --offline  # only recomputes the recorded digests
```

It exits 0 when every text is identical, 1 when a text differs ("content
changed, review required") and 2 when a source could not be compared. EUR-Lex
sometimes answers a script with a bot challenge instead of the document; that
is reported as unverified and never counts as a match. The script never writes
to this folder and is not part of CI.

The `relied_on_for` lists name the provisions that the rules in pull request
#34 rest on; the classifier does not read these files.

## Rules

- Never edit a snapshot. A changed digest means the source drifted; record a new
  retrieval as a new file and manifest entry, and have the change reviewed.
- Legal fixtures cite the `source_id` and pinpoint they were written from. Write
  the fixture from the snapshot before changing rule code.
- Interpretation choices are labelled `interpretation` in the fixture and in the
  engine's finding or open-question text. They are not statute.
