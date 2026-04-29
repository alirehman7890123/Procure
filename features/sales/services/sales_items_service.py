"""Sales feature bridge for sales item helpers."""

try:
    from medic.services.sales_items_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.sales_items_service import *  # noqa: F403
