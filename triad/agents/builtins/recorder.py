from __future__ import annotations

from ..core import Agent, Message, Role
from ..memory import MemoryStore


class RecorderAgent(Agent):
    """Silent observer that records every message to MemoryStore."""

    def __init__(self, store: MemoryStore, name: str = "recorder"):
        super().__init__(name, role=Role(name="system", icon="·"))
        self._store = store

    async def handle(self, msg: Message) -> None:
        # Record without responding
        try:
            self._store.record(msg)
        except Exception:
            # Never crash the bus due to recording issues
            pass