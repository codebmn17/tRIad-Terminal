from __future__ import annotations

from ..core import Agent, Message, Role
from .utils import safe_md


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
    def __init__(self, name: str = "planner"):
        super().__init__(name, role=Role(name="planner", icon="⚙"))

    async def handle(self, msg: Message) -> None:
        if msg.sender == self.name:
            return
        if msg.role == "system":
            return
        # Only respond to user messages or "exec" commands
        if msg.role != "user" and not msg.content.strip().lower().startswith("exec"):
            return
        plan = [
            "Clarify the user objective",
            "Break into steps",
            "Identify risks and checks",
            "Propose next action",
        ]
        text = "\n".join(f"- {p}" for p in plan)
        await self.say(msg.room, safe_md(f"Plan for: {msg.brief()}\n\n{text}"), meta={"icon": self.role.icon})
