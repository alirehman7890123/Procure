from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFrame, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt, QDate, QDateTime
from PySide6.QtSql import  QSqlQuery
from utilities.stylus import load_stylesheets



class EmployeeDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Employee Detail", objectName="SectionTitle")
        self.employeelist = QPushButton("Employees List", objectName="TopRightButton")
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
        
        labels = ["Employee", "Contact", "Email", "Address", "Badge No.", "Role", "Status", "Joining Date"]

        self.namedata = QLabel()
        self.contactdata = QLabel()
        self.emaildata = QLabel()
        self.addressdata = QLabel()
        self.badgedata = QLabel()
        self.roledata = QLabel()
        self.statusdata = QLabel()
        self.joining = QLabel()
        
        
        fields = [
            self.namedata,
            self.contactdata,
            self.emaildata,
            self.addressdata, self.badgedata, self.roledata, self.statusdata, self.joining
            
        ]
        
        for (label, field) in zip(labels, fields):

            row = QHBoxLayout()
            
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(lbl, 2)
            row.addWidget(field, 8)

            self.layout.addLayout(row)
            
            
        self.layout.addStretch()
        
        
        self.setStyleSheet(load_stylesheets())
        
        
        
        
        

    def load_employee_data(self, id):
        
        print("Loading purchase ID:", id)
        query = QSqlQuery()
        query.prepare("SELECT * FROM employee WHERE id = ?")
        query.addBindValue(id)
        
        if query.exec() and query.next():
            
            name = query.value(1)
            contact = query.value(2)
            email = query.value(3)
            address = query.value(4)
            badge = query.value(5)
            role = query.value(6)
            status = query.value(7)
            joining_date = query.value(8)
            
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)
            
            self.namedata.setText(name)
            self.contactdata.setText(contact)
            self.emaildata.setText(email)
            self.addressdata.setText(address)
            self.badgedata.setText(badge)
            self.roledata.setText(role)
            self.statusdata.setText(status)
            self.joining.setText(joining_date)
            
            
            
            
            
            
            




