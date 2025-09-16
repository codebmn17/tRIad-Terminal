#!/usr/bin/env python3

"""
Triad Terminal Enhanced UI
Dark theme with vivid colors and improved visuals
"""

import logging
import os
import random
import shutil
import sys
import time
from typing import Any

# Try imports with fallbacks for cross-platform compatibility
try:
    from rich import box
    from rich.console import Console
    from rich.layout import Layout
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.style import Style
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# For terminal colors if Rich is not available
try:
    import colorama
    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

logger = logging.getLogger("triad.ui")

class ThemeManager:
    """Manages terminal UI themes"""

    # Theme definitions with vivid colors
    THEMES = {
        "matrix": {
            "name": "Matrix",
            "description": "Classic digital rain look",
            "colors": {
                "background": "black",
                "foreground": "bright_green",
                "accent": "green",
                "secondary": "dark_green",
                "highlight": "#00ff00",
                "error": "bright_red",
                "warning": "bright_yellow",
                "success": "bright_green",
                "info": "bright_cyan",
                "panel": "dark_green"
            },
            "styles": {
                "header": "bold green on black",
                "title": "bold bright_green",
                "text": "green",
                "command": "bright_green",
                "link": "underline bright_green",
                "panel_border": "green"
            }
        },
        "cyberpunk": {
            "name": "Cyberpunk",
            "description": "Neon future vibes",
            "colors": {
                "background": "#120458",
                "foreground": "#f615a1",
                "accent": "#00e5ff",
                "secondary": "#a64dff",
                "highlight": "#ffff00",
                "error": "#ff3131",
                "warning": "#ff9900",
                "success": "#00ff9f",
                "info": "#00e5ff",
                "panel": "#1e0977"
            },
            "styles": {
                "header": "bold #f615a1 on #120458",
                "title": "bold #00e5ff",
                "text": "#f615a1",
                "command": "bold #00e5ff",
                "link": "underline #00e5ff",
                "panel_border": "#00e5ff"
            }
        },
        "synthwave": {
            "name": "Synthwave",
            "description": "Retro 80s aesthetic",
            "colors": {
                "background": "#241734",
                "foreground": "#ff71ce",
                "accent": "#01cdfe",
                "secondary": "#b967ff",
                "highlight": "#fffb96",
                "error": "#fe4450",
                "warning": "#ffaa00",
                "success": "#05ffa1",
                "info": "#01cdfe",
                "panel": "#342356"
            },
            "styles": {
                "header": "bold #ff71ce on #241734",
                "title": "bold #01cdfe",
                "text": "#ff71ce",
                "command": "bold #05ffa1",
                "link": "underline #01cdfe",
                "panel_border": "#b967ff"
            }
        },
        "bloodmoon": {
            "name": "Blood Moon",
            "description": "Dark crimson aesthetic",
            "colors": {
                "background": "#0F0000",
                "foreground": "#FF3333",
                "accent": "#FF5555",
                "secondary": "#AA0000",
                "highlight": "#FFAAAA",
                "error": "#FF0000",
                "warning": "#FFAA00",
                "success": "#FF6666",
                "info": "#FF9999",
                "panel": "#220000"
            },
            "styles": {
                "header": "bold #FF3333 on #0F0000",
                "title": "bold #FF5555",
                "text": "#FF3333",
                "command": "bold #FF5555",
                "link": "underline #FF5555",
                "panel_border": "#AA0000"
            }
        },
        "quantum": {
            "name": "Quantum",
            "description": "Futuristic sci-fi interface",
            "colors": {
                "background": "#070B34",
                "foreground": "#00B2FF",
                "accent": "#6D00CC",
                "secondary": "#0066FF",
                "highlight": "#FFFFFF",
                "error": "#FF0055",
                "warning": "#FF9900",
                "success": "#00CC99",
                "info": "#00B2FF",
                "panel": "#0A1555"
            },
            "styles": {
                "header": "bold #00B2FF on #070B34",
                "title": "bold #6D00CC",
                "text": "#00B2FF",
                "command": "bold #00CC99",
                "link": "underline #00B2FF",
                "panel_border": "#0066FF"
            }
        }
    }

    def __init__(self, theme_name: str = "matrix"):
        """Initialize with the selected theme"""
        self.current_theme = self.get_theme(theme_name)

    def get_theme(self, name: str) -> dict[str, Any]:
        """Get a theme by name"""
        return self.THEMES.get(name.lower(), self.THEMES["matrix"])

    def get_available_themes(self) -> list[dict[str, str]]:
        """Get list of available themes"""
        return [
            {"name": details["name"], "id": theme_id, "description": details["description"]}
            for theme_id, details in self.THEMES.items()
        ]

    def set_theme(self, name: str) -> bool:
        """Set the current theme"""
        if name.lower() in self.THEMES:
            self.current_theme = self.get_theme(name)
            return True
        return False

    def get_style(self, element: str) -> str:
        """Get style for a specific UI element"""
        return self.current_theme["styles"].get(element, "")

    def get_color(self, color_name: str) -> str:
        """Get a specific color from the current theme"""
        return self.current_theme["colors"].get(color_name, "")

