#!/usr/bin/env python3

"""
Triad Terminal - Performance Optimized Version
This version includes:
- Memory usage optimizations
- Faster startup time
- More efficient rendering
"""

import os
import sys
import json
import yaml
import click
import shutil
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Try imports with fallbacks for cross-platform compatibility
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    has_rich = True
except ImportError:
    has_rich = False

# Configuration
CONFIG_DIR = os.path.expanduser("~/.config/triad")
BASE_DIR = os.path.expanduser("~/.triad")
VERSION = "2.0.0"

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)

# Cache for expensive operations
@lru_cache(maxsize=32)
def get_theme_colors(theme_name):
    """Get theme colors with caching for performance"""
    themes = {
        "matrix": {
            "header": "green",
            "accent": "white",
            "text": "green",
            "error": "red",
            "success": "green",
            "warning": "yellow",
            "info": "cyan"
        },
        "cyberpunk": {
            "header": "blue",
            "accent": "magenta",
            "text": "cyan",
            "error": "red",
            "success": "green",
            "warning": "yellow",
            "info": "blue"
        },
        "synthwave": {
            "header": "magenta",
            "accent": "cyan",
            "text": "magenta",
            "error": "red",
            "success": "green",
            "warning": "yellow",
            "info": "blue"
        },
        "bloodmoon": {
            "header": "red",
            "accent": "white",
            "text": "red",
            "error": "yellow",
            "success": "magenta",
            "warning": "yellow",
            "info": "red"
        }
    }
    return themes.get(theme_name, themes["matrix"])

class Config:
    """Configuration manager with lazy loading"""
    _instance = None
    _config = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance
    
    def __init__(self):
        self.config_file = os.path.join(CONFIG_DIR, "config.yml")
        
    def load(self):
        """Load config only when needed"""
        if self._config is not None:
            return self._config
            
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
        if not os.path.exists(self.config_file):
            default_config = {
                "theme": "matrix",
                "plugins_enabled": ["git", "deployment", "api"],
                "api_keys": {},
                "user": {
                    "name": os.environ.get("USER", "developer"),
                    "email": ""
                },
                "performance": {
                    "animations": True,
                    "parallel_operations": True,
                    "cache_results": True
                }
            }
            with open(self.config_file, "w") as f:
                yaml.dump(default_config, f)
            self._config = default_config
        else:
            with open(self.config_file, "r") as f:
                self._config = yaml.safe_load(f)
        
        return self._config
    
    def save(self):
        """Save configuration changes"""
        if self._config is None:
            return
            
        with open(self.config_file, "w") as f:
            yaml.dump(self._config, f)
    
    def get(self, key, default=None):
        """Get configuration value with default"""
        config = self.load()
        return config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        config = self.load()
        config[key] = value
        self.save()

