from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from sales.createsales import CreateSalesWidget
from sales.receiptlist import ReceiptListWidget
from sales.salesdetail import SalesDetailWidget
from medic.utilities.basepage import BasePage

from medic.utilities.permissions import Permissions


class BaseSalesWidget(BasePage):


    def __init__(self, controller, parent=None):

        super().__init__(parent)

        # reference to main window 
        self.controller = controller


        self.stacked_layout = QStackedLayout()
        self.createsales_widget = None
        self.receiptlist_widget = None
        self.salesdetail_widget = None


        self.setLayout(self.stacked_layout)

    def _ensure_createsales_widget(self):
        if self.createsales_widget is None:
            self.createsales_widget = CreateSalesWidget()
            self.createsales_widget.invoicelist.clicked.connect(self.set_saleslist_widget)
            self.stacked_layout.addWidget(self.createsales_widget)
        return self.createsales_widget

    def _ensure_receiptlist_widget(self):
        if self.receiptlist_widget is None:
            self.receiptlist_widget = ReceiptListWidget()
            self.receiptlist_widget.addinvoice.clicked.connect(self.set_createsales_widget)
            self.receiptlist_widget.salesdetailsignal.connect(self.set_salesdetail_widget)
            self.stacked_layout.addWidget(self.receiptlist_widget)
        return self.receiptlist_widget

    def _ensure_salesdetail_widget(self):
        if self.salesdetail_widget is None:
            self.salesdetail_widget = SalesDetailWidget()
            self.salesdetail_widget.receiptlist.clicked.connect(self.set_saleslist_widget)
            self.stacked_layout.addWidget(self.salesdetail_widget)
        return self.salesdetail_widget


    @Permissions.require_permission('sales.create')
    def set_createsales_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_createsales_widget())

    
    @Permissions.require_permission('sales.view')
    def set_saleslist_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_receiptlist_widget())


    @Permissions.require_permission('sales.view')
    def set_salesdetail_widget(self, id):
        id = int(id)
        self._ensure_salesdetail_widget()
        self.salesdetail_widget.load_sales_data(id)
        self.stacked_layout.setCurrentWidget(self.salesdetail_widget)

    
    def set_holding_sales_widget(self, id):

        if self.controller is None:
            raise ValueError("Controller (MainWindow) must be provided to BaseSalesWidget")

        print("Reloading on hold pending sales order")
        id = int(id)
        print("Id is: ", id)
        
        self._ensure_createsales_widget()
        self.createsales_widget.reload_hold_order(id)
        
        self.controller.main_content_layout.setCurrentWidget(self)
        self.stacked_layout.setCurrentWidget(self.createsales_widget)
        
        
    def reset_to_default(self):
        if Permissions.has_permission('sales.view'):
            self.stacked_layout.setCurrentWidget(self._ensure_receiptlist_widget())
        elif Permissions.has_permission('sales.create'):
            self.stacked_layout.setCurrentWidget(self._ensure_createsales_widget())




