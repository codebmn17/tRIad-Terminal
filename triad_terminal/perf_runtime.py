"""
Performance Runtime Tracking for Triad Terminal

Tracks process uptime, command counts, and provides summary information.
Minimal state storage in memory with helper functions for performance monitoring.
"""

import time

__all__ = ["record_command", "perf_summary", "get_uptime", "get_command_count"]

# Global state for runtime tracking
_start_time: float = time.time()
_command_count: int = 0
_command_history: dict[str, int] = {}


def record_command(command: str = "") -> None:
    """
    Record that a command was executed.

    Increments the global command counter and optionally tracks
    specific command types for more detailed statistics.

    Args:
        command: The command that was executed (optional)
    """
    global _command_count
    _command_count += 1

    # Track specific command types if provided
    if command:
        # Extract base command (first word) for categorization
        base_command = command.split()[0] if command.split() else command
        _command_history[base_command] = _command_history.get(base_command, 0) + 1


def get_uptime() -> float:
    """
    Get the process uptime in seconds.

    Returns:
        Number of seconds since the process started
    """
    return time.time() - _start_time


def get_command_count() -> int:
    """
    Get the total number of commands executed.

    Returns:
        Total command count since process start
    """
    return _command_count


def perf_summary() -> str:
    """
    Generate a performance summary string with uptime and command statistics.

    Returns:
        Formatted string with performance metrics
    """
    uptime_seconds = get_uptime()

    # Format uptime in human-readable form
    if uptime_seconds < 60:
        uptime_str = f"{uptime_seconds:.1f}s"
    elif uptime_seconds < 3600:
        minutes = int(uptime_seconds // 60)
        seconds = int(uptime_seconds % 60)
        uptime_str = f"{minutes}m {seconds}s"
    else:
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        uptime_str = f"{hours}h {minutes}m"

    # Build summary
    lines = [
        "=== Triad Terminal Performance Summary ===",
        f"Uptime: {uptime_str}",
        f"Commands executed: {_command_count}",
    ]

    # Add command breakdown if we have history
    if _command_history:
        lines.append("")
        lines.append("Command breakdown:")
        # Sort by usage count (descending)
        sorted_commands = sorted(_command_history.items(), key=lambda x: x[1], reverse=True)
        for cmd, count in sorted_commands[:10]:  # Top 10 commands
            lines.append(f"  {cmd}: {count}")

        if len(_command_history) > 10:
            lines.append(f"  ... and {len(_command_history) - 10} more")

    # Add performance metrics if available
    if _command_count > 0 and uptime_seconds > 0:
        commands_per_minute = (_command_count / uptime_seconds) * 60
        lines.append("")
        lines.append(f"Average: {commands_per_minute:.1f} commands/minute")

    return "\n".join(lines)
