from __future__ import annotations

from .utils import safe_md
from ..core import Agent, Message, Role


class CriticAgent(Agent):
    def __init__(self, name: str = "critic"):
        super().__init__(name, role=Role(name="critic", icon="!"))

    async def handle(self, msg: Message) -> None:
        if msg.sender == self.name:
            return
        if not msg.content.strip():
            return
        cautions = [
            "Check for security implications",
            "Validate file paths and credentials",
            "Prefer dry‑run before executing",
            "Log the intent and outcome",
        ]
        text = "\n".join(f"- {c}" for c in cautions)
        await self.say(msg.room, safe_md(f"Cautions for: {msg.brief()}\n\n{text}"))