#!/usr/bin/env python3

"""
Triad Terminal Enhanced SSH Tunneling
Provides advanced SSH tunnel management capabilities
"""

import os
import sys
import json
import yaml
import time
import signal
import socket
import logging
import asyncio
import threading
import subprocess
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("triad.tunnel")

@dataclass
class TunnelConfig:
    """Configuration for an SSH tunnel"""
    name: str
    local_host: str
    local_port: int
    remote_host: str
    remote_port: int
    ssh_host: str
    ssh_port: int = 22
    ssh_user: str = None
    ssh_key: str = None
    reverse: bool = False
    auto_restart: bool = True
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TunnelConfig':
        return TunnelConfig(
            name=data.get('name', 'unnamed'),
            local_host=data.get('local_host', 'localhost'),
            local_port=data.get('local_port', 8000),
            remote_host=data.get('remote_host', 'localhost'),
            remote_port=data.get('remote_port', 8000),
            ssh_host=data.get('ssh_host', ''),
            ssh_port=data.get('ssh_port', 22),
            ssh_user=data.get('ssh_user'),
            ssh_key=data.get('ssh_key'),
            reverse=data.get('reverse', False),
            auto_restart=data.get('auto_restart', True)
        )

class TunnelManager:
    """Manages SSH tunnel configurations"""
    
    def __init__(self, config_dir: str = "~/.triad/tunnels"):
        self.config_dir = os.path.expanduser(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        self.tunnels_file = os.path.join(self.config_dir, "tunnels.yml")
        self._tunnels = None
    
    def get_tunnels(self) -> Dict[str, TunnelConfig]:
        """Get all configured tunnels"""
        if self._tunnels is not None:
            return self._tunnels
            
        self._tunnels = {}
        
        # Load tunnels from file
        if os.path.exists(self.tunnels_file):
            try:
                with open(self.tunnels_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
                    
                for name, tunnel_data in data.items():
                    tunnel_data['name'] = name  # Ensure name is in the data
                    self._tunnels[name] = TunnelConfig.from_dict(tunnel_data)
            except Exception as e:
                logger.error(f"Error loading SSH tunnels: {e}")
                
        return self._tunnels
    
    def save_tunnels(self) -> bool:
        """Save tunnel configurations to file"""
        if self._tunnels is None:
            return True  # Nothing to save
            
        try:
            data = {}
            for name, tunnel in self._tunnels.items():
                data[name] = {
                    'local_host': tunnel.local_host,
                    'local_port': tunnel.local_port,
                    'remote_host': tunnel.remote_host,
                    'remote_port': tunnel.remote_port,
                    'ssh_host': tunnel.ssh_host,
                    'ssh_port': tunnel.ssh_port,
                    'ssh_user': tunnel.ssh_user,
                    'ssh_key': tunnel.ssh_key,
                    'reverse': tunnel.reverse,
                    'auto_restart': tunnel.auto_restart
                }
                
            with open(self.tunnels_file, 'w') as f:
                yaml.dump(data, f)
                
            return True
        except Exception as e:
            logger.error(f"Error saving SSH tunnels: {e}")
            return False
    
    def add_tunnel(self, tunnel: TunnelConfig) -> bool:
        """Add a new SSH tunnel configuration"""
        tunnels = self.get_tunnels()
        tunnels[tunnel.name] = tunnel
        self._tunnels = tunnels
        return self.save_tunnels()
    
    def remove_tunnel(self, name: str) -> bool:
        """Remove an SSH tunnel configuration"""
        tunnels = self.get_tunnels()
        if name in tunnels:
            del tunnels[name]
            self._tunnels = tunnels
            return self.save_tunnels()
        return False
    
    def update_tunnel(self, name: str, updated_tunnel: TunnelConfig) -> bool:
        """Update an existing SSH tunnel configuration"""
        tunnels = self.get_tunnels()
        if name in tunnels:
            # Maintain the original name
            updated_tunnel.name = name
            tunnels[name] = updated_tunnel
            self._tunnels = tunnels
            return self.save_tunnels()
        return False

class TunnelProcess:
    """Manages a single SSH tunnel process"""
    
    def __init__(self, config: TunnelConfig):
        self.config = config
        self.process = None
        self.running = False
        self.start_time = None
        self.auto_restart_thread = None
        self.stop_event = threading.Event()
    
    def start(self) -> bool:
        """Start the SSH tunnel"""
        if self.running:
            return True
            
        try:
            logger.info(f"Starting SSH tunnel: {self.config.name}")
            
            # Build the SSH command
            cmd = ['ssh']
            
            # Add SSH port if not the default
            if self.config.ssh_port != 22:
                cmd.extend(['-p', str(self.config.ssh_port)])
            
            # Add SSH key if specified
            if self.config.ssh_key:
                cmd.extend(['-i', os.path.expanduser(self.config.ssh_key)])
            
            # Add options for tunneling
            cmd.extend([
                '-N',  # Don't execute remote command
                '-T',  # Disable pseudo-terminal allocation
                '-o', 'ExitOnForwardFailure=yes',  # Exit if forwarding fails
                '-o', 'ServerAliveInterval=60',    # Keep-alive packets every 60 seconds
                '-o', 'ServerAliveCountMax=3'      # Allow 3 missed keep-alives before disconnect
            ])
            
            # Add tunnel type (regular or reverse)
            if self.config.reverse:
                # Reverse tunnel: remote -> local
                cmd.extend([
                    '-R',
                    f"{self.config.remote_port}:{self.config.local_host}:{self.config.local_port}"
                ])
            else:
                # Regular tunnel: local -> remote
                cmd.extend([
                    '-L',
                    f"{self.config.local_port}:{self.config.remote_host}:{self.config.remote_port}"
                ])
            
            # SSH destination
            ssh_destination = self.config.ssh_host
            if self.config.ssh_user:
                ssh_destination = f"{self.config.ssh_user}@{ssh_destination}"
            
            cmd.append(ssh_destination)
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.running = True
            self.start_time = datetime.now()
            
            # Start auto-restart thread if enabled
            if self.config.auto_restart:
                self.stop_event.clear()
                self.auto_restart_thread = threading.Thread(
                    target=self._monitor_and_restart,
                    daemon=True
                )
                self.auto_restart_thread.start()
            
            logger.info(f"SSH tunnel {self.config.name} started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting SSH tunnel {self.config.name}: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the SSH tunnel"""
        if not self.running:
            return True
            
        try:
            logger.info(f"Stopping SSH tunnel: {self.config.name}")
            
            # Signal the auto-restart thread to stop
            if self.auto_restart_thread:
                self.stop_event.set()
            
            # Terminate the process
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                
                self.process = None
            
            self.running = False
            logger.info(f"SSH tunnel {self.config.name} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping SSH tunnel {self.config.name}: {e}")
            return False
    
    def status(self) -> Dict[str, Any]:
        """Get status of the tunnel"""
        result = {
            'name': self.config.name,
            'running': self.running,
            'uptime': None,
            'config': {
                'local_host': self.config.local_host,
                'local_port': self.config.local_port,
                'remote_host': self.config.remote_host,
                'remote_port': self.config.remote_port,
                'ssh_host': self.config.ssh_host,
                'reverse': self.config.reverse,
                'auto_restart': self.config.auto_restart
            }
        }
        
        # Calculate uptime if running
        if self.running and self.start_time:
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            hours, remainder = divmod(int(uptime_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            result['uptime'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Test if the tunnel is actually working
            result['status'] = self._test_tunnel()
        
        return result
    
    def _test_tunnel(self) -> str:
        """Test if the tunnel is actually working"""
        try:
            if not self.config.reverse:
                # For regular tunnels, check if we can connect locally
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((self.config.local_host, self.config.local_port))
                return "active"
            else:
                # For reverse tunnels, we can only check if the process is running
                if self.process and self.process.poll() is None:
                    return "active"
                else:
                    return "inactive"
        except:
            return "inactive"
    
    def _monitor_and_restart(self) -> None:
        """Monitor the tunnel and restart if it fails"""
        while not self.stop_event.is_set():
            if self.process and self.process.poll() is not None:
                # Process has terminated
                logger.warning(f"SSH tunnel {self.config.name} terminated unexpectedly, restarting")
                
                # Reset state
                self.running = False
                self.process = None
                
                # Restart the tunnel
                self.start()
            
            # Also test the tunnel connection
            if self.running and self._test_tunnel() == "inactive":
                logger.warning(f"SSH tunnel {self.config.name} is not working, restarting")
                
                # Stop and restart
                self.stop()
                time.sleep(1)  # Brief delay before restart
                self.start()
            
            # Check every 10 seconds
            time.sleep(10)

class TunnelService:
    """Main service for managing multiple SSH tunnels"""
    
    def __init__(self):
        self.manager = TunnelManager()
        self.active_tunnels: Dict[str, TunnelProcess] = {}
    
    def start_tunnel(self, name: str) -> Dict[str, Any]:
        """Start a tunnel by name"""
        tunnels = self.manager.get_tunnels()
        
        if name not in tunnels:
            return {
                'success': False,
                'error': f"Tunnel '{name}' not found"
            }
            
        # Create and start tunnel process
        if name in self.active_tunnels:
            tunnel_process = self.active_tunnels[name]
            if tunnel_process.running:
                return {
                    'success': True,
                    'message': f"Tunnel '{name}' is already running"
                }
        else:
            tunnel_process = TunnelProcess(tunnels[name])
            self.active_tunnels[name] = tunnel_process
        
        # Start the tunnel
        if tunnel_process.start():
            return {
                'success': True,
                'message': f"Tunnel '{name}' started successfully"
            }
        else:
            return {
                'success': False,
                'error': f"Failed to start tunnel '{name}'"
            }
    
    def stop_tunnel(self, name: str) -> Dict[str, Any]:
        """Stop a tunnel by name"""
        if name not in self.active_tunnels:
            return {
                'success': False,
                'error': f"Tunnel '{name}' is not running"
            }
            
        tunnel_process = self.active_tunnels[name]
        
        if tunnel_process.stop():
            del self.active_tunnels[name]
            return {
                'success': True,
                'message': f"Tunnel '{name}' stopped successfully"
            }
        else:
            return {
                'success': False,
                'error': f"Failed to stop tunnel '{name}'"
            }
    
    def get_tunnel_status(self, name: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get status of a tunnel or all tunnels"""
        if name:
            if name in self.active_tunnels:
                return self.active_tunnels[name].status()
            else:
                tunnels = self.manager.get_tunnels()
                if name in tunnels:
                    # Tunnel exists but not running
                    return {
                        'name': name,
                        'running': False,
                        'config': {
                            'local_host': tunnels[name].local_host,
                            'local_port': tunnels[name].local_port,
                            'remote_host': tunnels[name].remote_host,
                            'remote_port': tunnels[name].remote_port,
                            'ssh_host': tunnels[name].ssh_host,
                            'reverse': tunnels[name].reverse,
                            'auto_restart': tunnels[name].auto_restart
                        }
                    }
                else:
                    return {'name': name, 'error': 'Tunnel not found'}
        else:
            # Get status of all tunnels
            result = []
            
            # First get all configured tunnels
            tunnels = self.manager.get_tunnels()
            
            for name, config in tunnels.items():
                if name in self.active_tunnels:
                    # Running tunnel
                    result.append(self.active_tunnels[name].status())
                else:
                    # Configured but not running
                    result.append({
                        'name': name,
                        'running': False,
                        'config': {
                            'local_host': config.local_host,
                            'local_port': config.local_port,
                            'remote_host': config.remote_host,
                            'remote_port': config.remote_port,
                            'ssh_host': config.ssh_host,
                            'reverse': config.reverse,
                            'auto_restart': config.auto_restart
                        }
                    })
                    
            return result

class MultiplexerTunnel:
    """Manages a multiplexed SSH connection for faster tunnels"""
    
    def __init__(self, ssh_host: str, ssh_port: int = 22, 
                ssh_user: Optional[str] = None, ssh_key: Optional[str] = None):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_key = ssh_key
        self.control_path = None
        self.control_process = None
        self.tunnels = []
    
    def start_master_connection(self) -> bool:
        """Start the master SSH connection"""
        try:
            # Create a unique control path
            import tempfile
            import uuid
            control_dir = os.path.join(tempfile.gettempdir(), "triad_ssh")
            os.makedirs(control_dir, exist_ok=True)
            
            self.control_path = os.path.join(control_dir, f"master_{uuid.uuid4().hex}")
            
            # Build the SSH command for master connection
            cmd = ['ssh']
            
            # Add SSH port if not the default
            if self.ssh_port != 22:
                cmd.extend(['-p', str(self.ssh_port)])
            
            # Add SSH key if specified
            if self.ssh_key:
                cmd.extend(['-i', os.path.expanduser(self.ssh_key)])
            
            # Add control options
            cmd.extend([
                '-N',  # Don't execute remote command
                '-M',  # Master mode for connection sharing
                '-o', 'ControlPersist=yes',
                '-o', 'ControlMaster=yes',
                '-o', f"ControlPath={self.control_path}",
                '-o', 'ServerAliveInterval=60',
                '-o', 'ServerAliveCountMax=3'
            ])
            
            # SSH destination
            ssh_destination = self.ssh_host
            if self.ssh_user:
                ssh_destination = f"{self.ssh_user}@{ssh_destination}"
            
            cmd.append(ssh_destination)
            
            # Start the master process
            self.control_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to establish
            time.sleep(1)
            
            if self.control_process.poll() is not None:
                logger.error("Failed to start master SSH connection")
                return False
                
            logger.info(f"Master SSH connection established to {ssh_destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting master SSH connection: {e}")
            return False
    
    def add_tunnel(self, local_port: int, remote_host: str, remote_port: int, reverse: bool = False) -> bool:
        """Add a tunnel to the multiplexed connection"""
        if not self.control_path or not self.control_process or self.control_process.poll() is not None:
            logger.error("Master SSH connection is not active")
            return False
            
        try:
            # Build the SSH command for the tunnel
            cmd = ['ssh']
            
            # Add control path
            cmd.extend([
                '-o', f"ControlPath={self.control_path}",
                '-N',  # Don't execute remote command
                '-O', 'forward'  # Control command to add a forward
            ])
            
            # Add tunnel type
            if reverse:
                cmd.append(f"R:{remote_port}:{remote_host}:{local_port}")
            else:
                cmd.append(f"L:{local_port}:{remote_host}:{remote_port}")
            
            # SSH destination (same as master)
            ssh_destination = self.ssh_host
            if self.ssh_user:
                ssh_destination = f"{self.ssh_user}@{ssh_destination}"
            
            cmd.append(ssh_destination)
            
            # Execute the command
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if process.returncode == 0:
                # Track the tunnel
                self.tunnels.append({
                    'local_port': local_port,
                    'remote_host': remote_host,
                    'remote_port': remote_port,
                    'reverse': reverse
                })
                
                logger.info(f"Added {'reverse' if reverse else 'forward'} tunnel: {local_port} -> {remote_host}:{remote_port}")
                return True
            else:
                logger.error(f"Failed to add tunnel: {process.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding tunnel: {e}")
            return False
    
    def close(self) -> bool:
        """Close the multiplexed connection and all tunnels"""
        try:
            # Send exit command to control socket
            if self.control_path:
                cmd = [
                    'ssh',
                    '-O', 'exit',
                    '-o', f"ControlPath={self.control_path}"
                ]
                
                ssh_destination = self.ssh_host
                if self.ssh_user:
                    ssh_destination = f"{self.ssh_user}@{ssh_destination}"
                
                cmd.append(ssh_destination)
                
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Terminate the control process if still running
            if self.control_process and self.control_process.poll() is None:
                self.control_process.terminate()
                try:
                    self.control_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.control_process.kill()
            
            # Clean up control socket file
            if self.control_path and os.path.exists(self.control_path):
                os.remove(self.control_path)
                
            logger.info("Closed SSH multiplexed connection")
            return True
            
        except Exception as e:
            logger.error(f"Error closing SSH multiplexed connection: {e}")
            return False

class JumpHostTunnel:
    """Manage SSH tunnels through jump hosts (bastion servers)"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration
        
        config = {
            'local_port': 8000,
            'target_host': 'internal-server',
            'target_port': 80,
            'jump_hosts': [
                {'host': 'bastion1.example.com', 'user': 'user1', 'key': '~/.ssh/key1'},
                {'host': 'bastion2.example.com', 'user': 'user2', 'key': '~/.ssh/key2'}
            ]
        }
        """
        self.config = config
        self.process = None
    
    def start(self) -> bool:
        """Start the tunneled connection through jump hosts"""
        try:
            local_port = self.config['local_port']
            target_host = self.config['target_host']
            target_port = self.config['target_port']
            jump_hosts = self.config['jump_hosts']
            
            if not jump_hosts:
                logger.error("No jump hosts specified")
                return False
            
            # Build the SSH command
            cmd = ['ssh', '-N']
            
            # Add local forwarding
            cmd.extend(['-L', f"localhost:{local_port}:{target_host}:{target_port}"])
            
            # Add jump host chain
            jump_str = []
            for host in jump_hosts:
                jump_part = host['host']
                if 'user' in host:
                    jump_part = f"{host['user']}@{jump_part}"
                jump_str.append(jump_part)
            
            cmd.extend(['-J', ','.join(jump_str)])
            
            # Add key for the final jump if specified
            last_jump = jump_hosts[-1]
            if 'key' in last_jump:
                cmd.extend(['-i', os.path.expanduser(last_jump['key'])])
            
            # Add connection options
            cmd.extend([
                '-o', 'ExitOnForwardFailure=yes',
                '-o', 'ServerAliveInterval=60',
                '-o', 'ServerAliveCountMax=3'
            ])
            
            # Final destination is the last jump host (we're tunneling through it)
            final_host = last_jump['host']
            if 'user' in last_jump:
                final_host = f"{last_jump['user']}@{final_host}"
            
            cmd.append(final_host)
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to establish
            time.sleep(1)
            
            if self.process.poll() is not None:
                stderr = self.process.stderr.read().decode() if self.process.stderr else ""
                logger.error(f"Failed to establish jump host tunnel: {stderr}")
                return False
                
            logger.info(f"Jump host tunnel established: localhost:{local_port} -> {target_host}:{target_port}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating jump host tunnel: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the tunnel"""
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    
            logger.info("Jump host tunnel stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping jump host tunnel: {e}")
            return False