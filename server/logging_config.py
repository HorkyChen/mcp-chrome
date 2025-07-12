"""
Logging configuration for MCP Chrome Bridge Python server
Configures logging to output to both console and log files
"""

import logging
import logging.handlers
import sys
import os
from datetime import datetime

# Global flag to track if shared file handler has been added
_shared_file_handler_added = False


def setup_logging(name: str = "mcp-chrome-bridge", level: int = logging.INFO, use_stdout: bool = True, file_only: bool = False):
    """
    Setup logging to output to both console and log files

    Args:
        name: The logger name (used as identifier in log files)
        level: Logging level (default: INFO)
        use_stdout: Whether to use stdout for console output (False for native messaging host)
        file_only: If True, only log to files, no console output (for native messaging host)
    """
    global _shared_file_handler_added

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Create logs directory in the same directory as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Get the shared log filename
    today = datetime.now().strftime('%Y%m%d')
    shared_log_filename = os.path.join(logs_dir, f'mcp-chrome-bridge-{today}.log')

    # Check existing handlers
    current_stdout_handler = None

    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and hasattr(handler, 'stream'):
            if handler.stream in (sys.stdout, sys.stderr):
                current_stdout_handler = handler
                break

    # For file_only mode, remove any console handlers
    if file_only:
        handlers_to_remove = []
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and hasattr(handler, 'stream'):
                if handler.stream in (sys.stdout, sys.stderr):
                    handlers_to_remove.append(handler)

        for handler in handlers_to_remove:
            logger.removeHandler(handler)

        should_add_console = False
    else:
        # For normal mode, check if we need to reconfigure console handler
        should_reconfigure_console = (
            current_stdout_handler is None or
            (current_stdout_handler and
             ((use_stdout and current_stdout_handler.stream != sys.stdout) or
              (not use_stdout and current_stdout_handler.stream != sys.stderr)))
        )

        if should_reconfigure_console and current_stdout_handler:
            logger.removeHandler(current_stdout_handler)
            current_stdout_handler = None

        should_add_console = current_stdout_handler is None

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add console handler if needed
    if should_add_console:
        console_stream = sys.stdout if use_stdout else sys.stderr
        console_handler = logging.StreamHandler(console_stream)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add shared file handler only once globally
    if not _shared_file_handler_added:
        try:
            # Use rotating file handler to prevent logs from growing too large
            file_handler = logging.handlers.RotatingFileHandler(
                shared_log_filename,
                maxBytes=10*1024*1024,  # 10MB per file
                backupCount=5,  # Keep 5 backup files
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            _shared_file_handler_added = True

            # Log that file logging is working (only once)
            logger.info(f"Shared file logging configured - all logs saved to {shared_log_filename}")

        except Exception as e:
            # Fallback: if file logging is not available, just use console
            logger.warning(f"Could not configure file handler: {e}")
            if file_only:
                logger.info("File-only mode requested but file logging failed")

    return logger


def get_logger(module_name: str = None):
    """
    Get a logger instance for a specific module

    Args:
        module_name: Name of the module (if None, uses root logger)
    """
    if module_name:
        return logging.getLogger(module_name)
    return logging.getLogger()


# Note: No automatic logging configuration on import
# Each module should explicitly call setup_logging() with appropriate parameters
