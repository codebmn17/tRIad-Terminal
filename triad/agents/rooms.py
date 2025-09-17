from __future__ import annotations

from .core import Router

# Re-export Router as the main rooms interface
__all__ = ["Router"]
import asyncio

from .core import Agent, Message


class Room:
    def __init__(self, name: str):
        self.name = name
        self.subscribers: set[Agent] = set()
        self.history: list[Message] = []


class Router:
    def __init__(self):
        self.rooms: dict[str, Room] = {}
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
