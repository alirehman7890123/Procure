from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea

from medic.features.purchasereturn.ui.create_purchase_return import AddPurchaseReturnWidget
from medic.features.purchasereturn.ui.purchase_return_list import PurchaseReturnListWidget
from medic.features.purchasereturn.ui.purchase_return_detail import PurchaseReturnDetailWidget
from medic.utilities.basepage import BasePage

from medic.utilities.permissions import Permissions


class BasePurchaseReturnWidget(BasePage):


    def __init__(self, parent=None):

        super().__init__(parent)



        self.stacked_layout = QStackedLayout()


        # Add Supplier Widget
        self.addpurhcase_return_widget = AddPurchaseReturnWidget()
        self.addpurhcase_return_widget.invoicelist.clicked.connect(self.set_purchase_return_list_widget)


        # List Supplier Widget
        self.purchase_return_list_widget = PurchaseReturnListWidget()
        self.purchase_return_list_widget.addPurchaseReturn.clicked.connect(self.set_addpurchase_return_widget)
        self.purchase_return_list_widget.detailpagesignal.connect(self.set_purchase_return_detail_widget)


        # Detail Supplier Widget
        self.purchase_return_detail_widget = PurchaseReturnDetailWidget()
        self.purchase_return_detail_widget.purchasereturnlist.clicked.connect(self.set_purchase_return_list_widget)



        self.stacked_layout.addWidget(self.addpurhcase_return_widget)
        self.stacked_layout.addWidget(self.purchase_return_list_widget)
        self.stacked_layout.addWidget(self.purchase_return_detail_widget)



        self.setLayout(self.stacked_layout)


    @Permissions.require_permission('purchasereturn.create')
    def set_addpurchase_return_widget(self):
        self.stacked_layout.setCurrentWidget(self.addpurhcase_return_widget)

    @Permissions.require_permission('purchasereturn.view')
    def set_purchase_return_list_widget(self):
        self.stacked_layout.setCurrentWidget(self.purchase_return_list_widget)

    @Permissions.require_permission('purchasereturn.view')
    def set_purchase_return_detail_widget(self, id):
        self.purchase_return_detail_widget.load_purchase_data(id)
        self.stacked_layout.setCurrentWidget(self.purchase_return_detail_widget)

    # 🔑 reset method
    def reset_to_default(self):
        if Permissions.has_permission('purchasereturn.view'):
            self.stacked_layout.setCurrentWidget(self.purchase_return_list_widget)
        elif Permissions.has_permission('purchasereturn.create'):
            self.stacked_layout.setCurrentWidget(self.addpurhcase_return_widget)




