from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from medic.features.salesreturn.ui.create_sales_return import AddSalesReturnWidget
from medic.features.salesreturn.ui.sales_return_list import SalesReturnListWidget
from medic.features.salesreturn.ui.sales_return_detail import SalesReturnDetailWidget
from medic.utilities.basepage import BasePage

from medic.utilities.permissions import Permissions

class BaseSalesReturnWidget(BasePage):


    def __init__(self, parent=None):

        super().__init__(parent)



        self.stacked_layout = QStackedLayout()


        # Add Supplier Widget
        self.addsales_return_widget = AddSalesReturnWidget()
        self.addsales_return_widget.invoicelist.clicked.connect(self.set_sales_return_list_widget)


        # List Supplier Widget
        self.sales_return_list_widget = SalesReturnListWidget()
        self.sales_return_list_widget.addSalesReturn.clicked.connect(self.set_addsales_return_widget)
        self.sales_return_list_widget.detailpagesignal.connect(self.set_sales_return_detail_widget)

        # Detail Supplier Widget
        self.sales_return_detail_widget = SalesReturnDetailWidget()
        self.sales_return_detail_widget.SalesReturnlist.clicked.connect(self.set_sales_return_list_widget)



        self.stacked_layout.addWidget(self.addsales_return_widget)
        self.stacked_layout.addWidget(self.sales_return_list_widget)
        self.stacked_layout.addWidget(self.sales_return_detail_widget)


        self.setLayout(self.stacked_layout)



    @Permissions.require_permission('salesreturn.create')
    def set_addsales_return_widget(self):
        self.stacked_layout.setCurrentWidget(self.addsales_return_widget)

    
    @Permissions.require_permission('salesreturn.view')
    def set_sales_return_list_widget(self):
        self.stacked_layout.setCurrentWidget(self.sales_return_list_widget)


    @Permissions.require_permission('salesreturn.view')
    def set_sales_return_detail_widget(self, id):
        
        self.sales_return_detail_widget.load_sales_data(id)
        self.stacked_layout.setCurrentWidget(self.sales_return_detail_widget)


    # 🔑 reset method
    def reset_to_default(self):
        if Permissions.has_permission('salesreturn.view'):
            self.stacked_layout.setCurrentWidget(self.sales_return_list_widget)
        elif Permissions.has_permission('salesreturn.create'):
            self.stacked_layout.setCurrentWidget(self.addsales_return_widget)
