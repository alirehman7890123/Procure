from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from business.business import BusinessWidget
from business.discount_settings import DiscountSettingsWidget
from business.tax_settings import TaxSettingsWidget
from business.theme_settings import ThemeSettingsWidget
from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseBusinessWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)
        

        self.stacked_layout = QStackedLayout()
        self.business_widget = None
        self.discount_settings_widget = None
        self.tax_settings_widget = None
        self.theme_settings_widget = None
        
        self.setLayout(self.stacked_layout)

    def _ensure_business_widget(self):
        if self.business_widget is None:
            self.business_widget = BusinessWidget()
            self.business_widget.theme_settings_requested.connect(self.set_theme_settings_widget)
            self.business_widget.discount_settings_requested.connect(self.set_discount_settings_widget)
            self.business_widget.tax_settings_requested.connect(self.set_tax_settings_widget)
            self.stacked_layout.addWidget(self.business_widget)
        return self.business_widget

    def _ensure_theme_settings_widget(self):
        if self.theme_settings_widget is None:
            self.theme_settings_widget = ThemeSettingsWidget()
            self.theme_settings_widget.back_requested.connect(self.set_business_widget)
            self.stacked_layout.addWidget(self.theme_settings_widget)
        return self.theme_settings_widget

    def _ensure_discount_settings_widget(self):
        if self.discount_settings_widget is None:
            self.discount_settings_widget = DiscountSettingsWidget()
            self.discount_settings_widget.back_requested.connect(self.set_business_widget)
            self.stacked_layout.addWidget(self.discount_settings_widget)
        return self.discount_settings_widget

    def _ensure_tax_settings_widget(self):
        if self.tax_settings_widget is None:
            self.tax_settings_widget = TaxSettingsWidget()
            self.tax_settings_widget.back_requested.connect(self.set_business_widget)
            self.stacked_layout.addWidget(self.tax_settings_widget)
        return self.tax_settings_widget

    @Permissions.require_permission('business.view')
    def set_business_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_business_widget())

    @Permissions.require_permission('business.view')
    def set_theme_settings_widget(self):
        self._ensure_business_widget()
        self._ensure_theme_settings_widget()
        self.theme_settings_widget.load_theme_settings()
        self.stacked_layout.setCurrentWidget(self.theme_settings_widget)

    @Permissions.require_permission('business.view')
    def set_discount_settings_widget(self):
        self._ensure_business_widget()
        self._ensure_discount_settings_widget()
        self.discount_settings_widget.load_discount_groups()
        self.stacked_layout.setCurrentWidget(self.discount_settings_widget)

    @Permissions.require_permission('business.view')
    def set_tax_settings_widget(self):
        self._ensure_business_widget()
        self._ensure_tax_settings_widget()
        self.tax_settings_widget.load_tax_groups()
        self.stacked_layout.setCurrentWidget(self.tax_settings_widget)

    def reset_to_default(self):
        if Permissions.has_permission('business.view'):
            self.stacked_layout.setCurrentWidget(self._ensure_business_widget())



    
        
        
        
