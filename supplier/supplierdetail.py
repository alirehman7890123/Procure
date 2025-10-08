# from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
# from PySide6.QtCore import QFile, Qt,QDate, QDateTime
# from PySide6.QtSql import  QSqlQuery


# def load_stylesheet(filename):
#     """ Load and return the CSS stylesheet from a file. """
#     file = QFile(filename)
#     if not file.open(QFile.ReadOnly | QFile.Text):
#         print(f"Error opening file: {filename}")
#         return ""
    
#     css = file.readAll().data().decode()
#     file.close()
#     return css



# class SupplierDetailWidget(QWidget):

#     def __init__(self, parent=None):

#         super().__init__(parent)

#         self.layout = QVBoxLayout(self)
#         self.layout.setContentsMargins(40, 40, 40, 40)
#         self.layout.setSpacing(20)

#         # === Header Row ===
#         header_layout = QHBoxLayout()
#         heading = QLabel("Supplier Detail", objectName="SectionTitle")
#         self.supplierlist = QPushButton("Suppliers List", objectName="TopRightButton")
#         self.supplierlist.setCursor(Qt.PointingHandCursor)
#         self.supplierlist.setFixedWidth(200)
#         header_layout.setContentsMargins(0, 0, 0, 10)
#         header_layout.addWidget(heading)
#         header_layout.addWidget(self.supplierlist)

#         self.layout.addLayout(header_layout)
        

#         line = QFrame()
#         line.setObjectName("lineSeparator")

#         line.setFrameShape(QFrame.HLine)
#         line.setFrameShadow(QFrame.Sunken)
#         line.setStyleSheet("""
#                 QFrame#lineSeparator {
#                     border: none;
#                     border-top: 2px solid #333;
#                 }
#             """)

#         self.layout.addWidget(line)
#         self.layout.addSpacing(20)

#         labels = ["Supplier", "Contact", "Email", "Website", "Address", "Registration No.", "Status", "Joining Date", "Payable", "Receivable"]


#         self.namedata = QLabel()
#         self.contactdata = QLabel()
#         self.emaildata = QLabel()
#         self.websitedata = QLabel()
#         self.addressdata = QLabel()
#         self.regdata = QLabel()
#         self.statusdata = QLabel()
#         self.joiningdata = QLabel()
#         self.payabledata = QLabel()
#         self.receiveabledata = QLabel()
        
#         fields = [
#             self.namedata,
#             self.contactdata,
#             self.emaildata,
#             self.websitedata,
#             self.addressdata,
#             self.regdata,
#             self.statusdata,
#             self.joiningdata,
#             self.payabledata,
#             self.receiveabledata
#         ]
        
        
#         for (label, field) in zip(labels, fields):

#             row = QHBoxLayout()
            
#             lbl = QLabel(label)
#             lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
#             lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
#             lbl.setStyleSheet("font-weight: normal; color: #444;")
#             field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
#             lbl.setMinimumWidth(200)

#             row.addWidget(lbl, 2)
#             row.addWidget(field, 8)

#             self.layout.addLayout(row)
            
            
#         self.layout.addStretch()

#         global_css = load_stylesheet('global_style.css')
#         table_css = load_stylesheet('table_style.css')
#         self.setStyleSheet(global_css + "\n" + table_css)




#     def load_supplier_data(self, id):
        
#         print("Loading purchase ID:", id)
#         query = QSqlQuery()
#         query.prepare("SELECT * FROM supplier WHERE id = ?")
#         query.addBindValue(id)
        
#         if query.exec() and query.next():
            
            
#             self.namedata.setText(query.value(1))
#             self.contactdata.setText(query.value(2))
#             self.emaildata.setText(query.value(3))
#             self.websitedata.setText(query.value(4))
#             self.addressdata.setText(query.value(5))
#             self.statusdata.setText(query.value(6))
#             joining_date = query.value(7)
            
#             if isinstance(joining_date, QDateTime):
#                 joining_date = joining_date.date().toString("dd-MM-yyyy")
#             elif isinstance(joining_date, QDate):
#                 joining_date = joining_date.toString("dd-MM-yyyy")
#             else:
#                 joining_date = str(joining_date)
                
#             self.joiningdata.setText(joining_date)
#             self.regdata.setText(query.value(8))
#             self.payabledata.setText(str(query.value(9)))
#             self.receiveabledata.setText(str(query.value(10)))
            
            
            
