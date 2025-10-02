from PySide6.QtWidgets import QWidget, QComboBox, QGridLayout, QLabel, QMessageBox, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtSql import QSqlQuery
from functools import partial

from utilities.stylus import load_stylesheets





class SupplierTransactionListWidget(QWidget):
    
    transaction_detail_signal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        layout = QVBoxLayout(self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)

        print("Printing Transaction List")

        heading = QLabel("Transaction List", objectName='myheading')
        self.addpayment = QPushButton('Add New Payment', objectName='supplierlist')

        grid_layout.addWidget(heading, 0,0)
        grid_layout.addWidget(self.addpayment, 0,2)

        layout.addWidget(grid_widget)

        

        self.table = QTableWidget()
        
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "Supplier", "Type", "Paid", "Received", "Date", "Detail"
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

        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(['option 1', 'option 2', 'option 3'])

        combo.setStyleSheet("""
                                QComboBox {
                                    background-color: lightgray;
                                    color: #333;
                                    padding: 5px;
                                }
                                QComboBox QAbstractItemView {
                                    background-color: white;
                                    color: black;
                                    selection-background-color: lightblue;
                                    selection-color: black;
                                }
                            """)
        layout.addWidget(combo)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

        
        self.setStyleSheet(load_stylesheets())



    
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
        




            
        

