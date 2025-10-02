from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QFrame, QSizePolicy, QComboBox, QMessageBox
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
import bcrypt


def load_stylesheet(filename):
    """ Load and return the CSS stylesheet from a file. """
    file = QFile(filename)
    if not file.open(QFile.ReadOnly | QFile.Text):
        print(f"Error opening file: {filename}")
        return ""
    
    css = file.readAll().data().decode()
    file.close()
    return css




class AddUserWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        
    
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)


        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Add New User", objectName="SectionTitle")
        self.userlist = QPushButton("User List", objectName="TopRightButton")
        self.userlist.setCursor(Qt.PointingHandCursor)
        self.userlist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.userlist)
        

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
        labels = ["First Name", "Last Name", "Email", "Username", "Password", "Role"]
        
        self.editfirstname = QLineEdit()
        self.editlastname = QLineEdit()
        self.editemail = QLineEdit()
        self.editusername = QLineEdit()
        self.editpassword = QLineEdit()
        self.editpassword.setEchoMode(QLineEdit.Password)
        self.selectrole = QComboBox()
        self.selectrole.addItems(["manager", "regular"])

        fields = [
            self.editfirstname, self.editlastname, self.editemail, self.editusername, self.editpassword, self.selectrole
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
        

        # === Add Button ===
        adduser = QPushButton("Add User", objectName="SaveButton")
        adduser.setCursor(Qt.PointingHandCursor)
        adduser.clicked.connect(lambda: self.save_user())

        self.layout.addWidget(adduser)
        self.layout.addStretch()


        # Apply external stylesheet if present
        css = load_stylesheet("styles/global_style.css")
        self.setStyleSheet(css)
        

    
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #47034E; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)
    
    
    

    
    def save_user(self):
        
        firstname = self.editfirstname.text()
        lastname = self.editlastname.text()
        email = self.editemail.text()
        username = self.editusername.text()
        password = self.editpassword.text()
        role = self.selectrole.currentText()
        
        username_exists = self.check_username(username)
        
        if username_exists:
            QMessageBox.warning(None, "Warning", "Username already exists. Please choose another.")
            return
        
        
        salt = bcrypt.gensalt()
        password = bcrypt.hashpw(password.encode(), salt).decode()
        salt = salt.decode()
        
        query = QSqlQuery()
        query.prepare("""
                    INSERT INTO auth ( firstname, lastname, email, username, password_hash, salt, role, status )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """)
        
        query.addBindValue(firstname)
        query.addBindValue(lastname)
        query.addBindValue(email)
        query.addBindValue(username)
        query.addBindValue(password)
        query.addBindValue(salt)
        query.addBindValue(role)
        query.addBindValue("active")  # Default status
        
        
        if not query.exec():
            print("Insert failed:", query.lastError().text())
            QMessageBox.critical(None, "Error", query.lastError().text())
        else:
            QMessageBox.information(None, "Success", 'New User Record Saved Successfully')
            
            
        # inserting Employee
        
        employee_query = QSqlQuery()
        employee_query.prepare("""                               
                                INSERT INTO employee ( name, email, role, status )
                                VALUES (?, ?, ?, ?);
                    """)
        
        emp_name = firstname + " " + lastname
        employee_query.addBindValue(emp_name)
        employee_query.addBindValue(email)
        employee_query.addBindValue(role)
        employee_query.addBindValue("active")  # Default status
    
        if not employee_query.exec():
            print("Insert failed:", employee_query.lastError().text())
            QMessageBox.critical(None, "Error", employee_query.lastError().text())
        else:
            QMessageBox.information(None, "Success", 'Employee Record Saved Successfully')
            
    
        
        



    def check_username(self, username):
        
        query = QSqlQuery()
        query.prepare("SELECT COUNT(*) FROM auth WHERE username = ?")
        query.addBindValue(username)
        
        if query.exec() and query.next():
            
            if query.value(0) > 0:
                return True
            else:
                return False
    
        else:
            
            print("Error Checking Username")