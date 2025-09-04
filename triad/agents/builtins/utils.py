from __future__ import annotations

from typing import Any, Dict

from ..core import Agent, Message, Role


def safe_md(text: str) -> str:
    """Very light sanitation for terminal rendering."""
    return text.replace("\r", "").strip()


def create_simple_agent(name: str, description: str) -> type[Agent]:
    """Create a simple agent class with basic functionality."""
    
    class SimpleAgent(Agent):
        def __init__(self):
            super().__init__(name, role=Role("assistant", icon="🤖"))
            self.description = description
        
        async def handle(self, msg: Message) -> None:
            """Handle incoming messages."""
            if msg.sender == self.name:
                return
            
            # Simple echo response
            response = f"I'm {self.name}. {description}. You said: '{msg.content}'"
            await self.say(msg.room, response)
    
    SimpleAgent.__name__ = name
    SimpleAgent.__qualname__ = name
    return SimpleAgent