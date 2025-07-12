#!/usr/bin/env python3
"""
Extract Chrome Extension ID from manifest key
"""

import base64
import hashlib
import json


def get_extension_id_from_key(public_key_base64):
    """Calculate Chrome extension ID from public key"""
    # Decode the base64 key
    public_key_bytes = base64.b64decode(public_key_base64)

    # Calculate SHA256 hash
    sha256_hash = hashlib.sha256(public_key_bytes).digest()

    # Take first 16 bytes and convert to extension ID format
    # Chrome uses a-p instead of 0-f for the hex representation
    extension_id = ""
    for byte in sha256_hash[:16]:
        extension_id += chr(ord('a') + (byte & 0x0f))
        extension_id += chr(ord('a') + ((byte >> 4) & 0x0f))

    return extension_id


def main():
    # Read the manifest
    manifest_path = "/home/horky/projects/mcp/mcp-chrome/releases/chrome-extension/latest/chrome-mcp-server-lastest/manifest.json"

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        public_key = manifest.get('key', '')
        if public_key:
            extension_id = get_extension_id_from_key(public_key)
            print(f"Chrome Extension ID: {extension_id}")
        else:
            print("No key found in manifest")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
