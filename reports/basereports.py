from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from reports.mainpage import MainReportsPage
from utilities.basepage import BasePage

from utilities.permissions import Permissions


class BaseReportsWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()

        self.main_reports_page = MainReportsPage()
        self.stacked_layout.addWidget(self.main_reports_page)
        
        
        self.setLayout(self.stacked_layout)


    @Permissions.require_permission('reports.view')
    def set_reports_widget(self):
        print("Setting reports widget")
        self.stacked_layout.setCurrentWidget(self.main_reports_page)

    