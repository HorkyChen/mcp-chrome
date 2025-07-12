#!/usr/bin/env python3
"""
Interactive Chrome Extension Communication Test
"""

import json
import struct
import sys
import asyncio
import signal
from pathlib import Path

# Add current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from native_messaging_host import native_messaging_host_instance
from http_server import server_instance


class ChromeExtensionSimulator:
    """Simulate Chrome extension communication for testing"""

    def __init__(self):
        self.running = True

    def send_message(self, message):
        """Send message via stdout (to simulate Chrome -> Native Host)"""
        message_json = json.dumps(message)
        message_bytes = message_json.encode('utf-8')
        length_bytes = struct.pack('<I', len(message_bytes))

        sys.stdout.buffer.write(length_bytes + message_bytes)
        sys.stdout.buffer.flush()

    async def simulate_chrome_interaction(self):
        """Simulate Chrome extension interactions"""
        print("🔧 Simulating Chrome Extension Interactions", file=sys.stderr)

        # Wait a bit for native host to start
        await asyncio.sleep(1)

        # 1. Send START message
        print("📤 Sending START message to native host", file=sys.stderr)
        start_message = {
            "type": "start",
            "payload": {"port": 12306}
        }
        self.send_message(start_message)
        await asyncio.sleep(2)

        # 2. Send ping message
        print("📤 Sending PING message", file=sys.stderr)
        ping_message = {
            "type": "ping_from_extension"
        }
        self.send_message(ping_message)
        await asyncio.sleep(1)

        # 3. Send tool call request
        print("📤 Sending tool call request", file=sys.stderr)
        tool_call_message = {
            "type": "call_tool",
            "requestId": "test-tool-call-123",
            "payload": {
                "name": "chrome_get_web_content",
                "args": {"url": "https://example.com"}
            }
        }
        self.send_message(tool_call_message)
        await asyncio.sleep(3)

        # 4. Continue running for more tests
        print("✅ Basic tests completed. Keeping connection alive for manual testing...", file=sys.stderr)
        print("💡 You can now test with real Chrome extension!", file=sys.stderr)

        # Keep running
        while self.running:
            await asyncio.sleep(1)


async def main():
    """Run the test"""
    print("🚀 Starting Chrome Extension Communication Test", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # Setup signal handlers
    def signal_handler():
        print("\n🛑 Shutting down...", file=sys.stderr)
        sys.exit(0)

    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda s, f: signal_handler())

    # Associate server and native host
    server_instance.set_native_host(native_messaging_host_instance)
    native_messaging_host_instance.set_server(server_instance)

    # Create simulator
    simulator = ChromeExtensionSimulator()

    # Start both tasks
    tasks = [
        asyncio.create_task(native_messaging_host_instance.start()),
        asyncio.create_task(simulator.simulate_chrome_interaction())
    ]

    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
    finally:
        simulator.running = False


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
