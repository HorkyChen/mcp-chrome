#!/usr/bin/env python3
"""
Test Native Messaging Host - simulate Chrome extension communication
"""

import asyncio
import json
import struct
import sys
import subprocess
import tempfile
import os
from pathlib import Path


def send_native_message(process, message):
    """Send a message to native messaging host"""
    message_json = json.dumps(message)
    message_bytes = message_json.encode('utf-8')
    length_bytes = struct.pack('<I', len(message_bytes))

    process.stdin.write(length_bytes + message_bytes)
    process.stdin.flush()


def read_native_message(process):
    """Read a message from native messaging host"""
    # Read message length
    length_data = process.stdout.read(4)
    if not length_data:
        return None

    message_length = struct.unpack('<I', length_data)[0]

    # Read message content
    message_data = process.stdout.read(message_length)
    if not message_data:
        return None

    return json.loads(message_data.decode('utf-8'))


async def test_native_host():
    """Test the native messaging host"""
    print("Testing Native Messaging Host...")

    # Get the path to main.py
    script_dir = Path(__file__).parent
    main_script = script_dir / "main.py"

    # Start the native messaging host
    process = subprocess.Popen(
        [sys.executable, str(main_script)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Test 1: Send START message
        print("1. Sending START message...")
        start_message = {
            "type": "start",
            "payload": {"port": 12306}
        }
        send_native_message(process, start_message)

        # Wait for response
        await asyncio.sleep(2)

        # Test 2: Send ping message
        print("2. Sending PING message...")
        ping_message = {
            "type": "ping_from_extension"
        }
        send_native_message(process, ping_message)

        # Wait for pong response
        await asyncio.sleep(1)

        # Test 3: Send tool call request
        print("3. Sending tool call request...")
        tool_call_message = {
            "type": "call_tool",
            "requestId": "test-123",
            "payload": {
                "name": "chrome_screenshot",
                "args": {"storeBase64": True}
            }
        }
        send_native_message(process, tool_call_message)

        # Wait for response
        await asyncio.sleep(2)

        # Test 4: Send STOP message
        print("4. Sending STOP message...")
        stop_message = {
            "type": "stop"
        }
        send_native_message(process, stop_message)

        # Wait and check if process terminates
        await asyncio.sleep(2)

        print("Test completed!")

    except Exception as e:
        print(f"Test error: {e}")
    finally:
        # Clean up
        if process.poll() is None:
            process.terminate()
            await asyncio.sleep(1)
            if process.poll() is None:
                process.kill()


if __name__ == "__main__":
    asyncio.run(test_native_host())
