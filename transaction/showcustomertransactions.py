from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtSql import QSqlQuery
from functools import partial

from utilities.stylus import load_stylesheets




class CustomerTransactionWidget(QWidget):
    
    transaction_page_signal = Signal(int)

    def __init__(self, parent=None):

        super().__init__(parent)


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Customer Transaction List", objectName="SectionTitle")
        self.transactionpage = QPushButton("Main Transactions Page", objectName="TopRightButton")
        self.transactionpage.setCursor(Qt.PointingHandCursor)
        self.transactionpage.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.transactionpage)

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
        
        
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        headers = ["#", "Name", "Contact", "Email", "Payable", "Receiveable", "Pay / Receive"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        detail_col = headers.index("Pay / Receive")
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

        
        self.layout.addWidget(self.table)
        self.layout.addStretch()

        
        self.setStyleSheet(load_stylesheets())

        
        
        
        




    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_customers_into_table()
        



    def load_customers_into_table(self):
        
        
        query = QSqlQuery()
        query.exec("SELECT id, name, contact, email, payable, receiveable FROM customer")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            cust_id = int(query.value(0))
            name = str(query.value(1))
            contact = str(query.value(2))
            email = str(query.value(3))
            payable = str(query.value(4))
            receiveable = str(query.value(5))
            
            
            counter = QTableWidgetItem(row +1)
            name = QTableWidgetItem(name)
            contact = QTableWidgetItem(contact)
            email = QTableWidgetItem(email)
            payable = QTableWidgetItem(payable)
            receiveable = QTableWidgetItem(receiveable)
            
            self.table.setItem(row, 0, counter)
            self.table.setItem(row, 1, name)
            self.table.setItem(row, 2, contact)
            self.table.setItem(row, 3, email)
            self.table.setItem(row, 4, payable)
            self.table.setItem(row, 5, receiveable)
            
            pay = QPushButton('Pay / Receive')
            pay.setStyleSheet("""
                    background-color: #333;
                    color: #fff;
                    font-weight: 600;
                
            """)
            
            self.table.setCellWidget(row, 6, pay)
            pay.clicked.connect(partial(self.transaction_page_signal.emit, cust_id))
            
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



            
        

