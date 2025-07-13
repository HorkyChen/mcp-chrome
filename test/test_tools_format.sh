#!/bin/bash

echo "=== Testing Tools List Format ==="

# Initialize session first
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

    echo -e "\n2. Get tools list..."
    curl -s -X POST http://localhost:12306/mcp \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "mcp-session-id: $SESSION_ID" \
      -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
      }' | python3 -m json.tool
else
    echo "❌ No Session ID found - cannot proceed with tools list test"
fi
