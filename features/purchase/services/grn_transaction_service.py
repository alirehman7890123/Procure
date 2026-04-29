"""Purchase feature GRN-transaction-service bridge."""

try:
    from medic.services.grn_transaction_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.grn_transaction_service import *  # noqa: F403
