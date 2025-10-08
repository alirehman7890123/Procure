
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




# from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QHBoxLayout, QFrame
# from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
# from PySide6.QtGui import QColor

# class FocusRow(QWidget):
#     def __init__(self, label_text: str, field: QLineEdit, parent=None):
#         super().__init__(parent)

#         self._bar_color = QColor("#ccc")  # default gray

#         # Left indicator bar
#         self.indicator = QFrame()
#         self.indicator.setFixedWidth(4)
#         self.indicator.setStyleSheet("background: #ccc; border: none;")

#         # Label
#         self.label = QLabel(label_text)
#         self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
#         self.label.setMinimumWidth(200)

#         # Field
#         field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
#         field.installEventFilter(self)

#         # Layout
#         layout = QHBoxLayout(self)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(8)
#         layout.addWidget(self.indicator)
#         layout.addWidget(self.label, 1)
#         layout.addWidget(field, 8)

#         self.setLayout(layout)

#     # --- animation property ---
#     def getColor(self):
#         return self._bar_color

#     def setColor(self, color: QColor):
#         self._bar_color = color
#         self.indicator.setStyleSheet(f"background: {color.name()}; border: none;")

#     barColor = Property(QColor, getColor, setColor)

#     # --- focus handling ---

#     def eventFilter(self, obj, event):
#         if event.type() == QEvent.FocusIn:
#             self.indicators[obj].setStyleSheet("background-color: #0078d7; border: none;")  # active blue
#         elif event.type() == QEvent.FocusOut:
#             self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
#         return super().eventFilter(obj, event)



