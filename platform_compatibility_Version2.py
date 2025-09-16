#!/usr/bin/env python3

"""
Triad Terminal Platform Compatibility Layer
Ensures consistent behavior across different operating systems
"""

import os
import platform
import shutil
import subprocess
import sys


class PlatformInfo:
    """Information about the current platform"""

    @staticmethod
    def is_windows() -> bool:
        return os.name == 'nt' or platform.system() == 'Windows'

    @staticmethod
    def is_macos() -> bool:
        return platform.system() == 'Darwin'

    @staticmethod
    def is_linux() -> bool:
        return platform.system() == 'Linux' and not PlatformInfo.is_termux()

    @staticmethod
    def is_termux() -> bool:
        return os.path.exists('/data/data/com.termux')

    @staticmethod
    def get_platform_name() -> str:
        if PlatformInfo.is_termux():
            return 'termux'
        elif PlatformInfo.is_windows():
            return 'windows'
        elif PlatformInfo.is_macos():
            return 'macos'
        elif PlatformInfo.is_linux():
            return 'linux'
        else:
            return 'unknown'

    @staticmethod
    def get_home_directory() -> str:
        """Get user's home directory"""
        return os.path.expanduser('~')

    @staticmethod
    def get_config_directory() -> str:
        """Get platform-specific config directory"""
        home = PlatformInfo.get_home_directory()

        if PlatformInfo.is_windows():
            # Windows: %APPDATA%\TriadTerminal
            appdata = os.getenv('APPDATA')
            if appdata:
                return os.path.join(appdata, 'TriadTerminal')
            return os.path.join(home, 'AppData', 'Roaming', 'TriadTerminal')

        elif PlatformInfo.is_macos():
            # macOS: ~/Library/Application Support/TriadTerminal
            return os.path.join(home, 'Library', 'Application Support', 'TriadTerminal')

        else:
            # Linux/Termux: ~/.config/triad
            return os.path.join(home, '.config', 'triad')

    @staticmethod
    def get_data_directory() -> str:
        """Get platform-specific data directory"""
        home = PlatformInfo.get_home_directory()

        if PlatformInfo.is_windows():
            # Windows: %LOCALAPPDATA%\TriadTerminal
            localdata = os.getenv('LOCALAPPDATA')
            if localdata:
                return os.path.join(localdata, 'TriadTerminal')
            return os.path.join(home, 'AppData', 'Local', 'TriadTerminal')

        elif PlatformInfo.is_macos():
            # macOS: ~/Library/Application Support/TriadTerminal
            return os.path.join(home, 'Library', 'Application Support', 'TriadTerminal')

        else:
            # Linux/Termux: ~/.local/share/triad
            return os.path.join(home, '.local', 'share', 'triad')

    @staticmethod
    def get_temp_directory() -> str:
        """Get a temporary directory"""
        import tempfile
        return tempfile.gettempdir()

    @staticmethod
    def get_terminal_size() -> dict[str, int]:
        """Get terminal dimensions"""
        try:
            columns, lines = shutil.get_terminal_size()
            return {'columns': columns, 'lines': lines}
        except Exception:
            return {'columns': 80, 'lines': 24}  # Fallback values

    @staticmethod
    def supports_ansi_colors() -> bool:
        """Check if terminal supports ANSI colors"""
        if PlatformInfo.is_windows():
            # Windows Terminal, ConEmu, and modern PowerShell support ANSI
            if os.environ.get('WT_SESSION') or os.environ.get('ConEmuANSI') == 'ON':
                return True

            # Check Windows version - Windows 10 1607 and later support ANSI
            try:
                version = sys.getwindowsversion()
                if version.major >= 10:
                    return True
            except:
                pass

            return False

        # Most Unix-like terminals support ANSI colors
        return True

class SystemCommands:
    """Platform-specific system commands"""

    @staticmethod
    def clear_screen() -> None:
        """Clear the terminal screen"""
        if PlatformInfo.is_windows():
            os.system('cls')
        else:
            os.system('clear')

    @staticmethod
    def open_file(path: str) -> bool:
        """Open a file with default application"""
        try:
            if PlatformInfo.is_windows():
                os.startfile(path)
            elif PlatformInfo.is_macos():
                subprocess.run(['open', path], check=True)
            else:
                subprocess.run(['xdg-open', path], check=True)
            return True
        except Exception:
            return False

    @staticmethod
    def open_url(url: str) -> bool:
        """Open URL in default browser"""
        try:
            import webbrowser
            webbrowser.open(url)
            return True
        except Exception:
            return False

    @staticmethod
    def run_command(cmd: list[str], shell: bool = False) -> str | None:
        """Run system command and return output"""
        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                check=True,
                text=True,
                capture_output=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")
            print(f"Error output: {e.stderr}")
            return None
        except Exception as e:
            print(f"Error running command: {e}")
            return None

