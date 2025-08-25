#!/usr/bin/env python3

"""
Triad Terminal Plugin System
Provides an extensible plugin architecture
"""

import os
import sys
import json
import importlib.util
from dataclasses import dataclass
from typing import Dict, List, Any, Callable, Optional, Type

@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    main_file: str
    commands: List[str]
    hooks: List[str] = None
    dependencies: List[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        return cls(
            name=data.get('name', 'unknown'),
            version=data.get('version', '0.1.0'),
            description=data.get('description', ''),
            author=data.get('author', 'unknown'),
            main_file=data.get('main', 'plugin.py'),
            commands=data.get('commands', []),
            hooks=data.get('hooks', []),
            dependencies=data.get('dependencies', [])
        )

class PluginInterface:
    """Base class for all plugins"""
    
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.enabled = False
        
    def initialize(self) -> bool:
        """Initialize the plugin"""
        return True
        
    def get_commands(self) -> List[Callable]:
        """Return a list of click commands this plugin provides"""
        return []
        
    def cleanup(self) -> None:
        """Clean up resources when plugin is disabled"""
        pass
    
    def on_event(self, event_name: str, *args, **kwargs) -> Any:
        """Handle events from the terminal"""
        method_name = f"on_{event_name}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(*args, **kwargs)
        return None

class PluginLoader:
    """Handles loading plugin modules dynamically"""
    
    @staticmethod
    def load_from_path(plugin_dir: str) -> Optional[Type[PluginInterface]]:
        """Load a plugin from a directory path"""
        manifest_path = os.path.join(plugin_dir, 'manifest.json')
        
        if not os.path.exists(manifest_path):
            return None
            
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
                
            metadata = PluginMetadata.from_dict(manifest_data)
            
            # Load the main module
            main_file = os.path.join(plugin_dir, metadata.main_file)
            if not os.path.exists(main_file):
                return None
                
            # Import the module
            module_name = f"triad_plugin_{os.path.basename(plugin_dir)}"
            spec = importlib.util.spec_from_file_location(module_name, main_file)
            if spec is None or spec.loader is None:
                return None
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the plugin class (should be a subclass of PluginInterface)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, PluginInterface) and attr != PluginInterface:
                    plugin_class = attr
                    break
                    
            if plugin_class is None:
                return None
                
            # Create and return the plugin instance
            return plugin_class(metadata)
            
        except Exception as e:
            print(f"Error loading plugin from {plugin_dir}: {e}")
            return None

class PluginManager:
    """Central manager for all plugins"""
    
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, PluginInterface] = {}
        self.enabled_plugins: List[str] = []
        
    def discover_plugins(self) -> Dict[str, PluginMetadata]:
        """Find all available plugins"""
        results = {}
        
        if not os.path.exists(self.plugin_dir):
            return results
            
        for item in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, item)
            if not os.path.isdir(plugin_path):
                continue
                
            manifest_path = os.path.join(plugin_path, 'manifest.json')
            if not os.path.exists(manifest_path):
                continue
                
            try:
                with open(manifest_path, 'r') as f:
                    manifest_data = json.load(f)
                    metadata = PluginMetadata.from_dict(manifest_data)
                    results[item] = metadata
            except Exception:
                pass
                
        return results
        
    def load_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Load a plugin by name"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
            
        plugin_path = os.path.join(self.plugin_dir, plugin_name)
        if not os.path.exists(plugin_path):
            return None
            
        plugin = PluginLoader.load_from_path(plugin_path)
        if plugin is not None:
            self.plugins[plugin_name] = plugin
            
        return plugin
        
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        if plugin_name in self.enabled_plugins:
            return True
            
        # Load plugin if not already loaded
        plugin = self.load_plugin(plugin_name)
        if plugin is None:
            return False
            
        # Check dependencies
        if plugin.metadata.dependencies:
            for dep in plugin.metadata.dependencies:
                if dep not in self.enabled_plugins:
                    # Try to enable dependency
                    if not self.enable_plugin(dep):
                        return False
        
        # Initialize the plugin
        if not plugin.initialize():
            return False
            
        plugin.enabled = True
        self.enabled_plugins.append(plugin_name)
        
        # Trigger the enabled event
        plugin.on_event('enabled')
        
        return True
        
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        if plugin_name not in self.enabled_plugins:
            return True
            
        plugin = self.plugins.get(plugin_name)
        if plugin is None:
            self.enabled_plugins.remove(plugin_name)
            return True
            
        # Check if other plugins depend on this one
        for name, p in self.plugins.items():
            if name in self.enabled_plugins and p.metadata.dependencies and plugin_name in p.metadata.dependencies:
                # Disable dependent plugin first
                if not self.disable_plugin(name):
                    return False
        
        # Trigger the disabled event and cleanup
        plugin.on_event('disabled')
        plugin.cleanup()
        
        plugin.enabled = False
        self.enabled_plugins.remove(plugin_name)
        
        return True
        
    def get_commands(self) -> Dict[str, List[Callable]]:
        """Get all commands from enabled plugins"""
        commands = {}
        
        for plugin_name in self.enabled_plugins:
            plugin = self.plugins.get(plugin_name)
            if plugin:
                plugin_commands = plugin.get_commands()
                if plugin_commands:
                    commands[plugin_name] = plugin_commands
                    
        return commands
        
    def trigger_event(self, event_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Trigger an event on all enabled plugins"""
        results = {}
        
        for plugin_name in self.enabled_plugins:
            plugin = self.plugins.get(plugin_name)
            if plugin:
                try:
                    result = plugin.on_event(event_name, *args, **kwargs)
                    if result is not None:
                        results[plugin_name] = result
                except Exception as e:
                    print(f"Error in plugin {plugin_name} handling event {event_name}: {e}")
                    
        return results