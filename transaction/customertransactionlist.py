from PySide6.QtWidgets import QWidget, QFrame, QHBoxLayout, QMessageBox, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal, QDateTime
from PySide6.QtSql import QSqlQuery
from functools import partial

from utilities.stylus import load_stylesheets





class CustomerTransactionListWidget(QWidget):
    
    transaction_detail_signal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Transaction List", objectName="SectionTitle")
        self.transaction_list = QPushButton("All Customer Transactions", objectName="TopRightButton")
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


        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        headers = ["#", "Customer", "Type", "Paid", "Received", "Date", "Detail"]
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



    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_customer_transactions()
        



    # def load_customer_transactions(self):
        
    #     query = QSqlQuery()
    #     query.prepare("SELECT id, customer, transaction_type, paid, received, creation_date FROM customer_transaction")

    #     if not query.exec():
    #         QMessageBox.critical(self, "Error", "Failed to load customers: " + query.lastError().text())
    #         print("Error executing query:", query.lastError().text())
    #         return
        
    #     self.table.setRowCount(0)  # Clear existing rows

    #     row = 0
        
    #     while query.next():
            
    #         self.table.insertRow(row)
            
    #         transaction_id = int(query.value(0))
    #         customer_id = query.value(1)
            
    #         if customer_id is not None:
    #             customer_id = int(customer_id)
                
            
    #         transaction_type = str(query.value(2))
    #         paid = str(query.value(3))
    #         received = str(query.value(4))
    #         date = query.value(5)
            
    #         date = date.toString("yyyy-MM-dd HH:mm:ss")
            
    #         # Get Supplier
    #         # Get Supplier name from database
    #         if customer is not None:
    #             customer_query = QSqlQuery()
    #             customer_query.prepare("SELECT name FROM customer WHERE id = ?")
    #             customer_query.addBindValue(customer_id)
            
    #             customer_name = ""
                
    #             if customer_query.exec() and customer_query.next():
                    
    #                 customer_name = customer_query.value(0)
            
    #         else:
    #             customer_name = 'Walk-in Customer'  


    #         # Create table items
    #         counter = QTableWidgetItem(str(row + 1))
    #         customer = QTableWidgetItem(customer_name)
    #         trans_type = QTableWidgetItem(transaction_type) 
    #         paid_amount = QTableWidgetItem(paid)
    #         received_amount = QTableWidgetItem(received)
    #         date_item = QTableWidgetItem(str(date))

    #         # Add items to table
    #         self.table.setItem(row, 0, counter)
    #         self.table.setItem(row, 1, customer)
    #         self.table.setItem(row, 2, trans_type)
    #         self.table.setItem(row, 3, paid_amount)
    #         self.table.setItem(row, 4, received_amount) 
    #         self.table.setItem(row, 5, date_item)                        
                        
            
    #         detail = QPushButton('Details')
    #         detail.setStyleSheet("""
    #                 background-color: #333;
    #                 color: #fff;
    #                 font-weight: 600;
                
    #         """)
            
    #         self.table.setCellWidget(row, 6, detail)
    #         detail.clicked.connect(partial(self.transaction_detail_signal.emit, transaction_id))
            
    #         row += 1
        

    def load_customer_transactions(self):

        query = QSqlQuery()
        query.prepare("""
                    SELECT 
                        ct.id,
                        ct.customer,
                        COALESCE(c.name, 'Walk-in Customer'),
                        ct.transaction_type,
                        ct.paid,
                        ct.received,
                        ct.creation_date
                    FROM customer_transaction ct
                    LEFT JOIN customer c ON ct.customer = c.id
                    WHERE ct.customer IS NOT NULL
                    ORDER BY ct.id DESC
            """)

        if not query.exec():
            QMessageBox.critical(
                self,
                "Error",
                "Failed to load transactions: " + query.lastError().text()
            )
            return

        self.table.setRowCount(0)

        row = 0

        while query.next():

            self.table.insertRow(row)

            transaction_id = int(query.value(0))
            customer_name = str(query.value(2))
            transaction_type = str(query.value(3))
            paid = str(query.value(4) or "0")
            received = str(query.value(5) or "0")

            date_value = query.value(6)

            dt = QDateTime.fromString(str(date_value), "yyyy-MM-dd HH:mm:ss")
            date_str = dt.toString("yyyy-MM-dd HH:mm:ss") if dt.isValid() else str(date_value)

            # Table Items
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(customer_name))
            self.table.setItem(row, 2, QTableWidgetItem(transaction_type))
            self.table.setItem(row, 3, QTableWidgetItem(paid))
            self.table.setItem(row, 4, QTableWidgetItem(received))
            self.table.setItem(row, 5, QTableWidgetItem(date_str))

            detail_btn = QPushButton("Details")
            detail_btn.setStyleSheet("""
                background-color: #333;
                color: #fff;
                font-weight: 600;
            """)

            self.table.setCellWidget(row, 6, detail_btn)
            detail_btn.clicked.connect(
                lambda _, tid=transaction_id: self.transaction_detail_signal.emit(tid)
            )


            

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





           
        

