"""Purchase feature purchase-items-service bridge."""

try:
    from medic.services.purchase_items_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.purchase_items_service import *  # noqa: F403
