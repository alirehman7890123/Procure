"""Purchase feature purchase-posting-service bridge."""

try:
    from medic.services.purchase_posting_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.purchase_posting_service import *  # noqa: F403
