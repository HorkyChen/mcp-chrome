"""
HTTP Server implementation using FastAPI
"""

import asyncio
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import json

from constants import (
    NATIVE_SERVER_PORT, HOST, HTTPStatus, ErrorMessages,
    EXTENSION_REQUEST_TIMEOUT
)
from mcp_server import mcp_server_instance


class Server:
    def __init__(self):
        self.app = FastAPI(title="MCP Chrome Bridge")
        self.is_running = False
        self.native_host = None
        self.transports_map: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        self.server_task: Optional[asyncio.Task] = None
        self.setup_middleware()
        self.setup_routes()

    def setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/ask-extension")
        async def ask_extension(request: Request):
            """Endpoint for pinging extension"""
            if not self.native_host:
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=ErrorMessages.NATIVE_HOST_NOT_AVAILABLE
                )

            if not self.is_running:
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=ErrorMessages.SERVER_NOT_RUNNING
                )

            try:
                query_params = dict(request.query_params)
                extension_response = await self.native_host.send_request_to_extension_and_wait(
                    query_params,
                    "process_data",
                    EXTENSION_REQUEST_TIMEOUT * 1000
                )
                return {"status": "success", "data": extension_response}

            except Exception as e:
                if "timed out" in str(e):
                    raise HTTPException(
                        status_code=HTTPStatus.GATEWAY_TIMEOUT,
                        detail=ErrorMessages.REQUEST_TIMEOUT
                    )
                else:
                    raise HTTPException(
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail=f"Failed to get response from extension: {str(e)}"
                    )

        @self.app.get("/sse")
        async def sse_endpoint():
            """SSE endpoint for MCP communication"""
            try:
                # For simplicity, we'll return a basic SSE stream
                # In a full implementation, this would integrate with MCP's SSE transport
                async def event_stream():
                    session_id = str(uuid.uuid4())
                    yield f"data: {json.dumps({'sessionId': session_id})}\n\n"

                    # Keep connection alive
                    while True:
                        await asyncio.sleep(30)  # Heartbeat every 30 seconds
                        yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

                return StreamingResponse(
                    event_stream(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive"
                    }
                )

            except Exception as e:
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=ErrorMessages.INTERNAL_SERVER_ERROR
                )

        @self.app.post("/messages")
        async def post_messages(
            request: Request,
            session_id: str = Query(None)
        ):
            """Handle SSE POST messages"""
            if not session_id:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Missing session ID"
                )

            # In a full implementation, this would handle MCP message routing
            return {"status": "received"}

        @self.app.post("/mcp")
        async def mcp_post(request: Request):
            """Handle MCP client-to-server messages"""
            session_id = request.headers.get("mcp-session-id")
            body = await request.body()

            try:
                # Parse JSON body
                message = json.loads(body.decode('utf-8'))

                # Handle initialize request
                if message.get("method") == "initialize":
                    if not session_id:
                        session_id = str(uuid.uuid4())

                    # Store session
                    self.transports_map[session_id] = {"initialized": True}

                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {
                            "protocolVersion": "1.0.0",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "ChromeMcpServer",
                                "version": "1.0.0"
                            }
                        }
                    }

                # Handle list-tools request
                elif message.get("method") == "tools/list":
                    tools = await mcp_server_instance.server.list_tools()
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {
                            "tools": [tool.model_dump() for tool in tools]
                        }
                    }

                # Handle tool call request
                elif message.get("method") == "tools/call":
                    params = message.get("params", {})
                    name = params.get("name")
                    arguments = params.get("arguments", {})

                    result = await mcp_server_instance.handle_tool_call(name, arguments)
                    return {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": result.model_dump()
                    }

                # Handle other MCP requests
                return {"status": "processed"}

            except Exception as e:
                self.logger.error(f"MCP request processing error: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id") if 'message' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }

        @self.app.get("/mcp")
        async def mcp_get(request: Request):
            """Handle MCP SSE connections"""
            session_id = request.headers.get("mcp-session-id")

            if not session_id or session_id not in self.transports_map:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=ErrorMessages.INVALID_SSE_SESSION
                )

            async def event_stream():
                while True:
                    await asyncio.sleep(1)
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )

        @self.app.delete("/mcp")
        async def mcp_delete(request: Request):
            """Handle MCP session deletion"""
            session_id = request.headers.get("mcp-session-id")

            if not session_id or session_id not in self.transports_map:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=ErrorMessages.INVALID_SESSION_ID
                )

            try:
                del self.transports_map[session_id]
                return Response(status_code=HTTPStatus.NO_CONTENT)

            except Exception as e:
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=ErrorMessages.MCP_SESSION_DELETION_ERROR
                )

    def set_native_host(self, native_host):
        """Associate native messaging host instance"""
        self.native_host = native_host

    async def start(self, port: int = NATIVE_SERVER_PORT, native_host=None):
        """Start the HTTP server"""
        if native_host:
            self.native_host = native_host

        if self.is_running:
            return

        try:
            config = uvicorn.Config(
                app=self.app,
                host=HOST,
                port=port,
                log_level="error"  # Reduce log noise
            )
            server = uvicorn.Server(config)

            # Start server in background task
            self.server_task = asyncio.create_task(server.serve())
            self.is_running = True

            # Wait a bit for server to start
            await asyncio.sleep(1.0)  # Give more time for server to start

            self.logger.info(f"HTTP server is running on {HOST}:{port}")

        except Exception as e:
            self.is_running = False
            self.logger.error(f"Failed to start HTTP server: {e}")
            raise e

    async def stop(self):
        """Stop the HTTP server"""
        if not self.is_running:
            return

        try:
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass

            self.is_running = False

        except Exception as e:
            self.is_running = False
            raise e

    def get_instance(self):
        """Get FastAPI app instance"""
        return self.app


# Global server instance
server_instance = Server()
