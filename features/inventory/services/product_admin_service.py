"""Inventory feature bridge for product admin services."""

try:
    from medic.services.product_admin_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.product_admin_service import *  # noqa: F403
