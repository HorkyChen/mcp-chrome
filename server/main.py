#!/usr/bin/env python3
"""
MCP Chrome Bridge Python - Main entry point
"""

import asyncio
import sys
import signal
import logging
from http_server import server_instance
from native_messaging_host import native_messaging_host_instance

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    try:
        # Associate server and native host (like TypeScript version)
        server_instance.set_native_host(native_messaging_host_instance)
        native_messaging_host_instance.set_server(server_instance)

        # Setup signal handlers for graceful shutdown
        def signal_handler():
            logger.info("Received shutdown signal")
            sys.exit(0)

        # Register signal handlers
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, lambda s, f: signal_handler())

        # Start HTTP server immediately, don't wait for Chrome extension START message
        from constants import NATIVE_SERVER_PORT
        logger.info(f"Starting HTTP server on port {NATIVE_SERVER_PORT}")
        await server_instance.start(NATIVE_SERVER_PORT, native_messaging_host_instance)
        logger.info(f"HTTP server started successfully on http://127.0.0.1:{NATIVE_SERVER_PORT}")        # Then start native messaging host for Chrome extension communication
        logger.info("Starting native messaging host...")
        logger.info("Chrome extension can now connect to communicate with the server")

        # Keep native messaging host running in a loop to handle reconnections
        while True:
            try:
                # Start native messaging host (this will block until Chrome disconnects)
                await native_messaging_host_instance.start()
            except Exception as e:
                logger.error(f"Native messaging host error: {e}")

            # Chrome extension disconnected, wait a bit and try to restart
            logger.info("Chrome extension disconnected, waiting for reconnection...")
            await asyncio.sleep(1)  # Brief pause before attempting restart

    except Exception as e:
        logger.error(f"Fatal error in main(): {e}")
        sys.exit(1)


def handle_exit():
    """Handle process exit"""
    logger.info("Process exiting")


def handle_uncaught_exception(exctype, value, traceback):
    """Handle uncaught exceptions"""
    logger.error(f"Uncaught exception: {exctype.__name__}: {value}")
    sys.exit(1)


def handle_unhandled_rejection(loop, context):
    """Handle unhandled promise rejections"""
    logger.warning(f"Unhandled rejection: {context}")
    # Don't exit immediately, let the program continue running


if __name__ == "__main__":
    # Setup exception handlers
    sys.excepthook = handle_uncaught_exception

    # Setup event loop exception handler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(handle_unhandled_rejection)

    try:
        print("MCP Server is running....")
        # Run main
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        handle_exit()
        loop.close()
