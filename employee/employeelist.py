from PySide6.QtWidgets import QWidget, QLineEdit ,QHBoxLayout, QFrame, QGridLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, QDate, Signal
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from functools import partial
from datetime import date
from utilities.stylus import load_stylesheets



class EmployeeListWidget(QWidget):
    
    detailpagesignal = Signal(int)

    def __init__(self, parent=None):

        super().__init__(parent)

        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Employee Information", objectName="SectionTitle")
        self.addemployee = QPushButton("Add Employee", objectName="TopRightButton")
        self.addemployee.setCursor(Qt.PointingHandCursor)
        self.addemployee.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.addemployee)

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
        
        # Search Field
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search Employee...")
        search_edit.textChanged.connect(self.search_rows)
        search_layout.addWidget(search_edit)
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)
        
        
        
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        headers = ["No.", "Name", "Contact", "Role", "Badge", "Status", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        detail_col = headers.index("Detail")
        self.table.horizontalHeaderItem(detail_col).setTextAlignment(Qt.AlignCenter)
        
        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   

        self.table.setMinimumWidth(1000)
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)
        
        # Alternating row colors
        self.table.setAlternatingRowColors(True)

        # Selection behaviour
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        
        self.layout.addStretch()


        self.setStyleSheet(load_stylesheets())

        

    def search_rows(self, text):
        
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
            
            

    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_employees_into_table()
        



    def load_employees_into_table(self):
        
        query = QSqlQuery()
        query.exec("SELECT id, name, contact, role, badge, status FROM employee")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            row_no = row + 1
            employee_id = int(query.value(0))
            name = query.value(1)
            contact = query.value(2)
            role = query.value(3)
            badge = query.value(4)
            status = query.value(5)

            
            row_no_item = QTableWidgetItem(str(row_no))
            name = QTableWidgetItem(name)
            contact = QTableWidgetItem(contact)
            role = QTableWidgetItem(role)
            badge = QTableWidgetItem(badge)
            status = QTableWidgetItem(status)
            
            
            self.table.setItem(row, 0, row_no_item)
            self.table.setItem(row, 1, name)
            self.table.setItem(row, 2, contact)
            self.table.setItem(row, 3, role)
            self.table.setItem(row, 4, badge)
            self.table.setItem(row, 5, status)
            
            
            
            detail = QPushButton('Details')
            detail.setStyleSheet("""
                    background-color: #777;
                    color: blue;              
                    font-weight: 600;
                
            """)
            
            self.table.setCellWidget(row, 6, detail)
            detail.clicked.connect(partial(self.detailpagesignal.emit, employee_id))
            
            row += 1
        




class MyTable(QTableWidget):
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # user can drag

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)





