#!/usr/bin/env python3

"""
Triad Terminal Shell Interface
Provides enhanced shell integration capabilities
"""

import contextlib
import os
import sys
import re
import pty
import fcntl
import select
import signal
import shlex
import subprocess
import threading
import logging
import traceback
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Callable, Union, IO

logger = logging.getLogger("triad.shell")

class ShellEnvironment:
    """Manages shell environment variables and configuration"""
    
    def __init__(self, config_dir: str = "~/.triad/shell"):
        self.config_dir = os.path.expanduser(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Store original environment
        self.original_env = dict(os.environ)
        
        # Current environment
        self.current_env = dict(os.environ)
        
        # Shell history
        self.history_file = os.path.join(self.config_dir, "history")
        self.history = self._load_history()
        
        # Shell aliases
        self.aliases_file = os.path.join(self.config_dir, "aliases")
        self.aliases = self._load_aliases()
        
        # Path management
        self.original_path = os.environ.get('PATH', '')
        
        # Shell preferences
        self.preferences = {
            'prompt': '\\[\033[01;32m\\]\\u@triad\\[\033[00m\\]:\\[\033[01;34m\\]\\w\\[\033[00m\\]\\$ ',
            'editor': os.environ.get('EDITOR', 'nano'),
            'use_color': True,
            'history_size': 1000,
            'auto_completion': True
        }
    
    def _load_history(self) -> List[str]:
        """Load command history"""
        history = []
        
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = [line.strip() for line in f.readlines()]
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                
        return history
    
    def save_history(self) -> None:
        """Save command history"""
        try:
            # Limit history size
            max_size = self.preferences.get('history_size', 1000)
            history = self.history[-max_size:] if len(self.history) > max_size else self.history
            
            with open(self.history_file, 'w') as f:
                f.write('\n'.join(history))
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def add_to_history(self, command: str) -> None:
        """Add command to history"""
        if command and command.strip() and (not self.history or command != self.history[-1]):
            self.history.append(command)
            
            # Save history periodically
            if len(self.history) % 10 == 0:
                self.save_history()
    
    def _load_aliases(self) -> Dict[str, str]:
        """Load shell aliases"""
        aliases = {}
        
        if os.path.exists(self.aliases_file):
            try:
                with open(self.aliases_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                name, value = parts
                                aliases[name.strip()] = value.strip()
            except Exception as e:
                logger.error(f"Error loading aliases: {e}")
                
        return aliases
    
    def save_aliases(self) -> None:
        """Save shell aliases"""
        try:
            with open(self.aliases_file, 'w') as f:
                for name, value in self.aliases.items():
                    f.write(f"{name}={value}\n")
        except Exception as e:
            logger.error(f"Error saving aliases: {e}")
    
    def add_alias(self, name: str, value: str) -> bool:
        """Add or update a shell alias"""
        if not name or not value:
            return False
            
        self.aliases[name] = value
        self.save_aliases()
        return True
    
    def remove_alias(self, name: str) -> bool:
        """Remove a shell alias"""
        if name in self.aliases:
            del self.aliases[name]
            self.save_aliases()
            return True
        return False
    
    def get_aliases(self) -> Dict[str, str]:
        """Get all aliases"""
        return dict(self.aliases)
    
    def set_env_var(self, name: str, value: str) -> None:
        """Set an environment variable"""
        self.current_env[name] = value
        os.environ[name] = value
    
    def get_env_var(self, name: str) -> Optional[str]:
        """Get an environment variable"""
        return self.current_env.get(name)
    
    def unset_env_var(self, name: str) -> None:
        """Unset an environment variable"""
        if name in self.current_env:
            del self.current_env[name]
        if name in os.environ:
            del os.environ[name]
    
    def reset_env(self) -> None:
        """Reset environment to original state"""
        # Clear current environment
        for key in list(os.environ.keys()):
            del os.environ[key]
            
        # Restore original environment
        for key, value in self.original_env.items():
            os.environ[key] = value
            
        self.current_env = dict(self.original_env)
    
    def add_to_path(self, directory: str) -> None:
        """Add directory to PATH"""
        if not os.path.exists(directory):
            return
            
        path = self.current_env.get('PATH', '')
        paths = path.split(os.pathsep)
        
        if directory not in paths:
            paths.insert(0, directory)
            new_path = os.pathsep.join(paths)
            
            self.current_env['PATH'] = new_path
            os.environ['PATH'] = new_path
    
    def get_path(self) -> List[str]:
        """Get current PATH as a list"""
        path = self.current_env.get('PATH', '')
        return path.split(os.pathsep)
    
    def get_env(self) -> Dict[str, str]:
        """Get all environment variables"""
        return dict(self.current_env)
    
    def get_expanded_command(self, command: str) -> str:
        """Expand aliases in command"""
        parts = shlex.split(command)
        if not parts:
            return command
            
        # Check if the first part is an alias
        if parts[0] in self.aliases:
            # Replace the alias with its value
            expanded = self.aliases[parts[0]]
            if len(parts) > 1:
                # Add the remaining arguments
                expanded += ' ' + ' '.join(parts[1:])
            return expanded
            
        return command
    
    def set_preference(self, name: str, value: Any) -> None:
        """Set a shell preference"""
        if name in self.preferences:
            self.preferences[name] = value
    
    def get_preference(self, name: str) -> Any:
        """Get a shell preference"""
        return self.preferences.get(name)
    
    def get_formatted_prompt(self) -> str:
        """Get formatted shell prompt"""
        prompt = self.preferences.get('prompt', '> ')
        
        # Process special sequences
        prompt = prompt.replace('\\u', os.environ.get('USER', 'user'))
        prompt = prompt.replace('\\h', os.uname().nodename.split('.')[0])
        prompt = prompt.replace('\\w', os.getcwd().replace(os.path.expanduser('~'), '~'))
        prompt = prompt.replace('\\W', os.path.basename(os.getcwd()))
        
        return prompt

class InteractiveShell:
    """Interactive shell with advanced features"""
    
    def __init__(self, env: ShellEnvironment = None):
        self.env = env or ShellEnvironment()
        
        # Current working directory
        self.cwd = os.getcwd()
        
        # Terminal dimensions
        self.rows, self.cols = self._get_terminal_size()
        
        # Command handlers
        self.command_handlers = self._setup_command_handlers()
        
        # Callbacks
        self.output_callback = None
        
        # Run state
        self.running = False
        self.current_process = None
    
    def _setup_command_handlers(self) -> Dict[str, Callable]:
        """Set up internal command handlers"""
        return {
            'cd': self._handle_cd,
            'exit': self._handle_exit,
            'alias': self._handle_alias,
            'unalias': self._handle_unalias,
            'export': self._handle_export,
            'unset': self._handle_unset,
            'history': self._handle_history,
            'path': self._handle_path,
            'pwd': self._handle_pwd,
            'clear': self._handle_clear,
            'echo': self._handle_echo
        }
    
    def _get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal dimensions"""
        try:
            import shutil
            return shutil.get_terminal_size((80, 24))
        except (ImportError, OSError):
            return 24, 80
    
    def _update_terminal_size(self) -> None:
        """Update terminal dimensions"""
        self.rows, self.cols = self._get_terminal_size()
    
    def _handle_cd(self, args: List[str]) -> int:
        """Handle cd command"""
        target_dir = args[0] if args else '~'
        
        # Expand home directory
        if target_dir == '~' or target_dir.startswith('~/'):
            target_dir = os.path.expanduser(target_dir)
            
        # Handle - (previous directory)
        if target_dir == '-':
            target_dir = os.environ.get('OLDPWD', '')
            if not target_dir:
                print("OLDPWD not set")
                return 1
                
        try:
            # Save old directory
            old_cwd = os.getcwd()
            os.environ['OLDPWD'] = old_cwd
            
            # Change directory
            os.chdir(target_dir)
            self.cwd = os.getcwd()
            
            # Update PWD environment variable
            os.environ['PWD'] = self.cwd
            self.env.set_env_var('PWD', self.cwd)
            
            return 0
        except FileNotFoundError:
            print(f"cd: {target_dir}: No such file or directory")
            return 1
        except PermissionError:
            print(f"cd: {target_dir}: Permission denied")
            return 1
        except Exception as e:
            print(f"cd: error: {e}")
            return 1
    
    def _handle_exit(self, args: List[str]) -> int:
        """Handle exit command"""
        exit_code = 0
        if args and args[0].isdigit():
            exit_code = int(args[0])
            
        self.running = False
        return exit_code
    
    def _handle_alias(self, args: List[str]) -> int:
        """Handle alias command"""
        if not args:
            # Display all aliases
            for name, value in self.env.get_aliases().items():
                print(f"{name}='{value}'")
            return 0
            
        # Add/update alias
        if '=' in args[0]:
            name, value = args[0].split('=', 1)
            self.env.add_alias(name, value)
            return 0
            
        # Display specific alias
        if args[0] in self.env.aliases:
            print(f"{args[0]}='{self.env.aliases[args[0]]}'")
            return 0
            
        print(f"alias: {args[0]}: not found")
        return 1
    
    def _handle_unalias(self, args: List[str]) -> int:
        """Handle unalias command"""
        if not args:
            print("unalias: not enough arguments")
            return 1
            
        if args[0] == '-a':
            # Remove all aliases
            self.env.aliases.clear()
            self.env.save_aliases()
            return 0
            
        # Remove specific alias
        if args[0] in self.env.aliases:
            self.env.remove_alias(args[0])
            return 0
            
        print(f"unalias: {args[0]}: not found")
        return 1
    
    def _handle_export(self, args: List[str]) -> int:
        """Handle export command"""
        if not args:
            # Display all environment variables
            for name, value in sorted(self.env.get_env().items()):
                print(f"export {name}='{value}'")
            return 0
            
        for arg in args:
            if '=' in arg:
                # Set variable
                name, value = arg.split('=', 1)
                self.env.set_env_var(name, value)
            else:
                print(f"export: {arg}: invalid variable name")
                return 1
                
        return 0
    
    def _handle_unset(self, args: List[str]) -> int:
        """Handle unset command"""
        if not args:
            print("unset: not enough arguments")
            return 1
            
        for name in args:
            self.env.unset_env_var(name)
            
        return 0
    
    def _handle_history(self, args: List[str]) -> int:
        """Handle history command"""
        if args and args[0] == '-c':
            # Clear history
            self.env.history.clear()
            self.env.save_history()
            return 0
            
        # Display history
        for i, cmd in enumerate(self.env.history):
            print(f"{i+1}  {cmd}")
            
        return 0
    
    def _handle_path(self, args: List[str]) -> int:
        """Handle path command"""
        if not args:
            # Display path
            for path in self.env.get_path():
                print(path)
            return 0
            
        if args[0] == 'add' and len(args) > 1:
            # Add to path
            self.env.add_to_path(os.path.expanduser(args[1]))
            return 0
            
        print("Usage: path [add <directory>]")
        return 1
    
    def _handle_pwd(self, args: List[str]) -> int:
        """Handle pwd command"""
        print(os.getcwd())
        return 0
    
    def _handle_clear(self, args: List[str]) -> int:
        """Handle clear command"""
        os.system('cls' if os.name == 'nt' else 'clear')
        return 0
    
    def _handle_echo(self, args: List[str]) -> int:
        """Handle echo command"""
        # Process environment variable expansion
        processed_args = []
        for arg in args:
            if arg.startswith('$'):
                var_name = arg[1:]
                var_value = self.env.get_env_var(var_name) or ''
                processed_args.append(var_value)
            else:
                processed_args.append(arg)
                
        print(' '.join(processed_args))
        return 0
    
    def _process_internal_command(self, command: str) -> Tuple[bool, int]:
        """Process internal shell commands"""
        # Split command into tokens
        try:
            tokens = shlex.split(command)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            return True, 1
            
        if not tokens:
            return False, 0
            
        cmd = tokens[0].lower()
        args = tokens[1:]
        
        # Check if command is an internal handler
        if cmd in self.command_handlers:
            return True, self.command_handlers[cmd](args)
            
        return False, 0
    
    def execute_command(self, command: str) -> int:
        """Execute a shell command"""
        if not command or not command.strip():
            return 0
            
        # Save to history
        self.env.add_to_history(command)
        
        # Check for pipes
        if '|' in command:
            return self._execute_pipeline(command)
            
        # Check for redirections
        if '>' in command or '<' in command:
            return self._execute_with_redirection(command)
            
        # Try to execute as internal command
        expanded_command = self.env.get_expanded_command(command)
        is_internal, return_code = self._process_internal_command(expanded_command)
        
        if is_internal:
            return return_code
            
        # Execute as external command
        return self._execute_external_command(expanded_command)
    
    def _execute_external_command(self, command: str) -> int:
        """Execute an external command"""
        try:
            # Split command and arguments
            args = shlex.split(command)
            if not args:
                return 0
                
            # Run the command
            self.current_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self.env.get_env()
            )
            
            # Read output
            stdout_data, stderr_data = self.current_process.communicate()
            
            # Send to output callback if available
            if self.output_callback:
                self.output_callback(stdout_data)
                if stderr_data:
                    self.output_callback(stderr_data, is_error=True)
            else:
                # Print output directly
                if stdout_data:
                    print(stdout_data, end='')
                if stderr_data:
                    print(stderr_data, end='', file=sys.stderr)
            
            # Return exit code
            return self.current_process.returncode
            
        except FileNotFoundError:
            print(f"Command not found: {args[0]}", file=sys.stderr)
            return 127
        except PermissionError:
            print(f"Permission denied: {args[0]}", file=sys.stderr)
            return 126
        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            return 1
        finally:
            self.current_process = None
    
    def _execute_pipeline(self, command: str) -> int:
        """Execute a command pipeline"""
        try:
            # Split the pipeline into individual commands
            commands = [cmd.strip() for cmd in command.split('|')]
            if not all(commands):
                print("Invalid pipeline syntax", file=sys.stderr)
                return 1
                
            # Prepare the pipeline
            processes = []
            previous_stdout = None
            
            # Start all processes in the pipeline
            for i, cmd in enumerate(commands):
                # Get stdin for this process
                stdin = previous_stdout
                
                # Get stdout for this process
                stdout = subprocess.PIPE if i < len(commands) - 1 else subprocess.PIPE
                
                # Start the process
                expanded_cmd = self.env.get_expanded_command(cmd)
                args = shlex.split(expanded_cmd)
                
                process = subprocess.Popen(
                    args,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=self.env.get_env()
                )
                
                processes.append(process)
                previous_stdout = process.stdout
                
            # Get output from the last process
            final_process = processes[-1]
            stdout_data, stderr_data = final_process.communicate()
            
            # Collect any stderr output from other processes
            all_stderr = stderr_data
            for i in range(len(processes) - 1):
                _, stderr = processes[i].communicate()
                if stderr:
                    all_stderr += stderr
            
            # Send to output callback if available
            if self.output_callback:
                self.output_callback(stdout_data)
                if all_stderr:
                    self.output_callback(all_stderr, is_error=True)
            else:
                # Print output directly
                if stdout_data:
                    print(stdout_data, end='')
                if all_stderr:
                    print(all_stderr, end='', file=sys.stderr)
            
            # Return exit code from the last process
            return final_process.returncode
            
        except Exception as e:
            print(f"Error executing pipeline: {e}", file=sys.stderr)
            return 1
    
    def _execute_with_redirection(self, command: str) -> int:
        """Execute a command with I/O redirection"""
        try:
            # Parse command and redirections
            input_file = None
            output_file = None
            append_output = False
            
            # Handle input redirection
            if '<' in command:
                parts = command.split('<', 1)
                command = parts[0].strip()
                input_parts = parts[1].strip().split('>', 1)
                input_file = input_parts[0].strip()
                if len(input_parts) > 1:
                    output_part = input_parts[1]
                    if output_part.startswith('>'):
                        append_output = True
                        output_file = output_part[1:].strip()
                    else:
                        output_file = output_part.strip()
            
            # Handle output redirection
            if '>' in command and not output_file:
                parts = command.split('>', 1)
                command = parts[0].strip()
                output_part = parts[1].strip()
                if output_part.startswith('>'):
                    append_output = True
                    output_file = output_part[1:].strip()
                else:
                    output_file = output_part.strip()
            
            # Open the input file if specified
            stdin = None
            if input_file:
                stdin = open(input_file, 'r')
            
            # Open the output file if specified
            stdout = None
            if output_file:
                stdout = open(output_file, 'a' if append_output else 'w')
            
            # Execute the command
            expanded_command = self.env.get_expanded_command(command)
            is_internal, return_code = self._process_internal_command(expanded_command)
            
            if is_internal:
                # Redirect internal command output
                original_stdout = sys.stdout
                original_stderr = sys.stderr
                
                try:
                    if stdout:
                        sys.stdout = stdout
                        sys.stderr = stdout
                    
                    return_code = self.command_handlers[expanded_command.split()[0]](
                        shlex.split(expanded_command)[1:]
                    )
                    
                finally:
                    sys.stdout = original_stdout
                    sys.stderr = original_stderr
                    
                    if stdin:
                        stdin.close()
                    if stdout:
                        stdout.close()
                        
                return return_code
            
            # Execute as external command
            args = shlex.split(expanded_command)
            
            process = subprocess.Popen(
                args,
                stdin=stdin,
                stdout=stdout,
                stderr=subprocess.PIPE,
                text=True,
                env=self.env.get_env()
            )
            
            # Get stderr output
            _, stderr_data = process.communicate()
            
            # Print stderr
            if stderr_data:
                print(stderr_data, end='', file=sys.stderr)
            
            # Close files
            if stdin:
                stdin.close()
            if stdout:
                stdout.close()
                
            return process.returncode
            
        except Exception as e:
            print(f"Error executing command with redirection: {e}", file=sys.stderr)
            return 1
    
    def set_output_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Set callback for command output"""
        self.output_callback = callback
    
    def run_interactive(self) -> None:
        """Run an interactive shell session"""
        self.running = True
        
        # Display welcome message
        print("Triad Terminal Shell")
        print("Type 'exit' to quit")
        
        while self.running:
            try:
                # Update terminal size
                self._update_terminal_size()
                
                # Display prompt
                prompt = self.env.get_formatted_prompt()
                user_input = input(prompt)
                
                # Execute the command
                if user_input.strip():
                    self.execute_command(user_input.strip())
                    
            except KeyboardInterrupt:
                print("\nCtrl+C pressed")
            except EOFError:
                print("\nCtrl+D pressed")
                self.running = False
            except Exception as e:
                print(f"Shell error: {e}")
                traceback.print_exc()
    
    def stop(self) -> None:
        """Stop the shell"""
        self.running = False
        
        # Kill any running process
        if self.current_process:
            with contextlib.suppress(Exception):
                self.current_process.terminate()

class PseudoTerminal:
    """Pseudo-terminal for running interactive programs"""
    
    def __init__(self, env: ShellEnvironment = None):
        self.env = env or ShellEnvironment()
        self.fd = None
        self.pid = None
        self.running = False
        self.output_callback = None
    
    def spawn(self, command: str) -> bool:
        """Spawn a process in a pseudo-terminal"""
        try:
            # Split command
            args = shlex.split(command)
            if not args:
                return False
                
            # Create PTY
            self.pid, self.fd = pty.fork()
            
            if self.pid == 0:
                # Child process
                try:
                    # Set environment
                    for key, value in self.env.get_env().items():
                        os.environ[key] = value
                        
                    # Execute command
                    os.execvp(args[0], args)
                except Exception as e:
                    print(f"Error executing command: {e}", file=sys.stderr)
                    os._exit(1)
            else:
                # Parent process
                self.running = True
                
                # Start reading thread
                self.read_thread = threading.Thread(target=self._read_output)
                self.read_thread.daemon = True
                self.read_thread.start()
                
                return True
                
        except Exception as e:
            logger.error(f"Error spawning PTY: {e}")
            return False
    
    def _read_output(self) -> None:
        """Read output from the PTY"""
        try:
            # Set non-blocking mode
            fcntl.fcntl(self.fd, fcntl.F_SETFL, os.O_NONBLOCK)
            
            while self.running:
                r, w, e = select.select([self.fd], [], [], 0.1)
                
                if self.fd in r:
                    try:
                        data = os.read(self.fd, 1024).decode('utf-8', errors='replace')
                        
                        if data:
                            if self.output_callback:
                                self.output_callback(data)
                            else:
                                sys.stdout.write(data)
                                sys.stdout.flush()
                        else:
                            # EOF
                            self.running = False
                            break
                    except OSError:
                        # Read error
                        self.running = False
                        break
                        
            # Process has terminated
            self._cleanup()
            
        except Exception as e:
            logger.error(f"Error reading from PTY: {e}")
            self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up resources"""
        if self.fd:
            with contextlib.suppress(OSError):
                os.close(self.fd)
            self.fd = None
            
        self.running = False
    
    def write(self, data: str) -> bool:
        """Write data to the PTY"""
        if not self.running or not self.fd:
            return False
            
        try:
            os.write(self.fd, data.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Error writing to PTY: {e}")
            return False
    
    def resize(self, rows: int, cols: int) -> bool:
        """Resize the PTY"""
        if not self.running or not self.fd:
            return False
            
        try:
            import struct
            import termios
            
            fcntl.ioctl(self.fd, 
                       termios.TIOCSWINSZ, 
                       struct.pack('HHHH', rows, cols, 0, 0))
            return True
        except Exception as e:
            logger.error(f"Error resizing PTY: {e}")
            return False
    
    def terminate(self) -> bool:
        """Terminate the process"""
        if not self.running or not self.pid:
            return False
            
        try:
            os.kill(self.pid, signal.SIGTERM)
            self.running = False
            return True
        except Exception as e:
            logger.error(f"Error terminating process: {e}")
            return False
    
    def set_output_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for PTY output"""
        self.output_callback = callback
    
    def is_running(self) -> bool:
        """Check if the process is still running"""
        return self.running

class ShellCommandHelper:
    """Helper for shell command suggestions and documentation"""
    
    def __init__(self):
        # Common commands with descriptions
        self.common_commands = {
            'ls': "List directory contents",
            'cd': "Change directory",
            'pwd': "Print working directory",
            'mkdir': "Create directory",
            'rm': "Remove files or directories",
            'cp': "Copy files or directories",
            'mv': "Move/rename files or directories",
            'cat': "Display file contents",
            'less': "View file contents page by page",
            'grep': "Search for patterns in files",
            'find': "Find files in directory hierarchy",
            'echo': "Display text",
            'touch': "Create empty file or update timestamp",
            'chmod': "Change file permissions",
            'chown': "Change file owner and group",
            'ps': "Show process status",
            'kill': "Terminate processes",
            'top': "Monitor system processes",
            'df': "Display disk space usage",
            'du': "Display file and directory space usage",
            'tar': "Manipulate archive files",
            'gzip': "Compress/decompress files",
            'ssh': "Secure shell remote login",
            'scp': "Secure copy files between hosts",
            'wget': "Download files from the web",
            'curl': "Transfer data from/to a server",
            'ping': "Test network connection",
            'ifconfig': "Configure network interfaces",
            'netstat': "Show network status",
            'history': "Show command history",
            'alias': "Define or display aliases",
            'export': "Set environment variables",
            'env': "Display environment variables",
            'which': "Show full path of commands",
            'man': "Display command manual",
            'git': "Version control system",
            'python': "Python interpreter",
            'npm': "Node package manager",
            'docker': "Container platform"
        }
        
        # Command flags and options
        self.command_options = {
            'ls': ['-l', '-a', '-h', '--color', '-R', '-S', '-t'],
            'cp': ['-r', '-i', '-v', '-f', '-p', '-u'],
            'rm': ['-r', '-f', '-i', '-v'],
            'grep': ['-i', '-r', '-v', '-n', '-A', '-B', '-C', '--color'],
            'find': ['-name', '-type', '-size', '-mtime', '-exec'],
            'tar': ['-c', '-x', '-t', '-f', '-v', '-z', '-j'],
            'git': ['clone', 'pull', 'push', 'commit', 'checkout', 'branch', 'status', 'log'],
            'ssh': ['-p', '-i', '-L', '-R', '-D', '-f', '-N']
        }
        
        # Example usages
        self.command_examples = {
            'ls': ["ls -la", "ls -lh --color", "ls -la | grep ^d"],
            'find': ["find . -name '*.py'", "find /home -type d -name 'data'"],
            'grep': ["grep -i 'error' log.txt", "grep -r 'TODO' ."],
            'tar': ["tar -czvf archive.tar.gz folder/", "tar -xzvf archive.tar.gz"],
            'git': ["git clone https://github.com/user/repo.git", "git commit -m 'message'"]
        }
    
    def get_command_suggestions(self, partial_command: str, max_suggestions: int = 5) -> List[str]:
        """Get command suggestions based on partial input"""
        if not partial_command:
            # Return most common commands
            return list(self.common_commands.keys())[:max_suggestions]
            
        # Get the command and current argument being typed
        parts = shlex.split(partial_command) if partial_command.endswith(' ') else shlex.split(partial_command[:-1] + 'X')
        command = parts[0] if parts else ''
        
        # Suggest commands when typing the command name
        if len(parts) <= 1 and not partial_command.endswith(' '):
            matches = [cmd for cmd in self.common_commands if cmd.startswith(command)]
            return matches[:max_suggestions]
            
        # Suggest options for known commands
        if command in self.command_options and len(parts) > 1:
            current_arg = parts[-1]
            if current_arg.startswith('-'):
                matches = [opt for opt in self.command_options[command] if opt.startswith(current_arg)]
                return matches[:max_suggestions]
        
        # Suggest file paths if argument doesn't start with '-'
        if len(parts) > 1 and not parts[-1].startswith('-'):
            path = parts[-1]
            
            # Handle relative and absolute paths
            if path.startswith('/'):
                base_dir = os.path.dirname(path) or '/'
                prefix = os.path.basename(path)
            else:
                base_dir = os.path.dirname(path) or '.'
                prefix = os.path.basename(path)
                
            try:
                # Get matching files and directories
                matches = []
                if os.path.exists(base_dir) and os.path.isdir(base_dir):
                    for entry in os.listdir(base_dir):
                        if entry.startswith(prefix):
                            full_path = os.path.join(base_dir, entry)
                            if os.path.isdir(full_path):
                                entry += '/'
                            matches.append(entry)
                            
                return matches[:max_suggestions]
            except Exception:
                pass
        
        return []
    
    def get_command_help(self, command: str) -> Dict[str, Any]:
        """Get help information for a command"""
        result = {
            'command': command,
            'description': self.common_commands.get(command, "No description available"),
            'options': self.command_options.get(command, []),
            'examples': self.command_examples.get(command, [])
        }
        
        return result

def main():
    """Run interactive shell"""
    print("Triad Terminal Shell Interface")
    print("=============================")
    
    # Create shell environment and interactive shell
    env = ShellEnvironment()
    shell = InteractiveShell(env)
    
    # Run interactive shell
    shell.run_interactive()
    
    # Save history on exit
    env.save_history()
    
    print("Shell session ended")

if __name__ == "__main__":
    main()