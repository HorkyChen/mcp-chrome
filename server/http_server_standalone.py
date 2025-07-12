#!/usr/bin/env python3
"""
MCP Chrome Bridge Python - Standalone HTTP server for testing
"""

import asyncio
import sys
import signal
import logging
from http_server import server_instance
from constants import NATIVE_SERVER_PORT, HOST
from logging_config import setup_logging, get_logger

# Setup logging for standalone server - file only to avoid stdio conflicts
setup_logging("mcp-chrome-bridge-standalone", level=logging.INFO, file_only=True)
logger = get_logger(__name__)


async def main(use_real_native_host=False):
    """Main entry point for standalone HTTP server"""
    try:
        # Setup signal handlers for graceful shutdown
        def signal_handler():
            logger.info("Received shutdown signal")
            sys.exit(0)

        # Register signal handlers
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, lambda s, f: signal_handler())

        if use_real_native_host:
            # Use real NativeMessagingHost (for testing with actual Chrome extension)
            from native_messaging_host import native_messaging_host_instance

            logger.info("Using real NativeMessagingHost - Chrome extension connection required")
            server_instance.set_native_host(native_messaging_host_instance)
            native_messaging_host_instance.set_server(server_instance)
        else:
            # Use mock native host for standalone testing
            class MockNativeHost:
                async def send_request_to_extension_and_wait(self, payload, message_type, timeout):
                    # Mock response since we don't have Chrome extension connected
                    logger.info(f"Mock: Received request for extension - {message_type}: {payload}")
                    return {
                        "status": "mock_success",
                        "message": "Mock response from standalone server (no Chrome extension connected)",
                        "payload": payload,
                        "mock": True
                    }

            # Set mock native host for testing
            mock_host = MockNativeHost()
            server_instance.set_native_host(mock_host)
            logger.info("Using MockNativeHost - no Chrome extension required")

        # Start HTTP server
        logger.info(f"Starting standalone HTTP server on {HOST}:{NATIVE_SERVER_PORT}")
        await server_instance.start(NATIVE_SERVER_PORT)
        logger.info(f"HTTP server started successfully!")
        logger.info(f"Server is accessible at: http://{HOST}:{NATIVE_SERVER_PORT}")
        logger.info("Available endpoints:")
        logger.info("  GET  /ask-extension - Test extension communication")
        logger.info("  GET  /sse - SSE endpoint for MCP")
        logger.info("  POST /mcp - MCP endpoint")
        logger.info("  GET  /mcp - MCP SSE")
        logger.info("")
        logger.info("Test commands:")
        logger.info(f"  curl http://{HOST}:{NATIVE_SERVER_PORT}/ask-extension")
        if not use_real_native_host:
            logger.info("  (Mock responses will be returned)")
        logger.info("Press Ctrl+C to stop the server")

        # Keep the server running
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    # Check command line arguments
    use_real_host = "--real-native-host" in sys.argv

    try:
        asyncio.run(main(use_real_native_host=use_real_host))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
