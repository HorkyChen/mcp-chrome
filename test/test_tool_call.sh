#!/bin/bash

echo "=== Testing Tool Call ==="

# First, initialize to get session ID
echo "1. Initialize session..."
INIT_RESPONSE=$(curl -s -v -X POST http://localhost:12306/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }' 2>&1)

echo "Initialize response:"
echo "$INIT_RESPONSE"

# Extract session ID
SESSION_ID=$(echo "$INIT_RESPONSE" | grep -i "mcp-session-id:" | head -1 | cut -d: -f2 | tr -d ' \r\n')

if [ -n "$SESSION_ID" ]; then
    echo "Found Session ID: $SESSION_ID"

    echo -e "\n2. Call tool: get_windows_and_tabs..."
    curl -v -X POST http://localhost:12306/mcp \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "mcp-session-id: $SESSION_ID" \
      -d '{
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
          "name": "get_windows_and_tabs",
          "arguments": {}
        }
      }'
else
    echo "❌ No Session ID found - cannot proceed with tool call test"
fi
