from __future__ import annotations

import asyncio
import datetime as _dt
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Protocol


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


@dataclass
class Role:
    name: str
    icon: str = "•"
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    name: str
    icon: str = ""  # ASCII or Nerd Font glyph


@dataclass
class Message:
    room: str
    sender: str
    content: str
    role: str = "user"
    ts: _dt.datetime = field(default_factory=lambda: _dt.datetime.now(dt.UTC))
    meta: dict[str, Any] | None = None

    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


class MessageHandler(Protocol):
    async def handle(self, msg: Message) -> None:
        ...


class Agent:
    """Base class for all agents in the triad system."""

    def __init__(self, name: str, *, role: Role | None = None):
        self.name = name
        self.role = role or Role(name="agent")
        self._router: Router | None = None
        self._rooms: set[str] = set()
        self._running = False

    def attach(self, router: Router) -> None:
        """Attach this agent to a router."""
        self._router = router

    async def join(self, room: str) -> None:
        """Join a room."""
        if self._router:
            await self._router.subscribe(room, self)
            self._rooms.add(room)

    async def leave(self, room: str) -> None:
        """Leave a room."""
        if self._router:
            await self._router.unsubscribe(room, self)
            self._rooms.discard(room)

    async def start(self) -> None:
        """Start the agent."""
        self._running = True

    async def stop(self) -> None:
        """Stop the agent."""
        self._running = False
        for room in list(self._rooms):
            await self.leave(room)

    async def send(self, room: str, content: str, *, role: str = "assistant", meta: dict[str, Any] | None = None) -> None:
        """Send a message to a room."""
        if self._router:
            msg = Message(
                room=room,
                sender=self.name,
                content=content,
                role=role,
                meta=meta or {}
            )
            await self._router.post(msg)

    async def handle(self, msg: Message) -> None:
        """Handle an incoming message. Override in subclasses."""
        pass


class Router:
    """Routes messages between agents in rooms."""

    def __init__(self):
        self.rooms: dict[str, list[Agent]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, room: str, agent: Agent) -> None:
        """Subscribe an agent to a room."""
        async with self._lock:
            if agent not in self.rooms[room]:
                self.rooms[room].append(agent)

    async def unsubscribe(self, room: str, agent: Agent) -> None:
        """Unsubscribe an agent from a room."""
        async with self._lock:
            if agent in self.rooms[room]:
                self.rooms[room].remove(agent)
                if not self.rooms[room]:
                    del self.rooms[room]

    async def post(self, msg: Message) -> None:
        """Post a message to all agents in a room."""
        agents = list(self.rooms.get(msg.room, []))

        # Send to all agents concurrently
        await asyncio.gather(
            *[agent.handle(msg) for agent in agents],
            return_exceptions=True
        )
    ts: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.UTC))
    meta: dict[str, Any] = field(default_factory=dict)

    def brief(self) -> str:
        text = self.content.strip().replace("\n", " ")
        return (text[:120] + "…") if len(text) > 120 else text


class Agent:
    """Base class for simple asyncio agents."""

    def __init__(self, name: str, role: Role | None = None):
        self.name = name
        self.role = role or Role(name="agent", icon="∴")
        self._router: Router | None = None
        self._inbox: asyncio.Queue[Message] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    # Wiring
    def attach(self, router: Router) -> None:
        self._router = router

    async def join(self, room: str) -> None:
        assert self._router, "Agent must be attached before joining rooms"
        await self._router.join(room, self)

    # Lifecycle
    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name=f"agent:{self.name}")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        while True:
            msg = await self._inbox.get()
            try:
                await self.handle(msg)
            except Exception as e:  # pragma: no cover
                await self.say(msg.room, f"[error] {type(e).__name__}: {e}")

    # Messaging
    async def deliver(self, msg: Message) -> None:
        await self._inbox.put(msg)

    async def say(self, room: str, content: str, *, role: str | None = None, meta: dict[str, Any] | None = None) -> None:
        assert self._router, "Agent must be attached before speaking"
        await self._router.post(Message(room=room, sender=self.name, content=content, role=role or self.role.name, meta=meta or {}))

    # To override
    async def handle(self, msg: Message) -> None:  # pragma: no cover
        pass
