from __future__ import annotations

from .utils import safe_md
from ..core import Agent, Message, Role

SAFE_ACTIONS = {
    "open_url": "Open a URL in the preferred browser",
    "readme": "Show repository README instructions",
}


class ExecutorAgent(Agent):
    def __init__(self, name: str = "executor"):
        super().__init__(name, role=Role(name="executor", icon=">"))

    async def handle(self, msg: Message) -> None:
        if msg.sender == self.name:
            return
        # Only respond to user messages
        if msg.role != "user":
            return
        # This is a stub demonstrating safe intents rather than running shell commands.
        suggestion = (
            "I can: "
            + ", ".join(sorted(SAFE_ACTIONS.keys()))
            + ". Reply with 'exec <action> <args>' to proceed."
        )
        await self.say(msg.room, safe_md(suggestion), meta={"icon": self.role.icon})