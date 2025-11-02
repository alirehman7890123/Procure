from PySide6.QtWidgets import QWidget, QComboBox, QHBoxLayout, QFrame, QLabel, QDateEdit, QLineEdit, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, QDate, Signal, QDateTime
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from functools import partial
from datetime import date

from utilities.stylus import load_stylesheets



class ReceiptListWidget(QWidget):
    
    salesdetailsignal = Signal(int)

    def __init__(self, parent=None):

        super().__init__(parent)

        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Invoice Information", objectName="SectionTitle")
        self.addinvoice = QPushButton("Add Invoice", objectName="TopRightButton")
        self.addinvoice.setCursor(Qt.PointingHandCursor)
        self.addinvoice.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.addinvoice)

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
        search_edit.setPlaceholderText("Search Customer...")
        search_edit.textChanged.connect(self.search_rows)
        
        search_layout.addWidget(search_edit, 4)
        
        
        
        from_label = QLabel("Date From")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate())
        self.date_from.setStyleSheet("""
            QCalendarWidget QWidget {
                background-color: #2b2b2b;   /* dark gray background */
                color: white;                /* white text */
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: #2b2b2b;
                color: white;
                selection-background-color: #0078d7;  /* blue highlight */
                selection-color: white;
            }
            QCalendarWidget QToolButton {
                background-color: #444;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                margin: 2px;
            }
            QCalendarWidget QToolButton::menu-indicator {
                image: none; /* hide dropdown arrow */
            }
            QCalendarWidget QSpinBox {
                background-color: #444;
                color: white;
            }
        """)

        
        
        
        to_label = QLabel("Date To")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate()) 
        self.date_to.setStyleSheet(self.date_from.styleSheet())

        
        search_layout.addWidget(from_label)
        search_layout.addWidget(self.date_from)
        
        search_layout.addWidget(to_label)
        search_layout.addWidget(self.date_to)
        
        
        search_data = QPushButton("Get Data")
        search_data.setStyleSheet("color: #333; padding: 3px 5px;")
        
        search_data.clicked.connect(self.filter_rows_by_date)
        
        search_layout.addWidget(search_data)
        
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)
        
        
        
        
        
        
        
        

        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.15, 0.40, 0.10, 0.10, 0.08])
        headers = ["Id", "Customer", "Products", "Received", "Date", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setTextElideMode(Qt.ElideRight)
        
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





    def filter_rows_by_date(self):
        print("Searching rows by date")
        
        from_date = self.date_from.date()
        to_date = self.date_to.date()
        
        print("Dates are: ", from_date, " to ", to_date)

        for row in range(self.table.rowCount()):
            # adjust column index to your date column
            date_item = self.table.item(row, 4)  
            if not date_item:
                self.table.setRowHidden(row, True)
                continue
            
            
            
            row_dt = QDateTime.fromString(date_item.text(), "yyyy-MM-dd HH:mm:ss")
            if not row_dt.isValid():
                self.table.setRowHidden(row, True)
                continue


            row_date = row_dt.date()
            # inclusive check
            in_range = from_date <= row_date <= to_date
            self.table.setRowHidden(row, not in_range)




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
        self.load_sales_into_table()
        



    def load_sales_into_table(self):
        
        query = QSqlQuery()
        query.exec("SELECT id, customer, received, creation_date FROM sales")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            sales_id = int(query.value(0))
            customer = query.value(1)
            print("Customer type is: ", type(customer))
            if customer is None or customer == '':
                customer = 0
                
            customer = int(customer)
            salesman = str(query.value(2))
            received = query.value(3)
            creation = query.value(4)
            
            if customer == 0:
                
                customer = 'Walk-in Customer'
                
            else:
            
                query2 = QSqlQuery()
                query2.prepare("SELECT name FROM customer WHERE id = ?")
                query2.addBindValue(customer)
                
                if query2.exec() and query2.next():
                    
                    customer = str(query2.value(0))
                    
            
            products = ''
            
            # get salesitems 
            items_query = QSqlQuery()
            items_query.prepare("SELECT product FROM salesitem WHERE sales = ? ")
            items_query.addBindValue(sales_id)
            
            if items_query.exec():
                
                while items_query.next():
                    
                    product_id = items_query.value(0)
                    
                    product_query = QSqlQuery()
                    product_query.prepare("SELECT name, form FROM product WHERE id=?")
                    product_query.addBindValue(product_id)
                    
                    if product_query.exec() and product_query.next():
                        
                        product_name = product_query.value(0)
                        form = product_query.value(1)
                        
                        products += f"[ {product_name} {form} ]"


            
            sales_id = str(sales_id)
            customer = str(customer)
            received = str(received)
            
            joining_date = creation
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)
                        
                        
                    
            creation = joining_date
            
            id = QTableWidgetItem(sales_id)
            customer = QTableWidgetItem(customer)
            products = QTableWidgetItem(products)
            received = QTableWidgetItem(received)
            creation = QTableWidgetItem(creation)


            self.table.setItem(row, 0, id)
            self.table.setItem(row, 1, customer)
            self.table.setItem(row, 2, products)
            self.table.setItem(row, 3, received)
            self.table.setItem(row, 4, creation)
            
            
            detail = QPushButton('Details')
            detail.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #333;
                        padding: 4px 12px;
                        border-radius: 2px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #340238;
                        color: #fff;
                    }
                    QPushButton:pressed {
                        background-color: #47034E;
                        color: #fff;
                    }
                
            """)
            
            self.table.setCellWidget(row, 5, detail)
            print("Sales ID:", sales_id)
            sales_id = int(sales_id)  # Ensure sales_id is an integer for the signal
            detail.clicked.connect(partial(self.salesdetailsignal.emit, sales_id))
            
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



