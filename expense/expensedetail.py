from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFrame, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt,QDate, QDateTime
from PySide6.QtSql import  QSqlQuery

from utilities.stylus import load_stylesheets



class ExpenseDetailWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Expense Detail", objectName="SectionTitle")
        self.expenselist = QPushButton("Expenses List", objectName="TopRightButton")
        self.expenselist.setCursor(Qt.PointingHandCursor)
        self.expenselist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.expenselist)

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
        
        labels = ["Category", "Title", "Amount", "Description", "Date"]

        self.category = QLabel()
        self.title = QLabel()
        self.amount = QLabel()
        self.description = QLabel()
        self.creation = QLabel()

        
        fields = [self.category, self.title, self.amount, self.description, self.creation]
        
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







    def load_expense_data(self, id):
        
        print("Loading Expense ID:", id)
        query = QSqlQuery()
        query.prepare("SELECT * FROM expense WHERE id = ?")
        query.addBindValue(id)
        
        if query.exec() and query.next():
            
            self.category.setText(query.value(1))
            self.title.setText(query.value(2))
            self.amount.setText(str(query.value(3)))
            self.description.setText(query.value(4))
            creation_date = query.value(5)
            
            if isinstance(creation_date, QDateTime):
                creation_date = creation_date.date().toString("dd-MM-yyyy")
            elif isinstance(creation_date, QDate):
                creation_date = creation_date.toString("dd-MM-yyyy")
            else:
                creation_date = str(creation_date)
                
            self.creation.setText(creation_date)
            
            
            
            
            
            
            




