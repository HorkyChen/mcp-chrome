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
        # Associate server and native host
        server_instance.set_native_host(native_messaging_host_instance)
        native_messaging_host_instance.set_server(server_instance)

        # Setup signal handlers for graceful shutdown
        def signal_handler():
            logger.info("Received shutdown signal")
            sys.exit(0)

        # Register signal handlers
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, lambda s, f: signal_handler())

        # Start native messaging host
        await native_messaging_host_instance.start()

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
