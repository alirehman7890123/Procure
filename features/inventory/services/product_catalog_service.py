"""Inventory feature bridge for product catalog services."""

try:
    from medic.services.product_catalog_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.product_catalog_service import *  # noqa: F403
