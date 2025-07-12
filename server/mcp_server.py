"""
MCP Server implementation
"""

import asyncio
import logging
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult
from tools import TOOL_SCHEMAS
from native_messaging_host import native_messaging_host_instance
from constants import NativeMessageType
from logging_config import setup_logging, get_logger


class MCPServer:
    def __init__(self):
        self.server = Server("ChromeMcpServer", "1.0.0")

        # Configure logging for MCP server
        setup_logging("mcp-chrome-bridge-mcp", level=logging.INFO)
        self.logger = get_logger(__name__)

        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP request handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [Tool(**schema) for schema in TOOL_SCHEMAS]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            return await self.handle_tool_call(name, arguments)

    async def get_tools_list(self) -> List[Tool]:
        """Get the list of available tools"""
        return [Tool(**schema) for schema in TOOL_SCHEMAS]

    async def handle_tool_call(self, name: str, args: Dict[str, Any]) -> CallToolResult:
        """Handle tool call by forwarding to Chrome extension"""
        try:
            # Send request to Chrome extension and wait for response
            response = await native_messaging_host_instance.send_request_to_extension_and_wait(
                {"name": name, "args": args},
                NativeMessageType.CALL_TOOL.value,
                30000  # 30 second timeout
            )

            return CallToolResult(
                content=[TextContent(type="text", text=str(response))],
                isError=False
            )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error calling tool: {str(e)}")],
                isError=True
            )

    def get_server(self) -> Server:
        """Get the MCP server instance"""
        return self.server


# Global MCP server instance
mcp_server_instance = MCPServer()
