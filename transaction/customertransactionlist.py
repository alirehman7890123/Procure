from PySide6.QtWidgets import QWidget, QComboBox, QGridLayout, QMessageBox, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtSql import QSqlQuery
from functools import partial

from utilities.stylus import load_stylesheets





class CustomerTransactionListWidget(QWidget):
    
    transaction_detail_signal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        layout = QVBoxLayout(self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)


        heading = QLabel("Transaction List", objectName='myheading')
        self.addpayment = QPushButton('Add New Payment', objectName='supplierlist')

        grid_layout.addWidget(heading, 0,0)
        grid_layout.addWidget(self.addpayment, 0,2)

        layout.addWidget(grid_widget)

        

        self.table = QTableWidget()
        
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "Customer", "Type", "Paid", "Received", "Date", "Detail"
        ])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.setColumnWidths(table, [0.1, 0.4, 0.3, 0.2, 0.2]) 

        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setFixedHeight(30)

        header.setStyleSheet("""
                background-color: #333;
                color: white;              
                font-weight: 600;
            
        """)

        
        layout.addWidget(self.table)
        self.setLayout(layout)

        
        self.setStyleSheet(load_stylesheets())



    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_customer_transactions()
        



    def load_customer_transactions(self):
        
        query = QSqlQuery()
        query.prepare("SELECT id, customer, transaction_type, paid, received, creation_date FROM customer_transaction")

        if not query.exec():
            QMessageBox.critical(self, "Error", "Failed to load customers: " + query.lastError().text())
            print("Error executing query:", query.lastError().text())
            return
        
        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            transaction_id = int(query.value(0))
            customer_id = int(query.value(1))
            transaction_type = str(query.value(2))
            paid = str(query.value(3))
            received = str(query.value(4))
            date = query.value(5)
            
            date = date.toString("yyyy-MM-dd HH:mm:ss")
            
            # Get Supplier
            # Get Supplier name from database
            customer_query = QSqlQuery()
            customer_query.prepare("SELECT name FROM customer WHERE id = ?")
            customer_query.addBindValue(customer_id)
            
            customer_name = ""
            
            if customer_query.exec() and customer_query.next():
                
                customer_name = customer_query.value(0)    


            # Create table items
            counter = QTableWidgetItem(str(row + 1))
            customer = QTableWidgetItem(customer_name)
            trans_type = QTableWidgetItem(transaction_type) 
            paid_amount = QTableWidgetItem(paid)
            received_amount = QTableWidgetItem(received)
            date_item = QTableWidgetItem(str(date))

            # Add items to table
            self.table.setItem(row, 0, counter)
            self.table.setItem(row, 1, customer)
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
        




            
        

