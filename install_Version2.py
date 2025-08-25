#!/usr/bin/env python3

"""
Triad Terminal Installer
Sets up the Triad Terminal environment
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path
import argparse

def print_banner():
    """Print installation banner"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                   TRIAD TERMINAL INSTALLER                     ║
║                                                                ║
║  A secure and powerful development environment for your needs  ║
╚════════════════════════════════════════════════════════════════╝
    """)

def get_install_path():
    """Determine where to install Triad Terminal"""
    home = str(Path.home())
    
    # Default locations based on platform
    if platform.system() == "Windows":
        default_path = os.path.join(home, "AppData", "Local", "TriadTerminal")
    elif platform.system() == "Darwin":  # macOS
        default_path = os.path.join(home, "Library", "Application Support", "TriadTerminal")
    else:  # Linux and others
        default_path = os.path.join(home, ".triad")
    
    # Ask the user
    print(f"Default installation path: {default_path}")
    custom_path = input("Press Enter to use default path or enter custom path: ")
    
    if custom_path.strip():
        install_path = os.path.expanduser(custom_path)
    else:
        install_path = default_path
    
    return install_path

def check_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        "rich",
        "colorama",
        "pyyaml",
        "psutil",
        "cryptography"
    ]
    
    print("\nChecking dependencies...")
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: already installed")
        except ImportError:
            print(f"📦 {package}: installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package}: installed successfully")
            except subprocess.CalledProcessError:
                print(f"❌ {package}: installation failed")
                return False
    
    return True

def copy_files(install_path, source_dir="."):
    """Copy files to installation directory"""
    print(f"\nCopying files to {install_path}...")
    
    # Create directory structure
    directories = [
        "",
        "bin",
        "config",
        "plugins",
        "logs",
        "security",
        "ascii_art"
    ]
    
    for directory in directories:
        full_path = os.path.join(install_path, directory)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Copy Python modules
    module_files = [
        "optimized_terminal.py",
        "plugin_system.py",
        "platform_compatibility.py",
        "advanced_features.py",
        "config_manager.py",
        "code_formatter.py",
        "enhanced_deployment.py",
        "enhanced_tunnel.py",
        "monitoring_dashboard.py",
        "security_system.py",
        "enhanced_ui.py",
        "secure_terminal.py"
    ]
    
    for filename in module_files:
        source = os.path.join(source_dir, filename)
        destination = os.path.join(install_path, "bin", filename)
        
        if os.path.exists(source):
            shutil.copy2(source, destination)
            print(f"Copied: {filename}")
        else:
            print(f"Warning: Could not find {filename}")
    
    # Create ASCII art
    matrix_file = os.path.join(install_path, "ascii_art", "matrix.py")
    with open(matrix_file, "w") as f:
        f.write("""#!/usr/bin/env python3
import random
import time
import sys
import os

