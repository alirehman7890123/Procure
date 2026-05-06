from PySide6.QtWidgets import QStackedLayout

from medic.features.customer.ui.add_customer import AddCustomerWidget
from medic.features.customer.ui.customer_list import CustomerListWidget
from medic.features.customer.ui.customer_detail import CustomerDetailWidget
from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseCustomerWidget(BasePage):

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        
        # reference to main window 
        self.controller = controller

        self.stacked_layout = QStackedLayout()

        # Add customer Widget
        self.addcustomer_widget = AddCustomerWidget()
        self.addcustomer_widget.customerlist.clicked.connect(self.set_customerlist_widget)

        # List customer Widget
        self.customerlist_widget = CustomerListWidget()
        self.customerlist_widget.addcustomer.clicked.connect(self.set_addcustomer_widget)
        self.customerlist_widget.detailpagesignal.connect(self.set_customerdetail_widget)

        # Detail customer Widget
        self.customerdetail_widget = CustomerDetailWidget()
        self.customerdetail_widget.customerlist.clicked.connect(self.set_customerlist_widget)
        

        self.stacked_layout.addWidget(self.addcustomer_widget)
        self.stacked_layout.addWidget(self.customerlist_widget)
        self.stacked_layout.addWidget(self.customerdetail_widget)

        self.setLayout(self.stacked_layout)


    @Permissions.require_permission('customer.create')
    def set_addcustomer_widget(self):
        self.stacked_layout.setCurrentWidget(self.addcustomer_widget)

    @Permissions.require_permission('customer.view')
    def set_customerlist_widget(self):
        self.stacked_layout.setCurrentWidget(self.customerlist_widget)

    @Permissions.require_permission('customer.view')
    def set_customerdetail_widget(self, id):
        self.customerdetail_widget.load_customer_transactions(id)
        self.stacked_layout.setCurrentWidget(self.customerdetail_widget)


    # 🔑 reset method
    def reset_to_default(self):
        """Always show customer list when entering the module"""
        if Permissions.has_permission('customer.view'):
            self.stacked_layout.setCurrentWidget(self.customerlist_widget)
        elif Permissions.has_permission('customer.create'):
            self.stacked_layout.setCurrentWidget(self.addcustomer_widget)
        
        
        
