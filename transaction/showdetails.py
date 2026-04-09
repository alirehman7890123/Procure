from PySide6.QtWidgets import QWidget, QPushButton, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt,QDate
from PySide6.QtSql import  QSqlQuery
from utilities.stylus import load_stylesheets
from utilities.app_messagebox import AppMessageBox




class MainTransactionWidget(QWidget):

    def __init__(self, parent=None):
        self._last_reconciliation_signature = None

        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Transactions", objectName="SectionTitle")
        # self.transactionlist = QPushButton("Transaction List", objectName="TopRightButton")
        # self.transactionlist.setCursor(Qt.PointingHandCursor)
        # self.transactionlist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        # header_layout.addWidget(self.transactionlist)

        self.layout.addLayout(header_layout)
        
        line = QFrame()
        line.setObjectName("lineSeparator")

        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
                QFrame#lineSeparator {
                    border: none;
                    border-top: 2px solid #333;
                }
            """)

        self.layout.addWidget(line)
        self.layout.addSpacing(20)



        # Supplier Transactions Section

        supplierlabel = QLabel("Supplier Transactions", objectName='SectionTitle')
        self.layout.addWidget(supplierlabel)

        supplier_payable = QLabel("Supplier Payable")
        self.supplier_payable_amount = QLabel("0.00")
        
        supplier_receiveable = QLabel("Supplier Receiveable")
        self.supplier_receiveable_amount = QLabel("0.00")
        
        self.supplier_transactions_button = QPushButton("Supplier Transactions", objectName='SaveButton')
        self.supplier_transactions_button.setCursor(Qt.PointingHandCursor)
        
        # Supplier Payable Row
        sp_row = QHBoxLayout()
        
        sp_row.addWidget(supplier_payable, 2)
        sp_row.addWidget(self.supplier_payable_amount, 2)

        self.layout.addLayout(sp_row)
        
        # Supplier Receiveable Row
        sr_row = QHBoxLayout()

        sr_row.addWidget(supplier_receiveable, 2)
        sr_row.addWidget(self.supplier_receiveable_amount, 2)

        self.layout.addLayout(sr_row)


        # Supplier Transactions Button
        st_btn = QHBoxLayout()
        st_btn.addWidget(self.supplier_transactions_button)
        self.layout.addLayout(st_btn)

        self.supplier_reconcile_notice = QLabel("")
        self.supplier_reconcile_notice.setStyleSheet("color: #5A7183; font-size: 12px; font-weight: 600;")
        self.supplier_reconcile_notice.hide()
        self.layout.addWidget(self.supplier_reconcile_notice)
        
        
        
        
        # Customer Transactions Section
        
        customerlabel = QLabel("Customer Transactions", objectName='SectionTitle')
        self.layout.addWidget(customerlabel)

        customer_payable = QLabel("Customer Payable")
        self.customer_payable_amount = QLabel("0.00")

        customer_receiveable = QLabel("Customer Receiveable")
        self.customer_receiveable_amount = QLabel("0.00")
        
        self.customer_transactions_button = QPushButton("Customer Transactions", objectName='SaveButton')
        self.customer_transactions_button.setCursor(Qt.PointingHandCursor)
        

        # Customer Payable Row
        cp_row = QHBoxLayout()
        cp_row.addWidget(customer_payable)
        cp_row.addWidget(self.customer_payable_amount)
        self.layout.addLayout(cp_row)

        # Customer Receiveable Row
        cr_row = QHBoxLayout()
        cr_row.addWidget(customer_receiveable)
        cr_row.addWidget(self.customer_receiveable_amount)
        self.layout.addLayout(cr_row)

        # Customer Transactions Button
        ct_btn = QHBoxLayout()
        ct_btn.addWidget(self.customer_transactions_button)
        self.layout.addLayout(ct_btn)

        self.customer_reconcile_notice = QLabel("")
        self.customer_reconcile_notice.setStyleSheet("color: #5A7183; font-size: 12px; font-weight: 600;")
        self.customer_reconcile_notice.hide()
        self.layout.addWidget(self.customer_reconcile_notice)

        

        
        self.layout.addStretch()

        
        self.setStyleSheet(load_stylesheets())




    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_data()
        

    def load_data(self):
        
        supplier_query = QSqlQuery()
        supplier_query.prepare("SELECT payable, receiveable FROM supplier;")
        
        if supplier_query.exec():
            
            total_payable = 0.0
            total_receiveable = 0.0
            
            while supplier_query.next():
                
                payable = float(supplier_query.value(0))
                receiveable = float(supplier_query.value(1))
                
                total_payable += payable
                total_receiveable += receiveable
                
            self.supplier_payable_amount.setText(f"{total_payable:.2f}")
            self.supplier_receiveable_amount.setText(f"{total_receiveable:.2f}")         
        
        else:
            print(None, "Error Occurred in Getting Supplier Data: ", supplier_query.lastError().text())
            
            
        
        
        customer_query = QSqlQuery()
        customer_query.prepare("SELECT payable, receiveable FROM customer;")
        if customer_query.exec():

            total_payable = 0.0
            total_receiveable = 0.0

            while customer_query.next():

                payable = float(customer_query.value(0))
                receiveable = float(customer_query.value(1))

                total_payable += payable
                total_receiveable += receiveable

            self.customer_payable_amount.setText(f"{total_payable:.2f}")
            self.customer_receiveable_amount.setText(f"{total_receiveable:.2f}")
        
        self.update_reconciliation_notices()

    def get_reconciliation_counts(self):
        counts = {"supplier": 0, "customer": 0}

        supplier_query = QSqlQuery()
        supplier_query.prepare("""
            SELECT COUNT(*)
            FROM supplier
            WHERE COALESCE(payable, 0) > 0 AND COALESCE(receiveable, 0) > 0
        """)
        if supplier_query.exec() and supplier_query.next():
            counts["supplier"] = int(supplier_query.value(0) or 0)

        customer_query = QSqlQuery()
        customer_query.prepare("""
            SELECT COUNT(*)
            FROM customer
            WHERE COALESCE(payable, 0) > 0 AND COALESCE(receiveable, 0) > 0
        """)
        if customer_query.exec() and customer_query.next():
            counts["customer"] = int(customer_query.value(0) or 0)

        return counts

    def update_reconciliation_notices(self):
        counts = self.get_reconciliation_counts()

        if counts["supplier"] > 0:
            suffix = "supplier has" if counts["supplier"] == 1 else "suppliers have"
            self.supplier_reconcile_notice.setText(
                f"{counts['supplier']} {suffix} balances eligible for internal reconciliation."
            )
            self.supplier_reconcile_notice.show()
        else:
            self.supplier_reconcile_notice.hide()

        if counts["customer"] > 0:
            suffix = "customer has" if counts["customer"] == 1 else "customers have"
            self.customer_reconcile_notice.setText(
                f"{counts['customer']} {suffix} balances eligible for internal reconciliation."
            )
            self.customer_reconcile_notice.show()
        else:
            self.customer_reconcile_notice.hide()

        signature = (counts["supplier"], counts["customer"])
        if signature == self._last_reconciliation_signature:
            return

        self._last_reconciliation_signature = signature

        if counts["supplier"] == 0 and counts["customer"] == 0:
            return

        lines = []
        if counts["supplier"] > 0:
            lines.append(f"Suppliers eligible for reconciliation: {counts['supplier']}")
        if counts["customer"] > 0:
            lines.append(f"Customers eligible for reconciliation: {counts['customer']}")

        AppMessageBox.information(
            self,
            "Reconciliation Available",
            "\n".join(lines) + "\n\nOpen the relevant transaction list to reconcile balances."
        )
        
