"""Purchase feature GRN-draft-service bridge."""

try:
    from medic.services.grn_draft_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.grn_draft_service import *  # noqa: F403
