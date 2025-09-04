"""
Agent registry for managing available agent types.

Provides a central registry for agent classes and capabilities discovery.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Type

from .core import Agent


def discover_builtin_agents() -> Dict[str, Type[Agent]]:
    """Discover available builtin agents."""
    registry: Dict[str, Type[Agent]] = {}
    
    try:
        from .builtins.planner import PlannerAgent
        registry["PlannerAgent"] = PlannerAgent
    except ImportError:
        pass
    
    try:
        from .builtins.critic import CriticAgent
        registry["CriticAgent"] = CriticAgent
    except ImportError:
        pass
    
    try:
        from .builtins.executor import ExecutorAgent
        registry["ExecutorAgent"] = ExecutorAgent
    except ImportError:
        pass
    
    # Add a simple chat agent for demonstrations
    try:
        from .builtins.utils import create_simple_agent
        ChatAgent = create_simple_agent("ChatAgent", "I assist with general conversations")
        registry["ChatAgent"] = ChatAgent
    except ImportError:
        pass
    
    # Skip RecorderAgent for now as it requires special initialization
    # try:
    #     from .builtins.recorder import RecorderAgent
    #     registry["RecorderAgent"] = RecorderAgent
    # except ImportError:
    #     pass
    
    return registry


def get_available_agents() -> Dict[str, Type[Agent]]:
    """Get all available agent types."""
    return discover_builtin_agents()


def get_agent_class(name: str) -> Type[Agent]:
    """Get an agent class by name."""
    agents = get_available_agents()
    if name not in agents:
        raise ValueError(f"Unknown agent type: {name}")
    return agents[name]


def list_agent_names() -> list[str]:
    """Get list of available agent names."""
    return list(get_available_agents().keys())
