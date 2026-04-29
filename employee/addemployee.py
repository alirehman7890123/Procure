from PySide6.QtWidgets import QWidget, QPushButton,QMessageBox, QVBoxLayout, QHBoxLayout, QFrame, QLabel,QComboBox, QSpacerItem, QSizePolicy, QLineEdit
from PySide6.QtCore import QFile, Qt, QEvent
from PySide6.QtSql import QSqlDatabase

from medic.utilities.permissions import Permissions
from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from medic.services.employee_service import create_employee, employee_role_options, validate_employee_payload




class AddEmployeeWidget(QWidget):


    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Employee Information", objectName="SectionTitle")
        self.employeelist = QPushButton("Employee List", objectName="TopRightButton")
        self.employeelist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
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
        self.editrole.addItems(employee_role_options())
        

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
            self.layout.setSpacing(10)  # reduce space between rows
            
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
            self.indicators[obj].setStyleSheet("background-color: #2F5D7C; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)

    
    
    @Permissions.require_permission('employee.create')
    def save_employee(self):
        
        try:
            validate_employee_payload(
                name=self.editname.text(),
                contact=self.editcontact.text(),
                email=self.editemail.text(),
                address=self.editaddress.text(),
                badge=self.editbadge.text(),
                role=self.editrole.currentText(),
            )
            create_employee(
                name=self.editname.text(),
                contact=self.editcontact.text(),
                email=self.editemail.text(),
                address=self.editaddress.text(),
                badge=self.editbadge.text(),
                role=self.editrole.currentText(),
            )
        except ValueError as exc:
            AppMessageBox.warning(self, "Validation Error", str(exc))
            return
        except Exception as exc:
            print("Insert failed:", str(exc))
            AppMessageBox.critical(self, "Error", str(exc))
            return
        else:
            AppMessageBox.information(None, "Success", 'Employee Record Saved Successfully')
            # Clear the input fields after saving
        
            self.editname.clear()
            self.editcontact.clear()
            self.editemail.clear()
            self.editaddress.clear()
            self.editbadge.clear()
            self.editrole.setCurrentIndex(0)  # Reset to the first item in the combo box
        
        
            
        
        

        
        
        
        
        









