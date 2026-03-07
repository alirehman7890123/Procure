from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFrame, QLabel, QLineEdit, QVBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem, QSizePolicy, QMessageBox
from PySide6.QtCore import QFile, Qt, QDate, QDateTime, Signal
from PySide6.QtSql import  QSqlQuery
from utilities.stylus import load_stylesheets





class CustomerDetailWidget(QWidget):
    
    transaction_detail_signal = Signal(int)

    def __init__(self, parent=None):

        super().__init__(parent)
        
        self.supplier_id = None
        self.edit_mode = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Customer Detail", objectName="SectionTitle")
        self.customerlist = QPushButton("Customer List", objectName="TopRightButton")
        self.customerlist.setCursor(Qt.PointingHandCursor)
        self.customerlist.setFixedWidth(200)
        
        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedWidth(100)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.customerlist)

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
        
        labels = ["Customer", "Contact", "Email", "Status", "Joining Date", "Payable", "Receivable", 
                  "Bank Name", "Account Title", "Account Number", "IBAN",
                  "JazzCash Title", "JazzCash Number", "CNIC",
                  "EasyPaisa Title", "EasyPaisa Number", "CNIC"
                  ]

        self.namedata = QLabel() ; self.nameedit = QLineEdit()
        self.contactdata = QLabel() ; self.contactedit = QLineEdit()
        self.emaildata = QLabel() ; self.emailedit = QLineEdit()    
        self.statusdata = QLabel() ; self.statusedit = QLineEdit()
        self.joiningdata = QLabel()
        self.payabledata = QLabel()
        self.receiveabledata = QLabel()
        

        self.field_pairs = [
            (self.namedata, self.nameedit),
            (self.contactdata, self.contactedit),
            (self.emaildata, self.emailedit),
            (self.statusdata, self.statusedit),
            (self.joiningdata, None),
            (self.payabledata, None),
            (self.receiveabledata, None),
            
            
        ]

        for (label, (lbl_field, edit_field)) in zip(labels, self.field_pairs):

            row = QHBoxLayout()
            
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            
            lbl_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(lbl, 2)
            row.addWidget(lbl_field, 8)
            
            if edit_field:  # hidden initially
                edit_field.hide()
                row.addWidget(edit_field, 8)

            self.layout.addLayout(row)
            
            
        self.layout.addStretch()
        
        
        # Create Customer History Table
        
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.10, 0.15, 0.10, 0.10, 0.08, 0.12, 0.12, 0.08, 0.08, 0.09, 0.08])
        headers = ["Date", "Transaction Type", "Payment Type","Due", "Payable", "Receivable", "Paid", "Received", "Payable", "Receivable"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   

        self.table.setMinimumWidth(1000)
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)
        
        # Alternating row colors
        self.table.setAlternatingRowColors(True)

        # Selection behaviour
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        
        self.layout.addStretch()
        
        
        

        self.setStyleSheet(load_stylesheets())
        
        
    def hideEvent(self, event):
        
        if self.edit_mode:
            
            self.edit_mode = not self.edit_mode
            # reset state, discard edits
            self.edit_btn.setText("Edit")
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(edit.text())
                    edit.hide()
                    lbl.show()

        super().hideEvent(event)
           
        
        
    
    # === Toggle Edit Mode ===
    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.edit_btn.setText("Save")
            # Switch to QLineEdit
            for lbl, edit in self.field_pairs:
                if edit:
                    edit.setText(lbl.text())
                    lbl.hide()
                    edit.show()
        else:
            self.save_changes()
            self.edit_btn.setText("Edit")
            # Switch back to QLabel
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(edit.text())
                    edit.hide()
                    lbl.show()
    
    

      
    # === Save Changes ===
    def save_changes(self):
        
        if not self.customer_id:
            print("No customer loaded.")
            return

        query = QSqlQuery()
        query.prepare("""
            UPDATE customer
            SET name=?, contact=?, email=?, status=?
            WHERE id=?
        """)
        
        query.addBindValue(self.nameedit.text())
        query.addBindValue(self.contactedit.text())
        query.addBindValue(self.emailedit.text())
        query.addBindValue(self.statusedit.text())
        query.addBindValue(self.customer_id)

        if not query.exec():
            print("Error updating customer:", query.lastError().text())
        else:
            print("Customer updated successfully.")
            

            

    def load_customer_transactions(self, customer_id):
        
        self.customer_id = customer_id
        print("Loading customer ID:", self.customer_id)
        self.customer_id = int(self.customer_id)
        customer_query = QSqlQuery()
        customer_query.prepare("SELECT * FROM customer WHERE id = ?")
        customer_query.addBindValue(self.customer_id)
        
        if customer_query.exec() and customer_query.next():
            
            self.namedata.setText(customer_query.value(1))
            self.contactdata.setText(customer_query.value(2))
            self.emaildata.setText(customer_query.value(3))
            self.statusdata.setText(customer_query.value(4))
            joining_date = customer_query.value(5)
            
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)
                
            self.joiningdata.setText(joining_date)
            self.payabledata.setText(str(customer_query.value(6)))
            self.receiveabledata.setText(str(customer_query.value(7)))
            
            
           
        print("Loading Customer Transaction")
        query = QSqlQuery()
        query.prepare("""SELECT 
                                creation_date,                                
                                transaction_type, 
                                receiveable_now,
                                payable_before,
                                receiveable_before,
                                paid,
                                received,
                                payable_after,
                                receiveable_after, 
                                id
                                FROM customer_transaction 
                                WHERE customer = ?
                      
                      """)
        query.addBindValue(self.customer_id)
        
        
        if not query.exec():
            
            print("Error executing query:", query.lastError().text())
            return
        
        else:
            self.table.setRowCount(0)  # Clear existing rows
            row = 0
            
            while query.next():
                
                self.table.insertRow(row)
                
                
                creation_date = query.value(0)
                transaction_type = str(query.value(1))
                payment_type = "Cash"
                total_now = str(query.value(2))
                payable_before = str(query.value(3))
                receiveable_before = str(query.value(4))
                paid = str(query.value(5))
                received = str(query.value(6))
                payable_after = str(query.value(7))
                receiveable_after = str(query.value(8))
                transaction_id = int(query.value(9))

               
                
                date_item = QTableWidgetItem(str(creation_date))
                transaction_type = QTableWidgetItem(transaction_type)
                payment_type = QTableWidgetItem(payment_type)
                total_now = QTableWidgetItem(total_now)
                payable_before = QTableWidgetItem(payable_before)
                receiveable_before = QTableWidgetItem(receiveable_before)
                
                paid = QTableWidgetItem(paid)
                received = QTableWidgetItem(received)
                payable_after = QTableWidgetItem(payable_after)
                receiveable_after = QTableWidgetItem(receiveable_after)
                

                # Add items to table
                self.table.setItem(row, 0, date_item)
                self.table.setItem(row, 1, transaction_type)
                self.table.setItem(row, 2, payment_type)
                self.table.setItem(row, 3, total_now)
                self.table.setItem(row, 4, payable_before)
                self.table.setItem(row, 5, receiveable_before)
                self.table.setItem(row, 6, paid) 
                self.table.setItem(row, 7, received) 
                self.table.setItem(row, 8, payable_after) 
                self.table.setItem(row, 9, receiveable_after) 
                            
                
                row += 1
        
        
        
                
            



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



        

            
            
            




