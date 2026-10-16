# Model Context Protocol (MCP) Configuration Guide

The EU AI Act Classifier includes a Model Context Protocol (MCP) server that exposes the classification and obligation reasoning engine directly to AI clients such as Claude Desktop, Cursor, or other compatible workspaces.

This allows agentic workflows to perform compliance evaluations on system architectures in real-time.

## Recommended for Claude: eu-reg-mcp

[eu-reg-mcp](https://github.com/sebastianfoerste/eu-reg-mcp) serves this classifier as its `classify_eu_ai_act_system` tool, next to its MiCAR white paper linter and MiCAR register tools. It is on PyPI and pins a compatible `mcp` itself. The `lint` and `classify` extras install the linter and this classifier in the same environment:

```bash
uvx --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp
```

For Claude Code:

```bash
claude mcp add eu-reg -- uvx --from 'eu-reg-mcp[lint,classify]' eu-reg-mcp
```

For Claude Desktop, add `"eu-reg": {"command": "uvx", "args": ["--from", "eu-reg-mcp[lint,classify]", "eu-reg-mcp"]}` to the `mcpServers` object. The eu-reg-mcp README documents its tools and their review notices.

The rest of this guide covers this package's own two-tool server.

## Prerequisites

1. Python 3.13+ installed.
2. The [`eu-ai-act-classifier`](https://pypi.org/project/eu-ai-act-classifier/) package from PyPI with the `[mcp]` extra. Either let [uv](https://docs.astral.sh/uv/) fetch it when the client starts the server, which is what the Claude Desktop example below does:
   ```bash
   uvx --python 3.13 --from "eu-ai-act-classifier[mcp]" --with "mcp<2" eu-ai-act-classifier-mcp
   ```
   or install it into a virtual environment with pip:
   ```bash
   pip install "eu-ai-act-classifier[mcp]" "mcp<2"
   ```
   Keep the `mcp<2` constraint. The server is built on the 1.x `mcp` SDK, and `mcp` 2.x renamed the API the server imports. The `[mcp]` extra pins `mcp<2` from 0.2.1. The 0.2.0 extra does not rule out `mcp` 2.x, and the 0.2.0 server then exits with `The MCP extra is not installed` although the extra is installed. From a clone, `uv run --extra mcp eu-ai-act-classifier-mcp` runs your working copy with the pinned extra.

## Configuration for Claude Desktop

To add the classifier to Claude Desktop, edit your `claude_desktop_config.json` file.

On macOS, this is located at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

Add the following configuration to the `mcpServers` object:

```json
{
  "mcpServers": {
    "eu-ai-act-classifier": {
      "command": "uvx",
      "args": [
        "--python",
        "3.13",
        "--from",
        "eu-ai-act-classifier[mcp]",
        "--with",
        "mcp<2",
        "eu-ai-act-classifier-mcp"
      ]
    }
  }
}
```

> [!NOTE]
> If Claude Desktop cannot find `uvx`, set `command` to its absolute path (the output of `which uvx`). If you installed the package with pip instead, set `command` to the absolute path of the `eu-ai-act-classifier-mcp` executable in that virtual environment, for example `/path/to/venv/bin/eu-ai-act-classifier-mcp`, and remove `args`.

## Configuration for Cursor / VS Code

In Cursor, you can configure the MCP server by navigating to:
**Settings -> Features -> MCP**

1. Click **+ Add New MCP Server**.
2. Fill in the fields:
   - **Name**: `eu-ai-act-classifier`
   - **Type**: `command`
   - **Command**: `/path/to/venv/bin/eu-ai-act-classifier-mcp`, the server installed with pip as described under Prerequisites

## Verification

Once configured, the following tools will be made available to your assistant:

1. `classify_ai_system`: takes a `SystemProfile` object and returns the `ClassificationReport` as JSON: risk tier, disposition, obligations with article citations, documentation, the application timeline, open questions for review and citations pending verification.
2. `classify_ai_system_text`: the same classification as the human-readable report the CLI prints.

Both accept `include_advisory` to add the nonbinding Commission guidance notes.
