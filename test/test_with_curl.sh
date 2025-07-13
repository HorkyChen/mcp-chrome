#!/bin/bash

echo "=== Initialize Request ==="
curl -v -X POST http://localhost:12306/mcp \
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
  }' 2>&1 | tee initialize_response.txt

echo -e "\n\n=== Extracting Session ID ==="
# Try to extract session ID from headers
SESSION_ID=$(grep -i "mcp-session-id\|x-session-id\|session-id" initialize_response.txt | head -1 | cut -d: -f2 | tr -d ' \r\n')

if [ -n "$SESSION_ID" ]; then
    echo "Found Session ID: $SESSION_ID"

    echo -e "\n=== Tools List Request ==="
    curl -v -X POST http://localhost:12306/mcp \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "mcp-session-id: $SESSION_ID" \
      -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
      }'
else
    echo "No Session ID found in headers"
    echo "Full response saved to initialize_response.txt"
fi

