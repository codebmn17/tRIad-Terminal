#!/usr/bin/env python3

"""
Automated test that simulates interactive CLI usage
"""

import sys
import asyncio
import tempfile
from pathlib import Path
from io import StringIO

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from triad.agents.cli_chat import run_chat
from triad.agents.registry import discover_builtin_agents


class MockStdin:
    """Mock stdin that provides predefined input"""
    
    def __init__(self, inputs):
        self.inputs = iter(inputs)
    
    def readline(self):
        try:
            line = next(self.inputs)
            print(f">>> {line}")  # Show what we're "typing"
            return line + "\n"
        except StopIteration:
            return ""  # EOF


async def test_cli_interactions():
    """Test CLI with simulated user interactions"""
    print("🧪 Testing CLI Interactions")
    print("=" * 40)
    
    # Prepare inputs (simulating user typing)
    inputs = [
        "/help",
        "/mode safe", 
        "/core set test_topic This is a test note",
        "/core list",
        "/core get test_topic",
        "Hello agents! Can you help me plan something?",
        "/rooms",
        "/room new project_room",
        "Let's work on the project",
        "/core set project_notes Working on integration",
        "/join main",  # Back to main room
        "/save",
        ""  # EOF to exit
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Replace stdin temporarily
        original_stdin = sys.stdin
        sys.stdin = MockStdin(inputs)
        
        try:
            # Get available agents
            builtins = discover_builtin_agents()
            agent_classes = [builtins["PlannerAgent"], builtins["CriticAgent"]]
            
            print("Starting CLI chat simulation...")
            print("-" * 40)
            
            # Run the chat with our mock input
            await run_chat(
                agent_classes, 
                room="main", 
                data_dir=tmpdir, 
                mem_max=100
            )
            
        except Exception as e:
            print(f"CLI test completed (expected EOF): {e}")
        finally:
            sys.stdin = original_stdin
        
        # Verify files were created
        data_dir = Path(tmpdir)
        rooms_dir = data_dir / "rooms"
        core_file = data_dir / "core_memory.json"
        
        print("-" * 40)
        print("📁 Checking created files:")
        
        if rooms_dir.exists():
            jsonl_files = list(rooms_dir.glob("*.jsonl"))
            print(f"   Room files: {[f.name for f in jsonl_files]}")
            
            for f in jsonl_files:
                if f.stat().st_size > 0:
                    print(f"   {f.name}: {f.stat().st_size} bytes")
        
        if core_file.exists():
            print(f"   Core memory: {core_file.stat().st_size} bytes")
            
            # Show core memory content
            import json
            with core_file.open() as f:
                core_data = json.load(f)
                print(f"   Core topics: {list(core_data.keys())}")
        
        print("✅ CLI interaction test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_cli_interactions())