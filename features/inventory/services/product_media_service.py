"""Inventory feature bridge for product media services."""

try:
    from medic.services.product_media_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.product_media_service import *  # noqa: F403
