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
      "command": "python",
      "args": [
        "-m",
        "eu_ai_act_classifier.mcp_server"
      ],
      "env": {
        "PYTHONPATH": "/Users/sebastian/Developer/eu-ai-act-classifier/src"
      }
    }
  }
}
```

> [!NOTE]
> Adjust the `PYTHONPATH` or use the absolute path to your python executable inside the virtual environment (e.g. `/Users/sebastian/Developer/eu-ai-act-classifier/.venv/bin/python`) if needed.

## Configuration for Cursor / VS Code

In Cursor, you can configure the MCP server by navigating to:
**Settings -> Features -> MCP**

1. Click **+ Add New MCP Server**.
2. Fill in the fields:
   - **Name**: `eu-ai-act-classifier`
   - **Type**: `command`
   - **Command**: `/Users/sebastian/Developer/eu-ai-act-classifier/.venv/bin/python -m eu_ai_act_classifier.mcp_server`

## Verification

Once configured, the following tools will be made available to your assistant:

1. `eu_ai_act_classify_profile`: Takes a structured system profile (JSON) and returns a complete risk-tier classification and obligation report.
2. `eu_ai_act_get_timeline`: Exposes the Article 113 implementation timeline.
