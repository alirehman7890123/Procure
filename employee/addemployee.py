from PySide6.QtWidgets import QWidget, QPushButton,QMessageBox, QVBoxLayout, QHBoxLayout, QFrame, QLabel,QComboBox, QSpacerItem, QSizePolicy, QLineEdit
from PySide6.QtCore import QFile, Qt, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from utilities.stylus import load_stylesheets




class AddEmployeeWidget(QWidget):


    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Employee Information", objectName="SectionTitle")
        self.employeelist = QPushButton("Employee List", objectName="TopRightButton")
        self.employeelist.setCursor(Qt.PointingHandCursor)
        self.employeelist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.employeelist)

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


        labels = ["Name", "Contact", "Email", "Address", "Badge No.", "Role"]


        self.editname = QLineEdit()
        self.editcontact = QLineEdit()
        self.editemail = QLineEdit()
        self.editaddress = QLineEdit()
        self.editbadge = QLineEdit()
        self.editrole = QComboBox()
        self.editrole.addItems(['pharmacist', 'salesman'])
        

        fields = [self.editname, self.editcontact, self.editemail, self.editaddress, self.editbadge, self.editrole]
        
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
        addemployee = QPushButton("Add Employee", objectName="SaveButton")
        addemployee.setCursor(Qt.PointingHandCursor)
        addemployee.clicked.connect(self.save_employee)

        self.layout.addWidget(addemployee)
        self.layout.addStretch()
        
        
        
        self.setStyleSheet(load_stylesheets())




    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #47034E; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)

    
    
    def save_employee(self):
        
        name = self.editname.text()
        email = self.editemail.text()
        contact = self.editcontact.text()
        address = self.editaddress.text()
        badge = self.editbadge.text()
        role = self.editrole.currentText()
        
      
        query = QSqlQuery()
        
        query.prepare("""
                    INSERT INTO employee (name, contact, email, address, badge, role)
                    VALUES (?, ?, ?, ?, ?, ?);
                """)
                
        query.addBindValue(name)
        query.addBindValue(contact)
        query.addBindValue(email)
        query.addBindValue(address)  
        query.addBindValue(badge)
        query.addBindValue(role)
            
        if not query.exec():
            print("Insert failed:", query.lastError().text())
        else:
            QMessageBox.information(None, "Success", 'Employee Record Saved Successfully')
            # Clear the input fields after saving
        
            self.editname.clear()
            self.editcontact.clear()
            self.editemail.clear()
            self.editaddress.clear()
            self.editbadge.clear()
            self.editrole.setCurrentIndex(0)  # Reset to the first item in the combo box
        
        
            
        
        

        
        
        
        
        











