"""Inventory feature bridge for product write services."""

try:
    from medic.services.product_write_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.product_write_service import *  # noqa: F403
