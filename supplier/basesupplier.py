from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea, QSizePolicy, QApplication, QMessageBox

from supplier.addsupplier import AddSupplierWidget
from supplier.supplierlist import SupplierListWidget
from supplier.supplierdetail import SupplierDetailWidget

from utilities.basepage import BasePage
from utilities.permissions import Permissions


class BaseSupplierWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)


        self.stacked_layout = QStackedLayout()
        self.stacked_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_layout.setSpacing(0)
        


        # Add supplier Widget
        self.addsupplier_widget = AddSupplierWidget()
        self.addsupplier_widget.supplierlist.clicked.connect(self.set_supplierlist_widget)

        # List supplier Widget
        self.supplierlist_widget = SupplierListWidget()
        self.supplierlist_widget.addsupplier.clicked.connect(self.set_addsupplier_widget)
        self.supplierlist_widget.detailpagesignal.connect(self.set_supplierdetail_widget)

        # Detail supplier Widget
        self.supplierdetail_widget = SupplierDetailWidget()
        self.supplierdetail_widget.supplierlist.clicked.connect(self.set_supplierlist_widget)

        self.stacked_layout.addWidget(self.addsupplier_widget)
        self.stacked_layout.addWidget(self.supplierlist_widget)
        self.stacked_layout.addWidget(self.supplierdetail_widget)

        self.setLayout(self.stacked_layout)


    @Permissions.require_permission('supplier.create')
    def set_addsupplier_widget(self):
        self.stacked_layout.setCurrentWidget(self.addsupplier_widget)


    @Permissions.require_permission('supplier.view')
    def set_supplierlist_widget(self):
        self.stacked_layout.setCurrentWidget(self.supplierlist_widget)


    @Permissions.require_permission('supplier.view')
    def set_supplierdetail_widget(self, id):
        self.supplierdetail_widget.load_supplier_data(id)
        self.stacked_layout.setCurrentWidget(self.supplierdetail_widget)


    # 🔑 reset method
    def reset_to_default(self):
        self.stacked_layout.setCurrentWidget(self.supplierlist_widget)