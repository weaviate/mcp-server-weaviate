# mcp-server-weaviate
MCP server for Weaviate

## 🏎️ Quickstart

### Prerequisites

- Ensure you have `uv` installed (see
  [the docs](https://docs.astral.sh/uv/getting-started/installation/) for
  details)
- Clone this repository

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

Development/Unpublished Servers Configuration

```
"mcpServers": {
  "weaviate": {
    "command": "uv",
    "args": [
      "--directory",
      "parent_of_servers_repo/servers/src/weaviate",
      "run",
      "mcp-server-weaviate",
      "--weaviate-url",
      "https://your-weaviate-instance.weaviate.network",
      "--api-key",
      "your_weaviate_api_key",
      "--memory-collection-name",
      "AnthropicMemories",
      "--knowledge-base-collection-name",
      "KnowledgeBase",
      # Optional: OpenAI API key for embeddings
      "--openai-api-key",
      "your_openai_api_key",
      # Optional: Cohere API key for embeddings
      "--cohere-api-key", 
      "your_cohere_api_key"
    ]
  }
}
```
