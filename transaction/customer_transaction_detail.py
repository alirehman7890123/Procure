
from PySide6.QtWidgets import QWidget, QPushButton, QGridLayout, QLabel, QLineEdit, QComboBox,QMessageBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt, QDateTime
from PySide6.QtSql import  QSqlQuery

from utilities.stylus import load_stylesheets






class CustomerTransactionDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QGridLayout()

        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        heading = QLabel("Transaction Detail", objectName='SectionTitle')
        self.transactionlist = QPushButton('Transactions List', objectName='TopRightButton')
        self.transactionlist.setCursor(Qt.PointingHandCursor)

        layout.addWidget(heading, 0, 0, 1, 12)
        layout.addWidget(self.transactionlist, 0,2)

        
        customer_label = QLabel("Customer Information")
        
        self.customer_name = QLabel()
        self.customer_contact = QLabel()
        self.creation_date = QLabel()
        
        layout.addWidget(customer_label, 2, 1)
        layout.addWidget(self.customer_name, 2, 3)
        layout.addWidget(self.customer_contact, 3, 3)
        layout.addWidget(self.creation_date, 4, 3)
        
        salesman_label = QLabel("Sales Rep")
        self.salesman = QLabel()
        
        transaction_label = QLabel("Transaction Type")
        self.transaction = QLabel()

        balance_label = QLabel("Before Balance")
        self.balance = QLabel()
        
        paid_label = QLabel("Paid Amount")
        self.paid = QLabel()
        
        received_label = QLabel("Received Amount")
        self.received = QLabel()
        
        after_balance_label = QLabel("After Balance")
        self.after_balance = QLabel("0.00")
        
        layout.addWidget(salesman_label, 6, 1)
        layout.addWidget(self.salesman, 6, 3)
        
        layout.addWidget(transaction_label, 7, 1)
        layout.addWidget(self.transaction)
        
        layout.addWidget(balance_label, 8, 1)
        layout.addWidget(self.balance, 8, 3)
        
        layout.addWidget(paid_label, 9, 1)
        layout.addWidget(self.paid, 9, 3)
        
        layout.addWidget(received_label, 10, 1)
        layout.addWidget(self.received, 10, 3)
        
        layout.addWidget(after_balance_label, 11, 1)
        layout.addWidget(self.after_balance, 11, 3)
        
        note_label = QLabel("Note")
        self.note = QLabel()
        
        layout.addWidget(note_label, 12, 1)
        layout.addWidget(self.note, 12, 3)
        

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer, 17, 0, 1, 3)
        
        
        self.setStyleSheet(load_stylesheets())

        self.setLayout(layout)



        

    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        


    # def load_data(self, id):
        
    #     query = QSqlQuery()
    #     query.prepare("SELECT customer, transaction_type, balance_before, paid, received, balance_after, salesman, creation_date, note FROM customer_transaction WHERE id = ?")
        
    #     query.addBindValue(id)
        
    #     if query.exec() and query.next():
            
    #         customer_id = int(query.value(0))
    #         transaction_type = query.value(1)
    #         before = query.value(2)
    #         paid = query.value(3)
    #         received = query.value(4)
    #         after = query.value(5)
    #         salesman = query.value(6)
    #         creation = query.value(7)
    #         note = query.value(8)
            
    #         # Get Customer name from database
    #         customer_query = QSqlQuery()
    #         customer_query.prepare("SELECT name, contact FROM customer WHERE id = ?")
    #         customer_query.addBindValue(customer_id)
            
    #         if customer_query.exec() and customer_query.next():
                
    #             customer_name = customer_query.value(0)
    #             customer_contact = customer_query.value(1)

    #             self.customer_name.setText(customer_name)
    #             self.customer_contact.setText(customer_contact)
                
    #         self.transaction.setText(transaction_type)
    #         self.balance.setText(str(before))
    #         self.paid.setText(str(paid))
    #         self.received.setText(str(received))
    #         self.after_balance.setText(str(after))
    #         self.creation_date.setText(creation.toString("dd-MM-yyyy"))
    #         self.note.setText(note)
            
            
        
    #     salesman = int(salesman)
    #     # salesman Query   
    #     salesman_query = QSqlQuery()
    #     salesman_query.prepare("SELECT name FROM employee WHERE id = ?")
    #     salesman_query.addBindValue(salesman)
        
        
    #     if salesman_query.exec() and salesman_query.next():

    #         salesman_name = salesman_query.value(0)
    #         self.salesman.setText(salesman_name)
            
    #     else:
            
    #         QMessageBox.critical(self, "Error", salesman_query.lastError().text())
                
    def get_customer_transaction(self, id):
    
        query = QSqlQuery()
        query.prepare("""
            SELECT 
                customer, transaction_type, ref, return_ref,
                payable_before, due_amount, paid, remaining_due, payable_after,
                receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                salesman, note, creation_date
            FROM customer_transaction 
            WHERE id = ?
        """)
        query.addBindValue(id)

        if not query.exec():
            print("SQL Error:", query.lastError().text())
            return None

        if query.next():
            record = query.record()
            row_dict = {}
            for i in range(record.count()):
                field_name = record.fieldName(i)
                value = query.value(i)
                row_dict[field_name] = value
            return row_dict
        
        return None
    
        
    
    
    def load_data(self, id):
    
        row = self.get_customer_transaction(id)
        
        if not row:
            QMessageBox.critical(self, "Error", "Transaction not found.")
            return

        print("Customer Transaction Query Executed")

        customer_id = row["customer"]
        transaction_type = row["transaction_type"]
        before = row["payable_before"]
        paid = row["paid"]
        received = row["received"]
        after = row["payable_after"]
        salesman = row["salesman"]
        creation = row["creation_date"]
        note = row["note"]

        # ==========================
        # Customer Info
        # ==========================

        if customer_id is not None:

            customer_query = QSqlQuery()
            customer_query.prepare("SELECT name, contact FROM customer WHERE id = ?")
            customer_query.addBindValue(int(customer_id))
            
            if customer_query.exec() and customer_query.next():
                
                print("Customer Query Executed")
                
                customer_name = customer_query.value(0)
                customer_contact = customer_query.value(1)

            else:
                QMessageBox.critical(self, "Error", customer_query.lastError().text())
                return

        else:
            
            customer_name = "Walk-in Customer"
            customer_contact = "-"

        self.customer_name.setText(str(customer_name))
        self.customer_contact.setText(str(customer_contact))

        # ==========================
        # Transaction Info
        # ==========================

        self.transaction.setText(str(transaction_type))
        self.balance.setText(str(before))
        self.paid.setText(str(paid))
        self.received.setText(str(received))
        self.after_balance.setText(str(after))
        self.creation_date.setText(str(creation))
        self.note.setText(str(note))

        # ==========================
        # Salesman Info
        # ==========================

        if salesman is not None:

            rep_query = QSqlQuery()
            rep_query.prepare("SELECT name FROM employee WHERE id = ?")
            rep_query.addBindValue(int(salesman))
            
            if rep_query.exec() and rep_query.next():
                salesman_name = rep_query.value(0)
            else:
                salesman_name = "-"
        else:
            salesman_name = "-"

        self.salesman.setText(str(salesman_name))

    
        
    # def load_data(self, id):
        
    #     print("Looking for transaction ID:", id)

    #     debug_query = QSqlQuery()
    #     debug_query.exec("SELECT id FROM customer_transaction")
    #     while debug_query.next():
    #         print("Existing ID:", debug_query.value(0))

    #     query = QSqlQuery()
    #     query.prepare("""
    #         SELECT 
    #             ct.customer,
    #             COALESCE(c.name, 'Walk-in Customer'),
    #             COALESCE(c.contact, '-'),
    #             ct.transaction_type,
    #             ct.balance_before,
    #             ct.paid,
    #             ct.received,
    #             ct.balance_after,
    #             COALESCE(e.name, '-'),
    #             ct.creation_date,
    #             ct.note
    #         FROM customer_transaction ct
    #         LEFT JOIN customer c ON ct.customer = c.id
    #         LEFT JOIN employee e ON ct.salesman = e.id
    #         WHERE ct.id = ?
    #     """)

    #     query.addBindValue(id)

    #     if not query.exec():
    #         QMessageBox.critical(self, "Error", query.lastError().text())
    #         return

    #     if not query.next():
    #         QMessageBox.critical(self, "Error", "Transaction not found.")
    #         return

    #     # --- Extract Values ---
    #     customer_name = str(query.value(1))
    #     customer_contact = str(query.value(2))
    #     transaction_type = str(query.value(3))
    #     before = float(query.value(4) or 0)
    #     paid = float(query.value(5) or 0)
    #     received = float(query.value(6) or 0)
    #     after = float(query.value(7) or 0)
    #     salesman_name = str(query.value(8))
    #     creation_value = query.value(9)
    #     note = str(query.value(10) or "")

    #     # --- Handle Date ---
    #     if isinstance(creation_value, QDateTime):
    #         creation_str = creation_value.toString("dd-MM-yyyy")
    #     else:
    #         dt = QDateTime.fromString(str(creation_value), "yyyy-MM-dd HH:mm:ss")
    #         creation_str = dt.toString("dd-MM-yyyy") if dt.isValid() else str(creation_value)

    #     # --- Set UI ---
    #     self.customer_name.setText(customer_name)
    #     self.customer_contact.setText(customer_contact)

    #     self.transaction.setText(transaction_type)
    #     self.balance.setText(f"{before:.2f}")
    #     self.paid.setText(f"{paid:.2f}")
    #     self.received.setText(f"{received:.2f}")
    #     self.after_balance.setText(f"{after:.2f}")

    #     self.salesman.setText(salesman_name)
    #     self.creation_date.setText(creation_str)
    #     self.note.setText(note)




        
        