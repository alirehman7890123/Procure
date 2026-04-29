"""Inventory feature bridge for stock adjustment services."""

try:
    from medic.services.stock_adjustment_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.stock_adjustment_service import *  # noqa: F403
