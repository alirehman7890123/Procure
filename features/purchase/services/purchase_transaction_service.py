"""Purchase feature purchase-transaction-service bridge."""

try:
    from medic.services.purchase_transaction_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.purchase_transaction_service import *  # noqa: F403
