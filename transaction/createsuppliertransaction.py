from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QLabel, QLineEdit, QComboBox,QMessageBox, QVBoxLayout, QFrame, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt, QDate
from PySide6.QtSql import  QSqlQuery, QSql  
from PySide6.QtSql import QSqlDatabase

from PySide6.QtGui import QKeySequence, QShortcut

from utilities.stylus import load_stylesheets





class CreateSupplierTransactionWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        
        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Pay / Receive Payment by Supplier", objectName="SectionTitle")
        self.transactionlist = QPushButton("Transactions List", objectName="TopRightButton")
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
        receiveable_row.addWidget(self.payable, 2)
        
        self.layout.addLayout(receiveable_row)
        
        
        
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
        self.layout.addStretch()
        
        savepayment = QPushButton('Save Payment', objectName="SaveButton")
        savepayment.setCursor(Qt.PointingHandCursor)
        savepayment.clicked.connect(self.save_payment)
        
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.save_payment)     

        
        
        self.setStyleSheet(load_stylesheets())

        


    
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
                
        
    

    def save_payment(self):
        
        # Get Data to Insert into supplier transaction table
        
        db = QSqlDatabase.database()
        db.transaction()
        
        try:
                
            rep = self.rep.currentData()
            supplier = int(self.supp_id)
             
            supplier_query = QSqlQuery()
            supplier_query.prepare("SELECT payable, receiveable FROM supplier where id = ?")
            supplier_query.addBindValue(supplier)
            
            if supplier_query.exec() and supplier_query.next():
                
                supplier_payable = supplier_query.value(0)
                supplier_receiveable = supplier_query.value(1)

                supplier_payable = float(supplier_payable)
                supplier_receiveable = float(supplier_receiveable)
                                
            else:
                
                print("Error ", supplier_query.lastError().text())
                QMessageBox.critical(self, "Error", "Supplier not found or database error.")
                raise Exception
            
            
            paid_amount = self.paid.text()
            paid_amount = float(paid_amount)  
            
            received_amount = self.received.text()
            received_amount = float(received_amount)      
            
            transaction_type = 'payment'
            ref_no = None
            return_ref = None
            
            payable_before = supplier_payable
            due_amount = supplier_payable
            paid = paid_amount
            remaining_due = payable_before - paid_amount
            
            if remaining_due > 0:
                payable_after = remaining_due
            
            
            extra_receiveable = 0.0
            
            if remaining_due < 0:
                payable_after = 0
                extra_receiveable = abs(remaining_due)

            
            receiveable_before = supplier_receiveable + extra_receiveable
            receiveable_now = supplier_receiveable + extra_receiveable
            received = received_amount
            remaining_now = receiveable_now - received_amount
            receiveable_after = remaining_now
            
            # insert transaction
            query = QSqlQuery()
            query.prepare("""
                            INSERT INTO supplier_transaction 
                            (supplier, transaction_type, ref, return_ref,
                            payable_before, due_amount, paid, remaining_due, payable_after,
                            receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                            rep) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            
                            """)
            
            query.addBindValue(supplier)
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
            query.addBindValue(rep)
            
            
            if query.exec():
                    
                insert_id = query.lastInsertId()
                print("Transaction is saved ...")
                QMessageBox.information(None, "Success", "Supplier Transaction Stored Successfully with ID: " + str(insert_id) )
                
                
            else:
                
                QMessageBox.critical(None, "Error", query.lastError().text())
                print("Query error:", query.lastError().text())
                raise Exception 
            
            
            
            supplier_query = QSqlQuery()
            supplier_query.prepare("SELECT payable, receiveable FROM supplier where id = ?")
            supplier_query.addBindValue(supplier)
            
            if supplier_query.exec() and supplier_query.next():
                
                supplier_payable = supplier_query.value(0)
                supplier_receiveable = supplier_query.value(1)

                supplier_payable = float(supplier_payable)
                supplier_receiveable = float(supplier_receiveable)
                                
            else:
                
                print("Error ", supplier_query.lastError().text())
                QMessageBox.critical(self, "Error", "Supplier not found or database error.")
                raise Exception
            
            print("Payable and Receiveable are : ", supplier_payable, supplier_receiveable)
            
            supplier_payable = remaining_due
            supplier_receiveable = remaining_now
            
            update_supplier = QSqlQuery()
            update_supplier.prepare("UPDATE supplier SET payable = ? , receiveable = ? WHERE id = ?")
            
            update_supplier.addBindValue(supplier_payable)
            update_supplier.addBindValue(supplier_receiveable)
            update_supplier.addBindValue(supplier)
            
            print("New Payable and Receiveable are : ", supplier_payable, supplier_receiveable)
            
            if update_supplier.exec(): 
                
                print("Supplier Balance updated successfully")
            
            else:
                print("Supplier Updating Error...")
                QMessageBox.critical(self, "Error", update_supplier.lastError().text())
                raise Exception
            
            db.commit()
        
            self.clear_fields()
            
        except Exception as e:
            
            print("Exception ", str(e))
            db.rollback()
                
        
        
            
    def clear_fields(self):
        
        self.suppliername.clear()
        self.supplieraddress.clear()
        self.payable.clear()
        self.receiveable().clear()
        self.paid.clear() 
        self.received.clear()
        self.note.clear()                    

