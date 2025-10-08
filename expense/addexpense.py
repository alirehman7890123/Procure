
from PySide6.QtWidgets import QWidget, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QFrame, QLineEdit, QLabel, QSpacerItem, QSizePolicy, QMessageBox
from PySide6.QtCore import QSize, Qt, QFile, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from utilities.stylus import load_stylesheets



class AddExpenseWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Expense Information", objectName="SectionTitle")
        self.expenselist = QPushButton("Expense List", objectName="TopRightButton")
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


        labels = ["Category", "Title", "Amount", "Description"]
        
        self.category = QComboBox()
        self.category.addItems(['Office', 'Pharmacist', 'Utility', 'Food' ])
        
        self.title = QComboBox()
        self.title.setEditable(True)
        self.title.addItems(['Lunch', 'Guest Food', 'Refreshment', 'Fee'])
        self.title.setStyleSheet("""
            QComboBox { color: #333; }
            QComboBox:editable { color: #333; }              /* text in the line edit */
            QComboBox QAbstractItemView {
                color: #333;                                  /* unselected items */
                background: #fff;
                border: 1px solid #ccc;
                outline: 0;
            }
            QComboBox QAbstractItemView::item { padding: 6px 8px; }
            QComboBox QAbstractItemView::item:hover { background: #f5f5f5; }
            QComboBox QAbstractItemView::item:selected {
                background: #e4682a;                          /* your orange */
                color: #fff;                                  /* selected text */
            }
        """)
        
        self.amount = QLineEdit()
        self.description = QLineEdit()

        fields = [self.category, self.title, self.amount, self.description]

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



        addexpense = QPushButton("Add Expense", objectName="SaveButton")
        addexpense.setCursor(Qt.PointingHandCursor)
        addexpense.clicked.connect(self.save_expense)

        self.layout.addWidget(addexpense)
        self.layout.addStretch()

        
        self.setStyleSheet(load_stylesheets())


    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #0078d7; border: none;")
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")
        return super().eventFilter(obj, event)
    
    

    def save_expense(self):
        
        # Create database connection
        db = QSqlDatabase.database()
        query = QSqlQuery(db)
        
        # Get values from input fields
        category = self.category.currentText().strip()
        title = self.title.currentText().strip()
        amount = self.amount.text().strip()
        note = self.description.text()

        # Validate required fields
        if not amount or amount == '':
            QMessageBox.warning(self, "Required Fields", "Amount are required fields")
            return

        
        # Insert customer data
        query.prepare("""
            INSERT INTO expense (category, title, amount, note) 
            VALUES (?, ?, ?, ?)
        """)
        query.addBindValue(category)
        query.addBindValue(title) 
        query.addBindValue(amount)
        query.addBindValue(note)

        if query.exec():
            QMessageBox.information(self, "Success", "Expense added successfully")
            self.clear_fields()
        else:
            QMessageBox.critical(self, "Error", f"Error adding customer: {query.lastError().text()}")    





    def clear_fields(self):
        
        self.category.clear()
        self.title.clear()
        self.amount.clear()
        self.description.clear()