from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QHeaderView, QTableWidget, QTableWidgetItem, QSpacerItem,
    QLineEdit, QSizePolicy, QApplication, QMessageBox
)
from PySide6.QtCore import QFile, Qt, QDate, QDateTime
from PySide6.QtSql import QSqlQuery
from utilities.stylus import load_stylesheets


class SupplierDetailWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.supplier_id = None
        self.edit_mode = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Supplier Detail", objectName="SectionTitle")
        self.supplierlist = QPushButton("Suppliers List", objectName="TopRightButton")
        self.supplierlist.setCursor(Qt.PointingHandCursor)
        self.supplierlist.setFixedWidth(200)

        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedWidth(100)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)

        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.supplierlist)

        self.layout.addLayout(header_layout)

        # === Separator ===
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

        # === Labels + Fields ===
        labels = [
            "Supplier", "Contact", "Email", "Website", "Address",
            "Registration No.", "Status", "Joining Date",
            "Payable", "Receivable",
            "Bank Name", "Account Title", "Account Number", "IBAN",
            "JazzCash Title", "JazzCash Number", "CNIC",
            "EasyPaisa Title", "EasyPaisa Number", "CNIC"
                  
        ]

        # Use QLabel for display, QLineEdit for editing
        self.namedata = QLabel(); self.nameedit = QLineEdit()
        self.contactdata = QLabel(); self.contactedit = QLineEdit()
        self.emaildata = QLabel(); self.emailedit = QLineEdit()
        self.websitedata = QLabel(); self.websiteedit = QLineEdit()
        self.addressdata = QLabel(); self.addressedit = QLineEdit()
        self.regdata = QLabel(); self.regedit = QLineEdit()
        self.statusdata = QLabel(); self.statusedit = QLineEdit()
        self.joiningdata = QLabel(); # keep readonly
        self.payabledata = QLabel()   # keep readonly
        self.receiveabledata = QLabel()  # keep readonly
        
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
            (self.websitedata, self.websiteedit),
            (self.addressdata, self.addressedit),
            (self.regdata, self.regedit),
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
            lbl.setMinimumWidth(200)

            lbl_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            row.addWidget(lbl, 2)
            row.addWidget(lbl_field, 8)

            if edit_field:  # hidden initially
                edit_field.hide()
                row.addWidget(edit_field, 8)

            self.layout.addLayout(row)

        self.layout.addStretch()

        
        self.setStyleSheet(load_stylesheets())
        
        
        
        
        

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


    # === Save Changes ===
    def save_changes(self):
        
        if not self.supplier_id:
            print("No supplier loaded.")
            return

        query = QSqlQuery()
        query.prepare("""
            UPDATE supplier
            SET name=?, contact=?, email=?, website=?, address=?, status=?, reg_no=?
            WHERE id=?
        """)
        
        # supplier_name = self.nameedit.text()
        # contact = self.contactedit.text()
        # email = self.emailedit.text()
        # website = self.websitedit.text()
        # address = self.addressedit.text()
        # status = self.statusedit.text()
        registeration = self.regedit.text()

        registeration = registeration if registeration.strip() else None
        
        
        
        
        query.addBindValue(self.nameedit.text())
        query.addBindValue(self.contactedit.text())
        query.addBindValue(self.emailedit.text())
        query.addBindValue(self.websiteedit.text())
        query.addBindValue(self.addressedit.text())
        query.addBindValue(self.statusedit.text())
        query.addBindValue(registeration)
        query.addBindValue(self.supplier_id)

        if not query.exec():
            print("Error updating supplier:", query.lastError().text())
        else:
            print("Supplier updated successfully.")
        
        
        self.update_or_insert_banking_info()    
        self.update_or_insert_jazzcash_info()
        self.update_or_insert_easypaisa_info() 
        
            
            
    def update_or_insert_banking_info(self):

        supplier = int(self.supplier_id)
        customer = None
        bankname = self.banknameedit.text().strip() if self.banknameedit.text().strip() else None
        accounttitle = self.accounttitleedit.text().strip() if self.accounttitleedit.text().strip() else None
        accountnumber = self.accountnumberedit.text().strip() if self.accountnumberedit.text().strip() else None
        iban = self.ibanedit.text().strip() if self.ibanedit.text().strip() else None
        
        # Check if Bank info exists
        bank_check_query = QSqlQuery()
        bank_check_query.prepare("SELECT COUNT(*) FROM bank WHERE supplier = ?")
        bank_check_query.addBindValue(supplier)

        if not bank_check_query.exec() or not bank_check_query.next():
            print("Error checking bank info:", bank_check_query.lastError().text())
            return

        bank_info_exists = bank_check_query.value(0) > 0
        
        if not bank_info_exists: 
            # Insert new bank info
            insert_bank_query = QSqlQuery()
            insert_bank_query.prepare("""
                INSERT INTO bank (supplier, customer, bank, title, account, iban)
                VALUES (?, ?, ?, ?, ?, ?)
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
                WHERE supplier=?
            """)

            bank_query.addBindValue(bankname)
            bank_query.addBindValue(accounttitle)
            bank_query.addBindValue(accountnumber)
            bank_query.addBindValue(iban)
            bank_query.addBindValue(supplier)

            if not bank_query.exec():
                print("Error updating bank info:", bank_query.lastError().text())
            else:
                print("Bank info updated successfully.")      

    
    
    def update_or_insert_jazzcash_info(self):
        
        customer = None
        supplier = int(self.supplier_id)
        jazzcashtitle = self.jazzcashtitleedit.text().strip() if self.jazzcashtitleedit.text().strip() else None
        jazzcashnumber = self.jazzcashnumberedit.text().strip() if self.jazzcashnumberedit.text().strip() else None
        jazzcashcnic = self.jazzcashcnicedit.text().strip() if self.jazzcashcnicedit.text().strip() else None
        
        
        # Check if JazzCash info exists
        jazzcash_check_query = QSqlQuery()
        jazzcash_check_query.prepare("SELECT COUNT(*) FROM jazzcash WHERE supplier = ?")
        jazzcash_check_query.addBindValue(supplier)

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
            insert_jazzcash_query.addBindValue(customer)
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
                WHERE supplier=?
            """)

            jazzcash_query.addBindValue(jazzcashtitle)
            jazzcash_query.addBindValue(jazzcashnumber)
            jazzcash_query.addBindValue(jazzcashcnic)
            jazzcash_query.addBindValue(supplier)

            if not jazzcash_query.exec():
                print("Error updating JazzCash info:", jazzcash_query.lastError().text())
            else:
                print("JazzCash info updated successfully.")        
            
            
            
    def update_or_insert_easypaisa_info(self):
        
        customer = None
        supplier = int(self.supplier_id)
        easypaisatitle = self.easypaisatitleedit.text().strip() if self.easypaisatitleedit.text().strip() else None
        easypaisanumber = self.easypaisanumberedit.text().strip() if self.easypaisanumberedit.text().strip() else None
        easypaisacnic = self.easypaisacnicedit.text().strip() if self.easypaisacnicedit.text().strip() else None

        # Check if EasyPaisa info exists
        easypaisa_check_query = QSqlQuery()
        easypaisa_check_query.prepare("SELECT COUNT(*) FROM easypaisa WHERE supplier = ?")
        easypaisa_check_query.addBindValue(supplier)

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
            insert_easypaisa_query.addBindValue(customer)
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
                WHERE supplier=?
            """)

            easypaisa_query.addBindValue(easypaisatitle)
            easypaisa_query.addBindValue(easypaisanumber)
            easypaisa_query.addBindValue(easypaisacnic)
            easypaisa_query.addBindValue(supplier)

            if not easypaisa_query.exec():
                print("Error updating EasyPaisa info:", easypaisa_query.lastError().text())
            else:
                print("EasyPaisa info updated successfully.")       
            
            
    
            
            

    # === Load Data ===
    def load_supplier_data(self, id):
        self.supplier_id = id
        query = QSqlQuery()
        query.prepare("SELECT * FROM supplier WHERE id = ?")
        query.addBindValue(id)

        if query.exec() and query.next():
            self.namedata.setText(query.value(1))
            self.contactdata.setText(query.value(2))
            self.emaildata.setText(query.value(3))
            self.websitedata.setText(query.value(4))
            self.addressdata.setText(query.value(5))
            self.statusdata.setText(query.value(6))

            joining_date = query.value(7)
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)

            self.joiningdata.setText(joining_date)
            self.regdata.setText(query.value(8))
            self.payabledata.setText(str(query.value(9)))
            self.receiveabledata.setText(str(query.value(10)))
            
            
            
            

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



        

            
            
            






