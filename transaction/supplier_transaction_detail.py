
from PySide6.QtWidgets import QWidget, QPushButton, QGridLayout, QLabel, QLineEdit, QComboBox,QMessageBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt, QDate
from PySide6.QtSql import  QSqlQuery

from utilities.stylus import load_stylesheets





class SupplierTransactionDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QGridLayout()

        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        heading = QLabel("Transaction Detail", objectName='myheading')
        self.transactionlist = QPushButton('Show Suppliers Transactions', objectName='supplierlist')
        self.transactionlist.setCursor(Qt.PointingHandCursor)

        layout.addWidget(heading, 0, 0, 1, 12)
        layout.addWidget(self.transactionlist, 0,2)

        
        supplier_label = QLabel("Supplier Information")
        
        self.supplier_name = QLabel()
        self.supplier_contact = QLabel()
        self.creation_date = QLabel()
        
        layout.addWidget(supplier_label, 2, 1)
        layout.addWidget(self.supplier_name, 2, 3)
        layout.addWidget(self.supplier_contact, 3, 3)
        layout.addWidget(self.creation_date, 4, 3)
        
        rep_label = QLabel("Sales Rep")
        self.rep = QLabel()
        
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
        
        layout.addWidget(rep_label, 6, 1)
        layout.addWidget(self.rep, 6, 3)
        
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
        


    def get_supplier_transaction(self, id):
        
        query = QSqlQuery()
        query.prepare("""
            SELECT 
                supplier, transaction_type, ref, return_ref,
                payable_before, due_amount, paid, remaining_due, payable_after,
                receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                rep, note, creation_date
            FROM supplier_transaction 
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
        
        row = self.get_supplier_transaction(id)
        
            
        print("Supplier Transaction Query Executed")
        
        supplier_id = int(row["supplier"])
        transaction_type = row["transaction_type"]
        before = row["payable_before"]
        paid = row["paid"]
        received = row["received"]
        after = row["payable_after"]
        rep = int(row["rep"])
        creation = row["creation_date"]
        note = row["note"]
        
        print("Rep is, ", rep)
        
        # Get supplier name from database
        supplier_query = QSqlQuery()
        supplier_query.prepare("SELECT name, contact FROM supplier WHERE id = ?")
        supplier_query.addBindValue(supplier_id)
            
        if supplier_query.exec() and supplier_query.next():
            
            print("Supplier Query Executed")
            
            supplier_name = supplier_query.value(0)
            supplier_contact = supplier_query.value(1)

            self.supplier_name.setText(supplier_name)
            self.supplier_contact.setText(supplier_contact)
        
        else:
            print("Error Fetching Supplier, ", supplier_query.lastError().text())
            QMessageBox.critical(self, "Error", supplier_query.lastError().text())

            
        self.transaction.setText(transaction_type)
        self.balance.setText(str(before))
        self.paid.setText(str(paid))
        self.received.setText(str(received))
        self.after_balance.setText(str(after))
        self.creation_date.setText(creation.toString("dd-MM-yyyy"))
        self.note.setText(note)
        
        
        print("Bringing out Rep with name or rather id of ", rep)
        rep_query = QSqlQuery()
        rep_query.prepare("SELECT name FROM rep WHERE id = ?")
        rep_query.addBindValue(int(rep))
        
        
        if rep_query.exec() and rep_query.next():

            salesman_name = rep_query.value(0)
            self.rep.setText(salesman_name)
            
        else:
            QMessageBox.critical(self, "Error", rep_query.lastError().text())
        
    
        
                
        
    