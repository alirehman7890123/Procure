"""Finance feature UI exports."""

from . import financial_close_list, financial_close_page, financial_quarter_summary

# Expose submodules for compatibility with patch targets like
# `features.finance.ui.financial_close_page.*`.
financial_close_page = financial_close_page
financial_close_list = financial_close_list
financial_quarter_summary = financial_quarter_summary

__all__ = [
    "AddExpenseWidget",
    "BaseExpenseWidget",
    "BaseFinancialCloseWidget",
    "BaseTransactionWidget",
    "CreateCustomerTransactionWidget",
    "CreateSupplierTransactionWidget",
    "CustomerTransactionDetailWidget",
    "CustomerTransactionListWidget",
    "CustomerTransactionWidget",
    "DailySession",
    "ExpenseDetailWidget",
    "ExpenseListWidget",
    "FinancialClosingListPage",
    "FinancialClosingPage",
    "FinancialQuarterSummaryPage",
    "SupplierTransactionDetailWidget",
    "SupplierTransactionListWidget",
    "SupplierTransactionWidget",
    "MainTransactionWidget",
]
