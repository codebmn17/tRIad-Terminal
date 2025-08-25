from __future__ import annotations

import argparse
import asyncio
import sys
from typing import List, Type

from .core import Agent, Message
from .rooms import Router
from .registry import discover_builtin_agents
from .memory import MemoryStore
from .modes import ModeManager, VALID_MODES, DEFAULT_MODE
from .builtins.recorder import RecorderAgent

ANSI = {
    "reset": "\x1b[0m",
    "dim": "\x1b[2m",
    "bold": "\x1b[1m",
    "cyan": "\x1b[36m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "magenta": "\x1b[35m",
}


def color(c: str, s: str) -> str:
    return f"{ANSI.get(c, '')}{s}{ANSI['reset']}"


def banner(room: str, mode: str) -> None:
    print(color("bold", f"Triad multi‑agent chat — room '{room}' — mode {mode.upper()}"))
    print(color("dim", "Type your message. Use /help for commands. Ctrl+C to exit."))


async def run_chat(agent_classes: List[Type[Agent]], *, room: str = "main", data_dir: str = ".triad", mem_max: int = 10_000) -> None:
    router = Router()
    store = MemoryStore(data_dir=data_dir, maxlen=mem_max)
    modes = ModeManager()
    modes.set_mode(room, DEFAULT_MODE)

    # Instantiate agents
    agents: List[Agent] = [cls() for cls in agent_classes]
    recorder = RecorderAgent(store)
    agents.insert(0, recorder)

    for a in agents:
        a.attach(router)
        await a.join(room)
        await a.start()

    loop = asyncio.get_event_loop()
    current_room = room

    banner(current_room, modes.get_mode(current_room))

    try:
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            line = line.rstrip("\n")
            if not line:
                continue

            if line.startswith("/"):
                # REPL commands
                parts = line[1:].split()
                if not parts:
                    continue
                cmd, *args = parts
                cmd = cmd.lower()

                if cmd == "help":
                    print("Commands:\n"
                          "  /rooms                     List rooms\n"
                          "  /room new <name>           Create & switch room\n"
                          "  /join <name>               Switch room\n"
                          "  /mode <safe|anon|triad>    Set mode for current room\n"
                          "  /core set <topic> <text>   Save core memory note\n"
                          "  /core get <topic>          Show core memory topic\n"
                          "  /core list                 List core topics\n"
                          "  /core del <topic>          Delete core topic\n"
                          "  /save                      Flush (no‑op for JSONL)\n"
                          )
                    continue

                if cmd == "rooms":
                    print("Rooms:", ", ".join(sorted(router.rooms.keys()) or [current_room]))
                    continue

                if cmd == "room" and args and args[0] == "new" and len(args) >= 2:
                    new_room = args[1]
                    current_room = new_room
                    # Subscribe recorder + agents to new room
                    for a in agents:
                        await a.join(new_room)
                    # Initialize mode for new room if not present
                    if modes.get_mode(new_room) not in VALID_MODES:
                        modes.set_mode(new_room, DEFAULT_MODE)
                    banner(current_room, modes.get_mode(current_room))
                    continue

                if cmd == "join" and args:
                    target = args[0]
                    current_room = target
                    # ensure room exists in router map
                    if target not in router.rooms:
                        for a in agents:
                            await a.join(target)
                        if modes.get_mode(target) not in VALID_MODES:
                            modes.set_mode(target, DEFAULT_MODE)
                    banner(current_room, modes.get_mode(current_room))
                    continue

                if cmd == "mode" and args:
                    mode = args[0].lower()
                    if mode not in VALID_MODES:
                        print("Invalid mode. Choose one of:", ", ".join(sorted(VALID_MODES)))
                        continue
                    modes.set_mode(current_room, mode)
                    banner(current_room, modes.get_mode(current_room))
                    continue

                if cmd == "core" and args:
                    sub = args[0]
                    if sub == "set" and len(args) >= 3:
                        topic = args[1]
                        text = " ".join(args[2:])
                        store.core_set(topic, text)
                        print(color("green", f"[core] saved '{topic}'"))
                        continue
                    if sub == "get" and len(args) >= 2:
                        topic = args[1]
                        entries = store.core_get(topic)
                        if not entries:
                            print(color("yellow", f"[core] empty: {topic}"))
                        else:
                            for e in entries:
                                print(f"- {e['ts']}: {e['text']}")
                        continue
                    if sub == "list":
                        topics = store.core_list()
                        print("Core topics:", ", ".join(topics) if topics else "(none)")
                        continue
                    if sub == "del" and len(args) >= 2:
                        topic = args[1]
                        ok = store.core_del(topic)
                        print(color("yellow", f"[core] deleted '{topic}'") if ok else color("yellow", f"[core] not found '{topic}'"))
                        continue

                if cmd == "save":
                    store.flush()
                    print("[saved]")
                    continue

                print(color("yellow", "Unknown command. Use /help."))
                continue

            # normal user message
            meta = {"mode": modes.get_mode(current_room)}
            await router.post(Message(room=current_room, sender="you", content=line, role="user", meta=meta))

    except KeyboardInterrupt:
        print("\nbye")
    finally:
        await asyncio.gather(*(a.stop() for a in agents))


def main() -> int:
    parser = argparse.ArgumentParser(description="Triad Terminal multi‑agent chat")
    parser.add_argument("--agents", nargs="*", default=["PlannerAgent", "CriticAgent", "ExecutorAgent"], help="List of agent class names to load")
    parser.add_argument("--room", default="main")
    parser.add_argument("--data-dir", default=".triad", help="Data directory for memory store")
    parser.add_argument("--mem-max", type=int, default=10_000, help="Max messages per room to keep in rolling buffer")
    args = parser.parse_args()

    builtins = discover_builtin_agents()
    # Ensure recorder is always present regardless of specified agents
    missing = [a for a in args.agents if a not in builtins]
    if missing:
        print("Unknown agents:", ", ".join(missing))
        print("Available:", ", ".join(sorted(builtins.keys())))
        return 2

    classes: List[Type[Agent]] = [builtins[name] for name in args.agents]

    asyncio.run(run_chat(classes, room=args.room, data_dir=args.data_dir, mem_max=args.mem_max))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())