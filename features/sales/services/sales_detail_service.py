"""Sales feature bridge for sales detail helpers."""

try:
    from medic.services.sales_detail_service import *  # noqa: F403
except ModuleNotFoundError:
    from services.sales_detail_service import *  # noqa: F403
