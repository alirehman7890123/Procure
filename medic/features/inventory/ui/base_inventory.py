from PySide6.QtWidgets import QStackedLayout, QWidget

from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseInventoryWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()
        self.addproduct_widget = None
        self.productlist_widget = None
        self.productdetail_widget = None

        self.setLayout(self.stacked_layout)

    def _ensure_addproduct_widget(self):
        if self.addproduct_widget is None:
            from medic.features.inventory.ui.add_product import AddProductWidget

            self.addproduct_widget = AddProductWidget()
            self.addproduct_widget.productlist.clicked.connect(self.set_productlist_widget)
            self.addproduct_widget.detailpagesignal.connect(self.set_productdetail_widget)
            self.stacked_layout.addWidget(self.addproduct_widget)
        return self.addproduct_widget

    def _ensure_productlist_widget(self):
        if self.productlist_widget is None:
            from medic.features.inventory.ui.product_list import ProductListWidget

            self.productlist_widget = ProductListWidget()
            self.productlist_widget.addproduct.clicked.connect(self.set_addproduct_widget)
            self.productlist_widget.detailpagesignal.connect(self.set_productdetail_widget)
            self.stacked_layout.addWidget(self.productlist_widget)
        return self.productlist_widget

    def _ensure_productdetail_widget(self):
        if self.productdetail_widget is None:
            from medic.features.inventory.ui.product_detail import ProductDetailWidget

            self.productdetail_widget = ProductDetailWidget()
            self.productdetail_widget.productlist.clicked.connect(self.set_productlist_widget)
            self.productdetail_widget.modal_signal.connect(self.set_modal)
            self.stacked_layout.addWidget(self.productdetail_widget)
        return self.productdetail_widget

    def set_modal(self, batch_id):
        self._ensure_productdetail_widget()
        self.productdetail_widget.open_modal_window(batch_id)

    @Permissions.require_permission("product.create")
    def set_addproduct_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_addproduct_widget())

    @Permissions.require_permission("product.view")
    def set_productlist_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_productlist_widget())

    @Permissions.require_permission("product.view")
    def set_productdetail_widget(self, product_id):
        self._ensure_productdetail_widget()
        self.productdetail_widget.load_product_data(product_id)
        self.stacked_layout.setCurrentWidget(self.productdetail_widget)

    def reset_to_default(self):
        if Permissions.has_permission("product.view"):
            self.stacked_layout.setCurrentWidget(self._ensure_productlist_widget())
        elif Permissions.has_permission("product.create"):
            self.stacked_layout.setCurrentWidget(self._ensure_addproduct_widget())
