from __future__ import annotations

from ..core import Agent, Message, Role


class ExecutorAgent(Agent):
    """Agent that executes planned tasks."""

    def __init__(self, name: str = "executor"):
        super().__init__(name, role=Role(name="executor", icon="⚡"))

    async def handle(self, msg: Message) -> None:
        # Simple echo for now - can be enhanced later
        if msg.sender != self.name and "execute" in msg.content.lower():
            await self.send(
                msg.room,
                f"Executing: {msg.content[:100]}...",
                role="assistant"
            )