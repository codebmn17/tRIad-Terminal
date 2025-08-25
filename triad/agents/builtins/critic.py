from __future__ import annotations

from ..core import Agent, Message, Role


class CriticAgent(Agent):
    """Agent that provides critical analysis and feedback."""

    def __init__(self, name: str = "critic"):
        super().__init__(name, role=Role(name="critic", icon="🔍"))

    async def handle(self, msg: Message) -> None:
        # Simple echo for now - can be enhanced later
        if msg.sender != self.name and "review" in msg.content.lower():
            await self.send(
                msg.room,
                f"Let me analyze that: {msg.content[:100]}...",
                role="assistant"
            )