class Animation:
    """Terminal animations for Triad UI"""

    @staticmethod
    def loading(message: str = "Loading", duration: float = 3.0, fps: int = 10) -> None:
        """Display a loading animation"""
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        end_time = time.time() + duration

        try:
            while time.time() < end_time:
                for frame in frames:
                    sys.stdout.write(f"\r{frame} {message}..." + " " * 10)
                    sys.stdout.flush()
                    time.sleep(1/fps)

                    # Exit early if duration reached
                    if time.time() >= end_time:
                        break

            sys.stdout.write("\r" + " " * (len(message) + 15) + "\r")
            sys.stdout.flush()

        except KeyboardInterrupt:
            sys.stdout.write("\r" + " " * (len(message) + 15) + "\r")
            sys.stdout.flush()

    @staticmethod
    def matrix_rain(duration: float = 3.0) -> None:
        """Show matrix-style digital rain animation"""
        if not os.isatty(sys.stdout.fileno()):
            return

        try:
            # Get terminal size
            width = shutil.get_terminal_size().columns
            height = min(shutil.get_terminal_size().lines - 1, 20)  # Limit height

            # Set up the streams
            streams = []
            for i in range(width // 3):  # One stream every ~3 columns
                column = random.randint(0, width - 1)
                speed = random.uniform(0.1, 0.5)
                length = random.randint(5, height // 2)
                head_pos = -random.randint(0, height)
                streams.append({"column": column, "speed": speed, "length": length, "head_pos": head_pos})

            # Characters to use
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-=_+[]{}|;:,.<>?/"

            # Set up the screen buffer
            screen = [[" " for _ in range(width)] for _ in range(height)]

            # Color setup
            if HAS_COLORAMA:
                GREEN = colorama.Fore.GREEN
                BRIGHT_GREEN = colorama.Fore.GREEN + colorama.Style.BRIGHT
                RESET = colorama.Style.RESET_ALL
            else:
                GREEN = ""
                BRIGHT_GREEN = ""
                RESET = ""

            start_time = time.time()

            # Hide cursor
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()

            try:
                while time.time() - start_time < duration:
                    # Update the streams
                    for stream in streams:
                        # Clear old positions
                        for i in range(height):
                            screen[i][stream["column"]] = " "

                        # Update head position
                        stream["head_pos"] += stream["speed"]

                        # Draw new positions
                        for i in range(stream["length"]):
                            pos = int(stream["head_pos"]) - i
                            if 0 <= pos < height:
                                if i == 0:
                                    screen[pos][stream["column"]] = f"{BRIGHT_GREEN}{random.choice(chars)}{RESET}"
                                else:
                                    screen[pos][stream["column"]] = f"{GREEN}{random.choice(chars)}{RESET}"

                    # Render the screen
                    sys.stdout.write("\033[H")  # Move to top-left
                    for row in screen:
                        sys.stdout.write("".join(row) + "\n")
                    sys.stdout.flush()

                    time.sleep(0.05)
            finally:
                # Show cursor and restore screen
                sys.stdout.write("\033[?25h")  # Show cursor
                sys.stdout.write("\033[H")  # Move to top-left
                for _ in range(height):
                    sys.stdout.write(" " * width + "\n")
                sys.stdout.write("\033[H")  # Move to top-left
                sys.stdout.flush()

        except (KeyboardInterrupt, Exception):
            # Ensure cursor is visible on exit
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

class TerminalUI:
    """Enhanced terminal user interface with rich visuals"""

    def __init__(self, theme_name: str = "matrix"):
        self.theme_manager = ThemeManager(theme_name)
        self.console = Console() if HAS_RICH else None
        self.term_width = shutil.get_terminal_size().columns
        self.term_height = shutil.get_terminal_size().lines

    def clear_screen(self) -> None:
        """Clear the terminal screen"""
        if os.name == 'nt':  # For Windows
            os.system('cls')
        else:  # For Linux/Mac
            os.system('clear')

    def print_intro(self, skip_animation: bool = False) -> None:
        """Display startup animation and intro"""
        self.clear_screen()

        if not skip_animation:
            # Choose animation based on theme
            theme_name = self.theme_manager.current_theme["name"].lower()
            if theme_name == "matrix":
                Animation.matrix_rain(2.0)
            else:
                Animation.loading("Initializing Triad Terminal", 1.5)

        self.clear_screen()

        # Get ASCII logo based on theme
        logo = self._get_ascii_logo()

        if HAS_RICH and self.console:
            # Rich formatting
            style = self.theme_manager.get_style("title")
            panel_style = self.theme_manager.get_style("panel_border")

            self.console.print(Panel(
                Text(logo, style=style),
                border_style=panel_style,
                box=box.DOUBLE,
                expand=False,
                padding=(1, 2)
            ))

            # Version and info
            info_text = Text()
            info_text.append("Version: ", style="dim")
            info_text.append("2.0.0 ", style=self.theme_manager.get_style("text"))
            info_text.append("• ", style="dim")
            info_text.append("Welcome to the next generation of development environments",
                           style=self.theme_manager.get_style("text"))

            self.console.print(Panel(
                info_text,
                border_style=panel_style,
                box=box.SIMPLE,
                expand=False,
                padding=(0, 1)
            ))

        else:
            # Fallback for terminals without Rich
            if HAS_COLORAMA:
                color_start = getattr(colorama.Fore, self.theme_manager.get_color("foreground").upper(),
                                    colorama.Fore.WHITE)
                color_reset = colorama.Style.RESET_ALL
            else:
                color_start = ""
                color_reset = ""

            print(color_start + logo + color_reset)
            print("\nVersion: 2.0.0 • Welcome to the next generation of development environments\n")

    def _get_ascii_logo(self) -> str:
        """Get ASCII logo for current theme"""
        logos = {
            "matrix": r"""
 ▄▄▄█████▓ ██▀███   ██▓ ▄▄▄      ▓█████▄     ▄▄▄█████▓▓█████  ██▀███   ███▄ ▄███▓ ██▓ ███▄    █  ▄▄▄       ██▓    
 ▓  ██▒ ▓▒▓██ ▒ ██▒▓██▒▒████▄    ▒██▀ ██▌    ▓  ██▒ ▓▒▓█   ▀ ▓██ ▒ ██▒▓██▒▀█▀ ██▒▓██▒ ██ ▀█   █ ▒████▄    ▓██▒    
 ▒ ▓██░ ▒░▓██ ░▄█ ▒▒██▒▒██  ▀█▄  ░██   █▌    ▒ ▓██░ ▒░▒███   ▓██ ░▄█ ▒▓██    ▓██░▒██▒▓██  ▀█ ██▒▒██  ▀█▄  ▒██░    
 ░ ▓██▓ ░ ▒██▀▀█▄  ░██░░██▄▄▄▄██ ░▓█▄   ▌    ░ ▓██▓ ░ ▒▓█  ▄ ▒██▀▀█▄  ▒██    ▒██ ░██░▓██▒  ▐▌██▒░██▄▄▄▄██ ▒██░    
   ▒██▒ ░ ░██▓ ▒██▒░██░ ▓█   ▓██▒░▒████▓       ▒██▒ ░ ░▒████▒░██▓ ▒██▒▒██▒   ░██▒░██░▒██░   ▓██░ ▓█   ▓██▒░██████▒
   ▒ ░░   ░ ▒▓ ░▒▓░░▓   ▒▒   ▓▒█░ ▒▒▓  ▒       ▒ ░░   ░░ ▒░ ░░ ▒▓ ░▒▓░░ ▒░   ░  ░░▓  ░ ▒░   ▒ ▒  ▒▒   ▓▒█░░ ▒░▓  ░
     ░      ░▒ ░ ▒░ ▒ ░  ▒   ▒▒ ░ ░ ▒  ▒         ░     ░ ░  ░  ░▒ ░ ▒░░  ░      ░ ▒ ░░ ░░   ░ ▒░  ▒   ▒▒ ░░ ░ ▒  ░
   ░        ░░   ░  ▒ ░  ░   ▒    ░ ░  ░       ░         ░     ░░   ░ ░      ░    ▒ ░   ░   ░ ░   ░   ▒     ░ ░   
             ░      ░        ░  ░   ░                    ░  ░   ░            ░    ░           ░       ░  ░    ░  ░
                                  ░                                                                                
""",
            "cyberpunk": r"""
 _______ _____  _____  ___   _____     _____  _____ _____  ___  ___ _____ _   _  ___   _     
|_   _| \  ___|/  _  \|_  | |  _  \   |_   _||  ___|  __ \|  \/  ||_   _|| \ | |/   | | |    
  | |    \ `--.|  / \  \| | | |_| |     | |  | |__  | |  \/| .  . |  | |  |  \| |/ /| | | |    
  | |     `--. \ |_/ /   | | |  _  /     | |  |  __| | | __ | |\/| |  | |  | . ` / /_| | | |    
  | |    /\__/ /\   /|_  | | | | \ \    _| |_ | |___ | |_\ \| |  | | _| |_ | |\  \___  | | |____
  \_/    \____/  \_/ ( )_/ |_| |_|\|   \___/ \____/  \____/\_|  |_/ \___/ \_| \_|   |_/ \_____/
                     |/                                                                       
""",
            "synthwave": r"""
  _______  ______    ___   ______   ______       _______  _______  ______    __   __  ___   __    _  ______   ___     
 |       ||    _ |  |   | |      | |    _ |     |       ||       ||    _ |  |  |_|  ||   | |  |  | ||      | |   |    
 |_     _||   | ||  |   | |  _    ||   | ||     |_     _||    ___||   | ||  |       ||   | |   |_| ||  _    ||   |    
   |   |  |   |_||_ |   | | | |   ||   |_||_      |   |  |   |___ |   |_||_ |       ||   | |       || | |   ||   |    
   |   |  |    __  ||   | | |_|   ||    __  |     |   |  |    ___||    __  ||       ||   | |  _    || |_|   ||   |___ 
   |   |  |   |  | ||   | |       ||   |  | |     |   |  |   |___ |   |  | || ||_|| ||   | | | |   ||       ||       |
   |___|  |___|  |_||___| |______| |___|  |_|     |___|  |_______||___|  |_||_|   |_||___| |_|  |__||______| |_______|
""",
            "bloodmoon": r"""
██████╗  ██╗      ██████╗  ██████╗ ██████╗     ███╗   ███╗ ██████╗  ██████╗ ███╗   ██╗
██╔══██╗ ██║     ██╔═══██╗██╔═══██╗██╔══██╗    ████╗ ████║██╔═══██╗██╔═══██╗████╗  ██║
██████╔╝ ██║     ██║   ██║██║   ██║██║  ██║    ██╔████╔██║██║   ██║██║   ██║██╔██╗ ██║
██╔══██╗ ██║     ██║   ██║██║   ██║██║  ██║    ██║╚██╔╝██║██║   ██║██║   ██║██║╚██╗██║
██████╔╝ ███████╗╚██████╔╝╚██████╔╝██████╔╝    ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝██║ ╚████║
╚═════╝  ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝     ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
""",
            "quantum": r"""
 ██████  ██    ██  █████  ███    ██ ████████ ██    ██ ███    ███ 
██    ██ ██    ██ ██   ██ ████   ██    ██    ██    ██ ████  ████ 
██    ██ ██    ██ ███████ ██ ██  ██    ██    ██    ██ ██ ████ ██ 
██ ▄▄ ██ ██    ██ ██   ██ ██  ██ ██    ██    ██    ██ ██  ██  ██ 
 ██████   ██████  ██   ██ ██   ████    ██     ██████  ██      ██ 
    ▀▀                                                           
"""
        }

        theme_name = self.theme_manager.current_theme["name"].lower()
        return logos.get(theme_name, logos["matrix"])

    def print_header(self) -> None:
        """Print terminal header"""
        if HAS_RICH and self.console:
            # Current date/time and user
            import datetime
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user = os.getenv("USER", os.getenv("USERNAME", "user"))

            # Create header with theme colors
            panel_style = self.theme_manager.get_style("panel_border")
            header_style = self.theme_manager.get_style("header")

            header_text = Text()
            header_text.append("TRIAD TERMINAL", style="bold")
            header_text.append(f" • {now} • ", style="dim")
            header_text.append(f"User: {user}", style="")

            self.console.print(Panel(
                header_text,
                border_style=panel_style,
                style=header_style,
                box=box.DOUBLE,
                expand=True,
                padding=(0, 2)
            ))
        else:
            # Fallback for terminals without Rich
            import datetime
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user = os.getenv("USER", os.getenv("USERNAME", "user"))

            if HAS_COLORAMA:
                color = getattr(colorama.Fore, self.theme_manager.get_color("foreground").upper(),
                               colorama.Fore.WHITE)
                bright = colorama.Style.BRIGHT
                reset = colorama.Style.RESET_ALL
            else:
                color = ""
                bright = ""
                reset = ""

            print(f"{color}{bright}{'═' * self.term_width}{reset}")
            print(f"{color}{bright} TRIAD TERMINAL • {now} • User: {user}{reset}")
            print(f"{color}{bright}{'═' * self.term_width}{reset}")

    def print_footer(self) -> None:
        """Print terminal footer"""
        if HAS_RICH and self.console:
            # Create footer with theme colors
            panel_style = self.theme_manager.get_style("panel_border")

            footer_text = Text()
            footer_text.append("Press ", style="dim")
            footer_text.append("Ctrl+C", style="bold")
            footer_text.append(" to exit • ", style="dim")
            footer_text.append("Type ", style="dim")
            footer_text.append("help", style="bold")
            footer_text.append(" for commands", style="dim")

            self.console.print(Panel(
                footer_text,
                border_style=panel_style,
                box=box.SIMPLE,
                expand=True,
                padding=(0, 2)
            ))
        else:
            # Fallback for terminals without Rich
            if HAS_COLORAMA:
                color = getattr(colorama.Fore, self.theme_manager.get_color("foreground").upper(),
                               colorama.Fore.WHITE)
                reset = colorama.Style.RESET_ALL
            else:
                color = ""
                reset = ""

            print(f"{color}{'─' * self.term_width}{reset}")
            print(f"{color}Press Ctrl+C to exit • Type 'help' for commands{reset}")

    def print_command_list(self, commands: list[dict[str, str]]) -> None:
        """Print a list of available commands"""
        if HAS_RICH and self.console:
            # Create a table with commands
            table = Table(show_header=True, box=box.SIMPLE)

            table.add_column("Command", style=self.theme_manager.get_style("command"))
            table.add_column("Description")

            for cmd in commands:
                table.add_row(cmd["name"], cmd["description"])

            # Print with a title
            self.console.print()
            self.console.print("Available commands:", style="bold")
            self.console.print(table)
            self.console.print()
        else:
            # Fallback for terminals without Rich
            if HAS_COLORAMA:
                color = getattr(colorama.Fore, self.theme_manager.get_color("foreground").upper(),
                               colorama.Fore.WHITE)
                bright = colorama.Style.BRIGHT
                reset = colorama.Style.RESET_ALL
            else:
                color = ""
                bright = ""
                reset = ""

            print("\nAvailable commands:")
            for cmd in commands:
                print(f"  {color}{bright}{cmd['name']:<15}{reset} - {cmd['description']}")
            print()

    def print_message(self, message: str, level: str = "info") -> None:
        """Print a message with appropriate styling"""
        if HAS_RICH and self.console:
            # Map level to theme color
            color_map = {
                "error": self.theme_manager.get_color("error"),
                "warning": self.theme_manager.get_color("warning"),
                "success": self.theme_manager.get_color("success"),
                "info": self.theme_manager.get_color("info")
            }

            color = color_map.get(level, color_map["info"])

            # Add appropriate prefix
            prefix_map = {
                "error": "[bold red]ERROR:[/]",
                "warning": "[bold yellow]WARNING:[/]",
                "success": "[bold green]SUCCESS:[/]",
                "info": "[bold blue]INFO:[/]"
            }

            prefix = prefix_map.get(level, prefix_map["info"])

            # Print the message
            self.console.print(f"{prefix} {message}", style=color)
        else:
            # Fallback for terminals without Rich
            if HAS_COLORAMA:
                color_map = {
                    "error": colorama.Fore.RED,
                    "warning": colorama.Fore.YELLOW,
                    "success": colorama.Fore.GREEN,
                    "info": colorama.Fore.CYAN
                }

                color = color_map.get(level, colorama.Fore.CYAN)
                reset = colorama.Style.RESET_ALL
                bright = colorama.Style.BRIGHT

                prefix_map = {
                    "error": "ERROR:",
                    "warning": "WARNING:",
                    "success": "SUCCESS:",
                    "info": "INFO:"
                }

                prefix = prefix_map.get(level, prefix_map["info"])

                # Print the message
                print(f"{color}{bright}{prefix}{reset} {color}{message}{reset}")
            else:
                # No color support
                prefix_map = {
                    "error": "ERROR:",
                    "warning": "WARNING:",
                    "success": "SUCCESS:",
                    "info": "INFO:"
                }

                prefix = prefix_map.get(level, prefix_map["info"])
                print(f"{prefix} {message}")

    def create_dashboard_layout(self) -> Layout | None:
        """Create a rich dashboard layout"""
        if not HAS_RICH:
            return None

        # Create main layout
        layout = Layout(name="root")

        # Split into sections
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )

        # Further split the main area
        layout["main"].split_row(
            Layout(name="sidebar", ratio=1),
            Layout(name="content", ratio=3)
        )

        return layout

    def render_code(self, code: str, language: str = "python") -> None:
        """Render code with syntax highlighting"""
        if HAS_RICH and self.console:
            # Create syntax object
            syntax = Syntax(
                code,
                language,
                theme="monokai",
                line_numbers=True,
                word_wrap=True
            )

            # Display in a panel
            self.console.print(Panel(
                syntax,
                border_style=self.theme_manager.get_style("panel_border"),
                title=f"{language.capitalize()} Code",
                title_align="left"
            ))
        else:
            # Fallback without syntax highlighting
            print(f"\n--- {language.capitalize()} Code ---\n")
            print(code)
            print("\n-------------------\n")