# Improved UI rendering with caching
class TerminalUI:
    def __init__(self):
        self.config = Config.get_instance()
        self.console = Console() if has_rich else None
        self.term_width = shutil.get_terminal_size().columns
        self._cached_logo = None
        
    @property
    def current_theme(self):
        """Get current theme colors"""
        theme_name = self.config.get("theme", "matrix")
        return get_theme_colors(theme_name)
        
    def get_logo(self):
        """Get logo with caching"""
        if self._cached_logo is not None:
            return self._cached_logo
            
        logo_path = os.path.join(BASE_DIR, "ascii_art", "logo.txt")
        try:
            with open(logo_path, "r") as f:
                self._cached_logo = f.read()
        except:
            self._cached_logo = "TRIAD TERMINAL"
            
        return self._cached_logo
    
    def print_header(self):
        """Print terminal header"""
        if has_rich and self.console:
            # Current date/time and user
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user = self.config.get("user", {}).get("name", "user")
            status_line = f"{now} | User: {user}"
            
            self.console.print(Panel(
                f"{self.get_logo()}\n\n{status_line}",
                border_style=self.current_theme["header"],
                box=box.DOUBLE,
                expand=False,
                padding=(1, 2)
            ))
        else:
            # Fallback to simpler header
            from termcolor import colored
            print(colored("╔" + "═" * (self.term_width - 2) + "╗", self.current_theme["header"]))
            
            # Title centered
            title = "TRIAD TERMINAL"
            padding = (self.term_width - len(title) - 2) // 2
            print(colored("║", self.current_theme["header"]) + " " * padding + 
                  colored(title, self.current_theme["accent"], attrs=["bold"]) + 
                  " " * (self.term_width - len(title) - 2 - padding) + 
                  colored("║", self.current_theme["header"]))
            
            # Current date/time and user
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user = self.config.get("user", {}).get("name", "user")
            status_line = f"{now} | User: {user}"
            padding = (self.term_width - len(status_line) - 2) // 2
            print(colored("║", self.current_theme["header"]) + " " * padding + 
                  status_line + 
                  " " * (self.term_width - len(status_line) - 2 - padding) + 
                  colored("║", self.current_theme["header"]))
            
            print(colored("╚" + "═" * (self.term_width - 2) + "╝", self.current_theme["header"]))

    def print_footer(self):
        """Print terminal footer"""
        if has_rich and self.console:
            # Status information
            plugins_enabled = ", ".join(self.config.get("plugins_enabled", []))
            status_line = f"Plugins: {plugins_enabled} | v{VERSION}"
            
            self.console.print(Panel(
                status_line,
                border_style=self.current_theme["header"],
                box=box.DOUBLE,
                expand=False,
                padding=(0, 2)
            ))
        else:
            from termcolor import colored
            # Fallback to simpler footer
            print(colored("╔" + "═" * (self.term_width - 2) + "╗", self.current_theme["header"]))
            
            # Status information
            plugins_enabled = ", ".join(self.config.get("plugins_enabled", []))
            status_line = f"Plugins: {plugins_enabled} | v{VERSION}"
            print(colored("║", self.current_theme["header"]) + " " + status_line + 
                  " " * (self.term_width - len(status_line) - 3) + 
                  colored("║", self.current_theme["header"]))
            
            print(colored("╚" + "═" * (self.term_width - 2) + "╝", self.current_theme["header"]))

