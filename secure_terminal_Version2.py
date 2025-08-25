#!/usr/bin/env python3

"""
Triad Terminal Secure Launcher
Combines security system with enhanced UI
"""

import os
import sys
import time
import argparse
import logging
from typing import Dict, Any, List, Optional, Tuple

# Import our modules
from security_system import SecurityManager, AuthCLI
from enhanced_ui import TerminalUI, ThemeManager, Animation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser("~/.triad/logs/triad.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("triad.secure")

class SecureTerminal:
    """Secured Triad Terminal with authentication and enhanced UI"""
    
    def __init__(self, theme: str = "matrix"):
        self.security = SecurityManager()
        self.auth_cli = AuthCLI(self.security)
        self.ui = TerminalUI(theme)
        self.session_id = None
        self.username = None
    
    def launch(self, skip_auth: bool = False, skip_intro: bool = False) -> bool:
        """Launch the secure terminal"""
        if not skip_intro:
            self.ui.clear_screen()
            self.ui.print_intro()
        
        # Skip authentication if requested (development mode)
        if skip_auth:
            logger.warning("Authentication bypassed (development mode)")
            self.username = "dev_mode"
            return self.start_terminal()
        
        # Perform authentication
        authenticated = False
        
        # First try to get stored session
        session_file = os.path.expanduser("~/.triad/security/current_session")
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r') as f:
                    stored_session = f.read().strip()
                
                # Validate the session
                valid, username = self.security.validate_session(stored_session)
                if valid and username:
                    self.session_id = stored_session
                    self.username = username
                    authenticated = True
                    logger.info(f"User {username} authenticated via stored session")
            except Exception as e:
                logger.error(f"Error reading session file: {e}")
        
        # If not authenticated via session, show login prompt
        if not authenticated:
            # Offer biometric option if enabled
            biometric_enabled = self.security.settings.get("allow_biometric", True)
            if biometric_enabled:
                print("\nAuthentication Required")
                print("1. Password Login")
                print("2. Biometric Login")
                choice = input("Select login method (1/2): ")
                
                if choice == "2":
                    success, result = self.auth_cli.biometric_login_prompt()
                    if success:
                        self.session_id = result
                        valid, username = self.security.validate_session(self.session_id)
                        if valid and username:
                            self.username = username
                            authenticated = True
                            # Save session for future use
                            self._save_session()
            
            # If not authenticated via biometric, use password
            if not authenticated:
                success, result = self.auth_cli.login_prompt()
                if success:
                    self.session_id = result
                    valid, username = self.security.validate_session(self.session_id)
                    if valid and username:
                        self.username = username
                        authenticated = True
                        # Save session for future use
                        self._save_session()
        
        # If authentication succeeded, start the terminal
        if authenticated:
            return self.start_terminal()
        else:
            print("\nAuthentication failed. Exiting.")
            return False
    
    def _save_session(self) -> None:
        """Save current session to file for persistence"""
        if not self.session_id:
            return
            
        try:
            session_dir = os.path.expanduser("~/.triad/security")
            os.makedirs(session_dir, exist_ok=True)
            
            with open(os.path.join(session_dir, "current_session"), 'w') as f:
                f.write(self.session_id)
        except Exception as e:
            logger.error(f"Error saving session: {e}")
    
    def start_terminal(self) -> bool:
        """Start the terminal after successful authentication"""
        self.ui.clear_screen()
        
        # Display welcome
        self.ui.print_header()
        
        if self.username:
            self.ui.print_message(f"Welcome back, {self.username}!", "success")
        else:
            self.ui.print_message("Welcome to Triad Terminal!", "info")
        
        # Display available commands
        commands = self._get_available_commands()
        self.ui.print_command_list(commands)
        
        self.ui.print_footer()
        
        # In a real implementation, you would enter a command loop here
        # For demonstration purposes, we'll just return success
        return True
    
    def _get_available_commands(self) -> List[Dict[str, str]]:
        """Get available commands for the current user"""
        # Basic commands available to all users
        commands = [
            {"name": "projects", "description": "Manage development projects"},
            {"name": "deploy", "description": "Deploy applications"},
            {"name": "monitor", "description": "System monitoring dashboard"},
            {"name": "tunnel", "description": "SSH tunnel management"},
            {"name": "theme", "description": "Change terminal theme"},
            {"name": "help", "description": "Show help for commands"}
        ]
        
        # Add admin commands if the user is an admin
        users = self.security._load_users()
        if self.username in users and users[self.username].get("admin", False):
            commands.extend([
                {"name": "users", "description": "User management"},
                {"name": "config", "description": "System configuration"},
                {"name": "logs", "description": "View system logs"},
                {"name": "backup", "description": "Manage backups"}
            ])
        
        return commands
    
    def logout(self) -> bool:
        """Log out the current user"""
        if self.session_id:
            success = self.security.logout(self.session_id)
            
            # Remove session file
            try:
                session_file = os.path.expanduser("~/.triad/security/current_session")
                if os.path.exists(session_file):
                    os.remove(session_file)
            except Exception as e:
                logger.error(f"Error removing session file: {e}")
            
            self.session_id = None
            self.username = None
            
            return success
        
        return True  # Already logged out

def setup_initial_user() -> None:
    """Create initial admin user if no users exist"""
    security = SecurityManager()
    users = security._load_users()
    
    if not users:
        print("\nNo users found. Creating initial admin account.")
        username = input("Username: ")
        full_name = input("Full name: ")
        email = input("Email (optional): ")
        
        import getpass
        while True:
            password = getpass.getpass("Password: ")
            if len(password) < security.settings.get("min_password_length", 8):
                print(f"Password must be at least {security.settings.get('min_password_length', 8)} characters.")
                continue
                
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Passwords do not match. Try again.")
                continue
                
            break
        
        success = security.create_user(username, password, full_name, email, admin=True)
        
        if success:
            print("\n✅ Admin account created successfully!")
        else:
            print("\n❌ Error creating admin account.")

def main() -> None:
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Triad Terminal - Secure Development Environment")
    parser.add_argument("--dev", action="store_true", help="Development mode (skip authentication)")
    parser.add_argument("--theme", type=str, default="matrix", help="UI theme")
    parser.add_argument("--setup", action="store_true", help="Set up initial user")
    args = parser.parse_args()
    
    # Setup initial user if requested
    if args.setup:
        setup_initial_user()
        return
    
    # Create and launch the secure terminal
    terminal = SecureTerminal(theme=args.theme)
    terminal.launch(skip_auth=args.dev)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting Triad Terminal.")
        sys.exit(0)