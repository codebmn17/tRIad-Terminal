from __future__ import annotations

import contextlib

from ..core import Agent, Message, Role
from ..memory import MemoryStore


class RecorderAgent(Agent):
    """Silent observer that records every message to MemoryStore."""

    def __init__(self, store: MemoryStore, name: str = "recorder"):
        super().__init__(name, role=Role(name="system", icon="·"))
        self._store = store

    async def handle(self, msg: Message) -> None:
        # Record without responding
        with contextlib.suppress(Exception):
            # Never crash the bus due to recording issues
            self._store.record(msg)
