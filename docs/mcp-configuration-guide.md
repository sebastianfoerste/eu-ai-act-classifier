# Model Context Protocol (MCP) Configuration Guide

The EU AI Act Classifier includes a Model Context Protocol (MCP) server that exposes the classification and obligation reasoning engine directly to AI clients such as Claude Desktop, Cursor, or other compatible workspaces.

This allows agentic workflows to perform compliance evaluations on system architectures in real-time.

## Prerequisites

1. Python 3.13+ installed.
2. The `eu-ai-act-classifier` package installed in a virtual environment or globally with the `[mcp]` extra:
   ```bash
   pip install -e ".[mcp]"
   ```

## Configuration for Claude Desktop

To add the classifier to Claude Desktop, edit your `claude_desktop_config.json` file.

On macOS, this is located at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

Add the following configuration to the `mcpServers` object:

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

## Configuration for Cursor / VS Code

In Cursor, you can configure the MCP server by navigating to:
**Settings -> Features -> MCP**

1. Click **+ Add New MCP Server**.
2. Fill in the fields:
   - **Name**: `eu-ai-act-classifier`
   - **Type**: `command`
   - **Command**: `/path/to/eu-ai-act-classifier/.venv/bin/python -m eu_ai_act_classifier.mcp_server`

## Verification

Once configured, the following tools will be made available to your assistant:

1. `classify_ai_system`: takes a `SystemProfile` object and returns the `ClassificationReport` as JSON: risk tier, disposition, obligations with article citations, documentation, the application timeline, open questions for review and citations pending verification.
2. `classify_ai_system_text`: the same classification as the human-readable report the CLI prints.

Both accept `include_advisory` to add the nonbinding Commission guidance notes.
