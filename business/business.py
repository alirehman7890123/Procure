from PySide6.QtWidgets import QWidget,QApplication, QFrame, QPushButton, QVBoxLayout, QLineEdit, QLabel,QMessageBox, QHBoxLayout, QSizePolicy, QFrame
from PySide6.QtGui import QColor
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from utilities.permissions import Permissions
from utilities.stylus import load_stylesheets




class BusinessWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        
        print("Opening Business Page")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        
        
         # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Business Information", objectName="SectionTitle")
        
        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedWidth(100)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        header_layout.addWidget(self.edit_btn)
        self.edit_mode = False  # Track whether we are in edit mode or not
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)

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
        
        
        # Labels + Fields
        labels = ["Business Name", "Address", "Contact", "Email", "Website", "License #", "N.T.N"]
        
        
        self.businessname = QLabel(); self.businessnameedit = QLineEdit()
        self.address = QLabel(); self.addressedit = QLineEdit()
        self.contact = QLabel(); self.contactedit = QLineEdit()
        self.email = QLabel(); self.emailedit = QLineEdit()
        self.website = QLabel(); self.websiteedit = QLineEdit() 
        self.license = QLabel(); self.licenseedit = QLineEdit()
        self.ntn = QLabel(); self.ntnedit = QLineEdit() 
        
        self.field_pairs = [
            
           (self.businessname, self.businessnameedit),
           (self.address, self.addressedit),
           (self.contact, self.contactedit),
           (self.email, self.emailedit),
           (self.website, self.websiteedit),
           (self.license, self.licenseedit),
           (self.ntn, self.ntnedit),
            
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

    
    def showEvent(self, event):
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_business_data()
        
        


    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #47034E; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)

        
        
    
    # === Toggle Edit Mode ===
    @Permissions.require_permission('business.update')
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
    
    

    
    
    # === Load Data ===
    def load_business_data(self):
        
        
        query = QSqlQuery()
        query.prepare("""
                        SELECT id, businessname, address, contact, email, website, license, ntn
                        FROM business
                    """)
        

        if query.exec() and query.next():
            
            self.business_id = query.value(0)
            print("Business ID:", self.business_id)
            
            self.businessname.setText(query.value(1))
            self.address.setText(query.value(2))
            self.contact.setText(query.value(3))
            self.email.setText(query.value(4))
            self.website.setText(query.value(5))
            self.license.setText(query.value(6))
            self.ntn.setText(query.value(7))
            
            print("Business data loaded successfully.")
            
            

        
    # === Save Changes ===
    def save_changes(self):
        
        if not self.business_id:
            print("No Business loaded.")
            return

        query = QSqlQuery()
        query.prepare("""
            UPDATE business
            SET businessname=?, address=?, contact=?, email=?, website=?, license=?, ntn=?
            WHERE id=?
        """)
        
        businessname = self.businessnameedit.text()
        address = self.addressedit.text()
        contact = self.contactedit.text()
        email = self.emailedit.text()
        website = self.websiteedit.text()
        license = self.licenseedit.text()
        ntn = self.ntnedit.text()
        
        query.addBindValue(businessname)
        query.addBindValue(address)
        query.addBindValue(contact)
        query.addBindValue(email)
        query.addBindValue(website)
        query.addBindValue(license)
        query.addBindValue(ntn)
        query.addBindValue(self.business_id)

        

        if not query.exec():
            print("Error updating business:", query.lastError().text())
        else:
            print("Business updated successfully.")
        

   


