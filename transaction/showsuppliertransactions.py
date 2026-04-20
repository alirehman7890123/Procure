from PySide6.QtWidgets import QWidget, QFrame, QHBoxLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from functools import partial
from utilities.stylus import load_stylesheets
from utilities.permissions import Permissions
from utilities.session_service import get_active_session_id
from utilities.app_messagebox import AppMessageBox





class SupplierTransactionWidget(QWidget):
    
    transaction_page_signal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("All Suppliers Transactions", objectName="SectionTitle")
        self.transactionpage = QPushButton("Main Transactions Page", objectName="TopRightButton")
        self.transactionpage.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.transactionpage)

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
        self.layout.addSpacing(10)




        self.row_height = 35

        self.table = MyTable(column_ratios=[0.05, 0.22, 0.14, 0.18, 0.12, 0.12, 0.09, 0.08])
        headers = ["#", "Name", "Contact", "Email", "Payable", "Receiveable", "Pay / Receive", "Reconcile"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        

        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        detail_col = headers.index("Pay / Receive")
        reconcile_col = headers.index("Reconcile")
        self.table.horizontalHeaderItem(detail_col).setTextAlignment(Qt.AlignCenter)
        self.table.horizontalHeaderItem(reconcile_col).setTextAlignment(Qt.AlignCenter)
        
        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   

        self.table.setMinimumWidth(700)
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)
        
        # Alternating row colors
        self.table.setAlternatingRowColors(True)


        
        
        self.layout.addWidget(self.table)
        
        self.layout.addStretch()

        
        self.setStyleSheet(load_stylesheets())



    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_suppliers_transactions()
        



    def load_suppliers_transactions(self):
        
        query = QSqlQuery()
        query.exec("SELECT id, name, contact, email, payable, receiveable FROM supplier")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            suppid = int(query.value(0))
            name = str(query.value(1))
            contact = str(query.value(2))
            email = str(query.value(3))
            payable = str(query.value(4))
            receiveable = str(query.value(5))
            
            counter = str(row + 1)
            counter = QTableWidgetItem(counter)
            name = QTableWidgetItem(name)
            contact = QTableWidgetItem(contact)
            email = QTableWidgetItem(email)
            payable = QTableWidgetItem(payable)
            receiveable = QTableWidgetItem(receiveable)
            
            
            
            self.table.setItem(row, 0, counter)
            self.table.setItem(row, 1, name)
            self.table.setItem(row, 2, contact)
            self.table.setItem(row, 3, email)
            self.table.setItem(row, 4, payable)
            self.table.setItem(row, 5, receiveable)
            
            payable_amount = float(query.value(4) or 0.0)
            receiveable_amount = float(query.value(5) or 0.0)

            pay = QPushButton('Pay / Receive')
            pay.setStyleSheet("""
                    background-color: #333;
                    color: #fff;
                    font-weight: 600;
                    padding: 5px;    
            """)
            
            self.table.setCellWidget(row, 6, pay)
            pay.clicked.connect(partial(self.transaction_page_signal.emit, suppid))

            reconcile = QPushButton("Reconcile")
            reconcile.setStyleSheet("""
                    background-color: #2F5D7C;
                    color: #fff;
                    font-weight: 600;
                    padding: 5px;
            """)
            can_reconcile = payable_amount > 0 and receiveable_amount > 0
            reconcile.setEnabled(can_reconcile)
            if can_reconcile:
                reconcile.clicked.connect(
                    partial(self.reconcile_supplier_balance, suppid, str(query.value(1) or ""))
                )
            self.table.setCellWidget(row, 7, reconcile)
            
            row += 1

    @Permissions.require_permission('transactions.create')
    def reconcile_supplier_balance(self, supplier_id, supplier_name):
        query = QSqlQuery()
        query.prepare("SELECT payable, receiveable FROM supplier WHERE id = ?")
        query.addBindValue(supplier_id)

        if not query.exec() or not query.next():
            AppMessageBox.warning(self, "Not Found", "Supplier could not be loaded for reconciliation.")
            return

        payable_before = float(query.value(0) or 0.0)
        receiveable_before = float(query.value(1) or 0.0)
        reconcile_amount = min(payable_before, receiveable_before)

        if reconcile_amount <= 0:
            AppMessageBox.information(self, "Nothing to Reconcile", "This supplier has no balances to reconcile.")
            return

        _, accepted = AppMessageBox.confirm(
            self,
            "Internal Reconciliation",
            (
                f"{supplier_name} has payable {payable_before:.2f} and receivable {receiveable_before:.2f}.\n"
                f"Reconcile {reconcile_amount:.2f} internally?"
            ),
            confirm_label="Reconcile",
            cancel_label="Cancel",
            kind="warning",
        )

        if not accepted:
            return

        session_id = get_active_session_id(strict=True)
        if session_id is None:
            AppMessageBox.warning(self, "Session Required", "Open a daily session before reconciling balances.")
            return

        payable_after = payable_before - reconcile_amount
        receiveable_after = receiveable_before - reconcile_amount

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.critical(self, "Database Error", "Could not start reconciliation transaction.")
            return

        try:
            insert_query = QSqlQuery()
            insert_query.prepare("""
                INSERT INTO supplier_transaction
                (
                    supplier, transaction_type, ref, return_ref,
                    payable_before, due_amount, paid, remaining_due, payable_after,
                    receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                    rep, note, session_id,
                    payment_method, bank_name, account_no, transaction_mode,
                    wallet_provider, wallet_no, payment_reference
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
            insert_query.addBindValue(supplier_id)
            insert_query.addBindValue("INTERNAL_RECONCILIATION")
            insert_query.addBindValue(None)
            insert_query.addBindValue(None)
            insert_query.addBindValue(payable_before)
            insert_query.addBindValue(reconcile_amount)
            insert_query.addBindValue(0.0)
            insert_query.addBindValue(payable_after)
            insert_query.addBindValue(payable_after)
            insert_query.addBindValue(receiveable_before)
            insert_query.addBindValue(reconcile_amount)
            insert_query.addBindValue(0.0)
            insert_query.addBindValue(receiveable_after)
            insert_query.addBindValue(receiveable_after)
            insert_query.addBindValue(None)
            insert_query.addBindValue(f"Internally reconciled {reconcile_amount:.2f} against supplier balance.")
            insert_query.addBindValue(session_id)
            insert_query.addBindValue("Internal")
            insert_query.addBindValue(None)
            insert_query.addBindValue(None)
            insert_query.addBindValue(None)
            insert_query.addBindValue(None)
            insert_query.addBindValue(None)
            insert_query.addBindValue(None)

            if not insert_query.exec():
                raise Exception(insert_query.lastError().text())

            update_query = QSqlQuery()
            update_query.prepare("""
                UPDATE supplier
                SET payable = ?, receiveable = ?
                WHERE id = ?
            """)
            update_query.addBindValue(payable_after)
            update_query.addBindValue(receiveable_after)
            update_query.addBindValue(supplier_id)

            if not update_query.exec():
                raise Exception(update_query.lastError().text())

            if not db.commit():
                raise Exception("Could not commit reconciliation.")

            AppMessageBox.success(self, "Reconciled", f"{reconcile_amount:.2f} reconciled for {supplier_name}.")
            self.load_suppliers_transactions()

        except Exception as e:
            db.rollback()
            AppMessageBox.critical(self, "Error", str(e))
        





      

class MyTable(QTableWidget):
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # user can drag

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)




            
        
