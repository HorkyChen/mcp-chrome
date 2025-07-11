"""
Native Messaging Host for Chrome extension communication
"""

import asyncio
import json
import struct
import sys
import uuid
from typing import Dict, Any, Optional, Callable
import logging
from constants import NativeMessageType, DEFAULT_REQUEST_TIMEOUT


class PendingRequest:
    def __init__(self, future: asyncio.Future, timeout_handle: asyncio.Handle):
        self.future = future
        self.timeout_handle = timeout_handle


class NativeMessagingHost:
    def __init__(self):
        self.associated_server = None
        self.pending_requests: Dict[str, PendingRequest] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)

    def set_server(self, server_instance):
        """Associate server instance"""
        self.associated_server = server_instance

    async def start(self):
        """Start native messaging host"""
        try:
            self.running = True
            await self.setup_message_handling()
        except Exception as e:
            self.logger.error(f"Failed to start native messaging host: {e}")
            sys.exit(1)

    async def setup_message_handling(self):
        """Setup message handling for stdin/stdout communication"""
        loop = asyncio.get_event_loop()

        # Create reader for stdin
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        transport, _ = await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        try:
            while self.running:
                # Read message length (4 bytes)
                length_data = await reader.readexactly(4)
                if not length_data:
                    break

                message_length = struct.unpack('<I', length_data)[0]

                # Read message content
                message_data = await reader.readexactly(message_length)
                if not message_data:
                    break

                try:
                    message = json.loads(message_data.decode('utf-8'))
                    await self.handle_message(message)
                except json.JSONDecodeError as e:
                    self.send_error(f"Failed to parse message: {e}")

        except asyncio.IncompleteReadError:
            # Chrome extension disconnected
            pass
        except Exception as e:
            self.logger.error(f"Error in message handling: {e}")
        finally:
            transport.close()
            await self.cleanup()

    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming message from Chrome extension"""
        if not isinstance(message, dict):
            self.send_error("Invalid message format")
            return

        # Handle response to our request
        if "responseToRequestId" in message:
            request_id = message["responseToRequestId"]
            if request_id in self.pending_requests:
                pending = self.pending_requests[request_id]
                pending.timeout_handle.cancel()

                if "error" in message:
                    pending.future.set_exception(Exception(message["error"]))
                else:
                    pending.future.set_result(message.get("payload"))

                del self.pending_requests[request_id]
            return

        # Handle directive messages
        try:
            message_type = message.get("type")

            if message_type == NativeMessageType.START.value:
                port = message.get("payload", {}).get("port", 3000)
                await self.start_server(port)
            elif message_type == NativeMessageType.STOP.value:
                await self.stop_server()
            elif message_type == "ping_from_extension":
                self.send_message({"type": "pong_to_extension"})
            else:
                if "responseToRequestId" not in message:
                    self.send_error(f"Unknown message type: {message_type}")

        except Exception as e:
            self.send_error(f"Failed to handle directive message: {e}")

    async def send_request_to_extension_and_wait(
        self,
        message_payload: Any,
        message_type: str = "request_data",
        timeout_ms: int = DEFAULT_REQUEST_TIMEOUT * 1000
    ) -> Any:
        """Send request to Chrome extension and wait for response"""
        request_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()

        # Setup timeout
        def timeout_callback():
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
                if not future.done():
                    future.set_exception(Exception(f"Request timed out after {timeout_ms}ms"))

        timeout_handle = asyncio.get_event_loop().call_later(
            timeout_ms / 1000, timeout_callback
        )

        # Store pending request
        self.pending_requests[request_id] = PendingRequest(future, timeout_handle)

        # Send message
        self.send_message({
            "type": message_type,
            "payload": message_payload,
            "requestId": request_id
        })

        return await future

    async def start_server(self, port: int):
        """Start HTTP server"""
        if not self.associated_server:
            self.send_error("Internal error: server instance not set")
            return

        try:
            if self.associated_server.is_running:
                self.send_message({
                    "type": NativeMessageType.ERROR.value,
                    "payload": {"message": "Server is already running"}
                })
                return

            await self.associated_server.start(port, self)

            self.send_message({
                "type": NativeMessageType.SERVER_STARTED.value,
                "payload": {"port": port}
            })

        except Exception as e:
            self.send_error(f"Failed to start server: {e}")

    async def stop_server(self):
        """Stop HTTP server"""
        if not self.associated_server:
            self.send_error("Internal error: server instance not set")
            return

        try:
            if not self.associated_server.is_running:
                self.send_message({
                    "type": NativeMessageType.ERROR.value,
                    "payload": {"message": "Server is not running"}
                })
                return

            await self.associated_server.stop()

            self.send_message({
                "type": NativeMessageType.SERVER_STOPPED.value
            })

        except Exception as e:
            self.send_error(f"Failed to stop server: {e}")

    def send_message(self, message: Dict[str, Any]):
        """Send message to Chrome extension"""
        try:
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            length_bytes = struct.pack('<I', len(message_bytes))

            # Write to stdout
            sys.stdout.buffer.write(length_bytes + message_bytes)
            sys.stdout.buffer.flush()

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")

    def send_error(self, error_message: str):
        """Send error message to Chrome extension"""
        self.send_message({
            "type": NativeMessageType.ERROR_FROM_NATIVE_HOST.value,
            "payload": {"message": error_message}
        })

    async def cleanup(self):
        """Clean up resources"""
        self.running = False

        # Reject all pending requests
        for pending in self.pending_requests.values():
            pending.timeout_handle.cancel()
            if not pending.future.done():
                pending.future.set_exception(
                    Exception("Native host is shutting down or Chrome disconnected.")
                )
        self.pending_requests.clear()

        # Stop server if running
        if self.associated_server and self.associated_server.is_running:
            try:
                await self.associated_server.stop()
            except Exception as e:
                self.logger.error(f"Error stopping server during cleanup: {e}")


# Global instance
native_messaging_host_instance = NativeMessagingHost()
