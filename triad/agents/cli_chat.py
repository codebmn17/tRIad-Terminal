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


async def run_chat(agent_classes: List[Type[Agent]], room: str = "main") -> None:
    router = Router()

    # Instantiate agents
    agents: List[Agent] = [cls() for cls in agent_classes]
    for a in agents:
        a.attach(router)
        await a.join(room)
        await a.start()

    print(color("bold", f"Triad multi‑agent chat — room '{room}'"))
    print(color("dim", "Type your message. Ctrl+C to exit."))

    try:
        loop = asyncio.get_event_loop()
        while True:
            user_text = await loop.run_in_executor(None, sys.stdin.readline)
            if not user_text:
                break
            user_text = user_text.strip("\n")
            if not user_text:
                continue
            await router.post(Message(room=room, sender="you", content=user_text, role="user"))
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