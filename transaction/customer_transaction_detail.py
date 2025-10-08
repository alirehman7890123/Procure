
from PySide6.QtWidgets import QWidget, QPushButton, QGridLayout, QLabel, QLineEdit, QComboBox,QMessageBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt, QDate
from PySide6.QtSql import  QSqlQuery

from utilities.stylus import load_stylesheets






class CustomerTransactionDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QGridLayout()

        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        heading = QLabel("Transaction Detail", objectName='myheading')
        self.transactionlist = QPushButton('Transactions List', objectName='supplierlist')
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
        


    def load_data(self, id):
        
        query = QSqlQuery()
        query.prepare("SELECT customer, transaction_type, balance_before, paid, received, balance_after, salesman, creation_date, note FROM customer_transaction WHERE id = ?")
        
        query.addBindValue(id)
        
        if query.exec() and query.next():
            
            customer_id = int(query.value(0))
            transaction_type = query.value(1)
            before = query.value(2)
            paid = query.value(3)
            received = query.value(4)
            after = query.value(5)
            salesman = query.value(6)
            creation = query.value(7)
            note = query.value(8)
            
            # Get Customer name from database
            customer_query = QSqlQuery()
            customer_query.prepare("SELECT name, contact FROM customer WHERE id = ?")
            customer_query.addBindValue(customer_id)
            
            if customer_query.exec() and customer_query.next():
                
                customer_name = customer_query.value(0)
                customer_contact = customer_query.value(1)

                self.customer_name.setText(customer_name)
                self.customer_contact.setText(customer_contact)
                
            self.transaction.setText(transaction_type)
            self.balance.setText(str(before))
            self.paid.setText(str(paid))
            self.received.setText(str(received))
            self.after_balance.setText(str(after))
            self.creation_date.setText(creation.toString("dd-MM-yyyy"))
            self.note.setText(note)
            
            
            
        # salesman Query   
        salesman_query = QSqlQuery()
        salesman_query.prepare("SELECT name FROM employee WHERE id = ?")
        salesman_query.addBindValue(salesman)
        
        
        if salesman_query.exec() and salesman_query.next():

            salesman_name = salesman_query.value(0)
            self.salesman.setText(salesman_name)
            
        else:
            
            QMessageBox.critical(self, "Error", salesman_query.lastError().text())
                
        
    