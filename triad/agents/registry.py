from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Type

from .core import Agent


def discover_builtin_agents() -> Dict[str, Type[Agent]]:
    from . import builtins as mod
    discovered: Dict[str, Type[Agent]] = {}
    for m in pkgutil.iter_modules(mod.__path__, prefix=mod.__name__ + "."):
        module = importlib.import_module(m.name)
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, Agent) and obj is not Agent:
                discovered[obj.__name__] = obj
    return discovered