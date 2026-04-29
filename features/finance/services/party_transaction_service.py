"""Finance feature transaction-service bridge."""

try:
    from medic.services.party_transaction_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.party_transaction_service import *  # noqa: F403
