package main

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Printf("Warning: .env file not found or could not be loaded: %v", err)
	}
	
	transport := getEnvWithDefault("MCP_TRANSPORT", "stdio")
	s, err := NewMCPServer()
	if err != nil {
		log.Fatalf("failed to start mcp server: %v", err)
	}
	
	switch transport {
	case "sse":
		s.ServeSSE()
	case "stdio":
		s.ServeStdio()
	default:
		log.Fatalf("unsupported transport: %s. Supported transports: [stdio, sse]", transport)
	}
}

func getEnvWithDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