# Plugin system
class PluginManager:
    """Manages loading and running plugins"""
    def __init__(self):
        self.plugins = {}
        self.plugin_dir = os.path.join(BASE_DIR, "plugins")
        os.makedirs(self.plugin_dir, exist_ok=True)
        
    def discover_plugins(self):
        """Find all available plugins"""
        results = {}
        if not os.path.exists(self.plugin_dir):
            return results
            
        for item in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, item)
            if os.path.isdir(plugin_path):
                manifest_path = os.path.join(plugin_path, "manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            results[item] = manifest
                    except:
                        pass
        
        return results
    
    def load_plugin(self, plugin_name):
        """Load a specific plugin by name"""
        plugin_path = os.path.join(self.plugin_dir, plugin_name)
        if not os.path.exists(plugin_path):
            return None
            
        manifest_path = os.path.join(plugin_path, "manifest.json")
        if not os.path.exists(manifest_path):
            return None
            
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            # Import main plugin file
            sys.path.insert(0, plugin_path)
            main_file = manifest.get("main", "plugin.py")
            module_name = main_file.replace(".py", "")
            
            plugin_module = __import__(module_name)
            sys.path.pop(0)
            
            # Create plugin instance
            if hasattr(plugin_module, 'Plugin'):
                plugin = plugin_module.Plugin()
                self.plugins[plugin_name] = plugin
                return plugin
                
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
            return None
    
    def get_enabled_plugins(self):
        """Get all enabled plugins"""
        config = Config.get_instance()
        enabled_plugins = config.get("plugins_enabled", [])
        
        result = []
        for plugin_name in enabled_plugins:
            if plugin_name in self.plugins:
                result.append(self.plugins[plugin_name])
            else:
                plugin = self.load_plugin(plugin_name)
                if plugin:
                    result.append(plugin)
        
        return result
        
# Main CLI interface
@click.group()
@click.version_option(VERSION)
def cli():
    """Triad Terminal - Development Environment CLI"""
    pass

@cli.command()
@click.option('--no-animation', is_flag=True, help="Skip animations")
def start(no_animation):
    """Start the Triad Terminal interface"""
    config = Config.get_instance()
    ui = TerminalUI()
    plugin_manager = PluginManager()
    
    # Show matrix animation only if enabled and not skipped
    if (config.get("theme") == "matrix" and
            config.get("performance", {}).get("animations", True) and
            not no_animation):
        matrix_script = os.path.join(BASE_DIR, "ascii_art", "matrix.py")
        if os.path.exists(matrix_script):
            try:
                subprocess.run([sys.executable, matrix_script, "3"], check=True)
            except (subprocess.SubprocessError, KeyboardInterrupt):
                pass
    
    ui.print_header()
    
    # Load plugins in background
    executor.submit(plugin_manager.discover_plugins)
    
    # Use rich tables if available
    if has_rich:
        console = Console()
        table = Table(show_header=False, box=box.SIMPLE, border_style=ui.current_theme["text"])
        
        table.add_column("Command", style=ui.current_theme["accent"] + " bold")
        table.add_column("Description")
        
        table.add_row("project", "Project management")
        table.add_row("deploy", "Deployment tools")
        table.add_row("api", "API tools")
        table.add_row("github", "GitHub integration")
        table.add_row("config", "Configure settings")
        table.add_row("tunnel", "SSH tunneling")
        table.add_row("plugins", "Manage plugins")
        
        console.print("\n[bold]Welcome to Triad Terminal![/bold]\n")
        console.print("Available commands:")
        console.print(table)
        console.print("\nType 'triad COMMAND --help' for more information.\n")
    else:
        from termcolor import colored
        # Fallback to simpler output
        print("\nWelcome to Triad Terminal!\n")
        print("Available commands:")
        print(colored("  project", ui.current_theme["accent"], attrs=["bold"]) + "    - Project management")
        print(colored("  deploy", ui.current_theme["accent"], attrs=["bold"]) + "     - Deployment tools")
        print(colored("  api", ui.current_theme["accent"], attrs=["bold"]) + "        - API tools")
        print(colored("  github", ui.current_theme["accent"], attrs=["bold"]) + "     - GitHub integration")
        print(colored("  config", ui.current_theme["accent"], attrs=["bold"]) + "     - Configure settings")
        print(colored("  tunnel", ui.current_theme["accent"], attrs=["bold"]) + "     - SSH tunneling")
        print(colored("  plugins", ui.current_theme["accent"], attrs=["bold"]) + "   - Manage plugins")
        print("\nType 'triad COMMAND --help' for more information.\n")
    
    ui.print_footer()

@cli.group()
def plugins():
    """Plugin management commands"""
    pass

@plugins.command("list")
def plugins_list():
    """List all available plugins"""
    config = Config.get_instance()
    ui = TerminalUI()
    plugin_manager = PluginManager()
    
    all_plugins = plugin_manager.discover_plugins()
    enabled_plugins = config.get("plugins_enabled", [])
    
    if not all_plugins:
        if has_rich:
            Console().print("No plugins found.")
        else:
            print("No plugins found.")
        return
    
    if has_rich:
        console = Console()
        table = Table(show_header=True, header_style=f"bold {ui.current_theme['accent']}")
        
        table.add_column("Plugin Name")
        table.add_column("Version")
        table.add_column("Status")
        table.add_column("Description")
        
        for name, manifest in all_plugins.items():
            status = "[green]Enabled[/]" if name in enabled_plugins else "[gray]Disabled[/]"
            table.add_row(
                name,
                manifest.get("version", "0.1.0"),
                status,
                manifest.get("description", "")
            )
            
        console.print("\n[bold]Installed Plugins:[/bold]")
        console.print(table)
    else:
        from termcolor import colored
        print(colored("Installed Plugins:", ui.current_theme["accent"], attrs=["bold"]))
        for name, manifest in all_plugins.items():
            status = colored("Enabled", "green") if name in enabled_plugins else "Disabled"
            print(f"  - {name} (v{manifest.get('version', '0.1.0')}) [{status}]")
            print(f"    {manifest.get('description', '')}")

@plugins.command("enable")
@click.argument("plugin_name")
def plugins_enable(plugin_name):
    """Enable a plugin"""
    config = Config.get_instance()
    ui = TerminalUI()
    plugin_manager = PluginManager()
    
    all_plugins = plugin_manager.discover_plugins()
    enabled_plugins = config.get("plugins_enabled", [])
    
    if plugin_name not in all_plugins:
        if has_rich:
            Console().print(f"[bold {ui.current_theme['error']}]Error:[/] Plugin {plugin_name} not found")
        else:
            from termcolor import colored
            print(colored(f"Error: Plugin {plugin_name} not found", ui.current_theme["error"]))
        return
    
    if plugin_name in enabled_plugins:
        if has_rich:
            Console().print(f"Plugin {plugin_name} is already enabled")
        else:
            print(f"Plugin {plugin_name} is already enabled")
        return
    
    # Try loading the plugin
    plugin = plugin_manager.load_plugin(plugin_name)
    if plugin is None:
        if has_rich:
            Console().print(f"[bold {ui.current_theme['error']}]Error:[/] Failed to load plugin {plugin_name}")
        else:
            from termcolor import colored
            print(colored(f"Error: Failed to load plugin {plugin_name}", ui.current_theme["error"]))
        return
    
    # Enable the plugin
    enabled_plugins.append(plugin_name)
    config.set("plugins_enabled", enabled_plugins)
    
    if has_rich:
        Console().print(f"[bold {ui.current_theme['success']}]✅ Plugin {plugin_name} enabled[/]")
    else:
        from termcolor import colored
        print(colored(f"✅ Plugin {plugin_name} enabled", ui.current_theme["success"]))

@plugins.command("disable")
@click.argument("plugin_name")
def plugins_disable(plugin_name):
    """Disable a plugin"""
    config = Config.get_instance()
    ui = TerminalUI()
    
    enabled_plugins = config.get("plugins_enabled", [])
    
    if plugin_name not in enabled_plugins:
        if has_rich:
            Console().print(f"Plugin {plugin_name} is already disabled")
        else:
            print(f"Plugin {plugin_name} is already disabled")
        return
    
    # Disable the plugin
    enabled_plugins.remove(plugin_name)
    config.set("plugins_enabled", enabled_plugins)
    
    if has_rich:
        Console().print(f"[bold {ui.current_theme['success']}]Plugin {plugin_name} disabled[/]")
    else:
        from termcolor import colored
        print(colored(f"Plugin {plugin_name} disabled", ui.current_theme["success"]))

@plugins.command("create")
@click.argument("plugin_name")
def plugins_create(plugin_name):
    """Create a new plugin template"""
    ui = TerminalUI()
    plugin_dir = os.path.join(BASE_DIR, "plugins", plugin_name)
    
    if os.path.exists(plugin_dir):
        if has_rich:
            Console().print(f"[bold {ui.current_theme['error']}]Error:[/] Plugin {plugin_name} already exists")
        else:
            from termcolor import colored
            print(colored(f"Error: Plugin {plugin_name} already exists", ui.current_theme["error"]))
        return
    
    # Create plugin directory
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Create manifest.json
    manifest = {
        "name": plugin_name,
        "version": "0.1.0",
        "description": f"A plugin for Triad Terminal",
        "author": Config.get_instance().get("user", {}).get("name", "Unknown"),
        "main": "plugin.py",
        "commands": ["hello"]
    }
    
    with open(os.path.join(plugin_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create plugin.py
    with open(os.path.join(plugin_dir, "plugin.py"), "w") as f:
        f.write("""import click

class Plugin:
    """A Triad Terminal plugin"""
    
    def __init__(self):
        self.name = "PLUGIN_NAME"
    
    def get_commands(self):
        """Return a list of click commands this plugin provides"""
        @click.command()
        def hello():
            """Say hello from the plugin"""
            click.echo(f"Hello from {self.name} plugin!")
        
        return [hello]
""".replace("PLUGIN_NAME", plugin_name))
    
    if has_rich:
        Console().print(f"[bold {ui.current_theme['success']}]✅ Plugin {plugin_name} created[/]")
        Console().print(f"Location: {plugin_dir}")
    else:
        from termcolor import colored
        print(colored(f"✅ Plugin {plugin_name} created", ui.current_theme["success"]))
        print(f"Location: {plugin_dir}")

# More performance improvements for the other commands would go here

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # If no arguments, run the start command
        sys.argv.append("start")
    
    try:
        cli()
    except Exception as e:
        config = Config.get_instance()
        theme_name = config.get("theme", "matrix")
        theme = get_theme_colors(theme_name)
        
        if has_rich:
            Console().print(f"[bold {theme['error']}]Error: {str(e)}[/]")
        else:
            from termcolor import colored
            print(colored(f"Error: {str(e)}", theme["error"]))
        sys.exit(1)