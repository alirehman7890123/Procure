from PySide6.QtWidgets import QWidget, QComboBox,QMessageBox, QGridLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, QDate, Signal
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from functools import partial
from datetime import date

from utilities.stylus import load_stylesheets





class SaleHoldListWidget(QWidget):
    
    holddetailsignal = Signal(int)

    def __init__(self, parent=None):

        super().__init__(parent)

        
        layout = QVBoxLayout(self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)


        heading = QLabel("On-Hold Sales Order", objectName='myheading')

        grid_layout.addWidget(heading, 0,0)

        layout.addWidget(grid_widget)


        self.supplier_table = QTableWidget()
        
        self.supplier_table.setColumnCount(6)
        self.supplier_table.setHorizontalHeaderLabels([
            "#", "Customer", "SalesMan", "Status", "Date", "Details"
        ])
        self.supplier_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.supplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.setColumnWidths(supplier_table, [0.1, 0.4, 0.3, 0.2, 0.2]) 

        self.supplier_table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.supplier_table.verticalHeader().setFixedWidth(0)
        header = self.supplier_table.horizontalHeader()
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
        
        layout.addWidget(self.supplier_table)
        self.setLayout(layout)

        
        self.setStyleSheet(load_stylesheets())



    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_sales_into_table()
        



    def load_sales_into_table(self):
        
        query = QSqlQuery()
        query.exec("SELECT id, customer, salesman, status, creation_date FROM holdsale")

        self.supplier_table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.supplier_table.insertRow(row)
            
            holding_id = int(query.value(0))
            customer = int(query.value(1))
            salesman = str(query.value(2))
            status = query.value(3)
            creation = query.value(4)
            
            if customer == 0:
                
                customer = 'Walk-in Customer'
                
            else:
            
                query2 = QSqlQuery()
                query2.prepare("SELECT name FROM customer WHERE id = ?")
                query2.addBindValue(customer)
                
                if query2.exec() and query2.next():
                    
                    customer = str(query2.value(0))


            salesman_query = QSqlQuery()
            salesman_query.prepare("SELECT name FROM employee WHERE id = ?")
            salesman_query.addBindValue(salesman)
            

            if salesman_query.exec() and salesman_query.next():
                salesman = str(salesman_query.value(0))
                
            holding_id = str(holding_id)
            customer = str(customer)
            salesman = str(salesman)
            status = str(status)
            orderdate = creation
            
            
            if isinstance(orderdate, QDate):  # or QDateTime
                orderdate = orderdate.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
            else:
                orderdate = str(orderdate)
                        
            
            id = QTableWidgetItem(holding_id)
            customer = QTableWidgetItem(customer)
            salesman = QTableWidgetItem(salesman)
            status = QTableWidgetItem(status)
            orderdate = QTableWidgetItem(orderdate)
            
            
            self.supplier_table.setItem(row, 0, id)
            self.supplier_table.setItem(row, 1, customer)
            self.supplier_table.setItem(row, 2, salesman)
            self.supplier_table.setItem(row, 3, status)
            self.supplier_table.setItem(row, 4, orderdate)
            
            detail = QPushButton('Details')
            detail.setStyleSheet("""
                                 
                    background-color: #777;
                    color: blue;              
                    font-weight: 600;
                
            """)
            
            self.supplier_table.setCellWidget(row, 5, detail)
            print("Holding ID:", holding_id)
            holding_id = int(holding_id)  # Ensure sales_id is an integer for the signal
            detail.clicked.connect(partial(self.holddetailsignal.emit, holding_id))
            
            row += 1
        