class Dependencies:
    """Handle platform-specific dependencies"""

    @staticmethod
    def check_dependency(name: str) -> bool:
        """Check if a dependency is installed"""
        try:
            if PlatformInfo.is_windows():
                subprocess.run(['where', name], check=True, stdout=subprocess.PIPE)
            else:
                subprocess.run(['which', name], check=True, stdout=subprocess.PIPE)
            return True
        except Exception:
            return False

    @staticmethod
    def get_install_command(dependency: str) -> str:
        """Get platform-specific install command for a dependency"""
        if PlatformInfo.is_termux():
            return f"pkg install {dependency}"

        elif PlatformInfo.is_windows():
            # Try to suggest appropriate Windows package manager
            if Dependencies.check_dependency('choco'):
                return f"choco install {dependency}"
            elif Dependencies.check_dependency('scoop'):
                return f"scoop install {dependency}"
            else:
                return f"Please install {dependency} manually"

        elif PlatformInfo.is_macos():
            if Dependencies.check_dependency('brew'):
                return f"brew install {dependency}"
            else:
                return f"Please install Homebrew first, then run: brew install {dependency}"

        else:  # Linux
            if Dependencies.check_dependency('apt'):
                return f"sudo apt install {dependency}"
            elif Dependencies.check_dependency('dnf'):
                return f"sudo dnf install {dependency}"
            elif Dependencies.check_dependency('pacman'):
                return f"sudo pacman -S {dependency}"
            else:
                return f"Please install {dependency} using your package manager"

    @staticmethod
    def install_python_package(package: str) -> bool:
        """Install a Python package"""
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
            return True
        except Exception:
            return False

class ShellIntegration:
    """Handle shell integration"""

    @staticmethod
    def get_shell_type() -> str:
        """Detect current shell type"""
        shell = os.environ.get('SHELL', '')
        if 'zsh' in shell:
            return 'zsh'
        elif 'bash' in shell:
            return 'bash'
        elif 'fish' in shell:
            return 'fish'
        elif PlatformInfo.is_windows():
            if 'powershell' in os.environ.get('PSModulePath', '').lower():
                return 'powershell'
            return 'cmd'
        else:
            return 'sh'

    @staticmethod
    def get_shell_config_file() -> str | None:
        """Get path to shell configuration file"""
        home = PlatformInfo.get_home_directory()
        shell_type = ShellIntegration.get_shell_type()

        if shell_type == 'zsh':
            return os.path.join(home, '.zshrc')
        elif shell_type == 'bash':
            # Check for both possible bash config files
            bashrc = os.path.join(home, '.bashrc')
            if os.path.exists(bashrc):
                return bashrc
            return os.path.join(home, '.bash_profile')
        elif shell_type == 'fish':
            fish_dir = os.path.join(home, '.config', 'fish')
            os.makedirs(fish_dir, exist_ok=True)
            return os.path.join(fish_dir, 'config.fish')
        elif shell_type == 'powershell':
            # Get PowerShell profile path
            try:
                profile_path = subprocess.run(
                    ['powershell', '-Command', 'echo $PROFILE'],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
                return profile_path
            except Exception:
                return None
        return None

    @staticmethod
    def add_to_path(directory: str) -> bool:
        """Add directory to PATH in shell config"""
        config_file = ShellIntegration.get_shell_config_file()
        if not config_file:
            return False

        shell_type = ShellIntegration.get_shell_type()

        try:
            # Read existing config
            if os.path.exists(config_file):
                with open(config_file) as f:
                    content = f.read()
            else:
                content = ""

            # Check if already in config
            if directory in content:
                return True

            # Add to PATH based on shell type
            with open(config_file, 'a') as f:
                f.write('\n# Added by Triad Terminal\n')

                if shell_type == 'powershell':
                    f.write(f'$env:PATH = "$env:PATH;{directory}"\n')
                elif shell_type == 'fish':
                    f.write(f'set -gx PATH {directory} $PATH\n')
                else:  # bash, zsh, sh
                    f.write(f'export PATH="{directory}:$PATH"\n')

            return True
        except Exception:
            return False
