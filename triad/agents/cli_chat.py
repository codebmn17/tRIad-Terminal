from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import List, Type

from .core import Agent, Message, Role
from .rooms import Router
from .registry import discover_builtin_agents

ANSI = {
    "reset": "\x1b[0m",
    "dim": "\x1b[2m",
    "bold": "\x1b[1m",
    "cyan": "\x1b[36m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
}


def color(c: str, s: str) -> str:
    return f"{ANSI.get(c, '')}{s}{ANSI['reset']}"


def format_line(room: str, sender: str, role: str, text: str) -> str:
    head = f"[{room}] {sender}:{' ' if sender else ''}"
    return f"{color('cyan', head)} {text}"


class MessageDisplayAgent(Agent):
    """Special agent to display messages from other agents"""
    
    def __init__(self):
        super().__init__("_display", role=Role(name="display", icon=""))
    
    async def handle(self, msg: Message) -> None:
        if msg.sender == self.name or msg.sender == "you":
            return
        
        # Get the role icon
        icon = ""
        if hasattr(msg, 'meta') and 'icon' in msg.meta:
            icon = msg.meta['icon']
        
        # Format and display the message
        role_prefix = f"{icon} {msg.role}" if icon else msg.role
        sender_info = f"[{color('cyan', role_prefix)}] {color('green', msg.sender)}"
        print(f"{sender_info}: {msg.content}")


async def run_chat(agent_classes: List[Type[Agent]], room: str = "main") -> None:
    router = Router()

    # Instantiate agents
    agents: List[Agent] = [cls() for cls in agent_classes]
    
    # Add display agent to show responses
    display_agent = MessageDisplayAgent()
    agents.append(display_agent)
    
    for a in agents:
        a.attach(router)
        await a.join(room)
        await a.start()

    print(color("bold", f"Triad multi‑agent chat — room '{room}'"))
    print(color("dim", "Type your message. Ctrl+C to exit."))
    print()

    try:
        loop = asyncio.get_event_loop()
        while True:
            user_text = await loop.run_in_executor(None, sys.stdin.readline)
            if not user_text:
                break
            user_text = user_text.strip("\n")
            if not user_text:
                continue
            
            print(f"{color('yellow', '[you]')}: {user_text}")
            await router.post(Message(room=room, sender="you", content=user_text, role="user"))
            
            # Small delay to let agents respond
            await asyncio.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nbye")
    finally:
        await asyncio.gather(*(a.stop() for a in agents))


def main() -> int:
    parser = argparse.ArgumentParser(description="Triad Terminal multi‑agent chat")
    parser.add_argument("--agents", nargs="*", default=["PlannerAgent", "CriticAgent", "ExecutorAgent"], help="List of agent class names to load")
    parser.add_argument("--room", default="main")
    args = parser.parse_args()

    builtins = discover_builtin_agents()
    missing = [a for a in args.agents if a not in builtins]
    if missing:
        print("Unknown agents:", ", ".join(missing))
        print("Available:", ", ".join(sorted(builtins.keys())))
        return 2

    classes = [builtins[name] for name in args.agents]
    asyncio.run(run_chat(classes, room=args.room))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())