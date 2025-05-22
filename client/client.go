package main

import (
	"context"
	"fmt"
	"log"

	"github.com/mark3labs/mcp-go/client"
	"github.com/mark3labs/mcp-go/mcp"
)

func main() {
	ctx := context.Background()
	cmd := "./mcp-server"

	c, err := newMCPClient(ctx, cmd)
	if err != nil {
		log.Fatal(err)
	}
	defer c.Close()

	{
		insertRes, err := insertRequest(ctx, c)
		if err != nil {
			log.Fatal(err)
		}
		log.Printf("insert-one response: %+v", insertRes)
	}
	{
		queryRes, err := queryRequest(ctx, c)
		if err != nil {
			log.Fatal(err)
		}
		log.Printf("query response: %+v", queryRes)
	}
}

func newMCPClient(ctx context.Context, cmd string) (*client.Client, error) {
	c, _ := client.NewStdioMCPClient(cmd, nil)
	initRes, err := c.Initialize(ctx, mcp.InitializeRequest{})
	if err != nil {
		return nil, fmt.Errorf("failed to init client: %w", err)
	}
	log.Printf("init result: %+v", initRes)
	if err := c.Start(ctx); err != nil {
		return nil, fmt.Errorf("failed to start client: %w", err)
	}
	if err := c.Ping(ctx); err != nil {
		return nil, fmt.Errorf("failed to ping server: %w", err)
	}
	return c, nil
}

func insertRequest(ctx context.Context, c *client.Client) (*mcp.CallToolResult, error) {
	request := mcp.CallToolRequest{}
	request.Params.Name = "weaviate-insert-one"
	request.Params.Arguments = map[string]interface{}{
		"collection": "WorldMap",
		"properties": map[string]interface{}{
			"continent": "Europe",
			"country":   "Spain",
			"city":      "Valencia",
		},
	}
	log.Printf("insert request: %+v", request)
	res, err := c.CallTool(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to call insert-one tool: %v", err)
	}
	return res, nil
}

func queryRequest(ctx context.Context, c *client.Client) (*mcp.CallToolResult, error) {
	request := mcp.CallToolRequest{}
	request.Params.Name = "weaviate-query"
	request.Params.Arguments = map[string]interface{}{
		"collection":       "WorldMap",
		"query":            "What country is Valencia in?",
		"targetProperties": []string{"continent", "country", "city"},
	}
	log.Printf("query request: %+v", request)
	res, err := c.CallTool(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to call query tool: %v", err)
	}
	return res, nil
}
