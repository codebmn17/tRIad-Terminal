from __future__ import annotations

import importlib
import pkgutil

from .core import Agent


def discover_builtin_agents() -> dict[str, type[Agent]]:
    """Discover available builtin agents."""
copilot/fix-1f51a615-a20d-476a-b14f-a5ee1cba80a2
    registry: Dict[str, Type[Agent]] = {}

    registry: dict[str, type[Agent]] = {}
 main

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
 copilot/fix-1f51a615-a20d-476a-b14f-a5ee1cba80a2


        pass
 main

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
    discovered: dict[str, type[Agent]] = {}
    for m in pkgutil.iter_modules(mod.__path__, prefix=mod.__name__ + "."):
        module = importlib.import_module(m.name)
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, Agent) and obj is not Agent:
                discovered[obj.__name__] = obj
    return discovered
