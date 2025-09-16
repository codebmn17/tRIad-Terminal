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
        
    
    try:
    from .builtins.recorder import RecorderAgent
    registry["RecorderAgent"] = RecorderAgent
except ImportError:
    registry["RecorderAgent"] = None
        from .builtins.recorder import RecorderAgent
        registry["RecorderAgent"] = RecorderAgent
    except ImportError:
        pass
    
    return registry
    from . import builtins as mod
    discovered: Dict[str, Type[Agent]] = {}
    for m in pkgutil.iter_modules(mod.__path__, prefix=mod.__name__ + "."):
        module = importlib.import_module(m.name)
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, Agent) and obj is not Agent:
                discovered[obj.__name__] = obj
    return discovered
