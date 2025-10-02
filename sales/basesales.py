from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from sales.createsales import CreateSalesWidget
from sales.receiptlist import ReceiptListWidget
from sales.salesdetail import SalesDetailWidget
from utilities.basepage import BasePage

from utilities.permissions import Permissions


class BaseSalesWidget(BasePage):


    def __init__(self, controller, parent=None):

        super().__init__(parent)

        # reference to main window 
        self.controller = controller


        self.stacked_layout = QStackedLayout()


        # Add Supplier Widget
        self.createsales_widget = CreateSalesWidget()
        self.createsales_widget.invoicelist.clicked.connect(self.set_saleslist_widget)


        # List Supplier Widget
        self.receiptlist_widget = ReceiptListWidget()
        self.receiptlist_widget.addinvoice.clicked.connect(self.set_createsales_widget)
        self.receiptlist_widget.salesdetailsignal.connect(self.set_salesdetail_widget)


        # Detail Supplier Widget
        self.salesdetail_widget = SalesDetailWidget()
        self.salesdetail_widget.receiptlist.clicked.connect(self.set_saleslist_widget)


        self.stacked_layout.addWidget(self.createsales_widget)
        self.stacked_layout.addWidget(self.receiptlist_widget)
        self.stacked_layout.addWidget(self.salesdetail_widget)


        self.setLayout(self.stacked_layout)


    @Permissions.require_permission('sales.create')
    def set_createsales_widget(self):
        self.stacked_layout.setCurrentWidget(self.createsales_widget)

    
    @Permissions.require_permission('sales.view')
    def set_saleslist_widget(self):
        self.stacked_layout.setCurrentWidget(self.receiptlist_widget)


    @Permissions.require_permission('sales.view')
    def set_salesdetail_widget(self, id):
        id = int(id)
        self.salesdetail_widget.load_sales_data(id)
        self.stacked_layout.setCurrentWidget(self.salesdetail_widget)

    
    def set_holding_sales_widget(self, id):

        if self.controller is None:
            raise ValueError("Controller (MainWindow) must be provided to BaseSalesWidget")

        print("Reloading on hold pending sales order")
        id = int(id)
        print("Id is: ", id)
        
        self.createsales_widget.reload_hold_order(id)
        
        self.controller.main_content_layout.setCurrentWidget(self)
        self.stacked_layout.setCurrentWidget(self.createsales_widget)
        
        
    def reset_to_default(self):
        self.stacked_layout.setCurrentWidget(self.createsales_widget)






