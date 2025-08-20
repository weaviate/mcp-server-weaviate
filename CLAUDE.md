# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

```bash
# Build the MCP server binary
make build

# Run the test client
make run-client

# Alternative build command
go build -o client/mcp-server .

# Run client directly
cd client && go run client.go
```

## Architecture Overview

This is a Weaviate MCP (Model Context Protocol) server implementation that provides a bridge between MCP clients and Weaviate vector databases. The architecture consists of:

**Core Components:**
- `main.go` - Entry point that loads environment configuration and starts the MCP server
- `mcp.go` - MCP server implementation with tool registration and request handling
- `weaviate.go` - Weaviate client wrapper handling database operations
- `client/` - Test client for validating server functionality

**Key Dependencies:**
- `github.com/mark3labs/mcp-go` - MCP protocol implementation for Go
- `github.com/weaviate/weaviate-go-client/v4` - Official Weaviate Go client
- `github.com/joho/godotenv` - Environment variable loading

**MCP Tools Provided:**
1. `weaviate-insert-one` - Insert objects into Weaviate collections with auto-schema
2. `weaviate-query` - Hybrid search queries across collections with optional filtering support

## Configuration

Environment variables are loaded from `.env` file (copy from `.env.example`):

**Weaviate Configuration:**
- `WEAVIATE_HOST` - Weaviate server host (default: localhost:8080)
- `WEAVIATE_SCHEME` - Connection scheme (default: http)
- `WEAVIATE_API_KEY` - Authentication key (optional for local dev)
- `WEAVIATE_STARTUP_TIMEOUT` - Connection timeout in seconds
- `WEAVIATE_DEFAULT_COLLECTION` - Default collection name

**MCP Transport Configuration:**
- `MCP_TRANSPORT` - MCP transport protocol (default: stdio, options: stdio|sse)
- `MCP_PORT` - Port for SSE transport (default: 8080, only used when MCP_TRANSPORT=sse)
- `MCP_APIKEY` - API key for SSE transport authentication (optional, only used when MCP_TRANSPORT=sse)

When using SSE transport with `MCP_APIKEY` set, clients must include the API key in the Authorization header:
```
Authorization: Bearer your-secret-api-key-here
```

## Code Structure

The server follows a clean separation pattern:
- Connection management isolated in `WeaviateConnection` struct
- MCP protocol handling in `MCPServer` struct with tool registration
- Batch operations used for efficiency (auto-schema and gRPC)
- Error handling with proper MCP error responses
- Environment-based configuration with sensible defaults

## Testing

Use the included test client to verify functionality:
1. Build the server with `make build`
2. Run test scenarios with `make run-client`
3. The client tests insert, query, and filtered query operations against a "WorldMap" collection

## Filtering Support

The `weaviate-query` tool now supports optional filtering via the `where` parameter. Filter structure:

```json
{
  "operator": "Equal|NotEqual|LessThan|LessThanEqual|GreaterThan|GreaterThanEqual|Like|And|Or",
  "path": ["propertyName"],
  "valueText": "string value",
  "valueInt": 123,
  "valueNumber": 1.23,
  "valueBoolean": true,
  "valueDate": "2023-01-01T00:00:00Z",
  "operands": [/* for And/Or operators */]
}
```

**Examples:**
- Simple equality: `{"operator": "Equal", "path": ["continent"], "valueText": "Europe"}`
- Range filter: `{"operator": "GreaterThan", "path": ["population"], "valueInt": 1000000}`
- Complex AND: `{"operator": "And", "operands": [filter1, filter2]}`