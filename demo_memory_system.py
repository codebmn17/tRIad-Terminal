#!/usr/bin/env python3

"""
Demo script showing the Triad Terminal memory system in action
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from triad.agents.builtins.critic import CriticAgent
from triad.agents.builtins.planner import PlannerAgent
from triad.agents.builtins.recorder import RecorderAgent
from triad.agents.core import Message, Router
from triad.agents.memory import MemoryStore
from triad.agents.modes import ModeManager


async def demo():
    """Demonstrate the memory system with interactive agents"""
    print("🚀 Triad Terminal Memory System Demo")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize system
        router = Router()
        store = MemoryStore(data_dir=tmpdir, maxlen=10_000)
        modes = ModeManager()

        # Create agents
        recorder = RecorderAgent(store)
        planner = PlannerAgent()
        critic = CriticAgent()

        agents = [recorder, planner, critic]

        # Setup agents
        for agent in agents:
            agent.attach(router)
            await agent.join("demo_room")
            await agent.start()

        print(f"✓ Started {len(agents)} agents in 'demo_room'")

        # Set mode to safe
        modes.set_mode("demo_room", "safe")
        mode_flags = modes.flags("demo_room")
        print(f"✓ Mode set to 'safe': {mode_flags}")

        # Simulate some conversation
        messages = [
            Message(room="demo_room", sender="user", content="I need to plan a new project", role="user"),
            Message(room="demo_room", sender="user", content="Can you review my approach?", role="user"),
            Message(room="demo_room", sender="user", content="Let's execute the plan", role="user"),
        ]

        print("\n📝 Simulating conversation...")
        for msg in messages:
            print(f"   {msg.sender}: {msg.content}")
            await router.post(msg)
            await asyncio.sleep(0.1)  # Small delay for processing

        # Check recorded messages
        print("\n💾 Memory System Status:")
        recorded = list(store.iter("demo_room"))
        print(f"   Recorded {len(recorded)} messages")

        # Check room file
        room_file = Path(tmpdir) / "rooms" / "demo_room.jsonl"
        if room_file.exists():
            print(f"   JSONL file: {room_file} ({room_file.stat().st_size} bytes)")

        # Demonstrate core memory
        print("\n🧠 Core Memory Demo:")
        store.core_set("project_goals", "Build an awesome terminal interface")
        store.core_set("project_goals", "Add memory persistence")
        store.core_set("team_info", "Working with async Python agents")

        topics = store.core_list()
        print(f"   Topics: {topics}")

        for topic in topics:
            entries = store.core_get(topic)
            print(f"   {topic}: {len(entries)} entries")
            for entry in entries:
                print(f"     - {entry['ts'][:19]}: {entry['text']}")

        # Show summary
        summary = store.summarize("demo_room", limit=5)
        print("\n📊 Recent Activity Summary:")
        for line in summary.split('\n'):
            if line.strip():
                print(f"   {line}")

        # Test mode switching
        print("\n⚙️  Mode System Demo:")
        for mode in ["safe", "anon", "triad"]:
            modes.set_mode("demo_room", mode)
            flags = modes.flags("demo_room")
            print(f"   Mode '{mode}': {flags}")

        # Clean up
        for agent in agents:
            await agent.stop()

        print("\n🎉 Demo completed successfully!")
        print("   All components working: Memory, Modes, Agents, Persistence")


if __name__ == "__main__":
    asyncio.run(demo())
