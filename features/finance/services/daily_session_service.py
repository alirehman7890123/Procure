"""Finance feature daily-session-service bridge."""

try:
    from medic.services.daily_session_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.daily_session_service import *  # noqa: F403
