#!/usr/bin/env python3
"""
MCP Chrome Bridge Python - STDIO MCP Server
This provides a standalone MCP server that communicates via STDIO
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
import httpx
from mcp.server.stdio import StdioServerTransport
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult
from tools import TOOL_SCHEMAS
from logging_config import setup_logging, get_logger

# Setup logging for stdio server
setup_logging("mcp-chrome-bridge-stdio", level=logging.INFO)
logger = get_logger(__name__)


def load_config():
    """Load configuration from stdio-config.json"""
    try:
        config_path = Path(__file__).parent / "stdio-config.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load stdio-config.json: {e}")
        raise Exception("Configuration file stdio-config.json not found or invalid")


class StdioMCPServer:
    def __init__(self):
        self.server = Server("StdioChromeMcpServer", "1.0.0")
        self.http_client = None
        self.config = None
        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP request handlers"""

        @self.server.list_tools()
        async def list_tools():
            """List available tools"""
            return [Tool(**schema) for schema in TOOL_SCHEMAS]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool calls by forwarding to HTTP MCP server"""
            return await self.handle_tool_call(name, arguments)

    async def ensure_http_client(self):
        """Ensure HTTP client is connected to the MCP server"""
        try:
            if self.http_client:
                # Test connection with a ping
                response = await self.http_client.get(f"{self.config['url']}/ask-extension")
                if response.status_code == 200:
                    return self.http_client
        except Exception:
            pass

        # Create new client
        self.config = load_config()
        self.http_client = httpx.AsyncClient(timeout=30.0)

        return self.http_client

    async def handle_tool_call(self, name: str, args: dict) -> CallToolResult:
        """Handle tool call by forwarding to HTTP MCP server"""
        try:
            client = await self.ensure_http_client()

            # Forward the tool call to the HTTP server
            response = await client.post(
                f"{self.config['url']}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": name,
                        "arguments": args
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "mcp-session-id": "stdio-session"
                }
            )

            if response.status_code == 200:
                result = response.json()
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result))],
                    isError=False
                )
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error calling tool: {str(e)}")],
                isError=True
            )

    async def run(self):
        """Run the STDIO MCP server"""
        transport = StdioServerTransport()
        await self.server.run(transport)


async def main():
    """Main entry point"""
    try:
        server = StdioMCPServer()
        await server.run()
    except Exception as e:
        logger.error(f"Fatal error in Chrome MCP Server main(): {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
