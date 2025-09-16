#!/usr/bin/env python3

"""
Simple test script to verify the Triad Terminal memory system
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from triad.agents.builtins.recorder import RecorderAgent
from triad.agents.core import Agent, Message, Role, Router
from triad.agents.memory import MemoryStore
from triad.agents.modes import ModeManager


class TestAgent(Agent):
    """Simple test agent that responds to messages"""

    def __init__(self, name: str = "test_agent"):
        super().__init__(name, role=Role(name="test", icon="🧪"))

    async def handle(self, msg: Message) -> None:
        if msg.sender != self.name and "hello" in msg.content.lower():
            await self.send(
                msg.room,
                f"Hello {msg.sender}! I received: {msg.content}",
                role="assistant"
            )


async def test_full_system():
    """Test the complete agent system"""
    print("Testing Triad Terminal Agent System...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize components
        router = Router()
        store = MemoryStore(data_dir=tmpdir, maxlen=100)
        modes = ModeManager()

        # Create agents
        recorder = RecorderAgent(store)
        test_agent = TestAgent()

        # Setup agents
        for agent in [recorder, test_agent]:
            agent.attach(router)
            await agent.join("test_room")
            await agent.start()

        # Test mode setting
        modes.set_mode("test_room", "safe")
        assert modes.get_mode("test_room") == "safe"
        print("✓ Mode management works")

        # Test message routing
        msg = Message(
            room="test_room",
            sender="human",
            content="Hello everyone!",
            role="user",
            meta={"mode": "safe"}
        )

        await router.post(msg)
        await asyncio.sleep(0.1)  # Give agents time to process

        # Check that message was recorded
        recorded_messages = list(store.iter("test_room"))
        assert len(recorded_messages) >= 1
        assert recorded_messages[0].content == "Hello everyone!"
        print("✓ Message recording works")

        # Test core memory
        store.core_set("test_topic", "This is a test note")
        topics = store.core_list()
        assert "test_topic" in topics

        entries = store.core_get("test_topic")
        assert len(entries) == 1
        assert "test note" in entries[0]["text"]
        print("✓ Core memory works")

        # Test JSONL persistence
        room_file = Path(tmpdir) / "rooms" / "test_room.jsonl"
        assert room_file.exists()

        with room_file.open() as f:
            lines = f.readlines()
            assert len(lines) >= 1
        print("✓ JSONL persistence works")

        # Clean up
        for agent in [recorder, test_agent]:
            await agent.stop()

        print("\n🎉 All tests passed! The Triad Terminal Agent System is working correctly.")


if __name__ == "__main__":
    asyncio.run(test_full_system())
