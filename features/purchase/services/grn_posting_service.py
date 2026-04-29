"""Purchase feature GRN-posting-service bridge."""

try:
    from medic.services.grn_posting_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.grn_posting_service import *  # noqa: F403
