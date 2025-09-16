#!/usr/bin/env python3

"""
Integration example showing how to add the Triad Memory System to existing terminal
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from triad.agents.builtins.recorder import RecorderAgent
from triad.agents.core import Message, Router
from triad.agents.memory import MemoryStore
from triad.agents.modes import ModeManager


class TriadIntegration:
    """Integration class to add memory system to existing terminal"""

    def __init__(self, data_dir: str = ".triad", maxlen: int = 10_000):
        self.router = Router()
        self.store = MemoryStore(data_dir=data_dir, maxlen=maxlen)
        self.modes = ModeManager()
        self.recorder = RecorderAgent(self.store)
        self._started = False

    async def start(self, room: str = "main"):
        """Start the memory system for a room"""
        if not self._started:
            self.recorder.attach(self.router)
            await self.recorder.join(room)
            await self.recorder.start()
            self.modes.set_mode(room, "safe")  # Default to safe mode
            self._started = True

    async def stop(self):
        """Stop the memory system"""
        if self._started:
            await self.recorder.stop()
            self._started = False

    def log_command(self, room: str, command: str, user: str = "user", result: str = None):
        """Log a command and optionally its result"""
        # Log the command
        cmd_msg = Message(
            room=room,
            sender=user,
            content=command,
            role="user",
            meta={"type": "command", "mode": self.modes.get_mode(room)},
        )

        # Use asyncio to run the recording
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.router.post(cmd_msg))
        else:
            asyncio.run(self.router.post(cmd_msg))

        # Log result if provided
        if result:
            result_msg = Message(
                room=room,
                sender="system",
                content=result,
                role="assistant",
                meta={"type": "result", "mode": self.modes.get_mode(room)},
            )

            if loop.is_running():
                asyncio.create_task(self.router.post(result_msg))
            else:
                asyncio.run(self.router.post(result_msg))

    def set_mode(self, room: str, mode: str):
        """Set the mode for a room"""
        return self.modes.set_mode(room, mode)

    def get_history_summary(self, room: str, limit: int = 10) -> str:
        """Get a summary of recent history"""
        return self.store.summarize(room, limit=limit)

    def save_note(self, topic: str, text: str):
        """Save a note to core memory"""
        self.store.core_set(topic, text)

    def get_notes(self, topic: str = None):
        """Get notes from core memory"""
        if topic:
            return self.store.core_get(topic)
        else:
            return self.store.core_list()


# Example of how to integrate with existing terminal
async def integration_example():
    """Example showing integration with existing terminal system"""
    print("🔗 Triad Memory System Integration Example")
    print("=" * 50)

    # Initialize integration
    triad = TriadIntegration(data_dir=".triad_example")
    await triad.start("terminal_session")

    print("✓ Triad memory system started")

    # Simulate some terminal commands being logged
    commands = [
        (
            "ls -la",
            "total 8\ndrwxr-xr-x 2 user user 4096 Aug 25 21:00 .\ndrwxr-xr-x 3 user user 4096 Aug 25 21:00 ..",
        ),
        ("pwd", "/home/user/projects"),
        ("git status", "On branch main\nYour branch is up to date with 'origin/main'."),
        ("python3 --version", "Python 3.12.3"),
    ]

    print("\n📝 Logging terminal commands...")
    for cmd, result in commands:
        print(f"   $ {cmd}")
        triad.log_command("terminal_session", cmd, result=result)
        await asyncio.sleep(0.1)

    # Show history summary
    print("\n📊 Recent session summary:")
    summary = triad.get_history_summary("terminal_session")
    for line in summary.split("\n"):
        if line.strip():
            print(f"   {line}")

    # Save some notes
    print("\n🧠 Saving session notes...")
    triad.save_note("session_info", "Working on terminal integration")
    triad.save_note("session_info", "Testing memory system with commands")
    triad.save_note("project_status", "Memory system integration complete")

    # Show notes
    topics = triad.get_notes()
    print(f"   Saved topics: {topics}")
    for topic in topics:
        notes = triad.get_notes(topic)
        print(f"   {topic}: {len(notes)} notes")

    # Test mode switching
    print("\n⚙️  Testing mode switching...")
    for mode in ["safe", "anon", "triad"]:
        triad.set_mode("terminal_session", mode)
        flags = triad.modes.flags("terminal_session")
        print(f"   Mode '{mode}': {flags}")

    # Clean up
    await triad.stop()
    print("\n✅ Integration example completed!")


if __name__ == "__main__":
    asyncio.run(integration_example())
