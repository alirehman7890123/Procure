from PySide6.QtWidgets import QStackedLayout

from medic.features.purchase.ui.add_purchase import AddPurchaseWidget
from medic.features.purchase.ui.purchase_detail import PurchaseDetailWidget
from medic.features.purchase.ui.purchase_list import PurchaseListWidget
from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BasePurchaseWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()

        self.addpurchase_widget = AddPurchaseWidget()
        self.addpurchase_widget.invoicelist.clicked.connect(self.set_purchaselist_widget)

        self.purchaselist_widget = PurchaseListWidget()
        self.purchaselist_widget.addpurchase.clicked.connect(self.set_addpurchase_widget)
        self.purchaselist_widget.detailpagesignal.connect(self.set_purchasedetail_widget)

        self.purchasedetail_widget = PurchaseDetailWidget()
        self.purchasedetail_widget.invoicelist.clicked.connect(self.set_purchaselist_widget)

        self.stacked_layout.addWidget(self.addpurchase_widget)
        self.stacked_layout.addWidget(self.purchaselist_widget)
        self.stacked_layout.addWidget(self.purchasedetail_widget)

        self.setLayout(self.stacked_layout)

    @Permissions.require_permission("purchase.create")
    def set_addpurchase_widget(self):
        self.stacked_layout.setCurrentWidget(self.addpurchase_widget)

    @Permissions.require_permission("purchase.view")
    def set_purchaselist_widget(self):
        self.stacked_layout.setCurrentWidget(self.purchaselist_widget)

    @Permissions.require_permission("purchase.view")
    def set_purchasedetail_widget(self, purchase_id):
        self.purchasedetail_widget.load_purchase_data(purchase_id)
        self.stacked_layout.setCurrentWidget(self.purchasedetail_widget)

    def reset_to_default(self):
        if Permissions.has_permission("purchase.view"):
            self.stacked_layout.setCurrentWidget(self.purchaselist_widget)
        elif Permissions.has_permission("purchase.create"):
            self.stacked_layout.setCurrentWidget(self.addpurchase_widget)
