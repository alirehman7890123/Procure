from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFrame, QLabel, QLineEdit, QComboBox, QMessageBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt,QDate
from PySide6.QtSql import  QSqlQuery
from PySide6.QtSql import QSqlDatabase
from PySide6.QtGui import QKeySequence, QShortcut


from utilities.stylus import load_stylesheets
from utilities.payment_handler import PaymentMethodHandler
    
from utilities.get_session import get_current_session



class CreateCustomerTransactionWidget(QWidget):

    
    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Receive / Refund Payment by Customer", objectName="SectionTitle")
        self.transactionlist = QPushButton("All Transactions", objectName="TopRightButton")
        self.transactionlist.setCursor(Qt.PointingHandCursor)
        self.transactionlist.setFixedWidth(200)

        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.transactionlist)

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

        # === Customer Information Section ===
        customer_heading_layout = QHBoxLayout()
        customer_heading = QLabel("Customer Information", objectName="SubHeading")
        customer_heading_layout.addWidget(customer_heading)
        self.layout.addLayout(customer_heading_layout)

        customer_row = QHBoxLayout()

        customer_label = QLabel("Customer")
        customer_label.setFixedWidth(300)

        self.customername = QLabel()

        customer_row.addWidget(customer_label, 1)
        customer_row.addWidget(self.customername, 2)

        self.layout.addLayout(customer_row)

        contact_row = QHBoxLayout()

        contact_label = QLabel("Contact")
        contact_label.setFixedWidth(300)

        self.customercontact = QLabel()

        contact_row.addWidget(contact_label, 1)
        contact_row.addWidget(self.customercontact, 2)

        self.layout.addLayout(contact_row)

        self.layout.addSpacing(20)

        # === Payment Section ===
        payment_heading_layout = QHBoxLayout()
        payment_heading = QLabel("Process Payment", objectName="SubHeading")
        payment_heading_layout.addWidget(payment_heading)
        self.layout.addLayout(payment_heading_layout)

        salesman_row = QHBoxLayout()

        salesman_label = QLabel("Salesman")
        salesman_label.setFixedWidth(300)

        self.salesman = QComboBox()

        salesman_row.addWidget(salesman_label, 1)
        salesman_row.addWidget(self.salesman, 2)

        self.layout.addLayout(salesman_row)

        payable_row = QHBoxLayout()

        payable_label = QLabel("Payable Amount")
        payable_label.setFixedWidth(300)

        self.payable = QLabel()

        payable_row.addWidget(payable_label, 1)
        payable_row.addWidget(self.payable, 2)

        self.layout.addLayout(payable_row)

        receiveable_row = QHBoxLayout()

        receiveable_label = QLabel("Receivable Amount")
        receiveable_label.setFixedWidth(300)

        self.receiveable = QLabel()

        receiveable_row.addWidget(receiveable_label, 1)
        receiveable_row.addWidget(self.receiveable, 2)

        self.layout.addLayout(receiveable_row)
        
        
        # === Payment Method Section ===
        
        payment_method_layout = QHBoxLayout()
        
        payment_method_label = QLabel("Payment Method")
        payment_method_label.setFixedWidth(300)
        
        self.payment_handler = PaymentMethodHandler(self)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        
        payment_method_layout.addWidget(payment_method_label, 1)
        payment_method_layout.addWidget(self.payment_method, 2)
        
        self.layout.addLayout(payment_method_layout)
        
        

        # === Amount Inputs ===

        paid_row = QHBoxLayout()

        paid_label = QLabel("Refund Amount (You Pay)")
        paid_label.setFixedWidth(300)

        self.paid = QLineEdit()
        self.paid.setText("0")

        paid_row.addWidget(paid_label, 1)
        paid_row.addWidget(self.paid, 2)

        self.layout.addLayout(paid_row)

        received_row = QHBoxLayout()

        received_label = QLabel("Received Amount (Customer Pays)")
        received_label.setFixedWidth(300)

        self.received = QLineEdit()
        self.received.setText("0")

        received_row.addWidget(received_label, 1)
        received_row.addWidget(self.received, 2)

        self.layout.addLayout(received_row)

        note_row = QHBoxLayout()

        note_label = QLabel("Note")
        note_label.setFixedWidth(300)

        self.note = QLineEdit()
        self.note.setPlaceholderText("Note")

        note_row.addWidget(note_label, 1)
        note_row.addWidget(self.note, 2)

        self.layout.addLayout(note_row)

        savepayment = QPushButton("Save Payment", objectName="SaveButton")
        savepayment.setCursor(Qt.PointingHandCursor)
        savepayment.clicked.connect(self.save_payment)

        self.layout.addWidget(savepayment)

        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.save_payment)

        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())

    
    def showEvent(self, event):
        
        super().showEvent(event)
        
    
    
    



    def load_data(self, id):
        
        print("Loading customer ID:", id)
        id = int(id)
        
        query = QSqlQuery()
        query.prepare("SELECT id, name, contact, payable, receiveable FROM customer WHERE id = ?")
        query.addBindValue(id)
        
        if query.exec() and query.next():
     
            self.cust_id = int(query.value(0))    
            self.customername.setText(f"{ query.value(0)} - {query.value(1)}" )
            self.customercontact.setText(query.value(2))
            self.payable.setText(str(query.value(3)))
            self.receiveable.setText(str(query.value(4)))
            
        else:
            
            print("Error: ", query.lastError().text())
            
        
        emp_query = QSqlQuery()
        emp_query.prepare("SELECT id, name, contact FROM employee")
        
        if emp_query.exec():
            
            while emp_query.next():
     
                emp_id = emp_query.value(0)
                name = emp_query.value(1)
                contact = emp_query.value(2)
                
                name = f"{name} [{contact}]"
                print("name ", name)
                
                self.salesman.addItem(name, emp_id)
        
    
    
    def on_payment_method_changed(self, method):
        
        success = self.payment_handler.handle_method_change(method)

        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)
    
    
    
    # def save_payment(self):

    #     db = QSqlDatabase.database()
    #     db.transaction()

    #     try:

    #         salesman = self.salesman.currentData()
    #         customer = int(self.cust_id)

    #         # --- Fetch Customer Balance ---
    #         balance_query = QSqlQuery()
    #         balance_query.prepare("SELECT payable, receiveable FROM customer WHERE id = ?")
    #         balance_query.addBindValue(customer)

    #         if not balance_query.exec() or not balance_query.next():
    #             raise Exception("Customer not found.")

    #         payable_before = float(balance_query.value(0) or 0.0)
    #         receiveable_before = float(balance_query.value(1) or 0.0)

    #         paid_amount = float(self.paid.text() or 0)
    #         received_amount = float(self.received.text() or 0)

    #         if paid_amount > 0 and received_amount > 0:
    #             raise Exception("Cannot process both Paid and Received together.")

    #         if paid_amount < 0 or received_amount < 0:
    #             raise Exception("Amounts cannot be negative.")

    #         transaction_type = None

    #         payable_after = payable_before
    #         receiveable_after = receiveable_before

    #         # ====================================
    #         # CUSTOMER PAYMENT (Customer pays you)
    #         # ====================================
    #         if received_amount > 0:

    #             transaction_type = "RECEIPT"

    #             if received_amount <= receiveable_before:
    #                 receiveable_after = receiveable_before - received_amount

    #             else:
    #                 excess = received_amount - receiveable_before

    #                 reply = QMessageBox.question(
    #                     self,
    #                     "Excess Receipt",
    #                     "Received exceeds receivable.\n"
    #                     "Excess will be moved to Payable.\n\nContinue?",
    #                     QMessageBox.Yes | QMessageBox.No
    #                 )

    #                 if reply == QMessageBox.No:
    #                     raise Exception("Transaction cancelled.")

    #                 receiveable_after = 0
    #                 payable_after = payable_before + excess

    #         # ====================================
    #         # REFUND (You pay customer)
    #         # ====================================
    #         elif paid_amount > 0:

    #             transaction_type = "REFUND"

    #             if paid_amount <= payable_before:
    #                 payable_after = payable_before - paid_amount

    #             else:
    #                 excess = paid_amount - payable_before

    #                 reply = QMessageBox.question(
    #                     self,
    #                     "Excess Refund",
    #                     "Refund exceeds payable.\n"
    #                     "Excess will be moved to Receivable.\n\nContinue?",
    #                     QMessageBox.Yes | QMessageBox.No
    #                 )

    #                 if reply == QMessageBox.No:
    #                     raise Exception("Transaction cancelled.")

    #                 payable_after = 0
    #                 receiveable_after = receiveable_before + excess

    #         else:
    #             raise Exception("Enter Paid or Received amount.")

    #         # --- Insert Transaction ---
    #         query = QSqlQuery()
    #         query.prepare("""
    #             INSERT INTO customer_transaction
    #             (customer, transaction_type,
    #             payable_before, paid, payable_after,
    #             receiveable_before, received, receiveable_after,
    #             salesman)
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         """)

    #         query.addBindValue(customer)
    #         query.addBindValue(transaction_type)

    #         query.addBindValue(payable_before)
    #         query.addBindValue(paid_amount)
    #         query.addBindValue(payable_after)

    #         query.addBindValue(receiveable_before)
    #         query.addBindValue(received_amount)
    #         query.addBindValue(receiveable_after)

    #         query.addBindValue(salesman)

    #         if not query.exec():
    #             raise Exception(query.lastError().text())

    #         # --- Update Customer Master ---
    #         update_query = QSqlQuery()
    #         update_query.prepare("""
    #             UPDATE customer
    #             SET payable = ?, receiveable = ?
    #             WHERE id = ?
    #         """)

    #         update_query.addBindValue(payable_after)
    #         update_query.addBindValue(receiveable_after)
    #         update_query.addBindValue(customer)

    #         if not update_query.exec():
    #             raise Exception(update_query.lastError().text())

    #         db.commit()

    #         QMessageBox.information(self, "Success", "Customer Transaction Saved Successfully.")

    #         self.load_data(self.cust_id)
    #         self.paid.setText("0")
    #         self.received.setText("0")
    #         self.note.clear()

    #     except Exception as e:
    #         db.rollback()
    #         QMessageBox.critical(self, "Error", str(e))

    
    def save_payment(self):
        
        db = QSqlDatabase.database()

        if not db.transaction():
            QMessageBox.critical(self, "Error", "Could not start database transaction.")
            return

        try:
            data = self._collect_customer_payment_data()
            self._save_customer_payment_transaction(data)

            if not db.commit():
                raise Exception("Could not commit customer transaction.")

            QMessageBox.information(self, "Success", "Customer Transaction Saved Successfully.")

            self.load_data(self.cust_id)
            self.paid.setText("0")
            self.received.setText("0")
            self.note.clear()

        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", str(e))


    def _collect_customer_payment_data(self):
        salesman = self.salesman.currentData()
        customer = int(self.cust_id)
        note = self.note.toPlainText().strip() if hasattr(self.note, "toPlainText") else self.note.text().strip()

        paid_amount = float(self.paid.text() or 0)
        received_amount = float(self.received.text() or 0)

        if paid_amount > 0 and received_amount > 0:
            raise Exception("Cannot process both Paid and Received together.")

        if paid_amount < 0 or received_amount < 0:
            raise Exception("Amounts cannot be negative.")

        if paid_amount == 0 and received_amount == 0:
            raise Exception("Enter Paid or Received amount.")

        balance_query = QSqlQuery()
        balance_query.prepare("SELECT payable, receiveable FROM customer WHERE id = ?")
        balance_query.addBindValue(customer)

        if not balance_query.exec() or not balance_query.next():
            raise Exception("Customer not found.")

        payable_before = float(balance_query.value(0) or 0.0)
        receiveable_before = float(balance_query.value(1) or 0.0)

        transaction_type = None

        due_amount = 0.0
        remaining_due = 0.0
        payable_after = payable_before

        receiveable_now = 0.0
        remaining_now = 0.0
        receiveable_after = receiveable_before

        paid = 0.0
        received = 0.0

        # ====================================
        # CUSTOMER PAYMENT (Customer pays you)
        # ====================================
        if received_amount > 0:
            transaction_type = "RECEIPT"
            received = received_amount

            due_amount = 0.0
            remaining_due = payable_before
            receiveable_now = receiveable_before

            if received_amount <= receiveable_before:
                remaining_now = receiveable_before - received_amount
                receiveable_after = remaining_now
                payable_after = payable_before
            else:
                excess = received_amount - receiveable_before

                reply = QMessageBox.question(
                    self,
                    "Excess Receipt",
                    "Received exceeds receivable.\n"
                    "Excess will be moved to Payable.\n\nContinue?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.No:
                    raise Exception("Transaction cancelled.")

                remaining_now = 0.0
                receiveable_after = 0.0
                payable_after = payable_before + excess
                remaining_due = payable_after

        # ====================================
        # REFUND (You pay customer)
        # ====================================
        elif paid_amount > 0:
            transaction_type = "REFUND"
            paid = paid_amount

            due_amount = payable_before

            if paid_amount <= payable_before:
                remaining_due = payable_before - paid_amount
                payable_after = remaining_due
                receiveable_now = 0.0
                remaining_now = receiveable_before
                receiveable_after = receiveable_before
            else:
                excess = paid_amount - payable_before

                reply = QMessageBox.question(
                    self,
                    "Excess Refund",
                    "Refund exceeds payable.\n"
                    "Excess will be moved to Receivable.\n\nContinue?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.No:
                    raise Exception("Transaction cancelled.")

                remaining_due = 0.0
                payable_after = 0.0
                receiveable_now = excess
                remaining_now = receiveable_before + excess
                receiveable_after = receiveable_before + excess

        session_id = get_current_session(self)
        if session_id is None:
            raise Exception("No active session found.")

        payment = self.payment_handler.payment_data.copy()
        print(payment)

        return {
            "customer": customer,
            "salesman": salesman,
            "transaction_type": transaction_type,
            "ref": None,
            "return_ref": None,

            "payable_before": payable_before,
            "due_amount": due_amount,
            "paid": paid,
            "remaining_due": remaining_due,
            "payable_after": payable_after,

            "receiveable_before": receiveable_before,
            "receiveable_now": receiveable_now,
            "received": received,
            "remaining_now": remaining_now,
            "receiveable_after": receiveable_after,

            "payment_method": payment["payment_method"],
            "bank_name": payment["bank_name"],
            "account_no": payment["account_no"],
            "transaction_mode": payment["transaction_mode"],
            "wallet_provider": payment["wallet_provider"],
            "wallet_no": payment["wallet_no"],
            "payment_reference": payment["payment_reference"],

            "note": note if note else None,
            "session_id": session_id,
        }


    def _save_customer_payment_transaction(self, data):
        query = QSqlQuery()
        query.prepare("""
            INSERT INTO customer_transaction
            (
                customer, transaction_type, ref, return_ref,
                payable_before, due_amount, paid, remaining_due, payable_after,
                receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                payment_method, bank_name, account_no, transaction_mode,
                wallet_provider, wallet_no, payment_reference,
                salesman, note, session_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        query.addBindValue(data["customer"])
        query.addBindValue(data["transaction_type"])
        query.addBindValue(data["ref"])
        query.addBindValue(data["return_ref"])

        query.addBindValue(data["payable_before"])
        query.addBindValue(data["due_amount"])
        query.addBindValue(data["paid"])
        query.addBindValue(data["remaining_due"])
        query.addBindValue(data["payable_after"])

        query.addBindValue(data["receiveable_before"])
        query.addBindValue(data["receiveable_now"])
        query.addBindValue(data["received"])
        query.addBindValue(data["remaining_now"])
        query.addBindValue(data["receiveable_after"])

        query.addBindValue(data["payment_method"])
        query.addBindValue(data["bank_name"])
        query.addBindValue(data["account_no"])
        query.addBindValue(data["transaction_mode"])

        query.addBindValue(data["wallet_provider"])
        query.addBindValue(data["wallet_no"])
        query.addBindValue(data["payment_reference"])

        query.addBindValue(data["salesman"])
        query.addBindValue(data["note"])
        query.addBindValue(data["session_id"])

        if not query.exec():
            raise Exception(query.lastError().text())

        update_query = QSqlQuery()
        update_query.prepare("""
            UPDATE customer
            SET payable = ?, receiveable = ?
            WHERE id = ?
        """)

        update_query.addBindValue(data["payable_after"])
        update_query.addBindValue(data["receiveable_after"])
        update_query.addBindValue(data["customer"])

        if not update_query.exec():
            raise Exception(update_query.lastError().text())

            
            
         
        
        
    def clear_fields(self):
        
        self.customername.clear()
        self.customercontact.clear()
        self.payable.clear()
        self.receiveable().clear()
        self.paid.clear() 
        self.received.clear()
        self.note.clear()  
        
        self.payment_method.blockSignals(True); 
        self.payment_method.setCurrentIndex(0) 
        self.payment_method.blockSignals(False)                  



            
            
            

