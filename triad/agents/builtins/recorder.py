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
            self._store.record(msg)
 copilot/fix-1f51a615-a20d-476a-b14f-a5ee1cba80a2

        except Exception:
            # Never crash the bus due to recording issues
            pass
 main
