from __future__ import annotations

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
    
    try:
        from .builtins.recorder import RecorderAgent
        registry["RecorderAgent"] = RecorderAgent
    except ImportError:
        pass
    
    return registry