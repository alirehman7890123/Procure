from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout,QRadioButton,QButtonGroup, QLabel,QDialog,QFormLayout, QLineEdit, QComboBox,QMessageBox, QVBoxLayout, QFrame, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt, QDate
from PySide6.QtSql import  QSqlQuery, QSql  
from PySide6.QtSql import QSqlDatabase
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator

from PySide6.QtGui import QKeySequence, QShortcut

from medic.utilities.stylus import load_stylesheets
from medic.utilities.payment_handler import PaymentMethodHandler
from medic.utilities.permissions import Permissions
from medic.utilities.session_gate import require_open_session
from medic.utilities.session_service import get_active_session_id
from medic.utilities.app_messagebox import AppMessageBox



class CreateSupplierTransactionWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Pay / Receive Payment by Supplier", objectName="SectionTitle")
        self.transactionlist = QPushButton("All Transactions", objectName="TopRightButton")
        self.transactionlist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
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



        # Supplier Transactions Section
        
        supplier_heading_layout = QHBoxLayout()
        supplier_heading = QLabel("Supplier Information", objectName="SubHeading")
        supplier_heading_layout.addWidget(supplier_heading)

        self.layout.addLayout(supplier_heading_layout)
        
        
        supplier_row = QHBoxLayout()
        
        supplier_label = QLabel("Supplier")
        supplier_label.setFixedWidth(300)
        
        self.suppliername = QLabel()
        supplier_row.addWidget(supplier_label, 1)
        supplier_row.addWidget(self.suppliername, 2)
        
        self.layout.addLayout(supplier_row)


        address_row = QHBoxLayout()
        
        address_label = QLabel("Address")
        address_label.setFixedWidth(300)
        
        address_row.addWidget(address_label, 1)
        self.supplieraddress = QLabel()
        address_row.addWidget(self.supplieraddress, 2)
        
        self.layout.addLayout(address_row)
        
        self.layout.addSpacing(20)

        payment_heading_layout = QHBoxLayout()
        payment_heading = QLabel("Make Payment", objectName="SubHeading")
        payment_heading_layout.addWidget(payment_heading)

        self.layout.addLayout(payment_heading_layout)
        
        
        rep_row = QHBoxLayout()
        
        rep_label = QLabel("Sales Rep")
        rep_label.setFixedWidth(300)
        self.rep = QComboBox()
        rep_row.addWidget(rep_label, 1)
        rep_row.addWidget(self.rep, 2)
        
        self.layout.addLayout(rep_row)
        

        payable_row = QHBoxLayout()
        
        payable_label = QLabel("Payable Amount")
        payable_label.setFixedWidth(300)
        self.payable = QLabel()
        payable_row.addWidget(payable_label, 1) 
        payable_row.addWidget(self.payable, 2)
        
        self.layout.addLayout(payable_row)
        
        
        receiveable_row = QHBoxLayout()
        
        receiveable_label = QLabel("Receiveable Amount")
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
        
        
        paid_row = QHBoxLayout()
        
        paid_label = QLabel("Paid Amount")
        paid_label.setFixedWidth(300)
        self.paid= QLineEdit()
        self.paid.setText("0")
        paid_row.addWidget(paid_label, 1) 
        paid_row.addWidget(self.paid, 2)
        
        self.layout.addLayout(paid_row)
        
        
        
        received_row = QHBoxLayout()
        
        received_label = QLabel("Received Amount")
        received_label.setFixedWidth(300)
        self.received= QLineEdit()
        self.received.setText("0")
        received_row.addWidget(received_label) 
        received_row.addWidget(self.received)
        
        self.layout.addLayout(received_row)
          

        note_row = QHBoxLayout()
        
        note_label = QLabel("Note")
        note_label.setFixedWidth(300)
        self.note = QLineEdit()
        self.note.setPlaceholderText("Note")
        
        note_row.addWidget(note_label) 
        note_row.addWidget(self.note)
        
        self.layout.addLayout(note_row)
        
        savepayment = QPushButton('Save Payment', objectName="SaveButton")
        savepayment.setCursor(Qt.PointingHandCursor)
        savepayment.clicked.connect(self.save_payment)
        
        self.layout.addWidget(savepayment)
        
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.save_payment)     

        self.layout.addStretch()
        
        
        self.setStyleSheet(load_stylesheets())

        

    
    
    def on_payment_method_changed(self, method):
        
        success = self.payment_handler.handle_method_change(method)

        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)
    
    
    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        


    def load_data(self, id):
        
        print("Loading Supplier ID:", id)
        query = QSqlQuery()
        query.prepare("SELECT id, name, contact, address, payable, receiveable FROM supplier WHERE id = ?")
        query.addBindValue(id)
        
        if query.exec() and query.next():
     
            self.supp_id = int(query.value(0))    
            self.suppliername.setText(f"{ query.value(0)} - {query.value(1)}" )
            self.supplieraddress.setText(query.value(2))
            self.payable.setText(str(query.value(4)))
            self.receiveable.setText(str(query.value(5)))
            
        
        self.rep.clear()
        
        rep_query = QSqlQuery()
        rep_query.prepare("SELECT id, name, contact FROM rep WHERE supplier_id = ?")
        rep_query.addBindValue(id)
        
        if rep_query.exec():
            
            while rep_query.next():
     
                rep_id = int(rep_query.value(0))    
                name = rep_query.value(1)
                contact = rep_query.value(2)
                
                name = f"{name} [{contact}]"
                
                print("name ", name)
                
                self.rep.addItem(name, rep_id)
                
                # if isinstance(joining_date, QDate):  # or QDateTime
                #     joining_date = joining_date.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
                # else:
                #     joining_date = str(joining_date)
                
    
    
    # def save_payment(self):

    #     db = QSqlDatabase.database()
    #     db.transaction()

    #     try:

    #         rep = self.rep.currentData()
    #         supplier = int(self.supp_id)

    #         # --- Fetch Supplier Balance ---
    #         balance_query = QSqlQuery()
    #         balance_query.prepare("SELECT payable, receiveable FROM supplier WHERE id = ?")
    #         balance_query.addBindValue(supplier)

    #         if not balance_query.exec() or not balance_query.next():
    #             raise Exception("Supplier not found.")

    #         payable_before = float(balance_query.value(0) or 0.0)
    #         receiveable_before = float(balance_query.value(1) or 0.0)

    #         paid_amount = float(self.paid.text() or 0)
    #         received_amount = float(self.received.text() or 0)

    #         if paid_amount > 0 and received_amount > 0:
    #             raise Exception("Cannot process Payment and Receipt together.")

    #         if paid_amount < 0 or received_amount < 0:
    #             raise Exception("Amounts cannot be negative.")

    #         transaction_type = None

    #         payable_after = payable_before
    #         receiveable_after = receiveable_before

    #         # ==========================
    #         # PAYMENT (You pay supplier)
    #         # ==========================
    #         if paid_amount > 0:

    #             transaction_type = "PAYMENT"

    #             if paid_amount <= payable_before:
    #                 payable_after = payable_before - paid_amount

    #             else:
    #                 overpayment = paid_amount - payable_before
    #                 payable_after = 0
    #                 receiveable_after = receiveable_before + overpayment


    #         # ==========================
    #         # RECEIPT (Supplier pays you)
    #         # ==========================
    #         elif received_amount > 0:

    #             transaction_type = "RECEIPT"

    #             if received_amount <= receiveable_before:
    #                 receiveable_after = receiveable_before - received_amount

    #             else:
    #                 excess = received_amount - receiveable_before

    #                 reply = AppMessageBox.question(
    #                     self,
    #                     "Excess Receipt",
    #                     "Received amount exceeds receivable.\n"
    #                     "Excess will be moved to Payable.\n\nContinue?",
    #                     QMessageBox.Yes | QMessageBox.No
    #                 )

    #                 if reply == QMessageBox.No:
    #                     raise Exception("Receipt cancelled by user.")

    #                 receiveable_after = 0
    #                 payable_after = payable_before + excess

    #         else:
    #             raise Exception("Enter paid or received amount.")

    #         # --- Insert Transaction ---
    #         query = QSqlQuery()
    #         query.prepare("""
    #             INSERT INTO supplier_transaction
    #             (supplier, transaction_type,
    #             payable_before, paid, payable_after,
    #             receiveable_before, received, receiveable_after,
    #             rep)
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                
    #         """)

    #         query.addBindValue(supplier)
    #         query.addBindValue(transaction_type)

    #         query.addBindValue(payable_before)
    #         query.addBindValue(paid_amount)
    #         query.addBindValue(payable_after)

    #         query.addBindValue(receiveable_before)
    #         query.addBindValue(received_amount)
    #         query.addBindValue(receiveable_after)
            
            
            
            

    #         query.addBindValue(rep)

    #         if not query.exec():
    #             raise Exception(query.lastError().text())

    #         # --- Update Supplier Master ---
    #         update_query = QSqlQuery()
    #         update_query.prepare("""
    #             UPDATE supplier
    #             SET payable = ?, receiveable = ?
    #             WHERE id = ?
    #         """)

    #         update_query.addBindValue(payable_after)
    #         update_query.addBindValue(receiveable_after)
    #         update_query.addBindValue(supplier)

    #         if not update_query.exec():
    #             raise Exception(update_query.lastError().text())

    #         db.commit()

    #         AppMessageBox.information(self, "Success", "Transaction Saved Successfully.")

    #         self.load_data(self.supp_id)
    #         self.paid.setText("0")
    #         self.received.setText("0")
    #         self.note.clear()

    #     except Exception as e:
    #         db.rollback()
    #         AppMessageBox.critical(self, "Error", str(e))
    
    

    
    @Permissions.require_permission('transactions.create')
    def save_payment(self):

        if not require_open_session(self):
            return

        db = QSqlDatabase.database()

        if not db.transaction():
            AppMessageBox.critical(self, "Error", "Could not start database transaction.")
            return

        try:
            data = self._collect_supplier_payment_data()
            self._save_supplier_payment_transaction(data)

            if not db.commit():
                raise Exception("Could not commit supplier transaction.")

            AppMessageBox.information(self, "Success", "Transaction Saved Successfully.")

            self.load_data(self.supp_id)
            self.paid.setText("0")
            self.received.setText("0")
            self.note.clear()

        except Exception as e:
            db.rollback()
            AppMessageBox.critical(self, "Error", str(e))



    def _collect_supplier_payment_data(self):
        
        rep = self.rep.currentData()
        supplier = int(self.supp_id)

        paid_amount = float(self.paid.text() or 0)
        received_amount = float(self.received.text() or 0)

        if paid_amount > 0 and received_amount > 0:
            raise Exception("Cannot process Payment and Receipt together.")

        if paid_amount < 0 or received_amount < 0:
            raise Exception("Amounts cannot be negative.")

        if paid_amount == 0 and received_amount == 0:
            raise Exception("Enter paid or received amount.")

        balance_query = QSqlQuery()
        balance_query.prepare("SELECT payable, receiveable FROM supplier WHERE id = ?")
        balance_query.addBindValue(supplier)

        if not balance_query.exec() or not balance_query.next():
            raise Exception("Supplier not found.")

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

        if paid_amount > 0:
            transaction_type = "PAYMENT"
            paid = paid_amount

            due_amount = payable_before

            if paid_amount <= payable_before:
                remaining_due = payable_before - paid_amount
                payable_after = remaining_due
                receiveable_now = 0.0
                remaining_now = 0.0
                receiveable_after = receiveable_before
            else:
                overpayment = paid_amount - payable_before
                remaining_due = 0.0
                payable_after = 0.0
                receiveable_now = overpayment
                remaining_now = receiveable_before + overpayment
                receiveable_after = receiveable_before + overpayment

        elif received_amount > 0:
            transaction_type = "RECEIPT"
            received = received_amount

            due_amount = 0.0
            remaining_due = 0.0

            receiveable_now = 0.0

            if received_amount <= receiveable_before:
                remaining_now = receiveable_before - received_amount
                receiveable_after = remaining_now
                payable_after = payable_before
            else:
                excess = received_amount - receiveable_before

                _, accepted = AppMessageBox.confirm(
                    self,
                    "Excess Receipt",
                    "Received amount exceeds receivable.\n"
                    "Excess will be moved to Payable.\n\nContinue?",
                    confirm_label="Continue",
                    cancel_label="Cancel",
                    kind="warning",
                )

                if not accepted:
                    raise Exception("Receipt cancelled by user.")

                remaining_now = 0.0
                receiveable_after = 0.0
                payable_after = payable_before + excess
                remaining_due = excess


        session_id = get_active_session_id(strict=True)
        if session_id is None:
            raise Exception("No active session found.")

        payment = self.payment_handler.payment_data.copy()
        print(payment)
        
        
        return {
            "supplier": supplier,
            "rep": rep,
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

            "session_id": session_id,

            "payment_method": payment["payment_method"],
            "bank_name": payment["bank_name"],
            "account_no": payment["account_no"],
            "transaction_mode": payment["transaction_mode"],
            "wallet_provider": payment["wallet_provider"],
            "wallet_no": payment["wallet_no"],
            "payment_reference": payment["payment_reference"],
        }


    def _save_supplier_payment_transaction(self, data):
        
        query = QSqlQuery()
        query.prepare("""
            INSERT INTO supplier_transaction 
            (
                supplier, transaction_type, ref, return_ref,
                payable_before, due_amount, paid, remaining_due, payable_after,
                receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                rep, session_id,
                payment_method, bank_name, account_no, transaction_mode,
                wallet_provider, wallet_no, payment_reference
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        query.addBindValue(data["supplier"])
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

        query.addBindValue(data["rep"])
        query.addBindValue(data["session_id"])

        query.addBindValue(data["payment_method"])
        query.addBindValue(data["bank_name"])
        query.addBindValue(data["account_no"])
        query.addBindValue(data["transaction_mode"])

        query.addBindValue(data["wallet_provider"])
        query.addBindValue(data["wallet_no"])
        query.addBindValue(data["payment_reference"])

        if not query.exec():
            raise Exception(query.lastError().text())

        update_query = QSqlQuery()
        update_query.prepare("""
            UPDATE supplier
            SET payable = ?, receiveable = ?
            WHERE id = ?
        """)

        update_query.addBindValue(data["payable_after"])
        update_query.addBindValue(data["receiveable_after"])
        update_query.addBindValue(data["supplier"])

        if not update_query.exec():
            raise Exception(update_query.lastError().text())
        
        
    
    
    
    
    
    
    
    
    
        
        
            
    def clear_fields(self):
        
        self.suppliername.clear()
        self.supplieraddress.clear()
        self.payable.clear()
        self.receiveable.clear()
        self.paid.clear() 
        self.received.clear()
        self.note.clear()
        
        # clear rep combo
        self.rep.clear()
        
        self.payment_method.blockSignals(True); 
        self.payment_method.setCurrentIndex(0) 
        self.payment_method.blockSignals(False)
        
        self.populate_reps()                    
