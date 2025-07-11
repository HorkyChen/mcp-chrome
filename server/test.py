#!/usr/bin/env python3
"""
Test script for MCP Chrome Bridge Python
"""

import asyncio
import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from http_server import server_instance
from native_messaging_host import native_messaging_host_instance
from mcp_server import mcp_server_instance


async def test_server_creation():
    """Test server instance creation"""
    print("Testing server creation...")

    # Test HTTP server
    assert server_instance is not None
    assert hasattr(server_instance, 'app')
    assert hasattr(server_instance, 'is_running')
    print("✓ HTTP server instance created")

    # Test native messaging host
    assert native_messaging_host_instance is not None
    assert hasattr(native_messaging_host_instance, 'pending_requests')
    print("✓ Native messaging host instance created")

    # Test MCP server
    assert mcp_server_instance is not None
    assert hasattr(mcp_server_instance, 'server')
    print("✓ MCP server instance created")


async def test_tool_schemas():
    """Test tool schemas"""
    print("Testing tool schemas...")

    from tools import TOOL_SCHEMAS, ToolNames

    assert len(TOOL_SCHEMAS) > 0
    print(f"✓ Found {len(TOOL_SCHEMAS)} tool schemas")

    # Check that first tool has required fields
    first_tool = TOOL_SCHEMAS[0]
    assert 'name' in first_tool
    assert 'description' in first_tool
    assert 'inputSchema' in first_tool
    print("✓ Tool schemas have correct structure")


async def test_config_loading():
    """Test configuration loading"""
    print("Testing configuration...")

    from constants import NativeMessageType, NATIVE_SERVER_PORT

    assert NATIVE_SERVER_PORT == 56889
    assert hasattr(NativeMessageType, 'START')
    print("✓ Configuration loaded correctly")


async def test_stdio_config():
    """Test STDIO configuration"""
    print("Testing STDIO configuration...")

    config_file = Path(__file__).parent / "stdio-config.json"
    assert config_file.exists()

    with open(config_file) as f:
        config = json.load(f)

    assert 'url' in config
    assert config['url'] == "http://127.0.0.1:56889"
    print("✓ STDIO configuration is valid")


async def main():
    """Run all tests"""
    print("Running MCP Chrome Bridge Python tests...\n")

    tests = [
        test_server_creation,
        test_tool_schemas,
        test_config_loading,
        test_stdio_config
    ]

    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            return False
        print()

    print("✅ All tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
