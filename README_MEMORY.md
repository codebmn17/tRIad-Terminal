# Triad Terminal Memory System

A persistent, long-term memory system for terminal multi-agent chat with Python-first, stdlib-only implementation.

## Features

- 🗄️ **Persistent Memory**: 10,000 messages per room with JSONL append-only storage
- 🧠 **Core Memory**: Long-term knowledge storage by topic
- 🔄 **Runtime Modes**: Safe (default), Anon, and Triad modes
- 🤖 **Multi-Agent Framework**: Asynchronous agent system with message routing
- 💬 **REPL Commands**: Interactive terminal commands for memory management
- 📁 **Multi-Room Support**: Separate memory spaces for different contexts

## Quick Start

### 1. Interactive Chat Mode

```bash
python3 -m triad.agents.cli_chat
```

This starts an interactive multi-agent chat with memory persistence.

### 2. Integration with Existing Code

```python
from triad.agents.memory import MemoryStore
from triad.agents.modes import ModeManager

# Initialize memory system
store = MemoryStore(data_dir=".triad", maxlen=10_000)
modes = ModeManager()

# Set mode for a room
modes.set_mode("my_room", "safe")

# Record a message
from triad.agents.core import Message
msg = Message(room="my_room", sender="user", content="Hello!", role="user")
store.record(msg)

# Save core memory
store.core_set("important_topic", "Key information to remember")
```

### 3. Run Demo

```bash
python3 demo_memory_system.py
```

## REPL Commands

When running the CLI chat, use these commands:

- `/help` - Show all available commands
- `/rooms` - List all active rooms
- `/room new <name>` - Create and switch to a new room
- `/join <name>` - Switch to an existing room
- `/mode <safe|anon|triad>` - Set runtime mode for current room
- `/core set <topic> <text>` - Save a note to core memory
- `/core get <topic>` - Show notes for a topic
- `/core list` - List all core memory topics
- `/core del <topic>` - Delete a topic and its notes
- `/save` - Force flush (JSONL writes are immediate)

## Runtime Modes

### Safe Mode (Default)
- `cautious_execution`: True
- `redact_pii`: False
- `fast_cadence`: False

### Anon Mode
- `cautious_execution`: False
- `redact_pii`: True
- `fast_cadence`: False

### Triad Mode
- `cautious_execution`: False
- `redact_pii`: False
- `fast_cadence`: True

## Architecture

### Core Components

- **`triad/agents/core.py`** - Base Agent class and Router for message passing
- **`triad/agents/memory.py`** - MemoryStore with JSONL persistence and core memory
- **`triad/agents/modes.py`** - Runtime mode management
- **`triad/agents/rooms.py`** - Room management (re-exports Router)
- **`triad/agents/registry.py`** - Agent discovery and registration
- **`triad/agents/cli_chat.py`** - Interactive terminal interface

### Builtin Agents

- **`RecorderAgent`** - Silently records all messages to memory
- **`PlannerAgent`** - Helps plan tasks and break them down
- **`CriticAgent`** - Provides critical analysis and feedback
- **`ExecutorAgent`** - Executes planned tasks

### Data Layout

```
.triad/
├── rooms/
│   ├── main.jsonl      # Messages for 'main' room
│   ├── project.jsonl   # Messages for 'project' room
│   └── ...
└── core_memory.json    # Topic-based long-term memory
```

## Examples

### Basic Usage

```python
import asyncio
from triad.agents.core import Agent, Message, Router
from triad.agents.memory import MemoryStore
from triad.agents.builtins.recorder import RecorderAgent

async def example():
    # Setup
    router = Router()
    store = MemoryStore()
    recorder = RecorderAgent(store)

    # Start recorder
    recorder.attach(router)
    await recorder.join("example_room")
    await recorder.start()

    # Send a message
    msg = Message(room="example_room", sender="user", content="Hello world!")
    await router.post(msg)

    # Check recorded messages
    messages = list(store.iter("example_room"))
    print(f"Recorded {len(messages)} messages")

    # Clean up
    await recorder.stop()

asyncio.run(example())
```

### Custom Agent

```python
from triad.agents.core import Agent, Message, Role

class MyAgent(Agent):
    def __init__(self):
        super().__init__("my_agent", role=Role(name="helper", icon="🤖"))

    async def handle(self, msg: Message) -> None:
        if msg.sender != self.name and "help" in msg.content.lower():
            await self.send(msg.room, "I'm here to help!", role="assistant")
```

## Testing

Run the test suite:

```bash
python3 test_triad_system.py
```

Run the integration example:

```bash
python3 integration_example.py
```

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)

## File Structure

```
triad/
├── __init__.py
└── agents/
    ├── __init__.py
    ├── core.py          # Core agent framework
    ├── memory.py        # Memory persistence system
    ├── modes.py         # Runtime mode management
    ├── rooms.py         # Room management
    ├── registry.py      # Agent discovery
    ├── cli_chat.py      # Interactive terminal interface
    └── builtins/
        ├── __init__.py
        ├── recorder.py   # Message recording agent
        ├── planner.py    # Task planning agent
        ├── critic.py     # Analysis agent
        └── executor.py   # Task execution agent
```

## License

Part of the tRIad Terminal project.
