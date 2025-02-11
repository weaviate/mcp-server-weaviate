# mcp-server-weaviate
MCP server for Weaviate

## 🏎️ Quickstartå

### Prerequisites

- Ensure you have `uv` installed (see
  [the docs](https://docs.astral.sh/uv/getting-started/installation/) for
  details)
- Clone this repository

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>

```
"mcpServers": {
  "mcp-server-docker": {
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/repo",
      "run",
      "mcp-server-docker"
    ]
  }
}
```

</details>