def matrix_rain(duration=5):
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Get terminal size
    try:
        columns = os.get_terminal_size().columns
        lines = os.get_terminal_size().lines
    except:
        columns = 80
        lines = 24
    
    # Set up streams
    streams = []
    for i in range(columns // 3):
        streams.append({
            'pos': random.randint(0, columns - 1),
            'speed': random.uniform(0.2, 0.8),
            'length': random.randint(5, lines // 2),
            'head': -random.randint(1, lines)
        })
    
    # Characters to use
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-=_+[]{}|;:,.<>?/"
    
    # Hide cursor
    print("\\033[?25l", end="")
    
    try:
        start_time = time.time()
        while time.time() - start_time < duration:
            # Create empty screen
            screen = [[" " for _ in range(columns)] for _ in range(lines)]
            
            # Update streams
            for stream in streams:
                # Move stream down
                stream['head'] += stream['speed']
                
                # Draw stream
                for i in range(stream['length']):
                    row = int(stream['head']) - i
                    if 0 <= row < lines:
                        # Choose character
                        char = random.choice(chars)
                        
                        # Set color based on position in stream
                        if i == 0:
                            # Head of stream is bright
                            color = "\\033[1;32m"  # Bright green
                        else:
                            # Rest of stream is normal
                            color = "\\033[32m"    # Green
                        
                        # Place character on screen
                        screen[row][stream['pos']] = color + char + "\\033[0m"
                
                # Reset stream if it's off the bottom
                if stream['head'] > lines + stream['length']:
                    stream['head'] = -random.randint(1, lines // 2)
                    stream['pos'] = random.randint(0, columns - 1)
                    stream['speed'] = random.uniform(0.2, 0.8)
                    stream['length'] = random.randint(5, lines // 2)
            
            # Render screen
            os.system('cls' if os.name == 'nt' else 'clear')
            for row in screen:
                print("".join(row))
            
            time.sleep(0.05)
    
    finally:
        # Show cursor
        print("\\033[?25h", end="")
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    duration = 5
    if len(sys.argv) > 1:
        try:
            duration = float(sys.argv[1])
        except ValueError:
            pass
    
    matrix_rain(duration)
""")
    
    # Create launcher script
    launcher_path = os.path.join(install_path, "triad")
    with open(launcher_path, "w") as f:
        f.write(f"""#!/bin/bash
# Triad Terminal Launcher

# Set path to installation directory
TRIAD_HOME="{install_path}"

# Execute the terminal
python3 "$TRIAD_HOME/bin/secure_terminal.py" "$@"
""")
    
    # Make the launcher executable
    try:
        os.chmod(launcher_path, 0o755)
    except:
        print("Warning: Could not make launcher script executable")
    
    # Windows batch file launcher
    if platform.system() == "Windows":
        win_launcher = os.path.join(install_path, "triad.bat")
        with open(win_launcher, "w") as f:
            f.write(f"""@echo off
:: Triad Terminal Launcher for Windows
python "{install_path}\\bin\\secure_terminal.py" %*
""")
    
    return True

def create_symlink(install_path):
    """Create a symlink to the launcher in a directory in PATH"""
    if platform.system() == "Windows":
        print("\nTo add Triad Terminal to your PATH:")
        print(f"1. Add {install_path} to your PATH environment variable")
        print("2. You can then start the terminal by typing 'triad.bat'")
        return True
    
    # Unix-like systems
    bin_dirs = [
        os.path.expanduser("~/.local/bin"),
        os.path.expanduser("~/bin")
    ]
    
    # Find a suitable bin directory
    bin_dir = None
    for directory in bin_dirs:
        if os.path.exists(directory) and directory in os.environ.get("PATH", ""):
            bin_dir = directory
            break
    
    if bin_dir is None:
        # Create ~/.local/bin if it doesn't exist
        bin_dir = os.path.expanduser("~/.local/bin")
        os.makedirs(bin_dir, exist_ok=True)
        
        # Inform the user to add it to PATH
        print(f"\nCreated {bin_dir}")
        print(f"Add this to your PATH by adding the following to your ~/.bashrc or ~/.zshrc:")
        print(f'export PATH="$HOME/.local/bin:$PATH"')
    
    # Create the symlink
    source = os.path.join(install_path, "triad")
    target = os.path.join(bin_dir, "triad")
    
    try:
        # Remove existing symlink if it exists
        if os.path.exists(target):
            os.remove(target)
        
        # Create new symlink
        os.symlink(source, target)
        print(f"\nCreated symlink: {target} -> {source}")
        print("You can now start Triad Terminal by typing 'triad'")
        return True
    except Exception as e:
        print(f"Error creating symlink: {e}")
        print(f"\nTo manually add Triad Terminal to your PATH:")
        print(f"1. Add an alias to your shell configuration file:")
        print(f"   alias triad='{source}'")
        return False

def setup_initial_user(install_path):
    """Set up the initial admin user"""
    print("\nSetting up initial admin user...")
    subprocess.call([sys.executable, os.path.join(install_path, "bin", "secure_terminal.py"), "--setup"])

def main():
    """Main installation function"""
    parser = argparse.ArgumentParser(description="Triad Terminal Installer")
    parser.add_argument("--path", type=str, help="Installation path")
    parser.add_argument("--skip-dependencies", action="store_true", help="Skip dependency check")
    args = parser.parse_args()
    
    print_banner()
    
    # Determine installation path
    if args.path:
        install_path = args.path
    else:
        install_path = get_install_path()
    
    # Ensure the installation path exists
    os.makedirs(install_path, exist_ok=True)
    print(f"\nInstalling Triad Terminal to: {install_path}")
    
    # Check dependencies
    if not args.skip_dependencies:
        if not check_dependencies():
            print("\n❌ Failed to install required dependencies. Installation aborted.")
            return 1
    
    # Copy files
    if not copy_files(install_path):
        print("\n❌ Failed to copy files. Installation aborted.")
        return 1
    
    # Create symlink
    create_symlink(install_path)
    
    # Setup initial user
    setup_initial_user(install_path)
    
    print("\n✅ Triad Terminal installation complete!")
    print("\nTo start the terminal, run: triad")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())