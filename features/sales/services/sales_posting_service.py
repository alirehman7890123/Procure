"""Sales feature bridge for sales posting helpers."""

try:
    from medic.services.sales_posting_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.sales_posting_service import *  # noqa: F403
