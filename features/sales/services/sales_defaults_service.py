"""Sales feature bridge for sales defaults helpers."""

try:
    from medic.services.sales_defaults_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.sales_defaults_service import *  # noqa: F403
