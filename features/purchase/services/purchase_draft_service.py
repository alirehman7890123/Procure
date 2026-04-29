"""Purchase feature purchase-draft-service bridge."""

try:
    from medic.services.purchase_draft_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.purchase_draft_service import *  # noqa: F403
