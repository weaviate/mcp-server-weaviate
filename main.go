package main

import (
	"log"
)

func main() {
	// TODO: get all WeaviateConn config from env
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
