# Build stage
FROM golang:1.23.1-alpine AS builder

# Install git (needed for go mod download)
RUN apk add --no-cache git

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o mcp-server .

# Final stage
FROM alpine:latest

# Install ca-certificates for HTTPS connections to external services
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN adduser -D -s /bin/sh mcpuser

WORKDIR /home/mcpuser

# Copy the binary from builder stage
COPY --from=builder /app/mcp-server .

# Change ownership to non-root user
RUN chown -R mcpuser:mcpuser /home/mcpuser

# Switch to non-root user
USER mcpuser

# Expose port (if needed for future HTTP transport)
EXPOSE 8080

# Run the MCP server
CMD ["./mcp-server"]