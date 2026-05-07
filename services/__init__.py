"""Service layer modules for reusable business logic."""

import os
import sys
import types
from importlib import import_module


if not getattr(sys, "frozen", False):
    try:
        import_module("medic")
    except ModuleNotFoundError:
        if "medic" not in sys.modules:
            medic_pkg = types.ModuleType("medic")
            medic_pkg.__file__ = os.path.join(os.path.dirname(os.path.dirname(__file__)), "__init__.py")
            medic_pkg.__path__ = [os.path.dirname(os.path.dirname(__file__))]
            sys.modules["medic"] = medic_pkg

sys.modules.setdefault("medic.services", sys.modules[__name__])
