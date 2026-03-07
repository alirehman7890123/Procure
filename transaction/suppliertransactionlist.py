from PySide6.QtWidgets import QWidget, QFrame, QLineEdit, QHBoxLayout, QLabel, QMessageBox, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal, QEvent
from PySide6.QtSql import QSqlQuery
from functools import partial

from utilities.stylus import load_stylesheets





class SupplierTransactionListWidget(QWidget):
    
    transaction_detail_signal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        
        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("All Transactions", objectName="SectionTitle")
        self.transaction_list = QPushButton("All Supplier Transactions", objectName="TopRightButton")
        self.transaction_list.setCursor(Qt.PointingHandCursor)
        self.transaction_list.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.transaction_list)

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
        search_edit.setPlaceholderText("Search Supplier...")
        search_edit.textChanged.connect(self.search_rows)
        search_layout.addWidget(search_edit)
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)

        
        
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        headers = ["#", "Supplier", "Type", "Paid", "Received", "Date", "Detail"]
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
        self.load_supplier_transactions()
        



    def load_supplier_transactions(self):
        
        print("Loading Supplier Transactions....")
        
        query = QSqlQuery()
        query.prepare("SELECT id, supplier, transaction_type, paid, received, creation_date FROM supplier_transaction")

        if not query.exec():
            
            QMessageBox.critical(self, "Error", "Failed to load suppliers: " + query.lastError().text())
            print("Error executing query:", query.lastError().text())
            return
        
        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            transaction_id = int(query.value(0))
            supplier_id = int(query.value(1))
            transaction_type = str(query.value(2))
            paid = str(query.value(3))
            received = str(query.value(4))
            date = query.value(5)
            
            
            # Get Supplier name from database
            supplier_query = QSqlQuery()
            supplier_query.prepare("SELECT name FROM supplier WHERE id = ?")
            supplier_query.addBindValue(supplier_id)
            
            supplier_name = ""
            
            if supplier_query.exec() and supplier_query.next():
                
                supplier_name = supplier_query.value(0)    


            # Create table items
            counter = QTableWidgetItem(str(row + 1))
            supplier = QTableWidgetItem(supplier_name)
            trans_type = QTableWidgetItem(transaction_type) 
            paid_amount = QTableWidgetItem(paid)
            received_amount = QTableWidgetItem(received)
            date_item = QTableWidgetItem(str(date))

            # Add items to table
            self.table.setItem(row, 0, counter)
            self.table.setItem(row, 1, supplier)
            self.table.setItem(row, 2, trans_type)
            self.table.setItem(row, 3, paid_amount)
            self.table.setItem(row, 4, received_amount) 
            self.table.setItem(row, 5, date_item)                        
                        
            
            detail = QPushButton('Details')
            detail.setStyleSheet("""
                    background-color: #333;
                    color: #fff;
                    font-weight: 600;
                
            """)
            
            self.table.setCellWidget(row, 6, detail)
            detail.clicked.connect(partial(self.transaction_detail_signal.emit, transaction_id))
            
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









        

