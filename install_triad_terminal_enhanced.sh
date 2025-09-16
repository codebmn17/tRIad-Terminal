#!/bin/bash

# Enhanced Triad Terminal Installer
# A customizable terminal environment with striking visuals

echo -e "\e[38;5;39m▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\e[0m"
echo -e "\e[38;5;39m▓\e[0m                                       \e[38;5;39m▓\e[0m"
echo -e "\e[38;5;39m▓\e[0m     \e[38;5;213mTriad Terminal Installer\e[0m        \e[38;5;39m▓\e[0m"
echo -e "\e[38;5;39m▓\e[0m                                       \e[38;5;39m▓\e[0m"
echo -e "\e[38;5;39m▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\e[0m"
echo

# Detect environment
if [[ -d /data/data/com.termux ]]; then
  ENVIRONMENT="termux"
  echo -e "\e[38;5;46m📱 Termux environment detected\e[0m"
  BASE_DIR="$HOME/.triad"
  CONFIG_DIR="$HOME/.config/triad"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  ENVIRONMENT="macos"
  echo -e "\e[38;5;46m🍎 macOS environment detected\e[0m"
  BASE_DIR="$HOME/.triad"
  CONFIG_DIR="$HOME/.config/triad"
else
  ENVIRONMENT="linux"
  echo -e "\e[38;5;46m🐧 Linux environment detected\e[0m"
  BASE_DIR="$HOME/.triad"
  CONFIG_DIR="$HOME/.config/triad"
fi

# Create directories
mkdir -p "$BASE_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$BASE_DIR/bin"
mkdir -p "$BASE_DIR/themes"
mkdir -p "$BASE_DIR/plugins"
mkdir -p "$BASE_DIR/api"
mkdir -p "$BASE_DIR/projects"
mkdir -p "$BASE_DIR/ascii_art"

# Install dependencies based on environment
install_dependencies() {
  echo -e "\e[38;5;46m📦 Installing dependencies...\e[0m"

  if [[ "$ENVIRONMENT" == "termux" ]]; then
    pkg update -y
    pkg install -y python nodejs git openssh curl wget jq tmux zsh figlet toilet

    # Install Oh My Zsh if not already installed
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
      sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
    fi

  elif [[ "$ENVIRONMENT" == "macos" ]]; then
    # Check if brew is installed
    if ! command -v brew &> /dev/null; then
      echo "Installing Homebrew..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    brew install python node git openssh curl wget jq tmux zsh figlet toilet lolcat

    # Install Oh My Zsh if not already installed
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
      sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
    fi

  else # Linux
    if command -v apt-get &> /dev/null; then
      sudo apt-get update
      sudo apt-get install -y python3 python3-pip nodejs npm git openssh-client curl wget jq tmux zsh figlet toilet lolcat
    elif command -v dnf &> /dev/null; then
      sudo dnf install -y python3 python3-pip nodejs git openssh curl wget jq tmux zsh figlet toilet
    elif command -v pacman &> /dev/null; then
      sudo pacman -Syu --noconfirm python python-pip nodejs npm git openssh curl wget jq tmux zsh figlet
    else
      echo -e "\e[38;5;196m⚠️ Unsupported Linux distribution. Please install dependencies manually.\e[0m"
      return 1
    fi

    # Install Oh My Zsh if not already installed
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
      sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
    fi
  fi

  # Install Python packages
  pip install requests colorama termcolor pyyaml click python-dotenv rich

  echo -e "\e[38;5;46m✅ Dependencies installed successfully!\e[0m"
  return 0
}

