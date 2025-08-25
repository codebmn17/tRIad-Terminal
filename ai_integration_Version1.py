#!/usr/bin/env python3

"""
Triad Terminal AI Integration
Connects AI capabilities with the terminal interface
"""

import os
import re
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

from ai_assistant import AIAssistant

class AIIntegration:
    """Integrates AI capabilities with terminal interface"""
    
    def __init__(self, config_file: str = "~/.triad/config/ai_settings.json"):
        self.config_file = os.path.expanduser(config_file)
        self.config_dir = os.path.dirname(self.config_file)
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Default configuration
        self.default_config = {
            "enabled": True,
            "code_completion": True,
            "command_prediction": True,
            "nl_processing": True,
            "auto_feedback": True,
            "learning_mode": "passive",  # passive, active, or off
            "max_suggestions": 5,
            "min_confidence": 0.7
        }
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize AI assistant
        self.assistant = AIAssistant()
        
        # Status flag
        self.ready = False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load AI configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    
                # Update with any missing default values
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                        
                return config
                
            except Exception as e:
                logging.error(f"Error loading AI config: {e}")
                
        # Create default config if needed
        self._save_config(self.default_config)
        return dict(self.default_config)
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save AI configuration"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving AI config: {e}")
    
    def initialize(self, callback: Callable = None) -> None:
        """Initialize AI components (can be called in background)"""
        import threading
        
        def init_thread():
            # Nothing to do here, components are initialized on demand
            self.ready = True
            if callback:
                callback()
        
        thread = threading.Thread(target=init_thread)
        thread.daemon = True
        thread.start()
    
    def get_code_completions(self, code_context: str, language: str) -> List[str]:
        """Get code completion suggestions"""
        if not self.config["enabled"] or not self.config["code_completion"]:
            return []
            
        return self.assistant.complete_code(code_context, language)
    
    def get_command_suggestions(self, prefix: str = "") -> List[str]:
        """Get command suggestions based on prefix"""
        if not self.config["enabled"] or not self.config["command_prediction"]:
            return []
            
        return self.assistant.predict_command(prefix)
    
    def process_natural_language(self, nl_command: str) -> Dict[str, Any]:
        """Process natural language command"""
        if not self.config["enabled"] or not self.config["nl_processing"]:
            return {"success": False, "command": None, "message": "NL processing disabled"}
            
        result = self.assistant.process_nl_command(nl_command)
        
        if result["success"]:
            return {
                "success": True,
                "command": result["command"],
                "intent": result["intent"],
                "confidence": result["confidence"],
                "message": f"Translated to: {result['command']}"
            }
        elif result["command"]:
            # Partial command
            return {
                "success": False,
                "command": result["command"],
                "intent": result["intent"],
                "confidence": result["confidence"],
                "message": "Incomplete command translation - missing parameters"
            }
        else:
            return {
                "success": False,
                "command": None,
                "intent": result.get("intent"),
                "confidence": result.get("confidence", 0),
                "message": "Could not translate natural language command"
            }
    
    def record_executed_command(self, command: str, directory: str = None, output: str = None) -> None:
        """Record an executed command for learning"""
        if not self.config["enabled"]:
            return
            
        # Set context (current directory)
        if directory:
            self.assistant.set_context(directory)
            
        # Add command to history
        self.assistant.add_executed_command(command)
    
    def add_code_sample(self, code: str, language: str) -> None:
        """Add code sample for learning"""
        if not self.config["enabled"] or self.config["learning_mode"] == "off":
            return
            
        self.assistant.add_code_sample(code, language)
    
    def provide_command_feedback(self, nl_command: str, executed_command: str) -> None:
        """Provide feedback for NL command processing"""
        if not self.config["enabled"] or not self.config["auto_feedback"]:
            return
            
        self.assistant.provide_feedback(nl_command, executed_command)
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update AI settings"""
        for key, value in settings.items():
            if key in self.config:
                self.config[key] = value
                
        self._save_config(self.config)
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current AI settings"""
        return dict(self.config)
    
    def train_models(self, callback: Callable = None) -> None:
        """Trigger model training"""
        import threading
        
        def training_thread():
            self.assistant.train_models()
            if callback:
                callback()
        
        thread = threading.Thread(target=training_thread)
        thread.daemon = True
        thread.start()


class CommandLineInterface:
    """CLI for interacting with AI features"""
    
    def __init__(self, integration: AIIntegration):
        self.integration = integration
        self.last_nl_command = None
        self.last_suggestion = None
    
    def handle_input(self, user_input: str) -> Optional[str]:
        """Handle user input with AI assistance"""
        if not user_input:
            return None
            
        # Check if input is a special AI command
        if user_input.startswith("?"):
            # Natural language command
            nl_command = user_input[1:].strip()
            self.last_nl_command = nl_command
            result = self.integration.process_natural_language(nl_command)
            
            if result["success"]:
                self.last_suggestion = result["command"]
                print(f"🤖 {result['message']}")
                print(f"➡️  Run: {result['command']}")
                return result["command"]
            else:
                if result["command"]:
                    self.last_suggestion = result["command"]
                    print(f"🤖 {result['message']}")
                    print(f"➡️  Partial command: {result['command']}")
                else:
                    print(f"🤖 {result['message']}")
                return None
        
        elif user_input == "!!":
            # Execute last suggestion
            if self.last_suggestion:
                print(f"➡️  Running: {self.last_suggestion}")
                return self.last_suggestion
            else:
                print("No previous suggestion to execute")
                return None
        
        elif user_input.startswith("!learn "):
            # Manual learning example
            parts = user_input[7:].strip().split(" => ")
            if len(parts) == 2:
                nl_command, shell_command = parts
                self.integration.provide_command_feedback(nl_command, shell_command)
                print(f"🧠 Learned: '{nl_command}' => '{shell_command}'")
            else:
                print("Invalid format. Use: !learn natural language => shell command")
            return None
        
        elif user_input == "!ai settings":
            # Show AI settings
            settings = self.integration.get_settings()
            print("\nAI Assistant Settings:")
            print("=====================")
            for key, value in settings.items():
                print(f"{key}: {value}")
            return None
        
        elif user_input.startswith("!ai "):
            # Change AI settings
            setting = user_input[4:].strip().split(" ", 1)
            if len(setting) == 2:
                key, value = setting
                if key in self.integration.config:
                    # Convert value to appropriate type
                    if value.lower() in ("true", "yes", "on"):
                        value = True
                    elif value.lower() in ("false", "no", "off"):
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace(".", "", 1).isdigit():
                        value = float(value)
                        
                    self.integration.update_settings({key: value})
                    print(f"Updated setting: {key} = {value}")
                else:
                    print(f"Unknown setting: {key}")
            else:
                print("Invalid format. Use: !ai setting_name value")
            return None
        
        # Regular command, track for learning
        self.integration.record_executed_command(user_input)
        return user_input
    
    def suggest_commands(self, prefix: str = "") -> List[str]:
        """Get command suggestions"""
        return self.integration.get_command_suggestions(prefix)
    
    def complete_code(self, code: str, language: str) -> List[str]:
        """Get code completion suggestions"""
        return self.integration.get_code_completions(code, language)