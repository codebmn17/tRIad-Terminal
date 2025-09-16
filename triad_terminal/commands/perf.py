"""
Performance Command for Triad Terminal

Provides a /perf or :perf command to display performance summary.
Integrates with the existing command dispatch system.
"""

from ..perf_runtime import perf_summary

__all__ = ["run"]


def run(args: str | None = None) -> str:
    """
    Execute the performance command and return summary.

    This function can be called by the existing command dispatch system
    when a user types '/perf' or 'perf'.

    Args:
        args: Additional arguments (currently unused)

    Returns:
        Performance summary string ready for display
    """
    return perf_summary()


def print_perf() -> None:
    """
    Print the performance summary directly to stdout.

    Alternative interface for terminals that prefer direct printing
    over returning strings.
    """
    print(run())


# For backwards compatibility and direct usage
def perf_command(args: str | None = None) -> str:
    """Alias for run() function"""
    return run(args)
