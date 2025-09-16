#!/usr/bin/env python3

"""
Triad Terminal Security System
Provides secure authentication for the terminal
"""

import base64
import datetime
import getpass
import hashlib
import json
import logging
import os
import time
import uuid
from typing import Any

# For encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

logger = logging.getLogger("triad.security")

class SecurityManager:
    """Manages authentication and security for Triad Terminal"""

    def __init__(self, data_dir: str = "~/.triad/security"):
        self.data_dir = os.path.expanduser(data_dir)
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.sessions_file = os.path.join(self.data_dir, "sessions.json")
        self.settings_file = os.path.join(self.data_dir, "settings.json")

        # Create security directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)

        # Initialize security settings if they don't exist
        if not os.path.exists(self.settings_file):
            self._create_default_settings()

        # Load security settings
        self.settings = self._load_settings()

        # Initialize users file if it doesn't exist
        if not os.path.exists(self.users_file):
            self._create_empty_users_file()

    def _create_default_settings(self) -> None:
        """Create default security settings"""
        settings = {
            "authentication_required": True,
            "password_expiry_days": 90,
            "min_password_length": 8,
            "session_timeout_minutes": 30,
            "max_login_attempts": 5,
            "lockout_duration_minutes": 15,
            "allow_biometric": True,
            "require_2fa": False
        }

        with open(self.settings_file, "w") as f:
            json.dump(settings, f, indent=2)

    def _load_settings(self) -> dict[str, Any]:
        """Load security settings"""
        try:
            with open(self.settings_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading security settings: {e}")
            return {
                "authentication_required": True,
                "password_expiry_days": 90,
                "min_password_length": 8,
                "session_timeout_minutes": 30,
                "max_login_attempts": 5,
                "lockout_duration_minutes": 15,
                "allow_biometric": True,
                "require_2fa": False
            }

    def _create_empty_users_file(self) -> None:
        """Create an empty users file"""
        with open(self.users_file, "w") as f:
            json.dump({}, f)

    def _load_users(self) -> dict[str, Any]:
        """Load user data"""
        try:
            with open(self.users_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return {}

    def _save_users(self, users: dict[str, Any]) -> bool:
        """Save user data"""
        try:
            with open(self.users_file, "w") as f:
                json.dump(users, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving users: {e}")
            return False

    def _generate_salt(self) -> str:
        """Generate a random salt for password hashing"""
        return base64.b64encode(os.urandom(16)).decode('utf-8')

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash a password with the given salt"""
        # Use PBKDF2 with SHA256
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100,000 iterations for security
        )
        return base64.b64encode(hashed).decode('utf-8')

    def _encrypt_data(self, data: str, key: str) -> str | None:
        """Encrypt data using a key"""
        if not HAS_CRYPTO:
            logger.warning("Cryptography library not available, data not encrypted")
            return data

        try:
            # Derive encryption key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'TriadTerminalSecure',  # Fixed salt for key derivation
                iterations=100000
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(key.encode('utf-8')))

            # Encrypt the data
            f = Fernet(encryption_key)
            encrypted_data = f.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return None

    def _decrypt_data(self, encrypted_data: str, key: str) -> str | None:
        """Decrypt data using a key"""
        if not HAS_CRYPTO:
            logger.warning("Cryptography library not available, data not decrypted")
            return encrypted_data

        try:
            # Derive encryption key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'TriadTerminalSecure',  # Fixed salt for key derivation
                iterations=100000
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(key.encode('utf-8')))

            # Decrypt the data
            f = Fernet(encryption_key)
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted_data = f.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None

    def create_user(self, username: str, password: str, full_name: str = "",
                   email: str = "", admin: bool = False) -> bool:
        """Create a new user"""
        # Check if username already exists
        users = self._load_users()
        if username in users:
            logger.warning(f"User {username} already exists")
            return False

        # Check password length
        min_length = self.settings.get("min_password_length", 8)
        if len(password) < min_length:
            logger.warning(f"Password must be at least {min_length} characters")
            return False

        # Generate salt and hash password
        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)

        # Create user record
        users[username] = {
            "password_hash": password_hash,
            "salt": salt,
            "full_name": full_name,
            "email": email,
            "admin": admin,
            "created_at": datetime.datetime.now().isoformat(),
            "password_changed_at": datetime.datetime.now().isoformat(),
            "biometric_enabled": False,
            "biometric_data": None,
            "failed_attempts": 0,
            "locked_until": None
        }

        # Save users
        return self._save_users(users)

    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        """Authenticate a user with password"""
        users = self._load_users()

        # Check if user exists
        if username not in users:
            return False, "Invalid username or password"

        user = users[username]

        # Check if account is locked
        if "locked_until" in user and user["locked_until"]:
            locked_until = datetime.datetime.fromisoformat(user["locked_until"])
            if locked_until > datetime.datetime.now():
                minutes_remaining = int((locked_until - datetime.datetime.now()).total_seconds() / 60)
                return False, f"Account is locked. Try again in {minutes_remaining} minutes"

        # Check password
        salt = user["salt"]
        password_hash = self._hash_password(password, salt)

        if password_hash != user["password_hash"]:
            # Increment failed attempts
            user["failed_attempts"] = user.get("failed_attempts", 0) + 1

            # Check if we should lock the account
            max_attempts = self.settings.get("max_login_attempts", 5)
            if user["failed_attempts"] >= max_attempts:
                lockout_minutes = self.settings.get("lockout_duration_minutes", 15)
                locked_until = datetime.datetime.now() + datetime.timedelta(minutes=lockout_minutes)
                user["locked_until"] = locked_until.isoformat()

                self._save_users(users)
                return False, f"Too many failed attempts. Account locked for {lockout_minutes} minutes"

            self._save_users(users)
            return False, "Invalid username or password"

        # Reset failed attempts
        user["failed_attempts"] = 0
        user["locked_until"] = None
        self._save_users(users)

        # Check if password has expired
        if "password_changed_at" in user:
            password_changed = datetime.datetime.fromisoformat(user["password_changed_at"])
            expiry_days = self.settings.get("password_expiry_days", 90)
            if (datetime.datetime.now() - password_changed).days > expiry_days:
                return True, "password_expired"

        # Create session
        session_id = self._create_session(username)
        return True, session_id

    def authenticate_biometric(self, username: str, biometric_data: str) -> tuple[bool, str]:
        """Authenticate a user with biometric data"""
        if not self.settings.get("allow_biometric", True):
            return False, "Biometric authentication is disabled"

        users = self._load_users()

        # Check if user exists
        if username not in users:
            return False, "User not found"

        user = users[username]

        # Check if biometric is enabled for user
        if not user.get("biometric_enabled", False) or not user.get("biometric_data"):
            return False, "Biometric authentication not set up for this user"

        # In a real implementation, you would properly verify biometric data
        # Here we just simulate matching the stored data
        stored_biometric = user["biometric_data"]
        if self._verify_biometric(biometric_data, stored_biometric):
            # Create session
            session_id = self._create_session(username)
            return True, session_id

        return False, "Biometric verification failed"

    def _verify_biometric(self, provided_data: str, stored_data: str) -> bool:
        """Verify biometric data match"""
        # In a real implementation, this would do proper biometric verification
        # For this simulation, we'll just check equality
        # (never do this in real biometric systems!)
        return provided_data == stored_data

    def _create_session(self, username: str) -> str:
        """Create a new session for a user"""
        session_id = str(uuid.uuid4())

        # Load existing sessions
        sessions = self._load_sessions()

        # Add new session
        sessions[session_id] = {
            "username": username,
            "created_at": datetime.datetime.now().isoformat(),
            "expires_at": (datetime.datetime.now() + datetime.timedelta(
                minutes=self.settings.get("session_timeout_minutes", 30)
            )).isoformat()
        }

        # Save sessions
        self._save_sessions(sessions)

        return session_id

    def _load_sessions(self) -> dict[str, Any]:
        """Load active sessions"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file) as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            return {}

    def _save_sessions(self, sessions: dict[str, Any]) -> bool:
        """Save sessions"""
        try:
            # Clean expired sessions before saving
            now = datetime.datetime.now()
            active_sessions = {
                sid: session for sid, session in sessions.items()
                if datetime.datetime.fromisoformat(session["expires_at"]) > now
            }

            with open(self.sessions_file, "w") as f:
                json.dump(active_sessions, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
            return False

    def validate_session(self, session_id: str) -> tuple[bool, str | None]:
        """Check if a session is valid and return the associated username"""
        sessions = self._load_sessions()

        # Check if session exists
        if session_id not in sessions:
            return False, None

        session = sessions[session_id]

        # Check if session has expired
        if datetime.datetime.fromisoformat(session["expires_at"]) < datetime.datetime.now():
            # Remove expired session
            del sessions[session_id]
            self._save_sessions(sessions)
            return False, None

        # Extend session timeout
        sessions[session_id]["expires_at"] = (datetime.datetime.now() + datetime.timedelta(
            minutes=self.settings.get("session_timeout_minutes", 30)
        )).isoformat()

        self._save_sessions(sessions)

        return True, session["username"]

    def logout(self, session_id: str) -> bool:
        """Invalidate a session (logout)"""
        sessions = self._load_sessions()

        if session_id in sessions:
            del sessions[session_id]
            return self._save_sessions(sessions)

        return True  # Session wasn't there anyway

    def change_password(self, username: str, current_password: str,
                      new_password: str) -> tuple[bool, str]:
        """Change a user's password"""
        # Authenticate first with current password
        auth_result, _ = self.authenticate(username, current_password)

        if not auth_result:
            return False, "Current password is incorrect"

        # Check new password length
        min_length = self.settings.get("min_password_length", 8)
        if len(new_password) < min_length:
            return False, f"New password must be at least {min_length} characters"

        users = self._load_users()
        user = users[username]

        # Generate new salt and hash
        salt = self._generate_salt()
        password_hash = self._hash_password(new_password, salt)

        # Update user
        user["salt"] = salt
        user["password_hash"] = password_hash
        user["password_changed_at"] = datetime.datetime.now().isoformat()

        if self._save_users(users):
            return True, "Password changed successfully"
        else:
            return False, "Error saving new password"

    def setup_biometric(self, username: str, password: str, biometric_data: str) -> tuple[bool, str]:
        """Set up biometric authentication for a user"""
        if not self.settings.get("allow_biometric", True):
            return False, "Biometric authentication is disabled"

        # Authenticate first with password
        auth_result, _ = self.authenticate(username, password)

        if not auth_result:
            return False, "Password is incorrect"

        users = self._load_users()
        user = users[username]

        # Store biometric data (in a real system, store a secure template)
        user["biometric_enabled"] = True
        user["biometric_data"] = biometric_data

        if self._save_users(users):
            return True, "Biometric authentication enabled"
        else:
            return False, "Error saving biometric data"

    def disable_biometric(self, username: str, password: str) -> tuple[bool, str]:
        """Disable biometric authentication for a user"""
        # Authenticate first with password
        auth_result, _ = self.authenticate(username, password)

        if not auth_result:
            return False, "Password is incorrect"

        users = self._load_users()
        user = users[username]

        # Disable biometric auth
        user["biometric_enabled"] = False
        user["biometric_data"] = None

        if self._save_users(users):
            return True, "Biometric authentication disabled"
        else:
            return False, "Error updating user settings"

class AuthCLI:
    """Command-line interface for the authentication system"""

    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager

    def login_prompt(self) -> tuple[bool, str]:
        """Interactive login prompt"""
        print("\n")
        print("╔════════════════════════════════════════╗")
        print("║           TRIAD TERMINAL LOGIN         ║")
        print("╚════════════════════════════════════════╝")

        username = input("Username: ")
        password = getpass.getpass("Password: ")

        print("Authenticating...")
        success, result = self.security.authenticate(username, password)

        if success:
            if result == "password_expired":
                print("\nYour password has expired and must be changed.")
                return self.change_password_prompt(username)
            else:
                print("\n✅ Login successful!")
                return True, result
        else:
            print(f"\n❌ Login failed: {result}")
            return False, ""

    def biometric_login_prompt(self) -> tuple[bool, str]:
        """Interactive biometric login prompt"""
        print("\n")
        print("╔════════════════════════════════════════╗")
        print("║      TRIAD TERMINAL BIOMETRIC LOGIN    ║")
        print("╚════════════════════════════════════════╝")

        username = input("Username: ")

        print("Waiting for fingerprint scan...")
        # Simulate fingerprint scanning
        time.sleep(1.5)
        print("Processing...")
        time.sleep(0.5)

        # In a real system, we'd capture actual biometric data here
        # For this demo, we'll use a placeholder
        biometric_data = f"SIMULATED_BIOMETRIC_DATA_FOR_{username}"

        success, result = self.security.authenticate_biometric(username, biometric_data)

        if success:
            print("\n✅ Biometric authentication successful!")
            return True, result
        else:
            print(f"\n❌ Biometric authentication failed: {result}")
            return False, ""

    def register_prompt(self) -> bool:
        """Interactive user registration prompt"""
        print("\n")
        print("╔════════════════════════════════════════╗")
        print("║         TRIAD TERMINAL REGISTER        ║")
        print("╚════════════════════════════════════════╝")

        username = input("Choose a username: ")
        full_name = input("Enter your full name: ")
        email = input("Enter your email (optional): ")

        min_length = self.security.settings.get("min_password_length", 8)
        print(f"Password must be at least {min_length} characters long.")

        while True:
            password = getpass.getpass("Choose a password: ")
            if len(password) < min_length:
                print(f"Password must be at least {min_length} characters long.")
                continue

            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Passwords do not match. Try again.")
                continue

            break

        print("Creating account...")
        success = self.security.create_user(username, password, full_name, email)

        if success:
            print("\n✅ Account created successfully!")
            return True
        else:
            print("\n❌ Error creating account.")
            return False

    def change_password_prompt(self, username: str) -> tuple[bool, str]:
        """Interactive password change prompt"""
        print("\n")
        print("╔════════════════════════════════════════╗")
        print("║       TRIAD TERMINAL PASSWORD CHANGE   ║")
        print("╚════════════════════════════════════════╝")

        current_password = getpass.getpass("Current password: ")

        min_length = self.security.settings.get("min_password_length", 8)
        print(f"New password must be at least {min_length} characters long.")

        while True:
            new_password = getpass.getpass("New password: ")
            if len(new_password) < min_length:
                print(f"Password must be at least {min_length} characters long.")
                continue

            confirm = getpass.getpass("Confirm new password: ")
            if new_password != confirm:
                print("Passwords do not match. Try again.")
                continue

            break

        print("Changing password...")
        success, message = self.security.change_password(username, current_password, new_password)

        if success:
            print(f"\n✅ {message}")
            # Re-authenticate with new password
            success, result = self.security.authenticate(username, new_password)
            if success:
                return True, result
            else:
                return False, ""
        else:
            print(f"\n❌ {message}")
            return False, ""

    def setup_biometric_prompt(self, username: str) -> bool:
        """Interactive biometric setup prompt"""
        print("\n")
        print("╔════════════════════════════════════════╗")
        print("║     TRIAD TERMINAL BIOMETRIC SETUP     ║")
        print("╚════════════════════════════════════════╝")

        password = getpass.getpass("Enter your password to continue: ")

        print("Setting up biometric authentication...")
        print("Place your finger on the scanner...")

        # Simulate fingerprint scanning
        time.sleep(2)
        print("Scanning...")
        time.sleep(1)
        print("Processing...")
        time.sleep(1)

        # In a real system, we'd capture actual biometric data here
        # For this demo, we'll use a placeholder
        biometric_data = f"SIMULATED_BIOMETRIC_DATA_FOR_{username}"

        success, message = self.security.setup_biometric(username, password, biometric_data)

        if success:
            print(f"\n✅ {message}")
            return True
        else:
            print(f"\n❌ {message}")
            return False
