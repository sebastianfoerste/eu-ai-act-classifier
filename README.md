# eu-ai-act-classifier

[![CI](https://github.com/sebastianfoerste/eu-ai-act-classifier/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-ai-act-classifier/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/eu-ai-act-classifier)](https://pypi.org/project/eu-ai-act-classifier/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)

**Answer "Is our AI system high-risk under the EU AI Act?" with a cited, reviewable first pass instead of a one-word label.**

Find out which EU AI Act risk tier an AI system falls into, with every obligation cited to its article. Rules-based, offline, and built for a lawyer to confirm.

Encodes Regulation (EU) 2024/1689 as consolidated on 27 July 2026, plus Regulation (EU) 2026/1744 (Annex III high-risk dates shown as 2027-12-02, product-embedded high-risk as 2028-08-02). Not legal advice; the bundled example data is synthetic.

## Who it's for

- **General counsel, AI governance and compliance leads, and product counsel** doing a first-pass classification of an AI system before deeper legal review.
- **Lawyers who confirm the result** and need to check the reasoning: each obligation cites its Article, open questions name the Article and the fact to confirm, and generated work products are marked draft only.
- **Legal engineers** who need the same rules as a `--strict` gate in CI or an intake pipeline, as MCP tools or behind a local JSON API.
- **Developers** asking "am I high-risk?" before engaging counsel.

## Try it now

**[Open the live playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/)**: no install, and nothing you paste leaves the page. The playground runs the same engine as the CLI.

<!-- Screenshot/GIF placeholder: to be added. Put a short GIF or screenshot of the live playground here (describe the system, classify, review and export) and save it in docs/ next to the existing images. -->

*Screenshot/GIF placeholder: to be added*

> **If you don't code:** open the [playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/) and pick one of the 17 synthetic examples, or scroll to [Example output](#example-output). The point isn't the code; it's whether the legal work is structured, cited, reviewable, and testable.

## Quick start

The package is on PyPI as [`eu-ai-act-classifier`](https://pypi.org/project/eu-ai-act-classifier/) (Python 3.13+). With [uv](https://docs.astral.sh/uv/), `uvx` fetches it from PyPI and runs it without installing it. Save a profile and classify it:

```bash
cat > profile.json <<'JSON'
{
  "name": "CitizenScore",
  "description": "Scores individuals on social behaviour to gate access to services.",
  "roles": ["provider"],
  "purpose": "Social scoring",
  "sector": "GovTech",
  "prohibited_practices": ["5.1.c"]
}
JSON
uvx --from eu-ai-act-classifier eu-ai-act-classify profile.json
```

Or install it with pip:

```bash
pip install eu-ai-act-classifier
eu-ai-act-classify profile.json
```

To try changes on `main` that are not on PyPI yet, point uvx at the repository instead: `uvx --from git+https://github.com/sebastianfoerste/eu-ai-act-classifier eu-ai-act-classify profile.json`. To develop, work from a clone:

```bash
git clone https://github.com/sebastianfoerste/eu-ai-act-classifier
cd eu-ai-act-classifier
uv sync --extra dev
uv run eu-ai-act-classify examples/credit_scoring.json
```

Runs end to end, offline and deterministically. [Example output](#example-output) shows the output, and [Local verification](docs/surfaces.md#local-verification) has more commands, starting with the test suite.

Which Annex III points the classifier covers, with the citation each emits and the examples and tests behind it: [docs/coverage.md](docs/coverage.md), generated from the code.

JSON Schemas for the input profile and the report are in [schemas/](schemas/) (also `eu-ai-act-classify --schema profile` or `--schema report`). Add `"$schema": "https://raw.githubusercontent.com/sebastianfoerste/eu-ai-act-classifier/main/schemas/system-profile.v1.schema.json"` to a profile for editor autocomplete; the classifier ignores that key.

## Example output

Real output of `uv run eu-ai-act-classify examples/social_scoring.json` (excerpt, run on this repo):

```text
EU AI Act classification: CitizenScore
Risk tier: PROHIBITED (Art. 5 AIA)
Disposition: DETERMINED
Scope status: in_scope
Roles: provider

Findings:
  [blocker] Art. 5(1)(c) AIA: Social scoring leading to detrimental or unfavourable treatment
      Prohibited practice under Art. 5 AIA. The system may not be placed on the market, put into service, or used.

Binding application timeline:
  2025-02-02: Chapters I-II, incl. Art. 5 (prohibited practices)
  2025-08-02: Chapter V (general-purpose AI models)
  2026-08-02: General application for provisions without a later specific date
  2027-12-02: Regulation (EU) 2026/1744: Annex III high-risk systems
  2028-08-02: Regulation (EU) 2026/1744: product-embedded high-risk systems

Source manifest:
  - Regulation (EU) 2024/1689: binding_level_1, retrieved 2026-08-26
  - Regulation (EU) 2026/1744: binding_level_1, retrieved 2026-08-26
  ...
```

A high-risk case (`examples/credit_scoring.json`) returns `Risk tier: HIGH-RISK (Art. 6 AIA)`, the finding `Annex III(5)(b) AIA: Creditworthiness evaluation and credit scoring`, and 14 cited obligations, for example:

```text
  - Art. 9 AIA: Risk management system. Establish, document and maintain a continuous risk management system.
  - Art. 10 AIA: Data and data governance. Apply data governance to training, validation and testing data sets.
  - Art. 11 AIA: Technical documentation. Draw up technical documentation (Annex IV) before placing on the market.
```

When a point is unsettled the disposition becomes `REQUIRES_REVIEW` (see `examples/ambiguous_use_case.json`) and the report says it needs lawyer review before reliance. The full committed sample is in [`examples/classification-packet.md`](examples/classification-packet.md) and [`examples/classification-packet.json`](examples/classification-packet.json).

![CLI sample output: CreditSightScore classified high-risk with Articles 9, 10 and 11 obligations](docs/demo.png)

## What it checks

| Gate | Decides | Example from the eval set |
|---|---|---|
| Scope and intake | AI-system status, EU nexus, transitional dates | `examples/ambiguous_use_case.json` |
| Prohibited practices (Art. 5) | Flags prohibited use cases | `examples/social_scoring.json`, `examples/emotion_hiring.json` |
| High-risk (Art. 6, Annex III) | Risk tier and provider/deployer obligations | `examples/credit_scoring.json`, `examples/cv_screening.json` |
| GPAI | Systemic-risk status and compute scale | `examples/gpai_systemic_by_flops.json` |
| Transparency | Limited-risk cases | `examples/deepfake_generator.json`, `examples/support_chatbot.json` |

Which example lands in which tier is asserted in `tests/test_examples.py`. See [examples/README.md](examples/README.md).

## Surfaces

| Surface | Use it for | Details |
|---|---|---|
| Browser playground | Zero-install trial, nothing leaves the page | [playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) |
| CLI (`eu-ai-act-classify`) | Authoritative surface; `--json`, `--strict`, `--sources`, draft artifacts | [docs/surfaces.md](docs/surfaces.md) |
| MCP server | Let an agent call the classifier | [docs/mcp-configuration-guide.md](docs/mcp-configuration-guide.md) |
| Local API and web cockpit | Local inventory, review and export workflow | [docs/surfaces.md](docs/surfaces.md) |

[![Browser playground: CreditSightScore classified high-risk under Art. 6 AIA, with the cited provider obligations from Article 9 onwards](docs/playground.png)](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/)

MCP quick start: for Claude Code or Claude Desktop, use [eu-reg-mcp](https://github.com/sebastianfoerste/eu-reg-mcp). It serves this classifier as an MCP tool next to its MiCAR tools:

```bash
uvx --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp
```

To register it with Claude Code, put `claude mcp add eu-reg --` in front of that command. The Claude Desktop configuration is in the [MCP configuration guide](docs/mcp-configuration-guide.md#recommended-for-claude-eu-reg-mcp).

This package's own MCP server (tools: `classify_ai_system`, `classify_ai_system_text`) is the secondary option. An MCP client starts it with:

```bash
uvx --python 3.13 --from "eu-ai-act-classifier[mcp]" --with "mcp<2" eu-ai-act-classifier-mcp
```

Keep `mcp<2`: the server is built on the 1.x `mcp` SDK, and `mcp` 2.x renamed the API the server imports. The `[mcp]` extra pins `mcp<2` from 0.2.1; the 0.2.0 extra does not. Client configuration is in [docs/mcp-configuration-guide.md](docs/mcp-configuration-guide.md).

## Human-authored legal judgment

AI tools assisted the implementation, but the parts that carry the value are human-authored: the Annex/Article mappings, the obligation set, and the prohibited-practice and review-status logic. The point of this repository is not code volume; it is showing how legal judgment can be made structured, testable, and reviewable. The rules are plain Python under `src/eu_ai_act_classifier/`, and the eval set is tested for drift.

## Honest limits

- This is a screening tool for supervised legal review. It does not produce legal advice, a conformity assessment or a binding regulatory conclusion. Generated work products require human legal review before use.
- Example data is synthetic.
- Guidance changes, and national implementation and supervisory practice may vary by Member State.
- The engine applies rules to characterised facts and does not decide disputed intended purpose, operator role or factual deployment scope.
- `requires_review`, draft artifacts and advisory overlays must be reviewed before reliance.

## Docs and links

- [Playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) (hosted demo)
- [CASE_STUDY.md](CASE_STUDY.md): problem, controls and limitations
- [docs/surfaces.md](docs/surfaces.md): CLI verification, source statuses, MCP and local API, cockpit, collaboration workspace, eval set, stack
- [docs/methodology.md](docs/methodology.md), [docs/DESIGN.md](docs/DESIGN.md), [docs/launch-readiness.md](docs/launch-readiness.md)
- [DEPLOYMENT.md](DEPLOYMENT.md), [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [PRIVACY.md](PRIVACY.md)

## Part of the EU regulation as code suite

Deterministic, review-gated tools for EU regulation, by [sebastianfoerste](https://github.com/sebastianfoerste):

- [awesome-eu-fintech-regulation](https://github.com/sebastianfoerste/awesome-eu-fintech-regulation): curated index of EU financial-regulation primary sources and tools
- [contract-review-eval-harness](https://github.com/sebastianfoerste/contract-review-eval-harness)
- [legal-function-operating-system](https://github.com/sebastianfoerste/legal-function-operating-system)
- **eu-ai-act-classifier** (this repo, [PyPI](https://pypi.org/project/eu-ai-act-classifier/))
- [micar-whitepaper-linter](https://github.com/sebastianfoerste/micar-whitepaper-linter): MiCAR whitepaper linter with pinpoint citations ([PyPI](https://pypi.org/project/micar-whitepaper-linter/))
- [eu-reg-mcp](https://github.com/sebastianfoerste/eu-reg-mcp) ([PyPI](https://pypi.org/project/eu-reg-mcp/))
- [micar-register-observatory](https://github.com/sebastianfoerste/micar-register-observatory)

## License

MIT, see [LICENSE](LICENSE).
