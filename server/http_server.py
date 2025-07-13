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
from logging_config import setup_logging, get_logger


class Server:
    def __init__(self):
        self.app = FastAPI(title="MCP Chrome Bridge")
        self.is_running = False
        self.native_host = None
        self.transports_map: Dict[str, Any] = {}

        # Configure logging for HTTP server - file only to avoid stdio conflicts
        setup_logging("mcp-chrome-bridge-http", level=logging.INFO, file_only=True)
        self.logger = get_logger(__name__)

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
            client_ip = request.client.host if request.client else "unknown"
            self.logger.info(f"HTTP POST /messages from {client_ip}, session: {session_id}")

            if not session_id:
                self.logger.error("HTTP POST /messages missing session ID")
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Missing session ID"
                )

            self.logger.info(f"HTTP POST /messages processed for session: {session_id}")
            # In a full implementation, this would handle MCP message routing
            return {"status": "received"}

        @self.app.post("/mcp")
        async def mcp_post(request: Request, response: Response):
            """Handle MCP client-to-server messages"""
            client_ip = request.client.host if request.client else "unknown"

            # Log the incoming request immediately
            self.logger.info(f"🔄 Incoming MCP request from {client_ip}")

            try:
                session_id = request.headers.get("mcp-session-id")
                self.logger.info(f"🔄 Session ID from headers: {session_id}")
            except Exception as e:
                self.logger.error(f"❌ Error getting session ID from headers: {e}")
                session_id = "testing-session-id"

            self.logger.info(f"🌐 HTTP MCP request from {client_ip}, session: {session_id}")

            try:
                body = await request.body()
                self.logger.info(f"🌐 HTTP request body size: {len(body)} bytes")

                if len(body) == 0:
                    self.logger.error("❌ Empty request body received")
                    return {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Empty request body",
                            "data": "No data received"
                        }
                    }
            except Exception as e:
                self.logger.error(f"❌ Error reading request body: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Failed to read request body",
                        "data": str(e)
                    }
                }

            try:
                # Parse JSON body
                message = json.loads(body.decode('utf-8'))
                method = message.get("method")
                msg_id = message.get("id")

                self.logger.info(f"HTTP MCP message: method={method}, id={msg_id}")
                self.logger.info(f"HTTP MCP message content: {json.dumps(message, indent=2)}")

                # Handle initialize request
                if method == "initialize":
                    self.logger.info("HTTP MCP client initialization request")
                    if not session_id:
                        session_id = str(uuid.uuid4())
                        self.logger.info(f"Generated new session ID: {session_id}")

                    # Store session
                    self.transports_map[session_id] = {"initialized": True}
                    self.logger.info(f"HTTP MCP session {session_id} initialized")

                    # For initialize, return SSE format response
                    response.headers["mcp-session-id"] = session_id
                    response.headers["Content-Type"] = "text/event-stream"
                    response.headers["Cache-Control"] = "no-cache"
                    response.headers["Connection"] = "keep-alive"

                    # Create SSE formatted response
                    sse_data = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "ChromeMcpServer",
                                "version": "1.0.0"
                            }
                        }
                    }

                    return StreamingResponse(
                        iter([f"event: message\ndata: {json.dumps(sse_data)}\n\n"]),
                        media_type="text/event-stream",
                        headers={
                            "mcp-session-id": session_id,
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive"
                        }
                    )
                # Handle list-tools request
                elif method == "tools/list":
                    self.logger.info("HTTP MCP client requested tools/list")
                    if session_id:
                        response.headers["mcp-session-id"] = session_id

                    tools = await mcp_server_instance.get_tools_list()
                    self.logger.info(f"HTTP returning {len(tools)} tools: {[tool.name for tool in tools]}")

                    # Return SSE format response for tools/list
                    sse_data = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "tools": [tool.model_dump(exclude_none=True) for tool in tools]
                        }
                    }

                    return StreamingResponse(
                        iter([f"event: message\ndata: {json.dumps(sse_data)}\n\n"]),
                        media_type="text/event-stream",
                        headers={
                            "mcp-session-id": session_id,
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive"
                        }
                    )

                # Handle tool call request
                elif method == "tools/call":
                    params = message.get("params", {})
                    name = params.get("name")
                    arguments = params.get("arguments", {})

                    self.logger.info(f"HTTP MCP client requested tools/call: {name}")
                    self.logger.info(f"HTTP tool arguments: {arguments}")

                    if session_id:
                        response.headers["mcp-session-id"] = session_id

                    result = await mcp_server_instance.handle_tool_call(name, arguments)

                    if result.isError:
                        self.logger.error(f"HTTP tool call failed: {name}")
                    else:
                        self.logger.info(f"HTTP tool call successful: {name}")

                    # Return SSE format response for tools/call
                    sse_data = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": result.model_dump(exclude_none=True)
                    }

                    return StreamingResponse(
                        iter([f"event: message\ndata: {json.dumps(sse_data)}\n\n"]),
                        media_type="text/event-stream",
                        headers={
                            "mcp-session-id": session_id,
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive"
                        }
                    )

                # Handle other MCP requests
                else:
                    self.logger.warning(f"❓ HTTP Unknown MCP method: {method}")
                    self.logger.warning(f"❓ HTTP Unknown request content: {json.dumps(message, indent=2)}")
                    self.logger.warning(f"❓ Available methods: initialize, tools/list, tools/call")

                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}",
                            "data": f"Available methods: initialize, tools/list, tools/call"
                        }
                    }

            except json.JSONDecodeError as e:
                self.logger.error(f"HTTP JSON decode error: {e}")
                self.logger.error(f"HTTP Invalid JSON body: {body}")
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error",
                        "data": str(e)
                    }
                }
            except Exception as e:
                self.logger.error(f"HTTP MCP request processing error: {e}")
                self.logger.error(f"HTTP Error processing message: {locals().get('message', 'Unknown message')}")
                return {
                    "jsonrpc": "2.0",
                    "id": locals().get('message', {}).get("id"),
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
            client_ip = request.client.host if request.client else "unknown"

            self.logger.info(f"HTTP SSE connection request from {client_ip}, session: {session_id}")

            if not session_id or session_id not in self.transports_map:
                self.logger.error(f"HTTP Invalid SSE session: {session_id}")
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=ErrorMessages.INVALID_SSE_SESSION
                )

            self.logger.info(f"HTTP SSE connection established for session: {session_id}")

            async def event_stream():
                self.logger.info(f"HTTP SSE event stream started for session: {session_id}")
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

        @self.app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
        async def catch_all(request: Request, path: str):
            """Catch all unhandled requests and log them"""
            client_ip = request.client.host if request.client else "unknown"
            method = request.method
            headers = dict(request.headers)
            query_params = dict(request.query_params)

            self.logger.warning(f"❓ Unhandled request: {method} /{path} from {client_ip}")
            self.logger.info(f"❓ Request headers: {headers}")
            self.logger.info(f"❓ Request query params: {query_params}")

            # Try to read body for non-GET requests
            if method not in ["GET", "HEAD", "OPTIONS"]:
                try:
                    body = await request.body()
                    if body:
                        self.logger.info(f"❓ Request body size: {len(body)} bytes")
                        # Try to decode as text for logging (limit to first 500 chars)
                        try:
                            body_text = body.decode('utf-8')[:500]
                            self.logger.info(f"❓ Request body preview: {body_text}")
                        except UnicodeDecodeError:
                            self.logger.info(f"❓ Request body (binary): {body[:50]}...")
                except Exception as e:
                    self.logger.warning(f"❓ Could not read request body: {e}")

            # Return appropriate error response
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Endpoint {method} /{path} not found"
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
