#!/usr/bin/env python3
"""
Example integration showing how to add performance monitoring to an existing terminal.

This demonstrates how to integrate the Triad Terminal performance utilities
with the existing command processing systems.
"""

import time
from triad_terminal.perf_utils import timed, time_block
from triad_terminal.perf_runtime import record_command, perf_summary
from triad_terminal.commands.perf import run as perf_command


# Example: Wrapping existing functions with timing
@timed
def load_configuration():
    """Example function that loads configuration (simulated)"""
    time.sleep(0.01)  # Simulate config loading
    return {"theme": "matrix", "voice": True}


@timed(name="security_check")
def authenticate_user(username: str):
    """Example authentication function with custom timing name"""
    time.sleep(0.005)  # Simulate auth check
    return username == "admin"


def process_command(command: str) -> str:
    """Example command processor with integrated performance tracking"""
    # Record the command for statistics
    record_command(command)
    
    if command == "perf":
        # Return performance summary
        return perf_command()
    
    elif command == "help":
        # Use time_block for manual timing
        with time_block("help_generation"):
            time.sleep(0.001)  # Simulate help generation
            return "Available commands: help, perf, status, exit"
    
    elif command == "status":
        with time_block("status_check"):
            time.sleep(0.002)  # Simulate status check
            return "System status: OK"
    
    elif command == "exit":
        return "Goodbye!"
    
    else:
        return f"Unknown command: {command}"


def main():
    """Example main function demonstrating performance monitoring integration"""
    print("Starting Triad Terminal (Performance Demo)")
    
    # Example of timed startup sequence
    with time_block("initialization"):
        config = load_configuration()
        auth_result = authenticate_user("admin")
        print(f"Config loaded: {config}")
        print(f"Auth result: {auth_result}")
    
    # Simulate some command processing
    commands = ["help", "status", "perf", "unknown", "perf", "exit"]
    
    print("\nProcessing commands:")
    for cmd in commands:
        print(f"\n> {cmd}")
        result = process_command(cmd)
        print(result)
        time.sleep(0.1)  # Brief pause between commands
    
    print("\nFinal performance summary:")
    print(perf_summary())


if __name__ == "__main__":
    main()