# Create ASCII art
create_ascii_art() {
  mkdir -p "$BASE_DIR/ascii_art"

  # Create matrix rain animation script
  cat > "$BASE_DIR/ascii_art/matrix.py" << 'EOF'
#!/usr/bin/env python3
import os
import random
import time
import sys
from rich.console import Console
from rich.live import Live
from rich.text import Text

# Terminal dimensions
width = os.get_terminal_size().columns
height = 20

# Matrix characters
characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()"

# Streams configuration
streams = []
for i in range(width // 2):
    streams.append({
        'x': random.randint(0, width - 1),
        'y': random.randint(-height, 0),
        'speed': random.randint(1, 2),
        'length': random.randint(5, 15),
        'chars': []
    })
    for j in range(streams[i]['length']):
        streams[i]['chars'].append(random.choice(characters))

console = Console()

def update_streams():
    # Update positions
    for stream in streams:
        stream['y'] += stream['speed']
        # Reset if out of bounds
        if stream['y'] - stream['length'] > height:
            stream['y'] = random.randint(-height, 0)
            stream['x'] = random.randint(0, width - 1)
            stream['length'] = random.randint(5, 15)
            stream['chars'] = [random.choice(characters) for _ in range(stream['length'])]

        # Randomly change characters
        if random.random() < 0.1:
            idx = random.randint(0, stream['length'] - 1)
            stream['chars'][idx] = random.choice(characters)

def render():
    # Create screen buffer
    screen = [Text(' ' * width) for _ in range(height)]

    # Draw streams
    for stream in streams:
        for i in range(stream['length']):
            y = int(stream['y'] - i)
            if 0 <= y < height and 0 <= stream['x'] < width:
                # First character is brightest
                if i == 0:
                    color = "bright_white"
                # Next few are medium brightness
                elif i < 3:
                    color = "bright_green"
                # Rest are dimmer
                else:
                    color = "green"

                # Replace character in the text at the right position
                screen[y].stylize(f"bold {color}", stream['x'], stream['x'] + 1)
                screen[y] = Text(
                    screen[y].plain[:stream['x']] +
                    stream['chars'][i] +
                    screen[y].plain[stream['x']+1:],
                    style=screen[y].style
                )

    return Text.join("\n", screen)

def display_matrix(seconds=10):
    with Live(render(), refresh_per_second=15, screen=True) as live:
        start_time = time.time()
        while time.time() - start_time < seconds:
            update_streams()
            live.update(render())
            time.sleep(0.06)

if __name__ == "__main__":
    try:
        display_time = 5  # Default 5 seconds
        if len(sys.argv) > 1:
            try:
                display_time = int(sys.argv[1])
            except ValueError:
                pass

        display_matrix(display_time)
    except KeyboardInterrupt:
        sys.exit(0)
EOF

  # Create TRIAD ASCII art logo
  cat > "$BASE_DIR/ascii_art/logo.txt" << 'EOF'
████████╗██████╗ ██╗ █████╗ ██████╗
╚══██╔══╝██╔══██╗██║██╔══██╗██╔══██╗
   ██║   ██████╔╝██║███████║██║  ██║
   ██║   ██╔══██╗██║██╔══██║██║  ██║
   ██║   ██║  ██║██║██║  ██║██████╔╝
   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═════╝

████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗
╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║
   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║
   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║
   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝
EOF

  # Make scripts executable
  chmod +x "$BASE_DIR/ascii_art/matrix.py"
}

# Create main terminal script with enhanced visuals
create_terminal_script() {
  cat > "$BASE_DIR/bin/triad" << 'EOF'
#!/usr/bin/env python3

import os
import sys
import json
import yaml
import click
import shutil
import random
import subprocess
from pathlib import Path
from datetime import datetime
from termcolor import colored
import requests

# Try to import rich for enhanced visuals
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
VERSION = "1.0.0"

# Ensure config exists
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR, exist_ok=True)

# Load config
config_file = os.path.join(CONFIG_DIR, "config.yml")
if not os.path.exists(config_file):
    default_config = {
        "theme": "matrix",
        "plugins_enabled": ["git", "deployment", "api"],
        "api_keys": {},
        "user": {
            "name": os.environ.get("USER", "developer"),
            "email": ""
        }
    }
    with open(config_file, "w") as f:
        yaml.dump(default_config, f)

with open(config_file, "r") as f:
    config = yaml.safe_load(f)

# Colors for different themes
THEMES = {
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
    "bloodmoon": {
        "header": "red",
        "accent": "white",
        "text": "red",
        "error": "yellow",
        "success": "magenta",
        "warning": "yellow",
        "info": "red"
    },
    "synthwave": {
        "header": "magenta",
        "accent": "cyan",
        "text": "magenta",
        "error": "red",
        "success": "green",
        "warning": "yellow",
        "info": "blue"
    }
}

# Default to matrix if theme not found
current_theme = THEMES.get(config.get("theme", "matrix"), THEMES["matrix"])

# Terminal UI components
def print_header():
    term_width = shutil.get_terminal_size().columns

    # Use rich if available for fancier output
    if has_rich:
        console = Console()

        # Read ASCII logo
        try:
            with open(os.path.join(BASE_DIR, "ascii_art", "logo.txt"), "r") as f:
                logo = f.read()
        except:
            logo = "TRIAD TERMINAL"

        # Current date/time and user
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = config["user"]["name"]
        status_line = f"{now} | User: {user}"

        console.print(Panel(
            f"{logo}\n\n{status_line}",
            border_style=current_theme["header"],
            box=box.DOUBLE,
            expand=False,
            padding=(1, 2)
        ))
    else:
        # Fallback to simpler header
        print(colored("╔" + "═" * (term_width - 2) + "╗", current_theme["header"]))

        # Title centered
        title = "TRIAD TERMINAL"
        padding = (term_width - len(title) - 2) // 2
        print(colored("║", current_theme["header"]) + " " * padding + colored(title, current_theme["accent"], attrs=["bold"]) +
              " " * (term_width - len(title) - 2 - padding) + colored("║", current_theme["header"]))

        # Current date/time and user
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = config["user"]["name"]
        status_line = f"{now} | User: {user}"
        padding = (term_width - len(status_line) - 2) // 2
        print(colored("║", current_theme["header"]) + " " * padding + status_line +
              " " * (term_width - len(status_line) - 2 - padding) + colored("║", current_theme["header"]))

        print(colored("╚" + "═" * (term_width - 2) + "╝", current_theme["header"]))

def print_footer():
    term_width = shutil.get_terminal_size().columns

    # Use rich if available for fancier output
    if has_rich:
        console = Console()

        # Status information
        plugins_enabled = ", ".join(config.get("plugins_enabled", []))
        status_line = f"Plugins: {plugins_enabled} | v{VERSION}"

        console.print(Panel(
            status_line,
            border_style=current_theme["header"],
            box=box.DOUBLE,
            expand=False,
            padding=(0, 2)
        ))
    else:
        # Fallback to simpler footer
        print(colored("╔" + "═" * (term_width - 2) + "╗", current_theme["header"]))

        # Status information
        plugins_enabled = ", ".join(config.get("plugins_enabled", []))
        status_line = f"Plugins: {plugins_enabled} | v{VERSION}"
        print(colored("║", current_theme["header"]) + " " + status_line +
              " " * (term_width - len(status_line) - 3) + colored("║", current_theme["header"]))

        print(colored("╚" + "═" * (term_width - 2) + "╝", current_theme["header"]))

# Show matrix rain animation (if available)
def show_matrix_animation(seconds=3):
    matrix_script = os.path.join(BASE_DIR, "ascii_art", "matrix.py")
    if os.path.exists(matrix_script):
        try:
            subprocess.run([sys.executable, matrix_script, str(seconds)], check=True)
        except (subprocess.SubprocessError, KeyboardInterrupt):
            pass  # Ignore errors from the animation

# CLI interface with enhanced styling
@click.group()
@click.version_option(VERSION)
def cli():
    """Triad Terminal - Development Environment CLI"""
    pass

@cli.command()
def start():
    """Start the Triad Terminal interface"""
    # Show matrix animation for theme "matrix"
    if config.get("theme") == "matrix":
        show_matrix_animation(3)

    print_header()

    # Use rich tables if available
    if has_rich:
        console = Console()
        table = Table(show_header=False, box=box.SIMPLE, border_style=current_theme["text"])

        table.add_column("Command", style=current_theme["accent"] + " bold")
        table.add_column("Description")

        table.add_row("project", "Project management")
        table.add_row("deploy", "Deployment tools")
        table.add_row("api", "API tools")
        table.add_row("github", "GitHub integration")
        table.add_row("config", "Configure settings")
        table.add_row("tunnel", "SSH tunneling")

        console.print("\n[bold]Welcome to Triad Terminal![/bold]\n")
        console.print("Available commands:")
        console.print(table)
        console.print("\nType 'triad COMMAND --help' for more information.\n")
    else:
        # Fallback to simpler output
        print("\nWelcome to Triad Terminal!\n")
        print("Available commands:")
        print(colored("  project", current_theme["accent"], attrs=["bold"]) + "    - Project management")
        print(colored("  deploy", current_theme["accent"], attrs=["bold"]) + "     - Deployment tools")
        print(colored("  api", current_theme["accent"], attrs=["bold"]) + "        - API tools")
        print(colored("  github", current_theme["accent"], attrs=["bold"]) + "     - GitHub integration")
        print(colored("  config", current_theme["accent"], attrs=["bold"]) + "     - Configure settings")
        print(colored("  tunnel", current_theme["accent"], attrs=["bold"]) + "     - SSH tunneling")
        print("\nType 'triad COMMAND --help' for more information.\n")

    print_footer()

@cli.group()
def project():
    """Project management commands"""
    pass

@project.command("create")
@click.argument("name")
@click.option("--template", "-t", default="web",
              help="Project template (web, api, python, node)")
def project_create(name, template):
    """Create a new project"""
    project_dir = os.path.join(BASE_DIR, "projects", name)

    if os.path.exists(project_dir):
        if has_rich:
            Console().print(f"[bold {current_theme['error']}]Error:[/] Project {name} already exists")
        else:
            print(colored(f"Error: Project {name} already exists", current_theme["error"]))
        return

    if has_rich:
        Console().print(f"[bold {current_theme['info']}]Creating {template} project:[/] {name}...")
    else:
        print(colored(f"Creating {template} project: {name}...", current_theme["info"]))

    # Create project directory
    os.makedirs(project_dir, exist_ok=True)

    # Basic files based on template
    if template == "web":
        os.makedirs(os.path.join(project_dir, "css"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "js"), exist_ok=True)

        # Create index.html
        with open(os.path.join(project_dir, "index.html"), "w") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Project</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <h1>Welcome to your new project!</h1>
    <script src="js/main.js"></script>
</body>
</html>""")

        # Create style.css
        with open(os.path.join(project_dir, "css", "style.css"), "w") as f:
            f.write("""body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    line-height: 1.6;
}

