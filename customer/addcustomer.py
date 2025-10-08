from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel, QFrame, QSizePolicy, QMessageBox, QHBoxLayout
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import traceback
from utilities.stylus import load_stylesheets



def load_stylesheet(filename):
    """ Load and return the CSS stylesheet from a file. """
    file = QFile(filename)
    if not file.open(QFile.ReadOnly | QFile.Text):
        print(f"Error opening file: {filename}")
        return ""
    
    css = file.readAll().data().decode()
    file.close()
    return css




class AddCustomerWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 20, 30, 40)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Customer Information", objectName="SectionTitle")
        self.customerlist = QPushButton("Customers List", objectName="TopRightButton")
        self.customerlist.setCursor(Qt.PointingHandCursor)
        self.customerlist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.customerlist)

        self.layout.addLayout(header_layout)
        line = self.horizontal_line()
        
        self.layout.addWidget(line)
        
        self.layout.addSpacing(10)
        
        
        
        
        
        
        
        
        
        # Labels + Fields
        labels = ["Customer *", "Contact*", "Email", "Receivable", "Payable"]
        self.editname = QLineEdit()
        self.editcontact = QLineEdit()
        self.editemail = QLineEdit()
        self.editreceiveable = QLineEdit()
        self.editpayable = QLineEdit()
        fields = [
            self.editname, self.editcontact, self.editemail,
            self.editreceiveable, self.editpayable
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
            
            
        self.layout.addSpacing(15)
        
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
        
        
        addcustomer = QPushButton("Save Customer", objectName="SaveButton")
        addcustomer.setCursor(Qt.PointingHandCursor)
        addcustomer.clicked.connect(lambda: self.save_customer())

        self.layout.addWidget(addcustomer)
        self.layout.addStretch()


        self.setStyleSheet(load_stylesheets())




    def insert_customer(self, name, contact, email, payable, receiveable):
        
        valid, message, cleaned = self.validate_customer(name, contact, email, payable, receiveable)

        if valid:
            
            print(f"[VALIDATION SUCCESS] {message}")
            QMessageBox.information(self, "Validation Success", message)
            
            name, contact, email, payable, receiveable = cleaned

            try:
                query = QSqlQuery()
                query.prepare("""
                    INSERT INTO customer (name, contact, email, payable, receiveable)
                    VALUES (?, ?, ?, ?, ?)
                """)
                query.addBindValue(name)
                query.addBindValue(contact)
                query.addBindValue(email)
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


    def validate_customer(self, name, contact, email, payable, receiveable):
        
        name = name.strip()
        contact = contact.strip()
        email = email.strip()
        payable = payable.strip()
        receiveable = receiveable.strip()
        
        if not name or not name.strip():
            return False, "Customer name cannot be empty.", ""

        if any(char.isdigit() for char in name):
            return False, "Customer name cannot contain numbers.", ""

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

        return True, "Customer details are valid.", (name, contact, email, payable_val, receiveable_val)
    
    

    def insert_bank_account(self, customer, supplier, bank, title, account, iban):
        
        valid, message, cleaned = self.validate_bank_account(bank, title, account, iban)
        
        
        customer = int(customer)
        supplier = None
        
        
        if valid:
            
            print(message)
            
            bank, title, account, iban = cleaned
            
            
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

        account_title, mobile_number, cnic = cleaned
        supplier = None
        customer = int(customer)
        
        if valid:
            print(message)

            try:
                query = QSqlQuery()
                query.prepare("""
                    INSERT INTO jazzcash (supplier, customer, account_title, mobile_number, cnic)
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

        customer = int(customer)
        supplier = None

        if valid:
            
            print(message)
            account_title, mobile_number, cnic = cleaned

            try:
                query = QSqlQuery()
                query.prepare("""
                    INSERT INTO easypaisa (supplier, customer, account_title, mobile_number, cnic)
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
            self.indicators[obj].setStyleSheet("background-color: #47034E; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)
    
    
    

    def save_customer(self):
        
        print("[ACTION] Save Customer button clicked.")
        
        db = QSqlDatabase.database()
        db.transaction()
        
        try:
        
            customer_id = self.insert_customer(
                self.editname.text(),
                self.editcontact.text(),
                self.editemail.text(),
                self.editpayable.text(),
                self.editreceiveable.text()
            )
            
            if customer_id:
                
                customer_id = int(customer_id)
                print(f"[SUCCESS] Customer added with ID: {customer_id}")
                
                bank_saved = self.insert_bank_account(
                    customer=customer_id,
                    supplier=None,
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
                    customer=customer_id,
                    supplier=None,
                    account_title=self.jazzcash_title.text(),
                    mobile_number=self.jazzcash_number.text(),
                    cnic=self.jazzcash_cnic.text()
                )
                
                if jazzcash_saved:
                    print("[SUCCESS] JazzCash information saved.")
                else:
                    print("[WARNING] JazzCash information not saved or invalid.")
                
                easypaisa_saved = self.insert_easypaisa_account(
                    customer=customer_id,
                    supplier=None,
                    account_title=self.easypaisa_title.text(),
                    mobile_number=self.easypaisa_number.text(),
                    cnic=self.easypaisa_cnic.text()
                )
                
                if easypaisa_saved:
                    print("[SUCCESS] Easypaisa information saved.")
                else:
                    print("[WARNING] Easypaisa information not saved or invalid.")
                
                
                QMessageBox.information(self, "Success", "Customer and related information saved successfully.")
                self.clear_fields()
        
        
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Exception occurred while saving customer and related info.\n"
                f"Exception Type: {type(e).__name__}\n"
                f"Message: {e}\n"
                f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Error", "An error occurred while saving customer information.")
            return

        else:
            db.commit()
            print("[DB] Transaction committed successfully.")




    def clear_fields(self):
        
        self.editname.clear()
        self.editcontact.clear()
        self.editemail.clear()
        self.editpayable.clear()
        self.editreceiveable.clear()
        
        self.bank_name.clear()
        self.account_title.clear()
        self.account_number.clear()
        self.iban.clear()
        
        self.jazzcash_title.clear()
        self.jazzcash_number.clear()
        self.jazzcash_cnic.clear()
        
        self.easypaisa_title.clear()
        self.easypaisa_number.clear()
        self.easypaisa_cnic.clear()
        
        print("[ACTION] All input fields cleared.")
        
        
        
        