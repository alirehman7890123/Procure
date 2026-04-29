from PySide6.QtWidgets import QStackedLayout

from medic.utilities.basepage import BasePage
from medic.utilities.permissions import Permissions


class BaseTransactionWidget(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()
        self.maintransaction_widget = None
        self.supplier_transaction_widget = None
        self.customer_transaction_widget = None
        self.create_supplier_transaction_widget = None
        self.create_customer_transaction_widget = None
        self.supplier_transaction_list_widget = None
        self.customer_transaction_list_widget = None
        self.customer_transaction_detail_widget = None
        self.supplier_transaction_detail_widget = None

        self.setLayout(self.stacked_layout)

    def _ensure_maintransaction_widget(self):
        if self.maintransaction_widget is None:
            from medic.features.finance.ui.transaction_hub import MainTransactionWidget

            self.maintransaction_widget = MainTransactionWidget()
            self.maintransaction_widget.supplier_transactions_button.clicked.connect(self.set_suppliertransaction_widget)
            self.maintransaction_widget.customer_transactions_button.clicked.connect(self.set_customertransaction_widget)
            self.stacked_layout.addWidget(self.maintransaction_widget)
        return self.maintransaction_widget

    def _ensure_supplier_transaction_widget(self):
        if self.supplier_transaction_widget is None:
            from medic.features.finance.ui.supplier_transactions import SupplierTransactionWidget

            self.supplier_transaction_widget = SupplierTransactionWidget()
            self.supplier_transaction_widget.transaction_page_signal.connect(self.set_create_supplier_transaction_widget)
            self.supplier_transaction_widget.transactionpage.clicked.connect(self.set_maintransaction_widget)
            self.stacked_layout.addWidget(self.supplier_transaction_widget)
        return self.supplier_transaction_widget

    def _ensure_customer_transaction_widget(self):
        if self.customer_transaction_widget is None:
            from medic.features.finance.ui.customer_transactions import CustomerTransactionWidget

            self.customer_transaction_widget = CustomerTransactionWidget()
            self.customer_transaction_widget.transaction_page_signal.connect(self.set_create_customer_transaction_widget)
            self.customer_transaction_widget.transactionpage.clicked.connect(self.set_maintransaction_widget)
            self.stacked_layout.addWidget(self.customer_transaction_widget)
        return self.customer_transaction_widget

    def _ensure_create_supplier_transaction_widget(self):
        if self.create_supplier_transaction_widget is None:
            from medic.features.finance.ui.create_supplier_transaction import CreateSupplierTransactionWidget

            self.create_supplier_transaction_widget = CreateSupplierTransactionWidget()
            self.create_supplier_transaction_widget.transactionlist.clicked.connect(self.set_supplier_transaction_list_widget)
            self.stacked_layout.addWidget(self.create_supplier_transaction_widget)
        return self.create_supplier_transaction_widget

    def _ensure_create_customer_transaction_widget(self):
        if self.create_customer_transaction_widget is None:
            from medic.features.finance.ui.create_customer_transaction import CreateCustomerTransactionWidget

            self.create_customer_transaction_widget = CreateCustomerTransactionWidget()
            self.create_customer_transaction_widget.transactionlist.clicked.connect(self.set_customer_transaction_list_widget)
            self.stacked_layout.addWidget(self.create_customer_transaction_widget)
        return self.create_customer_transaction_widget

    def _ensure_supplier_transaction_list_widget(self):
        if self.supplier_transaction_list_widget is None:
            from medic.features.finance.ui.supplier_transaction_list import SupplierTransactionListWidget

            self.supplier_transaction_list_widget = SupplierTransactionListWidget()
            self.supplier_transaction_list_widget.transaction_list.clicked.connect(self.set_suppliertransaction_widget)
            self.supplier_transaction_list_widget.transaction_detail_signal.connect(self.set_supplier_transaction_detail_widget)
            self.stacked_layout.addWidget(self.supplier_transaction_list_widget)
        return self.supplier_transaction_list_widget

    def _ensure_customer_transaction_list_widget(self):
        if self.customer_transaction_list_widget is None:
            from medic.features.finance.ui.customer_transaction_list import CustomerTransactionListWidget

            self.customer_transaction_list_widget = CustomerTransactionListWidget()
            self.customer_transaction_list_widget.transaction_list.clicked.connect(self.set_customertransaction_widget)
            self.customer_transaction_list_widget.transaction_detail_signal.connect(self.set_customer_transaction_detail_widget)
            self.stacked_layout.addWidget(self.customer_transaction_list_widget)
        return self.customer_transaction_list_widget

    def _ensure_customer_transaction_detail_widget(self):
        if self.customer_transaction_detail_widget is None:
            from medic.features.finance.ui.customer_transaction_detail import CustomerTransactionDetailWidget

            self.customer_transaction_detail_widget = CustomerTransactionDetailWidget()
            self.customer_transaction_detail_widget.transactionlist.clicked.connect(self.set_customer_transaction_list_widget)
            self.stacked_layout.addWidget(self.customer_transaction_detail_widget)
        return self.customer_transaction_detail_widget

    def _ensure_supplier_transaction_detail_widget(self):
        if self.supplier_transaction_detail_widget is None:
            from medic.features.finance.ui.supplier_transaction_detail import SupplierTransactionDetailWidget

            self.supplier_transaction_detail_widget = SupplierTransactionDetailWidget()
            self.supplier_transaction_detail_widget.transactionlist.clicked.connect(self.set_suppliertransaction_widget)
            self.stacked_layout.addWidget(self.supplier_transaction_detail_widget)
        return self.supplier_transaction_detail_widget

    @Permissions.require_permission("transactions.view")
    def set_maintransaction_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_maintransaction_widget())

    @Permissions.require_permission("transactions.view")
    def set_suppliertransaction_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_supplier_transaction_widget())

    @Permissions.require_permission("transactions.view")
    def set_customertransaction_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_customer_transaction_widget())

    @Permissions.require_permission("transactions.create")
    def set_create_supplier_transaction_widget(self, supplier_id):
        self._ensure_create_supplier_transaction_widget()
        self.create_supplier_transaction_widget.load_data(supplier_id)
        self.stacked_layout.setCurrentWidget(self.create_supplier_transaction_widget)

    @Permissions.require_permission("transactions.create")
    def set_create_customer_transaction_widget(self, customer_id):
        self._ensure_create_customer_transaction_widget()
        self.create_customer_transaction_widget.load_data(customer_id)
        self.stacked_layout.setCurrentWidget(self.create_customer_transaction_widget)

    @Permissions.require_permission("transactions.view")
    def set_supplier_transaction_list_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_supplier_transaction_list_widget())

    @Permissions.require_permission("transactions.view")
    def set_customer_transaction_list_widget(self):
        self.stacked_layout.setCurrentWidget(self._ensure_customer_transaction_list_widget())

    @Permissions.require_permission("transactions.view")
    def set_customer_transaction_detail_widget(self, transaction_id):
        self._ensure_customer_transaction_detail_widget()
        self.customer_transaction_detail_widget.load_data(transaction_id)
        self.stacked_layout.setCurrentWidget(self.customer_transaction_detail_widget)

    @Permissions.require_permission("transactions.view")
    def set_supplier_transaction_detail_widget(self, transaction_id):
        self._ensure_supplier_transaction_detail_widget()
        self.supplier_transaction_detail_widget.load_data(transaction_id)
        self.stacked_layout.setCurrentWidget(self.supplier_transaction_detail_widget)

    def reset_to_default(self):
        if Permissions.has_permission("transactions.view"):
            self.stacked_layout.setCurrentWidget(self._ensure_maintransaction_widget())
        elif Permissions.has_permission("transactions.create"):
            self.stacked_layout.setCurrentWidget(self._ensure_create_supplier_transaction_widget())
