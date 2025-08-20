# Weaviate MCP Server

A Model Context Protocol (MCP) server implementation that provides a bridge between MCP clients and Weaviate vector databases. This server enables MCP-compatible applications to perform vector search operations, object insertion, and advanced filtering on Weaviate instances.

## Architecture

This implementation follows a clean separation pattern with the following components:

**Core Components:**
- `main.go` - Entry point that loads environment configuration and starts the MCP server
- `mcp.go` - MCP server implementation with tool registration and request handling
- `weaviate.go` - Weaviate client wrapper handling database operations
- `client/` - Test client for validating server functionality

**Key Dependencies:**
- `github.com/mark3labs/mcp-go` - MCP protocol implementation for Go
- `github.com/weaviate/weaviate-go-client/v4` - Official Weaviate Go client
- `github.com/joho/godotenv` - Environment variable loading

## Quick Start

### Prerequisites
- Go 1.21 or later
- Access to a Weaviate instance (local or remote)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp-server-weaviate
```

2. Set up environment configuration:
```bash
cp .env.example .env
# Edit .env with your Weaviate configuration
```

3. Build the server:
```bash
make build
```

4. Test the implementation:
```bash
make run-client
```

## Configuration

The server is configured via environment variables loaded from a `.env` file:

### Weaviate Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `WEAVIATE_HOST` | Weaviate server host | `localhost:8080` |
| `WEAVIATE_SCHEME` | Connection scheme (http/https) | `http` |
| `WEAVIATE_API_KEY` | Authentication key | (optional for local dev) |
| `WEAVIATE_STARTUP_TIMEOUT` | Connection timeout in seconds | `30` |
| `WEAVIATE_DEFAULT_COLLECTION` | Default collection name | `DefaultCollection` |

### MCP Transport Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TRANSPORT` | MCP transport protocol | `stdio` |
| `MCP_PORT` | Port for SSE transport | `8080` |
| `MCP_APIKEY` | API key for SSE authentication | (optional) |

**Transport Options:**
- `stdio` - Standard input/output (default, for CLI integration)
- `sse` - Server-Sent Events over HTTP (for web integration)

**API Key Authentication:**
When using SSE transport with `MCP_APIKEY` set, clients must include the API key in the Authorization header:
```
Authorization: Bearer your-secret-api-key-here
```

### Example .env file:
```bash
# Weaviate Configuration
WEAVIATE_HOST=localhost:8080
WEAVIATE_SCHEME=http
WEAVIATE_API_KEY=your-api-key-here
WEAVIATE_STARTUP_TIMEOUT=30
WEAVIATE_DEFAULT_COLLECTION=MyData

# MCP Transport Configuration
MCP_TRANSPORT=stdio
MCP_PORT=8080
MCP_APIKEY=your-secret-api-key-here
```

## Client Integration

### Claude Desktop Integration (stdio transport)

To use this MCP server with Claude Desktop, add the following configuration to your Claude Desktop settings:

```json
{
  "mcpServers": {
    "weaviate": {
      "command": "/path/to/mcp-server-weaviate/client/mcp-server",
      "env": {
        "WEAVIATE_HOST": "localhost:8080",
        "WEAVIATE_SCHEME": "http",
        "WEAVIATE_STARTUP_TIMEOUT": "5",
        "WEAVIATE_API_KEY": "your-weaviate-api-key",
        "WEAVIATE_DEFAULT_COLLECTION": "AcademicContent",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### Web Integration (SSE transport)

For web applications or HTTP-based clients, use SSE transport:

```bash
# Start the server with SSE transport
MCP_TRANSPORT=sse MCP_PORT=8080 MCP_APIKEY=secret-key ./client/mcp-server
```

Then connect to `http://localhost:8080` with the required Authorization header.

**Configuration Notes:**
- Update the `command` path to match your actual binary location
- Adjust environment variables to match your Weaviate setup
- The `WEAVIATE_API_KEY` should be set to your actual Weaviate API key for remote instances
- Use `WEAVIATE_SCHEME: "https"` for secure Weaviate connections
- Set `MCP_APIKEY` only for SSE transport to enable authentication

## MCP Tools

The server provides two main tools for interacting with Weaviate:

### 1. weaviate-insert-one

Insert objects into Weaviate collections with automatic schema creation.

**Parameters:**
- `collection` (string, required) - Target collection name
- `properties` (object, required) - Object properties as key-value pairs

**Example:**
```json
{
  "collection": "WorldMap",
  "properties": {
    "name": "Paris",
    "continent": "Europe",
    "population": 2161000,
    "isCapital": true,
    "coordinates": "48.8566,2.3522"
  }
}
```

