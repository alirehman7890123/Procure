from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from medic.utilities.basepage import BasePage

from medic.utilities.permissions import Permissions


class BaseReportsWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()
        self.main_reports_page = None
        
        
        self.setLayout(self.stacked_layout)

    def _ensure_main_reports_page(self):
        if self.main_reports_page is None:
            from medic.reports.mainpage import MainReportsPage

            self.main_reports_page = MainReportsPage()
            self.stacked_layout.addWidget(self.main_reports_page)
        return self.main_reports_page


    @Permissions.require_permission('reports.view')
    def set_reports_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_main_reports_page())

    def reset_to_default(self):
        if Permissions.has_permission('reports.view'):
            self.stacked_layout.setCurrentWidget(self._ensure_main_reports_page())

    
