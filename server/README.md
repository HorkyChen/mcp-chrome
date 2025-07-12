# MCP Chrome Bridge Python

A Python implementation of the MCP Chrome Bridge server that provides the same functionality as the TypeScript version.

## Features

- Native messaging host for Chrome extension communication
- HTTP server with MCP protocol support
- STDIO MCP server for direct integration
- Tool forwarding to Chrome extension
- Cross-platform support (Windows, macOS, Linux)

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Register the native messaging host:

```bash
python cli.py register
```

## Usage

### 1. Native Messaging Mode (Production - like TypeScript version)
This is the main mode that works with Chrome extension:
```bash
python cli.py start
# or directly:
python main.py
```
This starts the native messaging host that communicates with Chrome via stdin/stdout. The HTTP server will automatically start when the Chrome extension connects.

### 2. Standalone HTTP Server (Testing)
For testing the HTTP API without Chrome extension:
```bash
python cli.py start-http
# or directly:
python http_server_standalone.py
```
This starts only the HTTP server with mock responses on port 12306.

### 3. STDIO MCP Server (Direct MCP integration)
For direct MCP client integration:
```bash
python cli.py start-stdio
# or directly:
python mcp_server_stdio.py
```

### Register/unregister native messaging host:

```bash
# Register for current user
python cli.py register

# Register system-wide (requires admin/sudo)
python cli.py register --system

# Force re-registration
python cli.py register --force

# Unregister
python cli.py unregister
```

## Architecture

The Python implementation mirrors the TypeScript structure:

- `main.py` - Main entry point, coordinates native host and HTTP server
- `native_messaging_host.py` - Handles stdin/stdout communication with Chrome
- `http_server.py` - FastAPI-based HTTP server with MCP endpoints
- `mcp_server.py` - MCP server implementation with tool handling
- `mcp_server_stdio.py` - Standalone STDIO MCP server
- `tools.py` - Tool schemas and definitions
- `constants.py` - Configuration constants
- `cli.py` - Command-line interface

## Configuration

The STDIO server uses `stdio-config.json` to configure the HTTP server URL:

```json
{
  "url": "http://127.0.0.1:56889"
}
```

## Tool Support

Supports all the same tools as the TypeScript version:

- Browser navigation and control
- Screenshots and web content fetching
- Element interaction (click, fill, keyboard)
- Network request handling
- History and bookmark management
- Script injection and console access

## Requirements

- Python 3.8+
- Chrome browser with MCP Chrome extension
- Required Python packages (see requirements.txt)
