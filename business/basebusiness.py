from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from business.business import BusinessWidget
from business.discount_settings import DiscountSettingsWidget
from business.tax_settings import TaxSettingsWidget
from business.theme_settings import ThemeSettingsWidget
from utilities.basepage import BasePage
from utilities.permissions import Permissions


class BaseBusinessWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)
        

        self.stacked_layout = QStackedLayout()

        self.business_widget = BusinessWidget()
        self.discount_settings_widget = DiscountSettingsWidget()
        self.tax_settings_widget = TaxSettingsWidget()
        self.theme_settings_widget = ThemeSettingsWidget()
        self.business_widget.theme_settings_requested.connect(self.set_theme_settings_widget)
        self.business_widget.discount_settings_requested.connect(self.set_discount_settings_widget)
        self.business_widget.tax_settings_requested.connect(self.set_tax_settings_widget)
        self.theme_settings_widget.back_requested.connect(self.set_business_widget)
        self.discount_settings_widget.back_requested.connect(self.set_business_widget)
        self.tax_settings_widget.back_requested.connect(self.set_business_widget)
        
        self.stacked_layout.addWidget(self.business_widget)
        self.stacked_layout.addWidget(self.theme_settings_widget)
        self.stacked_layout.addWidget(self.discount_settings_widget)
        self.stacked_layout.addWidget(self.tax_settings_widget)
        
        self.setLayout(self.stacked_layout)

    @Permissions.require_permission('business.view')
    def set_business_widget(self):
        self.stacked_layout.setCurrentWidget(self.business_widget)

    @Permissions.require_permission('business.view')
    def set_theme_settings_widget(self):
        self.theme_settings_widget.load_theme_settings()
        self.stacked_layout.setCurrentWidget(self.theme_settings_widget)

    @Permissions.require_permission('business.view')
    def set_discount_settings_widget(self):
        self.discount_settings_widget.load_discount_groups()
        self.stacked_layout.setCurrentWidget(self.discount_settings_widget)

    @Permissions.require_permission('business.view')
    def set_tax_settings_widget(self):
        self.tax_settings_widget.load_tax_groups()
        self.stacked_layout.setCurrentWidget(self.tax_settings_widget)

    def reset_to_default(self):
        if Permissions.has_permission('business.view'):
            self.stacked_layout.setCurrentWidget(self.business_widget)



    
        
        
        
