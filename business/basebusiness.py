from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from business.business import BusinessWidget
from utilities.basepage import BasePage
from utilities.permissions import Permissions


class BaseBusinessWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)
        

        self.stacked_layout = QStackedLayout()

        self.business_widget = BusinessWidget()
        
        self.stacked_layout.addWidget(self.business_widget)
        
        self.setLayout(self.stacked_layout)



    
        
        
        