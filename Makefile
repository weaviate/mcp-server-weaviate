build:
	go build -o client/mcp-server .

run-client:
	cd client && go run client.go
