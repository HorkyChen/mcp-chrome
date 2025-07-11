#!/usr/bin/env python3
"""
Setup script for MCP Chrome Bridge Python
"""

import os
import subprocess
import sys
from pathlib import Path


def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        sys.exit(1)


def register_host():
    """Register native messaging host"""
    print("Registering native messaging host...")
    try:
        subprocess.check_call([sys.executable, "cli.py", "register"])
        print("✓ Native messaging host registered successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to register native messaging host: {e}")
        sys.exit(1)


def make_executable():
    """Make scripts executable on Unix systems"""
    if os.name != 'nt':  # Not Windows
        scripts = ['main.py', 'cli.py', 'mcp_server_stdio.py']
        for script in scripts:
            script_path = Path(script)
            if script_path.exists():
                script_path.chmod(0o755)
                print(f"✓ Made {script} executable")


def main():
    """Main setup function"""
    print("Setting up MCP Chrome Bridge Python...")

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Install requirements
    install_requirements()

    # Make scripts executable
    make_executable()

    # Register native messaging host
    register_host()

    print("\n✓ Setup completed successfully!")
    print("\nYou can now:")
    print("1. Start the main server: python cli.py start")
    print("2. Start the STDIO server: python cli.py start-stdio")
    print("3. Test with Chrome extension")


if __name__ == "__main__":
    main()
