from __future__ import annotations

from ..core import Agent, Message, Role


class PlannerAgent(Agent):
    """Agent that helps plan tasks and break them down."""

    def __init__(self, name: str = "planner"):
        super().__init__(name, role=Role(name="planner", icon="📋"))

    async def handle(self, msg: Message) -> None:
        # Simple echo for now - can be enhanced later
        if msg.sender != self.name and "plan" in msg.content.lower():
            await self.send(
                msg.room,
                f"I can help plan that task: {msg.content[:100]}...",
                role="assistant"
            )