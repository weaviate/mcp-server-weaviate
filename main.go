package main

import (
	"log"

	"github.com/joho/godotenv"
)

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Printf("Warning: .env file not found or could not be loaded: %v", err)
	}
	
	// TODO: support SSEs
	// var transport string
	// flag.StringVar(&transport, "transport", "stdio", "Specifies the transport protocol. One of [stdio|sse]")
	s, err := NewMCPServer()
	if err != nil {
		log.Fatalf("failed to start mcp server: %v", err)
	}
	_ = s
	s.Serve()
}
