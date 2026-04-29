from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseDashboardWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # reference to main window 

        self.stacked_layout = QStackedLayout()

        self.dashboard_widget = None
        self.welcome_widget = None
        self.daily_session_widget = None

        self.setLayout(self.stacked_layout)
        self._ensure_dashboard_widget()
        self._ensure_welcome_widget()

    def _ensure_dashboard_widget(self):
        if self.dashboard_widget is None:
            from medic.dashboard.dashboard import DashboardWidget

            self.dashboard_widget = DashboardWidget()
            self.dashboard_widget.session_history_btn.clicked.connect(self.set_daily_session_widget)
            self.stacked_layout.addWidget(self.dashboard_widget)
        return self.dashboard_widget

    def _ensure_welcome_widget(self):
        if self.welcome_widget is None:
            from medic.dashboard.welcome import WelcomeWidget

            self.welcome_widget = WelcomeWidget()
            self.stacked_layout.addWidget(self.welcome_widget)
        return self.welcome_widget


    @Permissions.require_permission('dashboard')
    def set_dashboard_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_dashboard_widget())

   
    def set_welcome_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_welcome_widget())
        
        
    @Permissions.require_permission('dashboard')
    def set_daily_session_widget(self):
        if self.daily_session_widget is None:
            from medic.features.finance.ui.daily_session import DailySession

            self.daily_session_widget = DailySession()
            self.daily_session_widget.dashboard_btn.clicked.connect(self.set_dashboard_widget)
            self.stacked_layout.addWidget(self.daily_session_widget)
        self.stacked_layout.setCurrentWidget(self.daily_session_widget)
        

    # 🔑 reset method
    def reset_to_default(self):
        if Permissions.has_permission('dashboard'):
            self.stacked_layout.setCurrentWidget(self._ensure_dashboard_widget())
        else:
            self.stacked_layout.setCurrentWidget(self._ensure_welcome_widget())
        
        
        
