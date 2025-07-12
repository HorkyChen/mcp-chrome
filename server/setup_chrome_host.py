#!/usr/bin/env python3
"""
Chrome Native Messaging Host Setup Script
Creates the proper manifest and sets up the environment for Chrome extension communication
"""

import json
import os
import platform
import shutil
import sys
from pathlib import Path

from constants import HOST_NAME, EXTENSION_ID, DESCRIPTION

from constants import HOST_NAME, EXTENSION_ID, DESCRIPTION


def get_chrome_manifest_dir():
    """Get the Chrome native messaging manifest directory"""
    system = platform.system()

    if system == "Windows":
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


def create_run_script():
    """Create a run script that Chrome will execute"""
    script_dir = Path(__file__).parent.absolute()
    python_executable = sys.executable
    main_script = script_dir / "main.py"

    system = platform.system()

    if system == "Windows":
        # Create .bat file for Windows
        run_script = script_dir / "run_mcp_chrome_bridge.bat"
        with open(run_script, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'"{python_executable}" "{main_script}"\n')
        return str(run_script)
    else:
        # Create shell script for Unix-like systems
        run_script = script_dir / "run_mcp_chrome_bridge.sh"
        with open(run_script, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(f'"{python_executable}" "{main_script}"\n')

        # Make it executable
        run_script.chmod(0o755)
        return str(run_script)


def create_manifest():
    """Create the native messaging manifest"""
    run_script_path = create_run_script()

    manifest = {
        "name": HOST_NAME,
        "description": f"{DESCRIPTION} - Native Messaging Host",
        "path": run_script_path,
        "type": "stdio",
        "allowed_origins": [
            f"chrome-extension://{EXTENSION_ID}/"
        ]
    }

    return manifest


def install_manifest(system_level=False):
    """Install the native messaging manifest"""
    try:
        manifest_dirs = get_chrome_manifest_dir()
        target_dir = Path(manifest_dirs["system"] if system_level else manifest_dirs["user"])

        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create manifest
        manifest = create_manifest()
        manifest_file = target_dir / f"{HOST_NAME}.json"

        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"✓ Manifest installed at: {manifest_file}")
        print(f"✓ Run script created at: {manifest['path']}")
        print(f"✓ Extension ID: {EXTENSION_ID}")

        return True

    except Exception as e:
        print(f"❌ Failed to install manifest: {e}")
        return False


def test_installation():
    """Test if the installation is working"""
    print("\nTesting installation...")

    script_dir = Path(__file__).parent
    main_script = script_dir / "main.py"

    if not main_script.exists():
        print("❌ main.py not found")
        return False

    # Check if run script exists
    system = platform.system()
    if system == "Windows":
        run_script = script_dir / "run_mcp_chrome_bridge.bat"
    else:
        run_script = script_dir / "run_mcp_chrome_bridge.sh"

    if not run_script.exists():
        print("❌ Run script not found")
        return False

    print("✓ Installation test passed")
    return True


def main():
    """Main setup function"""
    print("Chrome Native Messaging Host Setup")
    print("=" * 40)

    # Install manifest
    success = install_manifest()

    if success:
        # Test installation
        test_installation()

        print("\n" + "=" * 40)
        print("Setup completed successfully!")
        print("\nNext steps:")
        print("1. Install the Chrome extension")
        print("2. The extension should automatically connect to this native host")
        print("3. Run 'python main.py' to start the native messaging host")
        print("4. Check Chrome extension console for connection status")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
