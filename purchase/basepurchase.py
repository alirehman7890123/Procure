from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from purchase.addpurchase import AddPurchaseWidget
from purchase.purchaselist import PurchaseListWidget
from purchase.purchasedetail import PurchaseDetailWidget
from utilities.basepage import BasePage

from utilities.permissions import Permissions

class Purchase:
        
    def __init__(self, id, supplier, sellerinvoice, salesrep, address, status, creation_date,reg_no, parent=None):

        super().__init__(parent)

        self.id = id
        self.supplier = supplier
        self.sellerinvoice = sellerinvoice
        self.salesrep = salesrep
        self.address = address
        self.status = status
        self.creation_date = creation_date
        self.reg_no = reg_no


class PurchaseItems:
    
    def __init__(self, id, invoice, medicine, qty, unitcost, totalcost, parent=None):

        super().__init__(parent)

        self.id = id
        self.invoice = invoice
        self.medicine = medicine
        self.qty = qty
        self.unitcost = unitcost
        self.totalcost = totalcost
        
        


class BasePurchaseWidget(BasePage):


    def __init__(self, parent=None):

        super().__init__(parent)


        self.stacked_layout = QStackedLayout()


        # Add Supplier Widget
        self.addpurchase_widget = AddPurchaseWidget()
        self.addpurchase_widget.invoicelist.clicked.connect(self.set_purchaselist_widget)


        # List Supplier Widget
        self.purchaselist_widget = PurchaseListWidget()
        self.purchaselist_widget.addpurchase.clicked.connect(self.set_addpurchase_widget)
        self.purchaselist_widget.detailpagesignal.connect(self.set_purchasedetail_widget)

        # Detail Supplier Widget
        self.purchasedetail_widget = PurchaseDetailWidget()
        self.purchasedetail_widget.invoicelist.clicked.connect(self.set_purchaselist_widget)


        self.stacked_layout.addWidget(self.addpurchase_widget)
        self.stacked_layout.addWidget(self.purchaselist_widget)
        self.stacked_layout.addWidget(self.purchasedetail_widget)



        self.setLayout(self.stacked_layout)


    @Permissions.require_permission('purchase.create')
    def set_addpurchase_widget(self):
        self.stacked_layout.setCurrentWidget(self.addpurchase_widget)

    
    @Permissions.require_permission('purchase.view')
    def set_purchaselist_widget(self):
        self.stacked_layout.setCurrentWidget(self.purchaselist_widget)


    @Permissions.require_permission('purchase.view')
    def set_purchasedetail_widget(self, id):
        self.purchasedetail_widget.load_purchase_data(id)
        self.stacked_layout.setCurrentWidget(self.purchasedetail_widget)

    # 🔑 reset method
    def reset_to_default(self):
        self.stacked_layout.setCurrentWidget(self.addpurchase_widget)






