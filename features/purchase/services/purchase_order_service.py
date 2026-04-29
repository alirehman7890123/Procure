"""Purchase feature purchase-order-service bridge."""

try:
    from medic.services.purchase_order_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.purchase_order_service import *  # noqa: F403
