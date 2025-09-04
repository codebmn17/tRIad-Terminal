"""
Room management for multi-agent conversations.

Provides rooms (channels) where agents can communicate and coordinate.
"""

from __future__ import annotations

from .core import Router
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional

from .core import Agent, Message


# Re-export Router as the main rooms interface  
__all__ = ["Router", "RoomManager"]


class Room:
    def __init__(self, name: str):
        self.name = name
        self.subscribers: Set[Agent] = set()
        self.history: List[Message] = []
        self.config: Dict[str, Any] = {}
        
    async def add_agent(self, agent: Agent) -> None:
        """Add an agent to the room."""
        self.subscribers.add(agent)
    
    async def remove_agent(self, agent: Agent) -> None:
        """Remove an agent from the room."""
        self.subscribers.discard(agent)
    
    @property
    def agents(self) -> List[Agent]:
        """Get list of agents in the room."""
        return list(self.subscribers)


class Router:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self._lock = asyncio.Lock()

    def _get_room(self, name: str) -> Room:
        if name not in self.rooms:
            self.rooms[name] = Room(name)
        return self.rooms[name]

    async def join(self, room_name: str, agent: Agent) -> None:
        async with self._lock:
            room = self._get_room(room_name)
            room.subscribers.add(agent)

    async def leave(self, room_name: str, agent: Agent) -> None:
        async with self._lock:
            room = self._get_room(room_name)
            room.subscribers.discard(agent)

    async def post(self, message: Message) -> None:
        room = self._get_room(message.room)
        room.history.append(message)
        # fan out without awaiting each delivery serially
        await asyncio.gather(*(a.deliver(message) for a in list(room.subscribers)))


class RoomManager:
    """Enhanced room manager with configuration support."""
    
    def __init__(self):
        self.router = Router()
    
    async def create_room(self, name: str, config: Dict[str, Any] = None) -> Room:
        """Create a new room with configuration."""
        room = self.router._get_room(name)
        room.config = config or {}
        return room
    
    def get_room(self, name: str) -> Optional[Room]:
        """Get a room by name."""
        return self.router.rooms.get(name)
    
    def remove_room(self, name: str) -> bool:
        """Remove a room."""
        if name in self.router.rooms:
            del self.router.rooms[name]
            return True
        return False
    
    def list_rooms(self) -> List[str]:
        """Get list of room names."""
        return list(self.router.rooms.keys())
