# Weaviate MCP server

> **This standalone server is deprecated.** The Weaviate Model Context Protocol (MCP) server is now built into Weaviate itself — there is nothing to install or run separately.

## Use the built-in MCP server

Weaviate ships an MCP server inside the main `weaviate/weaviate` binary, available as a preview from **`v1.37.1`** onward. Enable it with a single environment variable:

```sh
MCP_SERVER_ENABLED=true
```

It listens on the same port as the Weaviate REST API at `/v1/mcp`, authenticates via the existing API-key flow, and respects RBAC.

### Tools exposed

| Tool | Purpose |
|---|---|
| `weaviate-collections-get-config` | Inspect collection schemas |
| `weaviate-tenants-list` | List tenants in a multi-tenant collection |
| `weaviate-query-hybrid` | Hybrid (vector + keyword) search |
| `weaviate-objects-upsert` | Create or update objects |

### Documentation

- **Setup, environment variables, RBAC permissions, and per-tool reference:** [docs.weaviate.io/weaviate/configuration/mcp-server](https://docs.weaviate.io/weaviate/configuration/mcp-server)
- **The MCP standard:** [modelcontextprotocol.io](https://modelcontextprotocol.io/)
- **Weaviate repo (issues, feature requests):** [github.com/weaviate/weaviate](https://github.com/weaviate/weaviate/issues/new/choose)

## About this repository

Earlier versions of this repo contained a standalone Go implementation of an MCP server that wrapped the Weaviate REST API. That implementation has been superseded by the built-in server and is no longer maintained. The history is preserved in git for reference; for the previous source, see the commits before this notice.
