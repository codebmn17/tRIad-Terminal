#!/usr/bin/env python3

"""
Triad Terminal Configuration Manager
Handles loading, saving, and updating configurations
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("triad.config")

class ConfigManager:
    """Manages configuration loading and saving with validation"""
    
    def __init__(self, config_dir: str, config_name: str = "config.yml"):
        self.config_dir = os.path.expanduser(config_dir)
        self.config_name = config_name
        self.config_path = os.path.join(self.config_dir, self.config_name)
        self._config = None
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Default configuration schema with types for validation
        self.schema = {
            "theme": {"type": str, "default": "matrix", "choices": ["matrix", "cyberpunk", "synthwave", "bloodmoon"]},
            "plugins_enabled": {"type": list, "default": ["git", "deployment", "api"]},
            "api_keys": {"type": dict, "default": {}},
            "user": {
                "type": dict,
                "default": {
                    "name": os.environ.get("USER", "developer"),
                    "email": ""
                }
            },
            "performance": {
                "type": dict,
                "default": {
                    "animations": True,
                    "parallel_operations": True,
                    "cache_results": True
                }
            },
            "advanced": {
                "type": dict,
                "default": {
                    "log_level": "info",
                    "max_processes": 4,
                    "save_history": True,
                    "auto_update_check": True
                }
            }
        }
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        config = {}
        for key, schema_item in self.schema.items():
            config[key] = schema_item["default"]
        return config
    
    def load(self) -> Dict[str, Any]:
        """Load configuration, creating default if doesn't exist"""
        if self._config is not None:
            return self._config
            
        if not os.path.exists(self.config_path):
            logger.info(f"Config file not found at {self.config_path}, creating default config")
            self._config = self._create_default_config()
            self.save()
            return self._config
            
        try:
            with open(self.config_path, "r") as f:
                if self.config_name.endswith((".yml", ".yaml")):
                    loaded_config = yaml.safe_load(f)
                elif self.config_name.endswith(".json"):
                    loaded_config = json.load(f)
                else:
                    logger.error(f"Unsupported config format: {self.config_name}")
                    self._config = self._create_default_config()
                    return self._config
            
            # Validate and merge with defaults to ensure all required keys exist
            self._config = self._validate_and_merge(loaded_config)
            return self._config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._config = self._create_default_config()
            return self._config
    
    def _validate_and_merge(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate config and merge with defaults for missing values"""
        result = {}
        
        for key, schema_item in self.schema.items():
            if key in loaded_config:
                value = loaded_config[key]
                # Check type and fix if needed
                if not isinstance(value, schema_item["type"]):
                    logger.warning(f"Config value for '{key}' is wrong type. Expected {schema_item['type'].__name__}, got {type(value).__name__}")
                    result[key] = schema_item["default"]
                # Check choices if specified
                elif "choices" in schema_item and value not in schema_item["choices"]:
                    logger.warning(f"Config value for '{key}' must be one of {schema_item['choices']}")
                    result[key] = schema_item["default"]
                else:
                    result[key] = value
            else:
                # Use default if key is missing
                result[key] = schema_item["default"]
                
            # Special handling for nested dictionaries
            if schema_item["type"] == dict and isinstance(schema_item["default"], dict):
                # If we have defaults for nested keys, ensure they exist
                if isinstance(result[key], dict):
                    for nested_key, default_value in schema_item["default"].items():
                        if nested_key not in result[key]:
                            result[key][nested_key] = default_value
        
        return result
    
    def save(self) -> bool:
        """Save current configuration"""
        if self._config is None:
            self._config = self._create_default_config()
            
        try:
            with open(self.config_path, "w") as f:
                if self.config_name.endswith((".yml", ".yaml")):
                    yaml.dump(self._config, f)
                elif self.config_name.endswith(".json"):
                    json.dump(self._config, f, indent=2)
                else:
                    logger.error(f"Unsupported config format: {self.config_name}")
                    return False
            
            logger.debug(f"Config saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        config = self.load()
        
        # Support dot notation for nested keys (e.g., "user.name")
        if "." in key:
            parts = key.split(".")
            value = config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        return config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        config = self.load()
        
        # Support dot notation for nested keys
        if "." in key:
            parts = key.split(".")
            target = config
            
            # Navigate to the parent dictionary
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                elif not isinstance(target[part], dict):
                    target[part] = {}
                target = target[part]
                
            # Set the value
            target[parts[-1]] = value
            
        else:
            config[key] = value
            
        # Save changes
        return self.save()
    
    def reset(self) -> bool:
        """Reset configuration to defaults"""
        self._config = self._create_default_config()
        return self.save()