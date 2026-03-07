from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFrame, QLabel, QLineEdit, QComboBox, QMessageBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt,QDate
from PySide6.QtSql import  QSqlQuery
from PySide6.QtSql import QSqlDatabase
from PySide6.QtGui import QKeySequence, QShortcut


from utilities.stylus import load_stylesheets





class CreateCustomerTransactionWidget(QWidget):

    # def __init__(self, parent=None):

    #     super().__init__(parent)

    #     self.layout = QVBoxLayout(self)
    #     self.layout.setContentsMargins(40, 40, 40, 40)
    #     self.layout.setSpacing(20)
        
    #     # === Header Row ===
    #     header_layout = QHBoxLayout()
    #     heading = QLabel("Pay / Receive Payment by Customer", objectName="SectionTitle")
    #     self.transactionlist = QPushButton("Transactions List", objectName="TopRightButton")
    #     self.transactionlist.setCursor(Qt.PointingHandCursor)
    #     self.transactionlist.setFixedWidth(200)
    #     header_layout.setContentsMargins(0, 0, 0, 10)
    #     header_layout.addWidget(heading)
    #     header_layout.addWidget(self.transactionlist)

    #     self.layout.addLayout(header_layout)



    #     line = QFrame()
    #     line.setObjectName("lineSeparator")

    #     line.setFrameShape(QFrame.HLine)
    #     line.setFrameShadow(QFrame.Sunken)
    #     line.setStyleSheet("""
    #             QFrame#lineSeparator {
    #                 border: none;
    #                 border-top: 2px solid #333;
    #             }
    #         """)

    #     self.layout.addWidget(line)
    #     self.layout.addSpacing(20)



    #     # customer Transactions Section
        
    #     customer_heading_layout = QHBoxLayout()
    #     customer_heading = QLabel("Customer Information", objectName="SubHeading")
    #     customer_heading_layout.addWidget(customer_heading)

    #     self.layout.addLayout(customer_heading_layout)
        
        
    #     customer_row = QHBoxLayout()
        
    #     customer_label = QLabel("Customer")
    #     customer_label.setFixedWidth(300)
        
    #     self.customername = QLabel()
    #     customer_row.addWidget(customer_label, 1)
    #     customer_row.addWidget(self.customername, 2)
        
    #     self.layout.addLayout(customer_row)
        
        
        
        
    #     self.customername = QLabel()
    #     self.customeraddress = QLabel()
        
    #     layout.addWidget(customer_label, 2, 1)
    #     layout.addWidget(self.customername, 2, 3)
    #     layout.addWidget(self.customeraddress, 3, 3)
        
    #     salesman_label = QLabel("Sales Man")
    #     self.salesman = QComboBox()
        
    #     makepayment = QLabel("Make Payment", objectName='myheading')
    #     layout.addWidget(makepayment, 5,1)

    #     payable_label = QLabel("Payable Amount")
    #     self.payable = QLabel()
        
    #     receiveable_label = QLabel("Receiveable Amount")
    #     self.receiveable = QLabel()
        
    #     paid_label = QLabel("Paid Amount")
    #     self.paid= QLineEdit()
    #     self.paid.setText("0")
        
        
    #     received_label = QLabel("Received Amount")
    #     self.received= QLineEdit()
    #     self.received.setText("0")
        
        
        
    #     layout.addWidget(salesman_label, 6, 1)
    #     layout.addWidget(self.salesman, 6, 3)
        
    #     layout.addWidget(payable_label, 7, 1)
    #     layout.addWidget(self.payable, 7, 3)
        
    #     layout.addWidget(receiveable_label, 8, 1)
    #     layout.addWidget(self.receiveable, 8, 3)
        
    #     layout.addWidget(paid_label, 9, 1)
    #     layout.addWidget(self.paid, 9, 3)
        
    #     layout.addWidget(received_label, 10, 1)
    #     layout.addWidget(self.received, 10, 3)
        
        
    #     note_label = QLabel("Note")
        
    #     self.note = QLineEdit()
    #     self.note.setPlaceholderText("Note")
        
        
    #     layout.addWidget(note_label, 13, 1)
    #     layout.addWidget(self.note, 13, 3)
        
        
    #     savepayment = QPushButton('Save Payment', objectName="supplierlist")
    #     savepayment.clicked.connect(self.save_payment)       
        
    #     layout.addWidget(savepayment, 16, 1) 


    #     spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    #     layout.addItem(spacer, 17, 0, 1, 3)
        
        
    #     self.setStyleSheet(load_stylesheets())

    #     self.setLayout(layout)


    
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
        
    
    
    
    def save_payment(self):

        db = QSqlDatabase.database()
        db.transaction()

        try:

            salesman = self.salesman.currentData()
            customer = int(self.cust_id)

            # --- Fetch Customer Balance ---
            balance_query = QSqlQuery()
            balance_query.prepare("SELECT payable, receiveable FROM customer WHERE id = ?")
            balance_query.addBindValue(customer)

            if not balance_query.exec() or not balance_query.next():
                raise Exception("Customer not found.")

            payable_before = float(balance_query.value(0) or 0.0)
            receiveable_before = float(balance_query.value(1) or 0.0)

            paid_amount = float(self.paid.text() or 0)
            received_amount = float(self.received.text() or 0)

            if paid_amount > 0 and received_amount > 0:
                raise Exception("Cannot process both Paid and Received together.")

            if paid_amount < 0 or received_amount < 0:
                raise Exception("Amounts cannot be negative.")

            transaction_type = None

            payable_after = payable_before
            receiveable_after = receiveable_before

            # ====================================
            # CUSTOMER PAYMENT (Customer pays you)
            # ====================================
            if received_amount > 0:

                transaction_type = "RECEIPT"

                if received_amount <= receiveable_before:
                    receiveable_after = receiveable_before - received_amount

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

                    receiveable_after = 0
                    payable_after = payable_before + excess

            # ====================================
            # REFUND (You pay customer)
            # ====================================
            elif paid_amount > 0:

                transaction_type = "REFUND"

                if paid_amount <= payable_before:
                    payable_after = payable_before - paid_amount

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

                    payable_after = 0
                    receiveable_after = receiveable_before + excess

            else:
                raise Exception("Enter Paid or Received amount.")

            # --- Insert Transaction ---
            query = QSqlQuery()
            query.prepare("""
                INSERT INTO customer_transaction
                (customer, transaction_type,
                payable_before, paid, payable_after,
                receiveable_before, received, receiveable_after,
                salesman)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)

            query.addBindValue(customer)
            query.addBindValue(transaction_type)

            query.addBindValue(payable_before)
            query.addBindValue(paid_amount)
            query.addBindValue(payable_after)

            query.addBindValue(receiveable_before)
            query.addBindValue(received_amount)
            query.addBindValue(receiveable_after)

            query.addBindValue(salesman)

            if not query.exec():
                raise Exception(query.lastError().text())

            # --- Update Customer Master ---
            update_query = QSqlQuery()
            update_query.prepare("""
                UPDATE customer
                SET payable = ?, receiveable = ?
                WHERE id = ?
            """)

            update_query.addBindValue(payable_after)
            update_query.addBindValue(receiveable_after)
            update_query.addBindValue(customer)

            if not update_query.exec():
                raise Exception(update_query.lastError().text())

            db.commit()

            QMessageBox.information(self, "Success", "Customer Transaction Saved Successfully.")

            self.load_data(self.cust_id)
            self.paid.setText("0")
            self.received.setText("0")
            self.note.clear()

        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", str(e))

    
    

        
        
         
        
        
    def clear_fields(self):
        
        self.customername.clear()
        self.customercontact.clear()
        self.payable.clear()
        self.receiveable().clear()
        self.paid.clear() 
        self.received.clear()
        self.note.clear()                    



            
            
            

