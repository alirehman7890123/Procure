from PySide6.QtWidgets import QWidget, QStackedLayout

from salesrep.addsalesrep import AddSalesRepWidget
from salesrep.salesreplist import SalesRepListWidget
from salesrep.salesrepdetail import SalesRepDetailWidget
from utilities.basepage import BasePage

from utilities.permissions import Permissions


class SalesRep:
        
    def __init__(self, id, supplier, supplier_id, name, contact, status, creation_date, parent=None):

        super().__init__(parent)    

        self.id = id
        self.supplier = supplier
        self.supplier_id = supplier_id
        self.name = name
        self.contact = contact
        self.status = status
        self.creation_date = creation_date




class BaseSalesRepWidget(BasePage):


    def __init__(self, parent=None):

        super().__init__(parent)


        self.stacked_layout = QStackedLayout()


        # Add Supplier Widget
        self.addsalesrep_widget = AddSalesRepWidget()
        self.addsalesrep_widget.replist.clicked.connect(self.set_salesreplist_widget)


        # List Supplier Widget
        self.salesreplist_widget = SalesRepListWidget()
        self.salesreplist_widget.addsalesrep.clicked.connect(self.set_addsalesrep_widget)
        self.salesreplist_widget.detailpagesignal.connect(self.set_salesrepdetail_widget)


        # Detail Supplier Widget
        self.salesrepdetail_widget = SalesRepDetailWidget()
        self.salesrepdetail_widget.salesreplist.clicked.connect(self.set_salesreplist_widget)


        self.stacked_layout.addWidget(self.addsalesrep_widget)
        self.stacked_layout.addWidget(self.salesreplist_widget)
        self.stacked_layout.addWidget(self.salesrepdetail_widget)



        self.setLayout(self.stacked_layout)




    @Permissions.require_permission('rep.create')
    def set_addsalesrep_widget(self):
        self.stacked_layout.setCurrentWidget(self.addsalesrep_widget)

    
    @Permissions.require_permission('rep.view')
    def set_salesreplist_widget(self):
        self.stacked_layout.setCurrentWidget(self.salesreplist_widget)

    @Permissions.require_permission('rep.view')
    def set_salesrepdetail_widget(self, id):
        self.salesrepdetail_widget.load_salesrep_data(id)
        self.stacked_layout.setCurrentWidget(self.salesrepdetail_widget)


    # 🔑 reset method
    def reset_to_default(self):
        self.stacked_layout.setCurrentWidget(self.salesreplist_widget)








