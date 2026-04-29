"""Sales feature bridge for product media helpers."""

try:
    from medic.services.product_media_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.product_media_service import *  # noqa: F403
