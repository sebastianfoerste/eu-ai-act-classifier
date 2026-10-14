# Model Context Protocol (MCP) Configuration Guide

There are two ways to give an AI client this classifier as an MCP tool:

1. **Recommended for Claude:** [eu-reg-mcp](https://github.com/sebastianfoerste/eu-reg-mcp), the supported Claude integration. It runs without a clone.
2. **Secondary:** this repository's own two-tool server, run from a local clone. It serves your working copy, which helps when you test rule changes locally.

## Recommended for Claude: eu-reg-mcp

eu-reg-mcp serves this classifier as its `classify_eu_ai_act_system` tool, next to its MiCAR white paper linter and MiCAR register tools. The `classify` and `lint` extras install the classifier and the linter in the same environment as the server:

```bash
uvx --from 'eu-reg-mcp[classify,lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp' eu-reg-mcp
```

### Claude Code

```bash
claude mcp add eu-reg -- uvx --from 'eu-reg-mcp[classify,lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp' eu-reg-mcp
```

### Claude Desktop

Add the server to the `mcpServers` object in `claude_desktop_config.json`. On macOS, the file is at `~/Library/Application Support/Claude/claude_desktop_config.json`.

```json
{
  "mcpServers": {
    "eu-reg": {
      "command": "uvx",
      "args": [
        "--from",
        "eu-reg-mcp[classify,lint] @ git+https://github.com/sebastianfoerste/eu-reg-mcp",
        "eu-reg-mcp"
      ]
    }
  }
}
```

The JSON form passes the package specification as one argument, so it needs no shell quotes. The eu-reg-mcp README documents its tools and their review notices.

## Secondary: the classifier's own MCP server

The rest of this guide covers the server in `src/eu_ai_act_classifier/mcp_server.py`. It exposes the classification and obligation reasoning engine directly to AI clients such as Claude Desktop, Cursor or other compatible workspaces.

### Prerequisites

1. Python 3.13+ installed.
2. A clone of `eu-ai-act-classifier` with the `[mcp]` extra installed in its virtual environment:
   ```bash
   uv sync --extra mcp
   ```

The `[mcp]` extra pins `mcp>=1.2,<2`. The server is built on `mcp.server.fastmcp`, which mcp 2.0 removed. If `mcp` is missing, or a 2.x release is installed, the server exits with a message that names the pin and the eu-reg-mcp command instead of starting.

### Configuration for Claude Desktop

Add the following configuration to the `mcpServers` object in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "eu-ai-act-classifier": {
      "command": "/path/to/eu-ai-act-classifier/.venv/bin/python",
      "args": [
        "-m",
        "eu_ai_act_classifier.mcp_server"
      ]
    }
  }
}
```

> [!NOTE]
> Replace `/path/to/eu-ai-act-classifier` with the absolute path of your clone. The virtual environment's Python already has the package and the `mcp` extra installed, so no `PYTHONPATH` is needed.

### Configuration for Cursor / VS Code

In Cursor, you can configure the MCP server by navigating to:
**Settings -> Features -> MCP**

1. Click **+ Add New MCP Server**.
2. Fill in the fields:
   - **Name**: `eu-ai-act-classifier`
   - **Type**: `command`
   - **Command**: `/path/to/eu-ai-act-classifier/.venv/bin/python -m eu_ai_act_classifier.mcp_server`

## Verification

Once the classifier's own server is configured, the following tools will be made available to your assistant:

1. `classify_ai_system`: takes a `SystemProfile` object and returns the `ClassificationReport` as JSON: risk tier, disposition, obligations with article citations, documentation, the application timeline, open questions for review and citations pending verification.
2. `classify_ai_system_text`: the same classification as the human-readable report the CLI prints.

Both accept `include_advisory` to add the nonbinding Commission guidance notes.
