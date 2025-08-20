package main

import (
	"context"
	"log"
	"net/http"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

type MCPServer struct {
	server            *server.MCPServer
	weaviateConn      *WeaviateConnection
	defaultCollection string
}

func NewMCPServer() (*MCPServer, error) {
	conn, err := NewWeaviateConnection()
	if err != nil {
		return nil, err
	}
	s := &MCPServer{
		server: server.NewMCPServer(
			"Weaviate MCP Server",
			"0.1.0",
			server.WithToolCapabilities(true),
			server.WithPromptCapabilities(true),
			server.WithResourceCapabilities(true, true),
			server.WithRecovery(),
		),
		weaviateConn: conn,
		defaultCollection: getEnvWithDefault("WEAVIATE_DEFAULT_COLLECTION", "DefaultCollection"),
	}
	s.registerTools()
	return s, nil
}

func (s *MCPServer) ServeStdio() {
	server.ServeStdio(s.server)
}

func (s *MCPServer) ServeSSE() {
	sseServer := server.NewSSEServer(s.server)
	
	// Get configuration from environment variables
	port := getEnvWithDefault("MCP_PORT", "8080")
	apiKey := getEnvWithDefault("MCP_APIKEY", "")
	addr := ":" + port
	
	// Set up handler with optional API key middleware
	var handler http.Handler = sseServer
	if apiKey != "" {
		handler = s.apiKeyMiddleware(apiKey, sseServer)
		log.Printf("Starting MCP SSE server on port %s with API key authentication", port)
	} else {
		log.Printf("Starting MCP SSE server on port %s without authentication", port)
	}
	
	if err := http.ListenAndServe(addr, handler); err != nil {
		log.Fatalf("failed to start SSE server: %v", err)
	}
}

func (s *MCPServer) apiKeyMiddleware(expectedAPIKey string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check for API key in Authorization header (Bearer token)
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			http.Error(w, "Missing Authorization header", http.StatusUnauthorized)
			return
		}
		
		// Extract Bearer token
		const bearerPrefix = "Bearer "
		if !strings.HasPrefix(authHeader, bearerPrefix) {
			http.Error(w, "Invalid Authorization header format. Expected: Bearer <token>", http.StatusUnauthorized)
			return
		}
		
		apiKey := strings.TrimPrefix(authHeader, bearerPrefix)
		if apiKey != expectedAPIKey {
			http.Error(w, "Invalid API key", http.StatusUnauthorized)
			return
		}
		
		// API key is valid, proceed with the request
		next.ServeHTTP(w, r)
	})
}

func (s *MCPServer) registerTools() {
	insertOne := mcp.NewTool(
		"weaviate-insert-one",
		mcp.WithString(
			"collection",
			mcp.Description("Name of the target collection"),
		),
		mcp.WithObject(
			"properties",
			mcp.Description("Object properties to insert"),
			mcp.Required(),
		),
	)
	query := mcp.NewTool(
		"weaviate-query",
		mcp.WithString(
			"query",
			mcp.Description("Query data within Weaviate"),
			mcp.Required(),
		),
		mcp.WithArray(
			"targetProperties",
			mcp.Description("Properties to return with the query"),
			mcp.Required(),
		),
		mcp.WithObject(
			"where",
			mcp.Description("Optional filter conditions. Structure: {operator: 'Equal|NotEqual|LessThan|LessThanEqual|GreaterThan|GreaterThanEqual|Like|And|Or', path: ['propertyName'], valueText: 'string', valueInt: 123, valueNumber: 1.23, valueBoolean: true, valueDate: '2023-01-01T00:00:00Z', operands: [...]}"),
		),
		mcp.WithNumber(
			"limit",
			mcp.Description("Maximum number of results to return"),
		),
		mcp.WithNumber(
			"offset",
			mcp.Description("Number of results to skip"),
		),
	)

	s.server.AddTools(
		server.ServerTool{Tool: insertOne, Handler: s.weaviateInsertOne},
		server.ServerTool{Tool: query, Handler: s.weaviateQuery},
	)
}

func (s *MCPServer) weaviateInsertOne(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	targetCol := s.parseTargetCollection(req)
	props := req.Params.Arguments["properties"].(map[string]interface{})

	res, err := s.weaviateConn.InsertOne(context.Background(), targetCol, props)
	if err != nil {
		return mcp.NewToolResultErrorFromErr("failed to insert object", err), nil
	}
	return mcp.NewToolResultText(res.ID.String()), nil
}

func (s *MCPServer) weaviateQuery(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	targetCol := s.parseTargetCollection(req)
	query := req.Params.Arguments["query"].(string)
	// TODO: how to enforce `Required` within the sdk so we don't have to validate here
	props := req.Params.Arguments["targetProperties"].([]interface{})
	var targetProps []string
	{
		for _, prop := range props {
			typed, ok := prop.(string)
			if !ok {
				return mcp.NewToolResultError("targetProperties must contain only strings"), nil
			}
			targetProps = append(targetProps, typed)
		}
	}
	// Parse optional filter
	var whereFilter map[string]interface{}
	if filter, ok := req.Params.Arguments["where"]; ok {
		if filterMap, ok := filter.(map[string]interface{}); ok {
			whereFilter = filterMap
		}
	}

	// Parse optional limit and offset
	var limit, offset *int
	if limitVal, ok := req.Params.Arguments["limit"]; ok {
		if limitFloat, ok := limitVal.(float64); ok {
			limitInt := int(limitFloat)
			limit = &limitInt
		}
	}
	if offsetVal, ok := req.Params.Arguments["offset"]; ok {
		if offsetFloat, ok := offsetVal.(float64); ok {
			offsetInt := int(offsetFloat)
			offset = &offsetInt
		}
	}

	res, err := s.weaviateConn.Query(context.Background(), targetCol, query, targetProps, whereFilter, limit, offset)
	if err != nil {
		return mcp.NewToolResultErrorFromErr("failed to process query", err), nil
	}
	return mcp.NewToolResultText(res), nil
}

func (s *MCPServer) parseTargetCollection(req mcp.CallToolRequest) string {
	var (
		targetCol = s.defaultCollection
	)
	col, ok := req.Params.Arguments["collection"].(string)
	if ok {
		targetCol = col
	}
	return targetCol
}

