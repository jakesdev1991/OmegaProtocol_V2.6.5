"""
Dynamic, lazy plug-in discovery for Omega optimisers.
Lightweight wrappers (LazyOptimizer) for entry-points.
"""

from __future__ import annotations
import sys
from typing import Dict

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points  # type: ignore
else:
    from importlib.metadata import entry_points

__all__ = ["LazyOptimizer", "discover_optimizer_plugins"]


class LazyOptimizer:
    def __init__(self, ep):
        self._ep = ep
        self._cls = None
        self._instance = None

    def _load_class(self):
        if self._cls is None:
            self._cls = self._ep.load()
        return self._cls

    def _get_instance(self):
        if self._instance is None:
            cls = self._load_class()
            self._instance = cls() if callable(cls) else cls
        return self._instance

    def optimize(self, *args, **kwargs):
        return self._get_instance().optimize(*args, **kwargs)

    def __getattr__(self, item):
        return getattr(self._get_instance(), item)


def discover_optimizer_plugins() -> Dict[str, LazyOptimizer]:
    found: Dict[str, LazyOptimizer] = {}
    for ep in entry_points(group="omega.optimizers"):
        found[ep.name] = LazyOptimizer(ep)
    return found