"""
Constants for the MCP Chrome Bridge Python server
"""

from enum import Enum


class NativeMessageType(Enum):
    START = "start"
    STARTED = "started"
    STOP = "stop"
    STOPPED = "stopped"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    PROCESS_DATA = "process_data"
    PROCESS_DATA_RESPONSE = "process_data_response"
    CALL_TOOL = "call_tool"
    CALL_TOOL_RESPONSE = "call_tool_response"
    SERVER_STARTED = "server_started"
    SERVER_STOPPED = "server_stopped"
    ERROR_FROM_NATIVE_HOST = "error_from_native_host"
    CONNECT_NATIVE = "connectNative"
    PING_NATIVE = "ping_native"
    DISCONNECT_NATIVE = "disconnect_native"


# Server configuration
NATIVE_SERVER_PORT = 56889
HOST = "127.0.0.1"

# Timeout constants (in seconds)
DEFAULT_REQUEST_TIMEOUT = 15
EXTENSION_REQUEST_TIMEOUT = 20
PROCESS_DATA_TIMEOUT = 20

# HTTP Status codes
class HTTPStatus:
    OK = 200
    NO_CONTENT = 204
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
    GATEWAY_TIMEOUT = 504


# Error messages
class ErrorMessages:
    NATIVE_HOST_NOT_AVAILABLE = "Native host connection not established."
    SERVER_NOT_RUNNING = "Server is not actively running."
    REQUEST_TIMEOUT = "Request to extension timed out."
    INVALID_MCP_REQUEST = "Invalid MCP request or session."
    INVALID_SESSION_ID = "Invalid or missing MCP session ID."
    INTERNAL_SERVER_ERROR = "Internal Server Error"
    MCP_SESSION_DELETION_ERROR = "Internal server error during MCP session deletion."
    MCP_REQUEST_PROCESSING_ERROR = "Internal server error during MCP request processing."
    INVALID_SSE_SESSION = "Invalid or missing MCP session ID for SSE."
