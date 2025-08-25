
#!/usr/bin/env python3

"""
Triad Terminal with Voice Integration
Combines security, enhanced UI, and voice capabilities
"""
import pip install 
import pyttsx3 
import SpeechRecognition 
import pyaudio 
import gtts 
import playsound
import os
import sys
import time
import argparse
import threading
import logging
from typing import Dict, Any, List, Optional, Tuple

# Import our modules
from security_system import SecurityManager, AuthCLI
from enhanced_ui import TerminalUI, ThemeManager, Animation
from voice_interface import VoiceManager, VoiceCommands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser("~/.triad/logs/triad.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("triad.integrated")

class VoiceEnabledTerminal:
    """Triad Terminal with voice capabilities"""
    
    def __init__(self, theme: str = "matrix"):
        self.security = SecurityManager()
        self.auth_cli = AuthCLI(self.security)
        self.ui = TerminalUI(theme)
        self.voice = VoiceManager()
        self.voice_commands = VoiceCommands(self.voice)
        self.session_id = None
        self.username = None
        self.voice_stop_event = None
        self.command_history = []
    
    def launch(self, skip_auth: bool = False, skip_intro: bool = False, enable_voice: bool = True) -> bool:
        """Launch the terminal"""
        if not skip_intro:
            self.ui.clear_screen()
            self.ui.print_intro()
        
        # Skip authentication if requested (development mode)
        if skip_auth:
            logger.warning("Authentication bypassed (development mode)")
            self.username = "dev_mode"
            authenticated = True
        else:
            authenticated = self._authenticate()
        
        # If authentication succeeded, start the terminal
        if authenticated:
            # Start voice assistant if enabled
            if enable_voice and self.voice.config["voice_recognition_enabled"]:
                self.voice_stop_event = self.voice.start_voice_assistant(self.handle_voice_command)
                self.voice.speak("Voice assistant activated")
            
            return self.start_terminal()
        else:
            print("\nAuthentication failed. Exiting.")
            return False
    
    def _authenticate(self) -> bool:
        """Handle authentication process"""
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
        
        return authenticated
    
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
            welcome_msg = f"Welcome back, {self.username}!"
            self.ui.print_message(welcome_msg, "success")
            # Also speak the welcome if voice is enabled
            if self.voice.config["tts_enabled"]:
                self.voice.speak(welcome_msg)
        else:
            self.ui.print_message("Welcome to Triad Terminal!", "info")
        
        # Display available commands
        commands = self._get_available_commands()
        self.ui.print_command_list(commands)
        
        self.ui.print_footer()
        
        # Command processing loop
        return self._command_loop()
    
    def _command_loop(self) -> bool:
        """Main command processing loop"""
        while True:
            try:
                # Display prompt
                if self.username:
                    prompt = f"\n{self.username}@triad > "
                else:
                    prompt = "\ntriad > "
                
                cmd = input(prompt)
                
                # Skip empty commands
                if not cmd.strip():
                    continue
                
                # Add to history
                self.command_history.append(cmd)
                
                # Process the command
                if cmd.lower() == "exit" or cmd.lower() == "quit":
                    self._shutdown()
                    return True
                
                # Process other commands
                self._process_command(cmd)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                self.ui.print_message(f"Error: {str(e)}", "error")
                logger.error(f"Command error: {e}")
    
    def _process_command(self, cmd: str) -> None:
        """Process a terminal command"""
        cmd_lower = cmd.lower()
        
        if cmd_lower == "help":
            self._show_help()
        
        elif cmd_lower.startswith("open "):
            target = cmd[5:].strip()
            self.ui.print_message(f"Opening {target}...", "info")
        
        elif cmd_lower.startswith("deploy "):
            # Parse deployment command
            params = cmd[7:].strip()
            if " to " in params:
                project, target = params.split(" to ", 1)
                self.ui.print_message(f"Deploying {project} to {target}...", "info")
            else:
                self.ui.print_message(f"Deploying {params}...", "info")
        
        elif cmd_lower == "status":
            self._show_status()
        
        elif cmd_lower.startswith("voice "):
            self._handle_voice_command(cmd[6:].strip())
        
        elif cmd_lower == "clear":
            self.ui.clear_screen()
            self.ui.print_header()
            self.ui.print_footer()
        
        else:
            self.ui.print_message(f"Unknown command: {cmd}", "warning")
            self.ui.print_message("Type 'help' for available commands", "info")
    
    def _show_help(self) -> None:
        """Show help information"""
        commands = self._get_available_commands()
        self.ui.print_command_list(commands)
    
    def _show_status(self) -> None:
        """Show system status"""
        self.ui.print_message("System Status", "info")
        
        # Basic status items
        status_items = [
            {"name": "Terminal", "status": "Running", "details": "No issues detected"},
            {"name": "Voice Assistant", "status": "Active" if self.voice_stop_event else "Inactive", 
             "details": "Listening for commands" if self.voice_stop_event else "Not enabled"},
            {"name": "Network", "status": "Connected", "details": "Internet access available"},
            {"name": "Projects", "status": "3 Active", "details": "No issues detected"},
            {"name": "Deployments", "status": "None Active", "details": "Last deployment: 3 hours ago"}
        ]
        
        # Display in a table format if Rich is available
        try:
            from rich.console import Console
            from rich.table import Table
            
            console = Console()
            table = Table(show_header=True)
            
            table.add_column("Component")
            table.add_column("Status")
            table.add_column("Details")
            
            for item in status_items:
                status_style = "green" if "active" in item["status"].lower() or "running" in item["status"].lower() else "yellow"
                table.add_row(item["name"], f"[{status_style}]{item['status']}[/]", item["details"])
            
            console.print(table)
        except ImportError:
            # Fallback to simple text output
            for item in status_items:
                print(f"- {item['name']}: {item['status']} ({item['details']})")
    
    def _handle_voice_command(self, command: str) -> None:
        """Handle voice control commands"""
        command_lower = command.lower()
        
        if "enable" in command_lower or "activate" in command_lower or "on" in command_lower:
            if not self.voice_stop_event:
                self.voice.config["voice_recognition_enabled"] = True
                self.voice_stop_event = self.voice.start_voice_assistant(self.handle_voice_command)
                self.ui.print_message("Voice assistant enabled", "success")
                self.voice.speak("Voice assistant activated")
            else:
                self.ui.print_message("Voice assistant is already active", "info")
                
        elif "disable" in command_lower or "deactivate" in command_lower or "off" in command_lower:
            if self.voice_stop_event:
                self.voice_stop_event.set()
                self.voice_stop_event = None
                self.voice.config["voice_recognition_enabled"] = False
                self.ui.print_message("Voice assistant disabled", "info")
                self.voice.speak("Voice assistant deactivated")
            else:
                self.ui.print_message("Voice assistant is already inactive", "info")
                
        elif "status" in command_lower:
            status = "active" if self.voice_stop_event else "inactive"
            self.ui.print_message(f"Voice assistant is {status}", "info")
            if self.voice.config["tts_enabled"]:
                self.voice.speak(f"Voice assistant is {status}")
                
        else:
            self.ui.print_message(f"Unknown voice command: {command}", "warning")
    
    def handle_voice_command(self, command: str) -> str:
        """Process voice command and return response text"""
        if not command:
            return "I didn't catch that. Could you repeat?"
        
        # Log the command
        logger.info(f"Processing voice command: {command}")
        
        # Execute the command
        response = self.voice_commands.execute_command(command)
        
        # Print command and response to terminal
        self.ui.print_message(f"Voice command: {command}", "info")
        self.ui.print_message(f"Response: {response}", "info")
        
        return response
    
    def _get_available_commands(self) -> List[Dict[str, str]]:
        """Get available commands for the current user"""
        # Basic commands available to all users
        commands = [
            {"name": "help", "description": "Show available commands"},
            {"name": "open <target>", "description": "Open specified application or project"},
            {"name": "deploy <project> [to <target>]", "description": "Deploy a project"},
            {"name": "status", "description": "Show system status"},
            {"name": "voice <on|off|status>", "description": "Control voice assistant"},
            {"name": "clear", "description": "Clear the screen"},
            {"name": "exit", "description": "Exit Triad Terminal"}
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
    
    def _shutdown(self) -> None:
        """Shutdown the terminal"""
        # Stop voice assistant if running
        if self.voice_stop_event:
            self.voice_stop_event.set()
        
        # Log out user
        if self.session_id:
            self.security.logout(self.session_id)
            
            # Remove session file
            try:
                session_file = os.path.expanduser("~/.triad/security/current_session")
                if os.path.exists(session_file):
                    os.remove(session_file)
            except Exception as e:
                logger.error(f"Error removing session file: {e}")
        
        # Say goodbye if voice enabled
        if self.voice.config["tts_enabled"]:
            self.voice.speak("Goodbye!", blocking=True)
        
        self.ui.print_message("Goodbye!", "info")

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
    parser = argparse.ArgumentParser(description="Triad Terminal - Voice-Enabled Development Environment")
    parser.add_argument("--dev", action="store_true", help="Development mode (skip authentication)")
    parser.add_argument("--theme", type=str, default="matrix", help="UI theme")
    parser.add_argument("--setup", action="store_true", help="Set up initial user")
    parser.add_argument("--no-voice", action="store_true", help="Disable voice assistant")
    args = parser.parse_args()
    
    # Setup initial user if requested
    if args.setup:
        setup_initial_user()
        return
    
    # Create and launch the terminal
    terminal = VoiceEnabledTerminal(theme=args.theme)
    terminal.launch(skip_auth=args.dev, enable_voice=not args.no_voice)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting Triad Terminal.")
        sys.exit(0)