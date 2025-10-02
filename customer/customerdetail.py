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
        
        self.banknamedata = QLabel() ; self.banknameedit = QLineEdit()
        self.accounttitledata = QLabel() ; self.accounttitleedit = QLineEdit()
        self.accountnumberdata = QLabel() ; self.accountnumberedit = QLineEdit()
        self.ibandata = QLabel() ; self.ibanedit = QLineEdit()
        
        self.jazzcashtitledata = QLabel() ; self.jazzcashtitleedit = QLineEdit()
        self.jazzcashnumberdata = QLabel() ; self.jazzcashnumberedit = QLineEdit()
        self.jazzcashcnicdata = QLabel() ; self.jazzcashcnicedit = QLineEdit()

        self.easypaisatitledata = QLabel() ; self.easypaisatitleedit = QLineEdit()
        self.easypaisanumberdata = QLabel() ; self.easypaisanumberedit = QLineEdit()
        self.easypaisacnicdata = QLabel() ; self.easypaisacnicedit = QLineEdit()

        self.field_pairs = [
            (self.namedata, self.nameedit),
            (self.contactdata, self.contactedit),
            (self.emaildata, self.emailedit),
            (self.statusdata, self.statusedit),
            (self.joiningdata, None),
            (self.payabledata, None),
            (self.receiveabledata, None),
            
            (self.banknamedata, self.banknameedit),
            (self.accounttitledata, self.accounttitleedit),
            (self.accountnumberdata, self.accountnumberedit),
            (self.ibandata, self.ibanedit),
            
            (self.jazzcashtitledata, self.jazzcashtitleedit),
            (self.jazzcashnumberdata, self.jazzcashnumberedit),
            (self.jazzcashcnicdata, self.jazzcashcnicedit),
            
            (self.easypaisatitledata, self.easypaisatitleedit),
            (self.easypaisanumberdata, self.easypaisanumberedit),
            (self.easypaisacnicdata, self.easypaisacnicedit)
            
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
    
    

      
    
    def load_banking_info(self, customer):
        
        # Check if banking info exists
        bank_check_query = QSqlQuery()
        bank_check_query.prepare("SELECT COUNT(*) FROM bank WHERE customer = ?")
        bank_check_query.addBindValue(customer)

        if not bank_check_query.exec() or not bank_check_query.next():
            print("Error checking banking info:", bank_check_query.lastError().text())
            return

        bank_info_exists = bank_check_query.value(0) > 0
        
        if not bank_info_exists:
            # Clear fields if no banking info
            self.banknamedata.setText("")
            self.accounttitledata.setText("")
            self.accountnumberdata.setText("")
            self.ibandata.setText("")
            return
        
        customer = int(customer)
        query = QSqlQuery()
        query.prepare("SELECT bank, title, account, iban FROM bank WHERE customer = ?")
        query.addBindValue(customer)

        if not query.exec():
            QMessageBox.critical(self, "Error", "Failed to load banking information: " + query.lastError().text())
            print("Error executing query:", query.lastError().text())
            return

        if query.next():
            self.banknamedata.setText(query.value(0))
            self.accounttitledata.setText(query.value(1))
            self.accountnumberdata.setText(query.value(2))
            self.ibandata.setText(query.value(3))


    def load_jazzcash_info(self, customer):
        
        # Check if JazzCash info exists
        jazzcash_check_query = QSqlQuery()
        jazzcash_check_query.prepare("SELECT COUNT(*) FROM jazzcash WHERE customer = ?")
        jazzcash_check_query.addBindValue(customer)

        if not jazzcash_check_query.exec() or not jazzcash_check_query.next():
            print("Error checking JazzCash info:", jazzcash_check_query.lastError().text())
            return

        jazzcash_info_exists = jazzcash_check_query.value(0) > 0

        if not jazzcash_info_exists:
            # Clear fields if no JazzCash info
            self.jazzcashtitledata.setText("")
            self.jazzcashnumberdata.setText("")
            self.jazzcashcnicdata.setText("")
            return
        
        
        customer = int(customer)
        query = QSqlQuery()
        query.prepare("SELECT title, mobile, cnic FROM jazzcash WHERE customer = ?")
        query.addBindValue(customer)

        if not query.exec():
            QMessageBox.critical(self, "Error", "Failed to load JazzCash information: " + query.lastError().text())
            print("Error executing query:", query.lastError().text())
            return

        if query.next():
            self.jazzcashtitledata.setText(query.value(0))
            self.jazzcashnumberdata.setText(query.value(1))
            self.jazzcashcnicdata.setText(query.value(2))
            
            
    def load_easypaisa_info(self, customer):
        
        # Check if EasyPaisa info exists
        easypaisa_check_query = QSqlQuery()
        easypaisa_check_query.prepare("SELECT COUNT(*) FROM easypaisa WHERE customer = ?")
        easypaisa_check_query.addBindValue(customer)    
        if not easypaisa_check_query.exec() or not easypaisa_check_query.next():
            print("Error checking EasyPaisa info:", easypaisa_check_query.lastError().text())
            return

        easypaisa_info_exists = easypaisa_check_query.value(0) > 0

        if not easypaisa_info_exists:
            # Clear fields if no EasyPaisa info
            self.easypaisatitledata.setText("")
            self.easypaisanumberdata.setText("")
            self.easypaisacnicdata.setText("")
            return

        customer = int(customer)
        query = QSqlQuery()
        query.prepare("SELECT account, mobile, cnic FROM easypaisa WHERE customer = ?")
        query.addBindValue(customer)

        if not query.exec():
            QMessageBox.critical(self, "Error", "Failed to load EasyPaisa information: " + query.lastError().text())
            print("Error executing query:", query.lastError().text())
            return

        if query.next():
            self.easypaisatitledata.setText(query.value(0))
            self.easypaisanumberdata.setText(query.value(1))
            self.easypaisacnicdata.setText(query.value(2))
            
            

            
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
            
            
        self.update_or_insert_banking_info()    
        self.update_or_insert_jazzcash_info()
        self.update_or_insert_easypaisa_info()    
        
            
        
        
    def update_or_insert_banking_info(self):
        
        customer = int(self.customer_id)
        supplier = None
        bankname = self.banknameedit.text().strip() if self.banknameedit.text().strip() else None
        accounttitle = self.accounttitleedit.text().strip() if self.accounttitleedit.text().strip() else None
        accountnumber = self.accountnumberedit.text().strip() if self.accountnumberedit.text().strip() else None
        iban = self.ibanedit.text().strip() if self.ibanedit.text().strip() else None
        
        # Check if Bank info exists
        bank_check_query = QSqlQuery()
        bank_check_query.prepare("SELECT COUNT(*) FROM bank WHERE customer = ?")
        bank_check_query.addBindValue(customer)

        if not bank_check_query.exec() or not bank_check_query.next():
            print("Error checking bank info:", bank_check_query.lastError().text())
            return

        bank_info_exists = bank_check_query.value(0) > 0
        
        if not bank_info_exists: 
            # Insert new bank info
            insert_bank_query = QSqlQuery()
            insert_bank_query.prepare("""
                INSERT INTO bank (supplier, customer, bank, title, account, iban)
                VALUES (?, ?, ?, ?, ?)
            """)

            insert_bank_query.addBindValue(supplier)
            insert_bank_query.addBindValue(customer)
            insert_bank_query.addBindValue(bankname)
            insert_bank_query.addBindValue(accounttitle)
            insert_bank_query.addBindValue(accountnumber)
            insert_bank_query.addBindValue(iban)

            if not insert_bank_query.exec():
                print("Error inserting bank info:", insert_bank_query.lastError().text())
            else:
                print("Bank info inserted successfully.")
            
            return
        
        else:
            
            # Update Bank Info
            bank_query = QSqlQuery()
            bank_query.prepare("""
                UPDATE bank
                SET bank=?, title=?, account=?, iban=?
                WHERE customer=?
            """)

            bank_query.addBindValue(bankname)
            bank_query.addBindValue(accounttitle)
            bank_query.addBindValue(accountnumber)
            bank_query.addBindValue(iban)
            bank_query.addBindValue(self.customer_id)

            if not bank_query.exec():
                print("Error updating bank info:", bank_query.lastError().text())
            else:
                print("Bank info updated successfully.")      

            
    
    
    def update_or_insert_jazzcash_info(self):
        
        supplier = None
        
        
        jazzcashtitle = self.jazzcashtitleedit.text().strip() if self.jazzcashtitleedit.text().strip() else None
        jazzcashnumber = self.jazzcashnumberedit.text().strip() if self.jazzcashnumberedit.text().strip() else None
        jazzcashcnic = self.jazzcashcnicedit.text().strip() if self.jazzcashcnicedit.text().strip() else None
        
        
        # Check if JazzCash info exists
        jazzcash_check_query = QSqlQuery()
        jazzcash_check_query.prepare("SELECT COUNT(*) FROM jazzcash WHERE customer = ?")
        jazzcash_check_query.addBindValue(self.customer_id)

        if not jazzcash_check_query.exec() or not jazzcash_check_query.next():
            print("Error checking JazzCash info:", jazzcash_check_query.lastError().text())
            return

        jazzcash_info_exists = jazzcash_check_query.value(0) > 0
        
        if not jazzcash_info_exists:
            # Insert new JazzCash info
            insert_jazzcash_query = QSqlQuery()
            insert_jazzcash_query.prepare("""
                INSERT INTO jazzcash (supplier, customer, title, mobile, cnic)
                VALUES (?, ?, ?, ?, ?)
            """)
            
            insert_jazzcash_query.addBindValue(supplier)
            insert_jazzcash_query.addBindValue(self.customer_id)
            insert_jazzcash_query.addBindValue(jazzcashtitle)
            insert_jazzcash_query.addBindValue(jazzcashnumber)
            insert_jazzcash_query.addBindValue(jazzcashcnic)

            if not insert_jazzcash_query.exec():
                print("Error inserting JazzCash info:", insert_jazzcash_query.lastError().text())
            else:
                print("JazzCash info inserted successfully.")
            
            return
        
        else:
            
            # Update JazzCash Info
            jazzcash_query = QSqlQuery()
            jazzcash_query.prepare("""
                UPDATE jazzcash
                SET title=?, mobile=?, cnic=?
                WHERE customer=?
            """)

            jazzcash_query.addBindValue(jazzcashtitle)
            jazzcash_query.addBindValue(jazzcashnumber)
            jazzcash_query.addBindValue(jazzcashcnic)
            jazzcash_query.addBindValue(self.customer_id)

            if not jazzcash_query.exec():
                print("Error updating JazzCash info:", jazzcash_query.lastError().text())
            else:
                print("JazzCash info updated successfully.")        
            
             
            
    def update_or_insert_easypaisa_info(self):
        
        supplier = None
        

        easypaisatitle = self.easypaisatitleedit.text().strip() if self.easypaisatitleedit.text().strip() else None
        easypaisanumber = self.easypaisanumberedit.text().strip() if self.easypaisanumberedit.text().strip() else None
        easypaisacnic = self.easypaisacnicedit.text().strip() if self.easypaisacnicedit.text().strip() else None

        # Check if EasyPaisa info exists
        easypaisa_check_query = QSqlQuery()
        easypaisa_check_query.prepare("SELECT COUNT(*) FROM easypaisa WHERE customer = ?")
        easypaisa_check_query.addBindValue(self.customer_id)

        if not easypaisa_check_query.exec() or not easypaisa_check_query.next():
            print("Error checking EasyPaisa info:", easypaisa_check_query.lastError().text())
            return

        easypaisa_info_exists = easypaisa_check_query.value(0) > 0
        
        if not easypaisa_info_exists:
            # Insert new EasyPaisa info
            insert_easypaisa_query = QSqlQuery()
            insert_easypaisa_query.prepare("""
                INSERT INTO easypaisa (supplier, customer, account, mobile, cnic)
                VALUES (?, ?, ?, ?, ?)
            """)
            insert_easypaisa_query.addBindValue(supplier)
            insert_easypaisa_query.addBindValue(self.customer_id)
            insert_easypaisa_query.addBindValue(easypaisatitle)
            insert_easypaisa_query.addBindValue(easypaisanumber)
            insert_easypaisa_query.addBindValue(easypaisacnic)

            if not insert_easypaisa_query.exec():
                print("Error inserting EasyPaisa info:", insert_easypaisa_query.lastError().text())
            else:
                print("EasyPaisa info inserted successfully.")
            
            return
        
        else:
            
            # Update EasyPaisa Info
            easypaisa_query = QSqlQuery()
            easypaisa_query.prepare("""
                UPDATE easypaisa
                SET account=?, mobile=?, cnic=?
                WHERE customer=?
            """)

            easypaisa_query.addBindValue(easypaisatitle)
            easypaisa_query.addBindValue(easypaisanumber)
            easypaisa_query.addBindValue(easypaisacnic)
            easypaisa_query.addBindValue(self.customer_id)

            if not easypaisa_query.exec():
                print("Error updating EasyPaisa info:", easypaisa_query.lastError().text())
            else:
                print("EasyPaisa info updated successfully.")       
            
            
            

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
            
            
            self.load_banking_info(self.customer_id)
            self.load_jazzcash_info(self.customer_id)
            self.load_easypaisa_info(self.customer_id)
            
            
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

                creation_date = creation_date.toString("yyyy-MM-dd HH:mm:ss")

                # # Get Supplier
                # # Get Supplier name from database
                # customer_query = QSqlQuery()
                # customer_query.prepare("SELECT name FROM customer WHERE id = ?")
                # customer_query.addBindValue(id)
                
                # customer_name = ""
                
                # if customer_query.exec() and customer_query.next():
                    
                #     customer_name = customer_query.value(0)    


                # Create table items
                # counter = QTableWidgetItem(str(row + 1))
                # customer = QTableWidgetItem(customer_name)
                
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
                            
                
                # detail = QPushButton('Details')
                # detail.setStyleSheet("""
                #         background-color: #333;
                #         color: #fff;
                #         font-weight: 600;
                    
                # """)
                
                # self.table.setCellWidget(row, 6, detail)
                # detail.clicked.connect(lambda _, tid=transaction_id: self.transaction_detail_signal.emit(tid))
                
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



        

            
            
            




