from PySide6.QtWidgets import QWidget, QStackedLayout, QScrollArea, QMessageBox

from transaction.showdetails import MainTransactionWidget
from transaction.showsuppliertransactions import SupplierTransactionWidget
from transaction.showcustomertransactions import CustomerTransactionWidget
from transaction.createsuppliertransaction import CreateSupplierTransactionWidget
from transaction.createcustomertransaction import CreateCustomerTransactionWidget
from transaction.customertransactionlist import CustomerTransactionListWidget
from transaction.suppliertransactionlist import SupplierTransactionListWidget
from transaction.customer_transaction_detail import CustomerTransactionDetailWidget
from transaction.supplier_transaction_detail import SupplierTransactionDetailWidget
from utilities.basepage import BasePage

from utilities.permissions import Permissions


class BaseTransactionWidget(BasePage):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stacked_layout = QStackedLayout()

        self.maintransaction_widget = MainTransactionWidget()
        self.maintransaction_widget.supplier_transactions_button.clicked.connect(self.set_suppliertransaction_widget)
        self.maintransaction_widget.customer_transactions_button.clicked.connect(self.set_customertransaction_widget)
        
        # Show Transactions
        self.supplier_transaction_widget = SupplierTransactionWidget()
        self.supplier_transaction_widget.transaction_page_signal.connect(self.set_create_supplier_transaction_widget)
        
        self.customer_transaction_widget = CustomerTransactionWidget()
        self.customer_transaction_widget.transaction_page_signal.connect(self.set_create_customer_transaction_widget)
        
        
        # Create Payment Transactions
        self.create_supplier_transaction_widget = CreateSupplierTransactionWidget()
        self.create_supplier_transaction_widget.transactionlist.clicked.connect(self.set_supplier_transaction_list_widget)
        
        self.create_customer_transaction_widget = CreateCustomerTransactionWidget()
        self.create_customer_transaction_widget.transactionlist.clicked.connect(self.set_customer_transaction_list_widget)
        
        

        # # List transaction Widget
        self.supplier_transaction_list_widget = SupplierTransactionListWidget()
        self.supplier_transaction_list_widget.addpayment.clicked.connect(self.set_suppliertransaction_widget)
        self.supplier_transaction_list_widget.transaction_detail_signal.connect(self.set_supplier_transaction_detail_widget)
        
        
        self.customer_transaction_list_widget = CustomerTransactionListWidget()
        self.customer_transaction_list_widget.addpayment.clicked.connect(self.set_customertransaction_widget)
        
        

        # # Detail transaction Widget
        self.customer_transaction_detail_widget = CustomerTransactionDetailWidget()
        self.customer_transaction_detail_widget.transactionlist.clicked.connect(self.set_customer_transaction_list_widget)
        self.customer_transaction_list_widget.transaction_detail_signal.connect(self.set_customer_transaction_detail_widget)



        self.supplier_transaction_detail_widget = SupplierTransactionDetailWidget()
        self.supplier_transaction_detail_widget.transactionlist.clicked.connect(self.set_suppliertransaction_widget)


        self.stacked_layout.addWidget(self.maintransaction_widget)
        self.stacked_layout.addWidget(self.supplier_transaction_widget)
        self.stacked_layout.addWidget(self.customer_transaction_widget)
        self.stacked_layout.addWidget(self.create_supplier_transaction_widget)
        self.stacked_layout.addWidget(self.create_customer_transaction_widget)
        self.stacked_layout.addWidget(self.supplier_transaction_list_widget)
        self.stacked_layout.addWidget(self.customer_transaction_list_widget)
        self.stacked_layout.addWidget(self.customer_transaction_detail_widget)
        self.stacked_layout.addWidget(self.supplier_transaction_detail_widget)
        

        self.setLayout(self.stacked_layout)
        


        
    @Permissions.require_permission('transactions.view')
    def set_maintransaction_widget(self):
        self.stacked_layout.setCurrentWidget(self.maintransaction_widget)

    @Permissions.require_permission('transactions.view')
    def set_suppliertransaction_widget(self):
        self.stacked_layout.setCurrentWidget(self.supplier_transaction_widget)
        
    @Permissions.require_permission('transactions.view')    
    def set_customertransaction_widget(self):
        self.stacked_layout.setCurrentWidget(self.customer_transaction_widget)

    @Permissions.require_permission('transactions.create')
    def set_create_supplier_transaction_widget(self, id):
        self.create_supplier_transaction_widget.load_data(id)
        self.stacked_layout.setCurrentWidget(self.create_supplier_transaction_widget)
        
    @Permissions.require_permission('transactions.create')   
    def set_create_customer_transaction_widget(self, id):
        
        self.create_customer_transaction_widget.load_data(id)
        self.stacked_layout.setCurrentWidget(self.create_customer_transaction_widget)
        
        
    
    @Permissions.require_permission('transactions.view')
    def set_supplier_transaction_list_widget(self):
        self.stacked_layout.setCurrentWidget(self.supplier_transaction_list_widget)
        
        
    @Permissions.require_permission('transactions.view')    
    def set_customer_transaction_list_widget(self):
        self.stacked_layout.setCurrentWidget(self.customer_transaction_list_widget)


    @Permissions.require_permission('transactions.view')
    def set_customer_transaction_detail_widget(self, id):
        self.customer_transaction_detail_widget.load_data(id)
        self.stacked_layout.setCurrentWidget(self.customer_transaction_detail_widget)


    @Permissions.require_permission('transactions.view')
    def set_supplier_transaction_detail_widget(self, id):
        self.supplier_transaction_detail_widget.load_data(id)
        self.stacked_layout.setCurrentWidget(self.supplier_transaction_detail_widget)

    # 🔑 reset method
    def reset_to_default(self):
        self.stacked_layout.setCurrentWidget(self.maintransaction_widget)    
        
        
        