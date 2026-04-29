from PySide6.QtWidgets import QStackedLayout

from medic.features.finance.ui.financial_close_list import FinancialClosingListPage
from medic.features.finance.ui.financial_close_page import FinancialClosingPage
from medic.features.finance.ui.financial_quarter_summary import FinancialQuarterSummaryPage
from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseFinancialCloseWidget(BasePage):
    def __init__(self, pro_enabled=True, parent=None):
        super().__init__(parent)
        self.pro_enabled = bool(pro_enabled)

        self.stacked_layout = QStackedLayout()
        self.financial_close_list_page = None
        self.main_financial_close_page = None
        self.financial_quarter_summary_page = None
        self.setLayout(self.stacked_layout)

    def _ensure_financial_close_list_page(self):
        if self.financial_close_list_page is None:
            self.financial_close_list_page = FinancialClosingListPage(pro_enabled=self.pro_enabled)
            self.financial_close_list_page.show_close_workflow.connect(self.set_financial_close_create_widget)
            self.financial_close_list_page.show_quarter_summary.connect(self.set_financial_quarter_summary_widget)
            self.stacked_layout.addWidget(self.financial_close_list_page)
        return self.financial_close_list_page

    def _ensure_main_financial_close_page(self):
        if self.main_financial_close_page is None:
            self.main_financial_close_page = FinancialClosingPage(pro_enabled=self.pro_enabled)
            self.main_financial_close_page.show_closing_list.connect(self.set_financial_close_widget)
            self.main_financial_close_page.show_quarter_summary.connect(self.set_financial_quarter_summary_widget)
            self.stacked_layout.addWidget(self.main_financial_close_page)
        return self.main_financial_close_page

    def _ensure_financial_quarter_summary_page(self):
        if self.financial_quarter_summary_page is None:
            self.financial_quarter_summary_page = FinancialQuarterSummaryPage()
            self.financial_quarter_summary_page.back_to_history.connect(self.set_financial_close_widget)
            self.stacked_layout.addWidget(self.financial_quarter_summary_page)
        return self.financial_quarter_summary_page

    @Permissions.require_permission("financialclose.view")
    def set_financial_close_widget(self):
        page = self._ensure_financial_close_list_page()
        if hasattr(page, "refresh_all_data"):
            page.refresh_all_data()
        self.stacked_layout.setCurrentWidget(page)

    @Permissions.require_permission("financialclose.view")
    def set_financial_close_create_widget(self):
        page = self._ensure_main_financial_close_page()
        if hasattr(page, "reset_to_default"):
            page.reset_to_default()
        self.stacked_layout.setCurrentWidget(page)

    @Permissions.require_permission("financialclose.view")
    def set_financial_quarter_summary_widget(self, quarter_label):
        page = self._ensure_financial_quarter_summary_page()
        if hasattr(page, "load_quarter_summary") and not page.load_quarter_summary(quarter_label):
            return
        self.stacked_layout.setCurrentWidget(page)

    def reset_to_default(self):
        if Permissions.has_permission("financialclose.view"):
            page = self._ensure_financial_close_list_page()
            self.stacked_layout.setCurrentWidget(page)
            if hasattr(page, "reset_to_default"):
                page.reset_to_default()
