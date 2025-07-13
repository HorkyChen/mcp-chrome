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

        # Configure logging for MCP server - file only to avoid stdio conflicts
        setup_logging("mcp-chrome-bridge-mcp", level=logging.INFO, file_only=True)
        self.logger = get_logger(__name__)

        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP request handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            self.logger.info("MCP Client requested tools list")
            tools = [Tool(**schema) for schema in TOOL_SCHEMAS]
            self.logger.info(f"Returning {len(tools)} tools to MCP client: {[tool.name for tool in tools]}")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            self.logger.info(f"MCP Client requested tool call: {name}")
            self.logger.info(f"Tool arguments: {arguments}")

            result = await self.handle_tool_call(name, arguments)

            if result.isError:
                self.logger.error(f"Tool call failed: {name} - {result.content[0].text if result.content else 'Unknown error'}")
            else:
                self.logger.info(f"Tool call successful: {name}")

            return result

    async def get_tools_list(self) -> List[Tool]:
        """Get the list of available tools"""
        self.logger.info("Internal tools list request")
        tools = [Tool(**schema) for schema in TOOL_SCHEMAS]
        self.logger.info(f"Available tools: {[tool.name for tool in tools]}")
        return tools

    async def handle_tool_call(self, name: str, args: Dict[str, Any]) -> CallToolResult:
        """Handle tool call by forwarding to Chrome extension"""
        try:
            self.logger.info(f"Forwarding tool call to Chrome extension: {name}")
            self.logger.info(f"Arguments being sent: {args}")

            # Send request to Chrome extension and wait for response
            response = await native_messaging_host_instance.send_request_to_extension_and_wait(
                {"name": name, "args": args},
                NativeMessageType.CALL_TOOL.value,
                30000  # 30 second timeout
            )

            self.logger.info(f"Received response from Chrome extension for tool {name}")
            self.logger.info(f"Response data: {response}")

            return CallToolResult(
                content=[TextContent(type="text", text=str(response))],
                isError=False
            )

        except Exception as e:
            self.logger.error(f"Error handling tool call {name}: {str(e)}")
            self.logger.error(f"Tool arguments: {args}")

            return CallToolResult(
                content=[TextContent(type="text", text=f"Error calling tool: {str(e)}")],
                isError=True
            )

    def get_server(self) -> Server:
        """Get the MCP server instance"""
        return self.server


# Global MCP server instance
mcp_server_instance = MCPServer()
