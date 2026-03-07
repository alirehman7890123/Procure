
from PySide6.QtWidgets import (
    QWidget, QPushButton, QMessageBox, QGridLayout, QLabel, 
    QSpacerItem, QSizePolicy, QLineEdit, QVBoxLayout, QHBoxLayout, QFrame
)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import QFile, Qt, QEvent
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from PySide6.QtGui import QFocusEvent
import traceback


from utilities.basepage import BasePage

from utilities.stylus import load_stylesheets




class AddSupplierWidget(BasePage):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Supplier Information", objectName="SectionTitle")
        self.supplierlist = QPushButton("Suppliers List", objectName="TopRightButton")
        self.supplierlist.setCursor(Qt.PointingHandCursor)
        self.supplierlist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.supplierlist)

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
        labels = ["Supplier", "Contact", "Email", "Website", "Address", "Registration No.", "Payable", "Receivable"]
        self.editname = QLineEdit()
        self.editcontact = QLineEdit()
        self.editemail = QLineEdit()
        self.editwebsite = QLineEdit()
        self.editaddress = QLineEdit()
        self.editreg_no = QLineEdit()
        self.editpayable = QLineEdit()
        self.editreceiveable = QLineEdit()

        fields = [
            self.editname, self.editcontact, self.editemail, self.editwebsite,
            self.editaddress, self.editreg_no, self.editpayable, self.editreceiveable
        ]
        
        self.indicators = {}


        for (label, field) in zip(labels, fields):

            row = QHBoxLayout()
            
            # Left line indicator
            indicator = QFrame()
            indicator.setFixedWidth(4)
            indicator.setStyleSheet("background-color: #ccc; border: none;")
            

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(indicator) 
            row.addWidget(lbl, 1)
            row.addWidget(field, 8)

            self.layout.addLayout(row)
            self.layout.setSpacing(15)  # reduce space between rows
            
            # Keep mapping
            self.indicators[field] = indicator

            # Install event filters to track focus
            field.installEventFilter(self)
            
       
        self.layout.addSpacing(10)
        
        
          
                
        

        # === Add Button ===
        addsupplier = QPushButton("Add Supplier", objectName="SaveButton")
        addsupplier.setCursor(Qt.PointingHandCursor)
        addsupplier.clicked.connect(lambda: self.save_supplier())
        
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.save_supplier)

        self.layout.addWidget(addsupplier)
        self.layout.addStretch()
        

        # Apply external stylesheet if present
        
        self.setStyleSheet(load_stylesheets())
        
        
        
    def insert_supplier(self, name, contact, email, website, address, registeration, payable, receiveable):
        
        valid, message, cleaned = self.validate_supplier(name, contact, email, website, address, registeration, payable, receiveable)

        if valid:
            
            print(f"[VALIDATION SUCCESS] {message}")
            QMessageBox.information(self, "Validation Success", message)
            
            name, contact, email, website, address, registeration, payable, receiveable = cleaned

            try:
                query = QSqlQuery()
                query.prepare("""
                    INSERT INTO supplier (name, contact, email, website, address, reg_no, payable, receiveable)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """)
                query.addBindValue(name)
                query.addBindValue(contact)
                query.addBindValue(email)
                query.addBindValue(website)
                query.addBindValue(address)
                query.addBindValue(registeration)
                query.addBindValue(payable)
                query.addBindValue(receiveable)

                if not query.exec():
                    error_msg = query.lastError().text()
                    print(f"[DB ERROR] Failed to insert customer.\n"
                        f"Table: customer\n"
                        f"Values: name={name}, contact={contact}, email={email}, "
                        f"payable={payable}, receiveable={receiveable}\n"
                        f"Reason: {error_msg}")
                    return False

                # return Id if insertion is successful
                return query.lastInsertId()
            

            except Exception as e:
                print(f"[PYTHON ERROR] Exception occurred while inserting customer.\n"
                    f"Function: insert_customer\n"
                    f"Values: name={name}, contact={contact}, email={email}, "
                    f"payable={payable}, receiveable={receiveable}\n"
                    f"Exception Type: {type(e).__name__}\n"
                    f"Message: {e}")
                return False
            
        
        else:
            
            print(f"[VALIDATION ERROR] {message}")
            QMessageBox.warning(self, "Validation Error", message)
            return False

    
    def validate_supplier(self, name, contact, email, website, address, registeration, payable, receiveable):
        
        print("Going to Validate Supplier")
        
        name = name.strip()
        contact = contact.strip()
        email = email.strip()
        website = website.strip()
        address = address.strip()
        registeration = registeration.strip()
        payable = payable.strip()
        receiveable = receiveable.strip()
        
        website = website if website else None
        address = address if address else None
        registeration = registeration if registeration else None

        if not name or not name.strip():
            return False, "Supplier name cannot be empty.", ""

        if not contact or not contact.strip():
            return False, "Contact cannot be empty.", ""

        if not contact.isdigit():
            return False, "Contact must contain only digits.", ""

        if len(contact) < 7:
            return False, "Contact must be at least 7 digits.", ""

        if email and ("@" not in email or "." not in email):
            return False, "Invalid email format.", ""


        try:
            payable_val = float(payable) if payable else 0.0
            receiveable_val = float(receiveable) if receiveable else 0.0
        except ValueError:
            return False, "Payable and Receivable must be numbers.", ""

        if payable_val < 0 or receiveable_val < 0:
            return False, "Payable and Receivable cannot be negative.", ""

        return True, "Supplier details are valid.", (name, contact, email, website, address, registeration, payable_val, receiveable_val)
    
    

    
    
    def horizontal_line(self):
        
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

        return line

        
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #0078d7; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)


    
    
    def save_supplier(self):

        print("[ACTION] Save Supplier button clicked.")

        db = QSqlDatabase.database()
        db.transaction()
        
        try:
        
            supplier_id = self.insert_supplier(
                self.editname.text(),
                self.editcontact.text(),
                self.editemail.text(),
                self.editwebsite.text(),
                self.editaddress.text(),
                self.editreg_no.text(),
                self.editpayable.text(),
                self.editreceiveable.text()
            )

        
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Exception occurred while saving supplier and related info.\n"
                f"Exception Type: {type(e).__name__}\n"
                f"Message: {e}\n"
                f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", "An error occurred while saving supplier information.")
            return

        else:
            db.commit()
            print("[DB] Transaction committed successfully.")


    
    
    

    def clear_fields(self):
        for field in [
            self.editname, self.editcontact, self.editemail,
            self.editwebsite, self.editaddress, self.editreg_no,
            self.editpayable, self.editreceiveable
        ]:
            field.clear()
