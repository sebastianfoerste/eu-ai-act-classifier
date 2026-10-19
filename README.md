# eu-ai-act-classifier

[![CI](https://github.com/sebastianfoerste/eu-ai-act-classifier/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianfoerste/eu-ai-act-classifier/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/eu-ai-act-classifier)](https://pypi.org/project/eu-ai-act-classifier/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/pyproject.toml)

Find out which EU AI Act risk tier an AI system falls into, with every obligation cited to its article. Rules-based, offline, and built for a lawyer to confirm; see [who it's for](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/overview.md#who-its-for).

**Status:** beta, on PyPI. It encodes Regulation (EU) 2024/1689 and, in part, the amending Regulation (EU) 2026/1744: its application dates, not its new Art. 5 prohibitions. Source versions are in the [methodology](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/methodology.md), and legal claims, including what is encoded, in the [regulatory claim ledger](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/REGULATORY_CLAIM_LEDGER.md).

**Not legal advice.** Output is a first pass for supervised legal review, and a qualified human must review every result before reliance. Example data is synthetic. The engine applies rules to characterised facts and does not decide disputed intended purpose, operator role or factual deployment scope ([honest limits](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/overview.md#honest-limits)).

No install needed: the [browser playground](https://sebastianfoerste.github.io/eu-ai-act-classifier/playground/) runs the same engine, and nothing you paste leaves the page.

## Install

Python 3.13+, from [PyPI](https://pypi.org/project/eu-ai-act-classifier/):

```bash
pip install eu-ai-act-classifier
```

With [uv](https://docs.astral.sh/uv/), prefix `eu-ai-act-classify` with `uvx --from eu-ai-act-classifier` to run it without installing.

## Quick start

Classify a profile from stdin, offline and deterministically (more profiles in [examples/](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/examples/README.md)):

```bash
echo '{"name":"CitizenScore","prohibited_practices":["5.1.c"]}' | eu-ai-act-classify -
```

Add `--json` for JSON, or `--strict` to exit 1 in CI when the system is prohibited or needs review.

Or from Python:

```python
from eu_ai_act_classifier import SystemProfile, classify, render_report

report = classify(SystemProfile(name="CitizenScore", prohibited_practices=["5.1.c"]))
print(render_report(report))
```

More: the [full quick start](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/SETUP.md#quick-start) and [example output](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/sample-output.md#example-output).

## MCP server

Lets an AI agent call the classifier (tools: `classify_ai_system`, `classify_ai_system_text`). An MCP client starts the server with:

```bash
uvx --python 3.13 --from "eu-ai-act-classifier[mcp]" --with "mcp<2" eu-ai-act-classifier-mcp
```

Keep `mcp<2` ([why](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/mcp-configuration-guide.md#prerequisites)). Client configuration is in [docs/mcp-configuration-guide.md](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/mcp-configuration-guide.md).

## Documentation

- [Docs index](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/README.md): every guide
- [Overview](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/overview.md): audience, playground, honest limits, human-authored legal judgment and related tools
- [What it checks](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/FEATURES.md#what-it-checks): scope, Art. 5 prohibited practices, Art. 6 and Annex III high-risk, GPAI and transparency, with [Annex III coverage](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/coverage.md)
- [Surfaces](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/surfaces.md#surfaces): playground, CLI, MCP server, local API and web cockpit
- [JSON Schemas](https://github.com/sebastianfoerste/eu-ai-act-classifier/tree/main/schemas) for profiles and reports
- [Launch readiness](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/docs/launch-readiness.md): a quick evaluator route

## License

MIT, see [LICENSE](https://github.com/sebastianfoerste/eu-ai-act-classifier/blob/main/LICENSE).
