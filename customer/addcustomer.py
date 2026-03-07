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
        
        print("[ACTION] All input fields cleared.")
        
        
        
        