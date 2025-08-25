from __future__ import annotations

import asyncio
import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


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
    ts: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    meta: Dict[str, Any] = field(default_factory=dict)

    def brief(self) -> str:
        text = self.content.strip().replace("\n", " ")
        return (text[:120] + "…") if len(text) > 120 else text


class Agent:
    """Base class for simple asyncio agents."""

    def __init__(self, name: str, role: Optional[Role] = None):
        self.name = name
        self.role = role or Role(name="agent", icon="∴")
        self._router: Optional["Router"] = None
        self._inbox: "asyncio.Queue[Message]" = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None

    # Wiring
    def attach(self, router: "Router") -> None:
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

    async def say(self, room: str, content: str, *, role: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> None:
        assert self._router, "Agent must be attached before speaking"
        await self._router.post(Message(room=room, sender=self.name, content=content, role=role or self.role.name, meta=meta or {}))

    # To override
    async def handle(self, msg: Message) -> None:  # pragma: no cover
        pass