**Features:**
- Automatic schema creation for new collections
- Support for multiple data types (string, number, boolean, date)
- Batch operations for efficiency
- Auto-vectorization using Weaviate's configured modules

### 2. weaviate-query

Perform hybrid search queries with optional filtering support.

**Parameters:**
- `collection` (string, required) - Target collection name
- `query` (string, required) - Search query text
- `limit` (number, optional) - Maximum results to return
- `offset` (number, optional) - Number of results to skip for pagination
- `where` (object, optional) - Filter conditions

**Example Basic Query:**
```json
{
  "collection": "WorldMap",
  "query": "European capitals",
  "limit": 5
}
```

**Example with Filtering:**
```json
{
  "collection": "WorldMap",
  "query": "large cities",
  "limit": 10,
  "where": {
    "operator": "And",
    "operands": [
      {
        "operator": "Equal",
        "path": ["continent"],
        "valueText": "Europe"
      },
      {
        "operator": "GreaterThan",
        "path": ["population"],
        "valueInt": 1000000
      }
    ]
  }
}
```

**Example with Pagination:**
```json
{
  "collection": "WorldMap",
  "query": "cities",
  "limit": 10,
  "offset": 20
}
```

## Filtering Support

The `weaviate-query` tool supports comprehensive filtering via the `where` parameter. The filter structure follows Weaviate's GraphQL where clause format:

### Filter Structure:
```json
{
  "operator": "Operator",
  "path": ["propertyName"],
  "value*": "value",
  "operands": []
}
```

### Supported Operators:
- **Comparison:** `Equal`, `NotEqual`, `LessThan`, `LessThanEqual`, `GreaterThan`, `GreaterThanEqual`, `Like`
- **Logical:** `And`, `Or`

### Value Types:
- `valueText` - String values
- `valueInt` - Integer values
- `valueNumber` - Float values
- `valueBoolean` - Boolean values
- `valueDate` - ISO 8601 date strings

### Filter Examples:

**Simple Equality:**
```json
{
  "operator": "Equal",
  "path": ["continent"],
  "valueText": "Europe"
}
```

**Range Filter:**
```json
{
  "operator": "GreaterThan",
  "path": ["population"],
  "valueInt": 1000000
}
```

**Complex AND Condition:**
```json
{
  "operator": "And",
  "operands": [
    {
      "operator": "Equal",
      "path": ["continent"],
      "valueText": "Europe"
    },
    {
      "operator": "Equal",
      "path": ["isCapital"],
      "valueBoolean": true
    }
  ]
}
```

**Text Search with LIKE:**
```json
{
  "operator": "Like",
  "path": ["name"],
  "valueText": "*paris*"
}
```

## Testing

The project includes a comprehensive test client that validates server functionality:

### Running Tests:
```bash
# Build and run the test client
make run-client

# Alternative approach
cd client && go run client.go
```

### Test Scenarios:
The test client performs the following operations:
1. **Insert Operation** - Adds sample data to a "WorldMap" collection
2. **Basic Query** - Performs hybrid search without filters
3. **Filtered Query** - Tests complex filtering with AND conditions
4. **Error Handling** - Validates proper error responses

### Sample Test Data:
The client inserts geographical data including cities with properties like:
- Name, continent, population
- Capital city status
- Geographic coordinates

## Development

### Build Commands:
```bash
# Build the MCP server binary
make build

# Alternative build command
go build -o client/mcp-server .

# Run client directly
cd client && go run client.go
```

### Code Structure:
- **Connection Management** - Isolated in `WeaviateConnection` struct
- **MCP Protocol Handling** - Centralized in `MCPServer` struct
- **Batch Operations** - Used for efficiency (auto-schema and gRPC)
- **Error Handling** - Proper MCP error responses
- **Configuration** - Environment-based with sensible defaults

### Error Handling:
The server implements comprehensive error handling:
- Connection failures
- Schema validation errors
- Query execution errors
- Malformed MCP requests
- Weaviate-specific errors

## Integration

This MCP server can be integrated with any MCP-compatible client application. The server follows the standard MCP protocol for tool registration and request/response handling.

### Supported MCP Features:
- Tool registration and discovery
- JSON-RPC 2.0 protocol compliance
- Structured parameter validation
- Comprehensive error responses
- Tool result formatting

## Contributing

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update documentation for any new features
4. Ensure proper error handling
5. Test with the included client before submitting changes

## License

[Add your license information here]