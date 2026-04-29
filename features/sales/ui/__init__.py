"""Sales feature UI exports."""

from .base_sales import BaseSalesWidget
from .create_sales import CreateSalesWidget
from .receipt_list import ReceiptListWidget
from .sales_detail import SalesDetailWidget

__all__ = [
    "BaseSalesWidget",
    "CreateSalesWidget",
    "ReceiptListWidget",
    "SalesDetailWidget",
]
