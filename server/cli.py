#!/usr/bin/env python3
"""
CLI for MCP Chrome Bridge Python
"""

import argparse
import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from constants import HOST_NAME, EXTENSION_ID, DESCRIPTION
from logging_config import setup_logging, get_logger

# Setup logging for CLI
setup_logging("mcp-chrome-bridge-cli", level=logging.INFO)
logger = get_logger(__name__)


def get_python_path():
    """Get the path to the current Python executable"""
    return sys.executable


def write_python_path():
    """Write Python path for host scripts"""
    try:
        python_path = get_python_path()
        python_path_file = Path(__file__).parent / "python_path.txt"

        print(f"Writing Python path: {python_path}")
        with open(python_path_file, 'w') as f:
            f.write(python_path)
        print("✓ Python path written for host scripts")
    except Exception as e:
        print(f"⚠️ Failed to write Python path: {e}")


def get_manifest_path():
    """Get the native messaging manifest path"""
    system = platform.system()

    if system == "Windows":
        # Windows Registry locations
        return {
            "user": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\NativeMessagingHosts"),
            "system": os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\NativeMessagingHosts")
        }
    elif system == "Darwin":  # macOS
        return {
            "user": os.path.expanduser("~/Library/Application Support/Google/Chrome/NativeMessagingHosts"),
            "system": "/Library/Application Support/Google/Chrome/NativeMessagingHosts"
        }
    else:  # Linux
        return {
            "user": os.path.expanduser("~/.config/google-chrome/NativeMessagingHosts"),
            "system": "/etc/opt/chrome/native-messaging-hosts"
        }


def create_manifest():
    """Create native messaging manifest"""
    script_dir = Path(__file__).parent.absolute()
    python_executable = get_python_path()

    manifest = {
        "name": HOST_NAME,
        "description": DESCRIPTION,
        "path": str(script_dir / "main.py"),
        "type": "stdio",
        "allowed_origins": [
            f"chrome-extension://{EXTENSION_ID}/"
        ]
    }

    return manifest


def register_host(force=False, system_level=False):
    """Register native messaging host"""
    try:
        write_python_path()

        manifest_paths = get_manifest_path()
        target_dir = Path(manifest_paths["system"] if system_level else manifest_paths["user"])

        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        manifest_file = target_dir / f"{HOST_NAME}.json"

        if manifest_file.exists() and not force:
            print(f"Manifest already exists at {manifest_file}")
            print("Use --force to overwrite")
            return

        # Create and write manifest
        manifest = create_manifest()
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        # Make main.py executable
        main_script = Path(__file__).parent / "main.py"
        if main_script.exists():
            main_script.chmod(0o755)

        print(f"✓ Native messaging host registered at {manifest_file}")
        print(f"✓ Manifest points to: {manifest['path']}")

    except Exception as e:
        print(f"❌ Failed to register native messaging host: {e}")
        sys.exit(1)


def check_registration_status():
    """Check native messaging host registration status"""
    try:
        manifest_paths = get_manifest_path()

        user_manifest = Path(manifest_paths["user"]) / f"{HOST_NAME}.json"
        system_manifest = Path(manifest_paths["system"]) / f"{HOST_NAME}.json"

        user_registered = user_manifest.exists()
        system_registered = system_manifest.exists()

        print("📋 Native Messaging Host Registration Status:")
        print(f"  User-level:   {'Registered ✓' if user_registered else 'Not registered ✗'}")
        print(f"  System-level: {'Registered ✓' if system_registered else 'Not registered ✗'}")

        if user_registered:
            print(f"  User manifest:   {user_manifest}")
        if system_registered:
            print(f"  System manifest: {system_manifest}")

        if not user_registered and not system_registered:
            print("\n📝 To register:")
            print("  User-level:   python cli.py register")
            print("  System-level: python cli.py register --system")
        else:
            print("\n📝 To unregister:")
            if user_registered:
                print("  User-level:   python cli.py unregister")
            if system_registered:
                print("  System-level: python cli.py unregister --system")

        return {"user": user_registered, "system": system_registered}

    except Exception as e:
        print(f"❌ Failed to check registration status: {e}")
        return {"user": False, "system": False}


def unregister_host(system_level=False):
    """Unregister native messaging host"""
    try:
        # First check what's currently registered
        print("🔍 Checking current registration status...")
        status = check_registration_status()

        manifest_paths = get_manifest_path()
        target_dir = Path(manifest_paths["system"] if system_level else manifest_paths["user"])
        manifest_file = target_dir / f"{HOST_NAME}.json"

        level_name = "system-level" if system_level else "user-level"

        if manifest_file.exists():
            manifest_file.unlink()
            print(f"✓ {level_name.capitalize()} native messaging host unregistered from {manifest_file}")
        else:
            print(f"⚠️ No {level_name} manifest found at {manifest_file}")

        # Check if other level still exists
        other_level = "system" if not system_level else "user"
        if status[other_level]:
            print(f"📝 Note: {other_level.capitalize()}-level registration still exists.")
            print(f"   To remove it, run: python cli.py unregister {'--system' if other_level == 'system' else ''}")

    except Exception as e:
        print(f"❌ Failed to unregister native messaging host: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="MCP Chrome Bridge Python - CLI for managing native messaging host"
    )
    parser.add_argument("--version", action="version", version="1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register command
    register_parser = subparsers.add_parser("register", help="Register native messaging host")
    register_parser.add_argument("-f", "--force", action="store_true", help="Force re-registration")
    register_parser.add_argument("-s", "--system", action="store_true", help="Use system-level installation")

    # Unregister command
    unregister_parser = subparsers.add_parser("unregister", help="Unregister native messaging host")
    unregister_parser.add_argument("-s", "--system", action="store_true", help="Remove from system-level")

    # Status command
    status_parser = subparsers.add_parser("status", help="Check native messaging host registration status")    # Start command
    start_parser = subparsers.add_parser("start", help="Start the MCP server")

    # Start HTTP server only
    http_parser = subparsers.add_parser("start-http", help="Start only the HTTP server (for testing)")
    http_parser.add_argument("--real-native-host", action="store_true",
                           help="Use real NativeMessagingHost instead of mock (requires Chrome extension)")

    # Start STDIO command
    stdio_parser = subparsers.add_parser("start-stdio", help="Start the STDIO MCP server")

    args = parser.parse_args()

    if args.command == "register":
        register_host(force=args.force, system_level=args.system)
    elif args.command == "unregister":
        unregister_host(system_level=args.system)
    elif args.command == "status":
        check_registration_status()
    elif args.command == "start":
        from main import main as start_main
        try:
            asyncio.run(start_main())
        except KeyboardInterrupt:
            print("\nServer stopped")
    elif args.command == "start-http":
        from http_server_standalone import main as http_main
        try:
            # Pass the real-native-host flag
            use_real_host = getattr(args, 'real_native_host', False)
            asyncio.run(http_main(use_real_native_host=use_real_host))
        except KeyboardInterrupt:
            print("\nHTTP server stopped")
    elif args.command == "start-stdio":
        from mcp_server_stdio import main as stdio_main
        try:
            asyncio.run(stdio_main())
        except KeyboardInterrupt:
            print("\nSTDIO server stopped")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
