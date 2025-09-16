# Triad Terminal — Multi‑Agent Runtime (Terminal‑first)

This module introduces a minimal, Python‑first multi‑agent framework using `asyncio` and a terminal group‑chat. It is additive and off by default.

## Why
- Coordinate multiple specialists (planner, critic, executor) in one room.
- Keep the terminal as the primary surface.
- Favor safety: no shell execution by default (executor proposes actions only).

## Quick start

```bash
python -m triad.agents.cli_chat
# or pick specific agents
python -m triad.agents.cli_chat --agents PlannerAgent CriticAgent ExecutorAgent
```

Type your message and watch the agents coordinate in the `main` room.

## Concepts
- Room: a channel where agents subscribe and messages broadcast.
- Message: `{room, sender, content, role, ts}`.
- Agent: subclass `triad.agents.core.Agent` and implement `async def handle(self, msg)`. Use `await self.say(room, text)` to respond.

## Safety model
- The provided `ExecutorAgent` is conservative. It suggests safe actions and requires explicit consent to run anything that might be risky.
- To extend with real system actions, add a new executor that wraps commands in checks, dry‑run previews, and user confirmations.

## Extend with your own agents
Create a new file under `triad/agents/plugins/your_agent.py`:

```python
from triad.agents.core import Agent, Message, Role

class YourAgent(Agent):
    def __init__(self):
        super().__init__("your-agent", role=Role("specialist", icon="★"))

    async def handle(self, msg: Message) -> None:
        if msg.sender == self.name:
            return
        if "hello" in msg.content.lower():
            await self.say(msg.room, "Hello back from YourAgent!")
```

Then run with:

```bash
python -m triad.agents.cli_chat --agents PlannerAgent CriticAgent ExecutorAgent YourAgent
```

## Icons and symbols
- Terminal uses plain ASCII by default.
- If you use a Nerd Font, you can swap icons by changing `Role.icon` in your agents.

## Next steps
- Optional web/electron chat surface with WebSockets.
- Shared memory/blackboard with persistence.
- Tool calling to integrate repo commands, tests, and docs lookup.
