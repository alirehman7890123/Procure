from PySide6.QtWidgets import QWidget, QPushButton, QGridLayout, QLabel, QLineEdit, QComboBox, QMessageBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt,QDate
from PySide6.QtSql import  QSqlQuery
from utilities.stylus import load_stylesheets





class CreateCustomerTransactionWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QGridLayout()

        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        heading = QLabel("Pay / Receive Payment by customer", objectName='myheading')
        self.transactionlist = QPushButton('Transactions List', objectName='supplierlist')
        self.transactionlist.setCursor(Qt.PointingHandCursor)

        layout.addWidget(heading, 0, 0, 1, 12)
        layout.addWidget(self.transactionlist, 0,2)



        # customer Transactions Section
        
        customer_label = QLabel("customer Information")
        
        self.customername = QLabel()
        self.customeraddress = QLabel()
        
        layout.addWidget(customer_label, 2, 1)
        layout.addWidget(self.customername, 2, 3)
        layout.addWidget(self.customeraddress, 3, 3)
        
        salesman_label = QLabel("Sales Man")
        self.salesman = QComboBox()
        
        makepayment = QLabel("Make Payment", objectName='myheading')
        layout.addWidget(makepayment, 5,1)

        payable_label = QLabel("Payable Amount")
        self.payable = QLabel()
        
        receiveable_label = QLabel("Receiveable Amount")
        self.receiveable = QLabel()
        
        paid_label = QLabel("Paid Amount")
        self.paid= QLineEdit()
        self.paid.setText("0")
        
        
        received_label = QLabel("Received Amount")
        self.received= QLineEdit()
        self.received.setText("0")
        
        
        
        layout.addWidget(salesman_label, 6, 1)
        layout.addWidget(self.salesman, 6, 3)
        
        layout.addWidget(payable_label, 7, 1)
        layout.addWidget(self.payable, 7, 3)
        
        layout.addWidget(receiveable_label, 8, 1)
        layout.addWidget(self.receiveable, 8, 3)
        
        layout.addWidget(paid_label, 9, 1)
        layout.addWidget(self.paid, 9, 3)
        
        layout.addWidget(received_label, 10, 1)
        layout.addWidget(self.received, 10, 3)
        
        
        note_label = QLabel("Note")
        
        self.note = QLineEdit()
        self.note.setPlaceholderText("Note")
        
        
        layout.addWidget(note_label, 13, 1)
        layout.addWidget(self.note, 13, 3)
        
        
        savepayment = QPushButton('Save Payment', objectName="supplierlist")
        savepayment.clicked.connect(self.save_payment)       
        
        layout.addWidget(savepayment, 16, 1) 


        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer, 17, 0, 1, 3)
        
        
        self.setStyleSheet(load_stylesheets())

        self.setLayout(layout)


    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        
    
    
    



    def load_data(self, id):
        
        print("Loading customer ID:", id)
        id = int(id)
        
        query = QSqlQuery()
        query.prepare("SELECT id, name, contact, payable, receiveable FROM customer WHERE id = ?")
        query.addBindValue(id)
        
        if query.exec() and query.next():
     
            self.cust_id = int(query.value(0))    
            self.customername.setText(f"{ query.value(0)} - {query.value(1)}" )
            self.customeraddress.setText(query.value(2))
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
        
        # Get Data to Insert into supplier transaction table
        
        salesman = self.salesman
        
        customer = self.cust_id
        customer = int(customer)
        
        customer_query = QSqlQuery()
        customer_query.prepare("SELECT payable, receiveable FROM customer where id = ?")
        customer_query.addBindValue(customer)
        
        if customer_query.exec() and customer_query.next():
            
            payable_before = customer_query.value(0)
            receiveable_before = customer_query.value(1)
            payable = float(payable_before)
            receiveable = float(receiveable_before)
            
        else:
            
            print("Error ", customer_query.lastError().text())
            QMessageBox.critical(self, "Error", "Customer not found or database error.")
            raise Exception 
        
        
        paid_amount = self.paid.text()
        paid_amount = float(paid_amount)  
        
        received_amount = self.received.text()
        received_amount = float(received_amount)  

        transaction_type = 'payment'
        ref_no = None
        return_ref = None        
        payable_before = payable
        due_amount = payable
        paid = paid_amount
        remaining_due = payable - paid_amount
        payable_after = remaining_due
        
        receiveable_before = receiveable
        receiveable_now = receiveable
        received = received_amount
        remaining_now = receiveable_now - received
        receiveable_after = remaining_now 
        
    
    
    
        # insert transaction
        query = QSqlQuery()
        query.prepare("""
                        INSERT INTO customer_transaction 
                        (customer, transaction_type, ref, return_ref,
                        payable_before, due_amount, paid, remaining_due, payable_after,
                        receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                        salesman) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        
                        """)
        
        query.addBindValue(customer)
        query.addBindValue(transaction_type)
        query.addBindValue(ref_no)
        query.addBindValue(return_ref)
        query.addBindValue(payable_before)
        query.addBindValue(due_amount)
        query.addBindValue(paid)
        query.addBindValue(remaining_due)
        query.addBindValue(payable_after)
        query.addBindValue(receiveable_before)
        query.addBindValue(receiveable_now)
        query.addBindValue(received)
        query.addBindValue(remaining_now)
        query.addBindValue(receiveable_after)
        query.addBindValue(salesman)
        
        
        if query.exec():
            
            insert_id = query.lastInsertId()
            print("Transaction is saved ...")
            QMessageBox.information(None, "Success", "Customer Transaction Stored Successfully with ID: " + str(insert_id) )
            
            
        else:
            
            QMessageBox.critical(None, "Error", query.lastError().text())
            print("Query error:", query.lastError().text())
            raise Exception 
        
        
        
        customer_query = QSqlQuery()
        customer_query.prepare("SELECT payable, receiveable FROM customer where id = ?")
        customer_query.addBindValue(customer)
        
        if customer_query.exec() and customer_query.next():
            
            customer_payable = customer_query.value(0)
            customer_receiveable = customer_query.value(1)

            customer_payable = float(customer_payable)
            customer_receiveable = float(customer_receiveable)
                            
        else:
            
            print("Error ", customer_query.lastError().text())
            QMessageBox.critical(self, "Error", "customer not found or database error.")
            raise Exception
        
        print("Payable and Receiveable are : ", customer_payable, customer_receiveable)
        
        
        update_customer = QSqlQuery()
        update_customer.prepare("UPDATE customer SET payable = ? , receiveable = ? WHERE id = ?")
        
        update_customer.addBindValue(remaining_due)
        update_customer.addBindValue(remaining_now)
        update_customer.addBindValue(customer)
        
        print("New Payable and Receiveable are : ", remaining_due, remaining_now)
        
        if update_customer.exec(): 
            
            print("customer Balance updated successfully")
        
        else:
            QMessageBox.critical(self, "Error", update_customer.lastError().text())
            raise Exception
        
        
        
        
        
        
    def clear_fields(self):
        
        self.customername.clear()
        self.customeraddress.clear()
        self.payable.clear()
        self.receiveable().clear()
        self.paid.clear() 
        self.received.clear()
        self.note.clear()                    



            
            
            

