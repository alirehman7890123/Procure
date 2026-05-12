from PySide6.QtWidgets import QStackedLayout

from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BasePurchaseWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()
        self.addpurchase_widget = None
        self.purchaselist_widget = None
        self.purchasedetail_widget = None

        self.setLayout(self.stacked_layout)

    def _ensure_addpurchase_widget(self):
        if self.addpurchase_widget is None:
            from medic.features.purchase.ui.add_purchase import AddPurchaseWidget

            self.addpurchase_widget = AddPurchaseWidget()
            self.addpurchase_widget.invoicelist.clicked.connect(self.set_purchaselist_widget)
            self.stacked_layout.addWidget(self.addpurchase_widget)
        return self.addpurchase_widget

    def _ensure_purchaselist_widget(self):
        if self.purchaselist_widget is None:
            from medic.features.purchase.ui.purchase_list import PurchaseListWidget

            self.purchaselist_widget = PurchaseListWidget()
            self.purchaselist_widget.addpurchase.clicked.connect(self.set_addpurchase_widget)
            self.purchaselist_widget.detailpagesignal.connect(self.set_purchasedetail_widget)
            self.stacked_layout.addWidget(self.purchaselist_widget)
        return self.purchaselist_widget

    def _ensure_purchasedetail_widget(self):
        if self.purchasedetail_widget is None:
            from medic.features.purchase.ui.purchase_detail import PurchaseDetailWidget

            self.purchasedetail_widget = PurchaseDetailWidget()
            self.purchasedetail_widget.invoicelist.clicked.connect(self.set_purchaselist_widget)
            self.stacked_layout.addWidget(self.purchasedetail_widget)
        return self.purchasedetail_widget

    @Permissions.require_permission("purchase.create")
    def set_addpurchase_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_addpurchase_widget())

    @Permissions.require_permission("purchase.view")
    def set_purchaselist_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_purchaselist_widget())

    @Permissions.require_permission("purchase.view")
    def set_purchasedetail_widget(self, purchase_id):
        self._ensure_purchasedetail_widget()
        self.purchasedetail_widget.load_purchase_data(purchase_id)
        self.stacked_layout.setCurrentWidget(self.purchasedetail_widget)

    def reset_to_default(self):
        if Permissions.has_permission("purchase.view"):
            self.stacked_layout.setCurrentWidget(self._ensure_purchaselist_widget())
        elif Permissions.has_permission("purchase.create"):
            self.stacked_layout.setCurrentWidget(self._ensure_addpurchase_widget())
