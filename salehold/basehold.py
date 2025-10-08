from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from salehold.saleholdlist import SaleHoldListWidget
from salehold.salehold_detail import HoldSalesDetailWidget
from utilities.basepage import BasePage


class BaseHoldSalesWidget(BasePage):


    def __init__(self, controller, parent=None):

        super().__init__(parent)

        self.controller = controller


        self.stacked_layout = QStackedLayout()
        

        # List Supplier Widget
        self.saleholdlist_widget = SaleHoldListWidget()
        self.saleholdlist_widget.holddetailsignal.connect(self.set_salesdetail_widget)

        # Detail Supplier Widget
        self.holdsalesdetail_widget = HoldSalesDetailWidget()
        self.holdsalesdetail_widget.holdinglist.clicked.connect(self.set_saleslist_widget)
        self.holdsalesdetail_widget.reload_order_signal.connect(self.controller.base_sales.set_holding_sales_widget)


        self.stacked_layout.addWidget(self.saleholdlist_widget)
        self.stacked_layout.addWidget(self.holdsalesdetail_widget)


        self.setLayout(self.stacked_layout)



    
    def set_saleslist_widget(self):
        self.stacked_layout.setCurrentWidget(self.saleholdlist_widget)


    def set_salesdetail_widget(self, id):
        id = int(id)
        self.holdsalesdetail_widget.load_holdsales_data(id)
        self.stacked_layout.setCurrentWidget(self.holdsalesdetail_widget)









