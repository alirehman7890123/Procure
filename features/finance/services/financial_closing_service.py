"""Finance feature financial-closing-service bridge."""

try:
    from medic.services.financial_closing_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.financial_closing_service import *  # noqa: F403
