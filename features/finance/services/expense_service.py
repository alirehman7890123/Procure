"""Finance feature expense-service bridge."""

try:
    from medic.services.expense_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.expense_service import *  # noqa: F403