h1 {
    color: #333;
}""")

        # Create main.js
        with open(os.path.join(project_dir, "js", "main.js"), "w") as f:
            f.write("""console.log('Project initialized!');""")

    elif template == "api":
        os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)

        # Create package.json
        with open(os.path.join(project_dir, "package.json"), "w") as f:
            f.write("""{
  "name": "%s",
  "version": "1.0.0",
  "description": "API project",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js"
  },
  "dependencies": {
    "express": "^4.17.1",
    "cors": "^2.8.5",
    "dotenv": "^10.0.0"
  },
  "devDependencies": {
    "nodemon": "^2.0.12"
  }
}""" % name)

        # Create index.js
        with open(os.path.join(project_dir, "src", "index.js"), "w") as f:
            f.write("""const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
  res.json({ message: 'API is running!' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});""")

        # Create .env
        with open(os.path.join(project_dir, ".env"), "w") as f:
            f.write("""PORT=3000""")

        # Create .gitignore
        with open(os.path.join(project_dir, ".gitignore"), "w") as f:
            f.write("""node_modules/
.env
.DS_Store""")

    elif template == "python":
        os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)

        # Create main.py
        with open(os.path.join(project_dir, "src", "main.py"), "w") as f:
            f.write("""def main():
    print("Hello from your Python project!")

if __name__ == "__main__":
    main()""")

        # Create requirements.txt
        with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
            f.write("""requests==2.28.1
pytest==7.1.2""")

        # Create README.md
        with open(os.path.join(project_dir, "README.md"), "w") as f:
            f.write("""# %s

A Python project created with Triad Terminal.

## Setup

```bash
pip install -r requirements.txt
