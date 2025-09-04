"""
Storm Integration Service

Provides enhanced multi-agent coordination using Storm-like patterns for
distributed agent communication and task orchestration.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field

import websockets
from websockets.server import WebSocketServerProtocol


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(Enum):
    """Storm message types."""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    TASK_UPDATE = "task_update"
    AGENT_REGISTRATION = "agent_registration"
    AGENT_HEARTBEAT = "agent_heartbeat"
    COORDINATION = "coordination"
    BROADCAST = "broadcast"


@dataclass
class StormMessage:
    """Storm protocol message."""
    id: str
    type: MessageType
    sender: str
    recipient: str = None  # None for broadcast
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = None  # For request-response correlation


@dataclass
class TaskDefinition:
    """Distributed task definition."""
    id: str
    type: str
    description: str
    payload: Dict[str, Any]
    required_capabilities: List[str] = field(default_factory=list)
    priority: int = 1
    timeout_seconds: int = 300
    created_at: float = field(default_factory=time.time)
    assigned_agent: str = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None


@dataclass  
class AgentCapabilities:
    """Agent capability description."""
    agent_id: str
    capabilities: List[str]
    load_factor: float = 0.0  # 0.0 = idle, 1.0 = fully loaded
    last_heartbeat: float = field(default_factory=time.time)


class StormIntegrationService:
    """Storm-like integration service for multi-agent coordination."""

    def __init__(
        self, 
        websocket_port: int = 8765,
        redis_url: str = None,
        coordination_timeout: float = 30.0
    ):
        self.websocket_port = websocket_port
        self.redis_url = redis_url
        self.coordination_timeout = coordination_timeout
        
        # In-memory state (in production, this would use Redis)
        self.connected_agents: Dict[str, WebSocketServerProtocol] = {}
        self.agent_capabilities: Dict[str, AgentCapabilities] = {}
        self.active_tasks: Dict[str, TaskDefinition] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        
        # WebSocket server
        self.websocket_server = None
        self.running = False
        
        # Setup default message handlers
        self._setup_default_handlers()

    async def start(self) -> None:
        """Start the Storm integration service."""
        if self.running:
            return
            
        # Start WebSocket server for agent communication
        self.websocket_server = await websockets.serve(
            self._handle_websocket_connection,
            "localhost",
            self.websocket_port
        )
        
        self.running = True
        
        # Start background tasks
        asyncio.create_task(self._heartbeat_monitor())
        asyncio.create_task(self._task_scheduler())
        
        print(f"Storm Integration Service started on ws://localhost:{self.websocket_port}")

    async def stop(self) -> None:
        """Stop the Storm integration service."""
        if not self.running:
            return
            
        self.running = False
        
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
            
        # Disconnect all agents
        for agent_id, websocket in list(self.connected_agents.items()):
            await websocket.close()
            
        self.connected_agents.clear()
        self.agent_capabilities.clear()

    async def submit_task(
        self,
        task_type: str,
        description: str,
        payload: Dict[str, Any],
        required_capabilities: List[str] = None,
        priority: int = 1,
        timeout_seconds: int = 300
    ) -> str:
        """Submit a new task for distributed execution."""
        task_id = str(uuid.uuid4())
        
        task = TaskDefinition(
            id=task_id,
            type=task_type,
            description=description,
            payload=payload,
            required_capabilities=required_capabilities or [],
            priority=priority,
            timeout_seconds=timeout_seconds
        )
        
        self.active_tasks[task_id] = task
        
        # Try to assign task immediately
        await self._try_assign_task(task)
        
        return task_id

    async def get_task_status(self, task_id: str) -> Optional[TaskDefinition]:
        """Get the current status of a task."""
        return self.active_tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task."""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
            
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
            
        task.status = TaskStatus.CANCELLED
        
        # Notify assigned agent if any
        if task.assigned_agent:
            await self._send_message_to_agent(
                task.assigned_agent,
                StormMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.TASK_UPDATE,
                    sender="storm_service",
                    recipient=task.assigned_agent,
                    payload={
                        "task_id": task_id,
                        "action": "cancel"
                    }
                )
            )
            
        return True

    async def broadcast_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        sender: str = "storm_service"
    ) -> None:
        """Broadcast a message to all connected agents."""
        message = StormMessage(
            id=str(uuid.uuid4()),
            type=message_type,
            sender=sender,
            payload=payload
        )
        
        for agent_id in list(self.connected_agents.keys()):
            await self._send_message_to_agent(agent_id, message)

    async def get_connected_agents(self) -> List[Dict[str, Any]]:
        """Get list of currently connected agents."""
        agents = []
        current_time = time.time()
        
        for agent_id, capabilities in self.agent_capabilities.items():
            agents.append({
                "agent_id": agent_id,
                "capabilities": capabilities.capabilities,
                "load_factor": capabilities.load_factor,
                "last_heartbeat": capabilities.last_heartbeat,
                "connected": agent_id in self.connected_agents,
                "heartbeat_age": current_time - capabilities.last_heartbeat
            })
            
        return agents

    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        active_tasks_by_status = {}
        for task in self.active_tasks.values():
            status = task.status.value
            active_tasks_by_status[status] = active_tasks_by_status.get(status, 0) + 1
            
        return {
            "connected_agents": len(self.connected_agents),
            "registered_capabilities": len(self.agent_capabilities),
            "active_tasks": len(self.active_tasks),
            "tasks_by_status": active_tasks_by_status,
            "running": self.running,
            "websocket_port": self.websocket_port
        }

    def register_message_handler(
        self,
        message_type: MessageType,
        handler: Callable[[StormMessage], None]
    ) -> None:
        """Register a custom message handler."""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)

    async def _handle_websocket_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle new WebSocket connection from an agent."""
        agent_id = None
        
        try:
            async for raw_message in websocket:
                try:
                    message_data = json.loads(raw_message)
                    message = StormMessage(**message_data)
                    
                    # Handle agent registration
                    if message.type == MessageType.AGENT_REGISTRATION:
                        agent_id = message.sender
                        self.connected_agents[agent_id] = websocket
                        
                        capabilities = AgentCapabilities(
                            agent_id=agent_id,
                            capabilities=message.payload.get("capabilities", [])
                        )
                        self.agent_capabilities[agent_id] = capabilities
                        
                        # Send registration confirmation
                        confirmation = StormMessage(
                            id=str(uuid.uuid4()),
                            type=MessageType.AGENT_REGISTRATION,
                            sender="storm_service",
                            recipient=agent_id,
                            payload={"status": "registered", "agent_id": agent_id}
                        )
                        await websocket.send(json.dumps(confirmation.__dict__))
                        
                        print(f"Agent registered: {agent_id} with capabilities: {capabilities.capabilities}")
                        continue
                    
                    # Route message to handlers
                    await self._handle_message(message)
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "error": "Invalid JSON message"
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        "error": f"Message processing error: {str(e)}"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Clean up on disconnect
            if agent_id:
                self.connected_agents.pop(agent_id, None)
                self.agent_capabilities.pop(agent_id, None)
                print(f"Agent disconnected: {agent_id}")

    async def _handle_message(self, message: StormMessage) -> None:
        """Handle incoming message from agents."""
        # Update heartbeat for sender
        if message.sender in self.agent_capabilities:
            self.agent_capabilities[message.sender].last_heartbeat = time.time()
        
        # Route to registered handlers
        handlers = self.message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                print(f"Error in message handler: {e}")

    async def _send_message_to_agent(self, agent_id: str, message: StormMessage) -> bool:
        """Send a message to a specific agent."""
        websocket = self.connected_agents.get(agent_id)
        if not websocket:
            return False
            
        try:
            await websocket.send(json.dumps(message.__dict__))
            return True
        except Exception as e:
            print(f"Failed to send message to agent {agent_id}: {e}")
            # Clean up disconnected agent
            self.connected_agents.pop(agent_id, None)
            return False

    async def _try_assign_task(self, task: TaskDefinition) -> bool:
        """Try to assign a task to a capable agent."""
        if task.status != TaskStatus.PENDING:
            return False
        
        # Find capable agents
        capable_agents = []
        for agent_id, capabilities in self.agent_capabilities.items():
            if agent_id not in self.connected_agents:
                continue
                
            # Check if agent has required capabilities
            if all(cap in capabilities.capabilities for cap in task.required_capabilities):
                capable_agents.append((agent_id, capabilities.load_factor))
        
        if not capable_agents:
            return False
            
        # Sort by load factor (prefer less loaded agents)
        capable_agents.sort(key=lambda x: x[1])
        chosen_agent = capable_agents[0][0]
        
        # Assign task
        task.assigned_agent = chosen_agent
        task.status = TaskStatus.RUNNING
        
        # Send task to agent
        task_message = StormMessage(
            id=str(uuid.uuid4()),
            type=MessageType.TASK_REQUEST,
            sender="storm_service",
            recipient=chosen_agent,
            payload={
                "task": {
                    "id": task.id,
                    "type": task.type,
                    "description": task.description,
                    "payload": task.payload,
                    "timeout_seconds": task.timeout_seconds
                }
            }
        )
        
        success = await self._send_message_to_agent(chosen_agent, task_message)
        if not success:
            # Reset task if sending failed
            task.assigned_agent = None
            task.status = TaskStatus.PENDING
            
        return success

    async def _heartbeat_monitor(self) -> None:
        """Monitor agent heartbeats and clean up stale connections."""
        while self.running:
            try:
                current_time = time.time()
                stale_agents = []
                
                for agent_id, capabilities in self.agent_capabilities.items():
                    if current_time - capabilities.last_heartbeat > 60:  # 60 second timeout
                        stale_agents.append(agent_id)
                
                # Clean up stale agents
                for agent_id in stale_agents:
                    self.connected_agents.pop(agent_id, None)
                    self.agent_capabilities.pop(agent_id, None)
                    print(f"Removed stale agent: {agent_id}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(30)

    async def _task_scheduler(self) -> None:
        """Background task scheduler for unassigned tasks."""
        while self.running:
            try:
                # Find pending tasks and try to assign them
                pending_tasks = [
                    task for task in self.active_tasks.values()
                    if task.status == TaskStatus.PENDING
                ]
                
                # Sort by priority and creation time
                pending_tasks.sort(key=lambda t: (-t.priority, t.created_at))
                
                for task in pending_tasks:
                    # Check timeout
                    if time.time() - task.created_at > task.timeout_seconds:
                        task.status = TaskStatus.FAILED
                        task.error = "Task timeout"
                        continue
                        
                    # Try to assign
                    await self._try_assign_task(task)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Error in task scheduler: {e}")
                await asyncio.sleep(5)

    def _setup_default_handlers(self) -> None:
        """Setup default message handlers."""
        
        async def handle_task_response(message: StormMessage):
            """Handle task completion responses."""
            task_id = message.payload.get("task_id")
            task = self.active_tasks.get(task_id)
            
            if not task:
                return
                
            if message.payload.get("success", True):
                task.status = TaskStatus.COMPLETED
                task.result = message.payload.get("result")
            else:
                task.status = TaskStatus.FAILED
                task.error = message.payload.get("error", "Unknown error")
        
        async def handle_heartbeat(message: StormMessage):
            """Handle agent heartbeat messages."""
            agent_id = message.sender
            if agent_id in self.agent_capabilities:
                capabilities = self.agent_capabilities[agent_id]
                capabilities.last_heartbeat = time.time()
                capabilities.load_factor = message.payload.get("load_factor", 0.0)
        
        self.register_message_handler(MessageType.TASK_RESPONSE, handle_task_response)
        self.register_message_handler(MessageType.AGENT_HEARTBEAT, handle_heartbeat)

    async def create_coordination_session(
        self,
        session_id: str,
        participating_agents: List[str],
        coordination_goal: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a coordination session for multi-agent collaboration."""
        coordination_message = StormMessage(
            id=str(uuid.uuid4()),
            type=MessageType.COORDINATION,
            sender="storm_service",
            payload={
                "action": "create_session",
                "session_id": session_id,
                "participating_agents": participating_agents,
                "coordination_goal": coordination_goal,
                "context": context or {}
            }
        )
        
        # Notify all participating agents
        for agent_id in participating_agents:
            if agent_id in self.connected_agents:
                await self._send_message_to_agent(agent_id, coordination_message)
        
        return {
            "session_id": session_id,
            "status": "created",
            "participating_agents": participating_agents,
            "coordination_goal": coordination_goal
        }