#     def animateBar(self, target_color: QColor):
#         anim = QPropertyAnimation(self, b"barColor", self)
#         anim.setDuration(200)
#         anim.setEasingCurve(QEasingCurve.InOutQuad)
#         anim.setStartValue(self._bar_color)
#         anim.setEndValue(target_color)
#         anim.start()
#         self._anim = anim  # keep reference alive




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
            
        # for label, field in zip(labels, fields):
        #     row = FocusRow(label, field)
        #     self.layout.addWidget(row)

        
        self.layout.addSpacing(10)
        
        
        
        # ====== Banking Information ======
        banking = QHBoxLayout()
        subheading = QLabel("Banking Information", objectName="SectionTitle")
        banking.setContentsMargins(0, 0, 0, 10)
        banking.addWidget(subheading)
        self.layout.addLayout(banking)
        
        line = self.horizontal_line()
        self.layout.addWidget(line)
        self.layout.addSpacing(10)
        
        
        labels = ["Bank Name", "Account Title.", "Account Number", "IBAN"]
        
        self.bank_name = QLineEdit()
        self.account_title = QLineEdit()
        self.account_number = QLineEdit()
        self.iban = QLineEdit()

        fields = [
            self.bank_name, self.account_title, self.account_number, self.iban
        ]
        
        
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
            self.layout.setSpacing(8)  # reduce space between rows
            
            # Keep mapping
            self.indicators[field] = indicator

            # Install event filters to track focus
            field.installEventFilter(self)
          
        
        
        # === JazzCash Info ===
        self.layout.addSpacing(15)
        jazzcash = QHBoxLayout()
        subheading = QLabel("Jazz Cash Information", objectName="SectionTitle")
        jazzcash.setContentsMargins(0, 0, 0, 10)
        jazzcash.addWidget(subheading)
        self.layout.addLayout(jazzcash)
        
        line = self.horizontal_line()
        self.layout.addWidget(line)
        self.layout.addSpacing(10)
        
        jazz_labels = ["JazzCash Account Title", "JazzCash Number", "CNIC"]

        self.jazzcash_title = QLineEdit()
        self.jazzcash_number = QLineEdit()
        self.jazzcash_cnic = QLineEdit()

        jazz_fields = [ self.jazzcash_title, self.jazzcash_number, self.jazzcash_cnic ] 
        
        for (label, field) in zip(jazz_labels, jazz_fields):

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
            self.layout.setSpacing(8)  # reduce space between rows
            
            # Keep mapping
            self.indicators[field] = indicator

            # Install event filters to track focus
            field.installEventFilter(self)
            
              
        
        
        # === Easypaisa Info ===
        self.layout.addSpacing(15)
        easypaisa = QHBoxLayout()
        subheading = QLabel("EasyPaisa Information", objectName="SectionTitle")
        easypaisa.setContentsMargins(0, 0, 0, 10)
        easypaisa.addWidget(subheading)
        self.layout.addLayout(easypaisa)
        
        line = self.horizontal_line()
        self.layout.addWidget(line)
        self.layout.addSpacing(10)
        
        easypaisa_labels = ["Easypaisa Account Title", "Easypaisa Number", "CNIC"]

        self.easypaisa_title = QLineEdit()
        self.easypaisa_number = QLineEdit()
        self.easypaisa_cnic = QLineEdit()

        easypaisa_fields = [ self.easypaisa_title, self.easypaisa_number, self.easypaisa_cnic ]

        for (label, field) in zip(easypaisa_labels, easypaisa_fields):

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
            self.layout.setSpacing(8)  # reduce space between rows
            
            # Keep mapping
            self.indicators[field] = indicator

            # Install event filters to track focus
            field.installEventFilter(self)
            
          
                
        
            
         # === Add Button ===
        
          

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
    
    
    
    
    def insert_bank_account(self, customer, supplier, bank, title, account, iban):
        
        valid, message, cleaned = self.validate_bank_account(bank, title, account, iban)
        

        customer = None
        supplier = int(supplier)

        if valid:
            bank, title, account, iban = cleaned
            print(message)
            
            try:
                query = QSqlQuery()
                
                query.prepare("""
                    INSERT INTO bank (supplier, customer, bank, title, account, iban)
                    VALUES (?, ?, ?, ?, ?)
                """)

                query.addBindValue(supplier)
                query.addBindValue(customer)
                query.addBindValue(bank)
                query.addBindValue(title)
                query.addBindValue(account)
                query.addBindValue(iban)

                if not query.exec():
                    error_msg = query.lastError().text()
                    print(f"[DB ERROR] Failed to insert bank account.\n"
                        f"Table: bank\n"
                        f"Values: bank={bank}, title={title}, "
                        f"account={account}, iban={iban}\n"
                        f"Reason: {error_msg}")
                    return False

                return True

            except Exception as e:
                print(f"[PYTHON ERROR] Exception occurred while inserting bank account.\n"
                    f"Function: insert_bank_account\n"
                    f"Values: bank={bank}, title={title}, "
                    f"account={account}, iban={iban}\n"
                    f"Exception Type: {type(e).__name__}\n"
                    f"Message: {e}")
                return False

        else:
            print(f"[VALIDATION ERROR] {message}")
            return False


    def validate_bank_account(self, bank_name, account_title, account_number, iban):
        
        bank_name = bank_name.strip()
        account_title = account_title.strip()
        account_number = account_number.strip()
        iban = iban.strip()
        

        # Check bank name
        if bank_name or not bank_name.strip():
            return False, "Bank Name cannot be empty.", ""

        if len(bank_name) < 3:
            return False, "Bank Name must be at least 3 characters.", ""

        # Check account title
        if not account_title or not account_title.strip():
            return False, "Account Title cannot be empty.", ""

        if any(char.isdigit() for char in account_title):
            return False, "Account Title cannot contain numbers.", ""

        # Check account number
        if not account_number or not account_number.strip():
            return False, "Account Number cannot be empty.", ""

        if not account_number.isdigit():
            return False, "Account Number must contain only digits.", ""

        if len(account_number) < 8:
            return False, "Account Number must be at least 8 digits.", ""

        
        # Check IBAN

        if iban and not (len(iban) >= 24):
            return False, "Invalid IBAN format. Must be at least 24 characters.", ""

        return True, "Bank account details are valid." , (bank_name, account_title, account_number, iban)



    def insert_jazzcash_account(self, customer, supplier, account_title, mobile_number, cnic):
        """Insert a JazzCash account into DB with validation and error handling."""

        valid, message, cleaned = self.validate_jazzcash_account(account_title, mobile_number, cnic)

        
        supplier = int(supplier)
        customer = None
        
        if valid:
            account_title, mobile_number, cnic = cleaned
            print(message)

            try:
                query = QSqlQuery()
                query.prepare("""
                    INSERT INTO jazzcash (supplier, customer, title, mobile, cnic)
                    VALUES (?, ?, ?, ?, ?)
                """)
                query.addBindValue(supplier)
                query.addBindValue(customer)
                query.addBindValue(account_title)
                query.addBindValue(mobile_number)
                query.addBindValue(cnic)

                if not query.exec():
                    error_msg = query.lastError().text()
                    print(f"[DB ERROR] Failed to insert JazzCash account.\n"
                        f"Table: jazzcash\n"
                        f"Values: customer={customer}, supplier={supplier}, "
                        f"account_title={account_title}, mobile_number={mobile_number}, cnic={cnic}\n"
                        f"Reason: {error_msg}")
                    return False

                return True

            except Exception as e:
                print(f"[PYTHON ERROR] Exception occurred while inserting JazzCash account.\n"
                    f"Function: insert_jazzcash_account\n"
                    f"Values: customer={customer}, supplier={supplier}, "
                    f"account_title={account_title}, mobile_number={mobile_number}, cnic={cnic}\n"
                    f"Exception Type: {type(e).__name__}\n"
                    f"Message: {e}")
                return False

        else:
            print(f"[VALIDATION ERROR] {message}")
            return False


    def validate_jazzcash_account(self, account_title, mobile_number, cnic):
        """Validate JazzCash account details before insertion."""
        
        account_title = account_title.strip()
        mobile_number = mobile_number.strip()
        cnic = cnic.strip()
        
        account_title = account_title if account_title else None
        mobile_number = mobile_number if mobile_number else None
        cnic = cnic if cnic else None
        
        


        # Mobile number check

        if mobile_number and mobile_number.isdigit():
            return False, "Mobile Number must contain only digits.", ""



        return True, "JazzCash account details are valid.", (account_title, mobile_number, cnic)


    
    def insert_easypaisa_account(self, customer, supplier, account_title, mobile_number, cnic):
        """Insert a Easypaisa account into DB with validation and error handling."""

        valid, message, cleaned = self.validate_easypaisa_account(account_title, mobile_number, cnic)

        supplier = int(supplier)
        customer = None

        if valid:
            
            print(message)
            account_title, mobile_number, cnic = cleaned
            

            try:
                query = QSqlQuery()
                query.prepare("""
                    INSERT INTO easypaisa (supplier, customer, account, mobile, cnic)
                    VALUES (?, ?, ?, ?, ?)
                """)
                query.addBindValue(supplier)
                query.addBindValue(customer)
                query.addBindValue(account_title)
                query.addBindValue(mobile_number)
                query.addBindValue(cnic)

                if not query.exec():
                    error_msg = query.lastError().text()
                    print(f"[DB ERROR] Failed to insert Easypaisa account.\n"
                        f"Table: easypaisa\n"
                        f"Values: customer={customer}, supplier={supplier}, "
                        f"account_title={account_title}, mobile_number={mobile_number}, cnic={cnic}\n"
                        f"Reason: {error_msg}")
                    return False

                return True

            except Exception as e:
                print(f"[PYTHON ERROR] Exception occurred while inserting Easypaisa account.\n"
                    f"Function: insert_easypaisa_account\n"
                    f"Values: customer={customer}, supplier={supplier}, "
                    f"account_title={account_title}, mobile_number={mobile_number}, cnic={cnic}\n"
                    f"Exception Type: {type(e).__name__}\n"
                    f"Message: {e}")
                return False

        else:
            print(f"[VALIDATION ERROR] {message}")
            return False


    def validate_easypaisa_account(self, account_title, mobile_number, cnic):
        """Validate Easypaisa account details before insertion."""
        
        account_title = account_title.strip()
        mobile_number = mobile_number.strip()
        cnic = cnic.strip()
        
        account_title = account_title if account_title else None
        mobile_number = mobile_number if mobile_number else None
        cnic = cnic if cnic else None
        
        return True, "Easypaisa account details are valid.", (account_title, mobile_number, cnic)





    
    
    
    
    
    
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
            
            if supplier_id:
                supplier_id = int(supplier_id)
                print(f"[SUCCESS] Supplier added with ID: {supplier_id}")

                bank_saved = self.insert_bank_account(
                    customer=None,
                    supplier=supplier_id,
                    bank=self.bank_name.text(),
                    title=self.account_title.text(),
                    account=self.account_number.text(),
                    iban=self.iban.text()
                )
                
                if bank_saved:
                    print("[SUCCESS] Bank account information saved.")
                else:
                    print("[WARNING] Bank account information not saved or invalid.")
                
                jazzcash_saved = self.insert_jazzcash_account(
                    customer=None,
                    supplier=supplier_id,
                    account_title=self.jazzcash_title.text(),
                    mobile_number=self.jazzcash_number.text(),
                    cnic=self.jazzcash_cnic.text()
                )
                
                if jazzcash_saved:
                    print("[SUCCESS] JazzCash information saved.")
                else:
                    print("[WARNING] JazzCash information not saved or invalid.")
                
                easypaisa_saved = self.insert_easypaisa_account(
                    customer=None,
                    supplier=supplier_id,
                    account_title=self.easypaisa_title.text(),
                    mobile_number=self.easypaisa_number.text(),
                    cnic=self.easypaisa_cnic.text()
                )
                
                if easypaisa_saved:
                    print("[SUCCESS] Easypaisa information saved.")
                else:
                    print("[WARNING] Easypaisa information not saved or invalid.")
                
                
                QMessageBox.information(self, "Success", "Supplier and related information saved successfully.")
                self.clear_fields()
        
        
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
            self.editpayable, self.editreceiveable, self.bank_name,
            self.account_title, self.account_number, self.iban,
            self.jazzcash_title, self.jazzcash_number,
            self.easypaisa_title, self.easypaisa_number
        ]:
            field.clear()
