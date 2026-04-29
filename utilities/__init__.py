import os
import sys
import types

# Packaging fallback:
# when the bundled app imports modules via the local ``utilities`` package
# path, some modules still reference ``medic.utilities`` absolute imports.
# Register aliases so both import styles resolve to the same package.
if "medic" not in sys.modules:
    medic_pkg = types.ModuleType("medic")
    medic_pkg.__file__ = os.path.join(os.path.dirname(os.path.dirname(__file__)), "__init__.py")
    medic_pkg.__path__ = [os.path.dirname(os.path.dirname(__file__))]
    sys.modules["medic"] = medic_pkg

sys.modules.setdefault("medic.utilities", sys.modules[__name__])

from .label_printer import send_label_print_command
