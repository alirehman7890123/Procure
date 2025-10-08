from PySide6.QtWidgets import QWidget, QComboBox, QGridLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal, QDate
from PySide6.QtSql import QSqlQuery
from functools import partial


from utilities.stylus import load_stylesheets




class SalesReturnListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        layout = QVBoxLayout(self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)


        heading = QLabel("Sales Return List", objectName='SectionTitle')
        self.addSalesReturn = QPushButton('Add Sales Return', objectName='TopRightButton')

        grid_layout.addWidget(heading, 0,0)
        grid_layout.addWidget(self.addSalesReturn, 0,2)

        layout.addWidget(grid_widget)

        

        self.table = QTableWidget()
        
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Id", "Supplier", "Rep", "Date", "Detail"
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
        self.load_sales_into_table()
        



    def load_sales_into_table(self):
        
        
        query = QSqlQuery()
        query.exec("SELECT id, customer, salesman, creation_date FROM salesreturn")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            id = int(query.value(0))
            customer = query.value(1)
            salesman = query.value(2)
            creation = query.value(3)
            
            
            # Get Customer
            if customer == '':
                customer = None
            
            if customer is not None:
                customer = int(customer)
            
                customer_query = QSqlQuery()
                customer_query.prepare("SELECT name FROM customer WHERE id = ?")
                customer_query.addBindValue(customer)        
                
                if customer_query.exec():
                    while customer_query.next():
                        customer = customer_query.value(0)
            
            else:
                customer = "Walk-In Customer"


            salesman_query = QSqlQuery()
            salesman_query.prepare("SELECT firstname, lastname FROM auth WHERE id = ?")
            salesman_query.addBindValue(int(salesman))
            
            if salesman_query.exec():
                while salesman_query.next():
                    firstname = salesman_query.value(0)
                    lastname = salesman_query.value(1)
                    
                    salesman = f"{firstname} {lastname}"
                    
                    
                    
            if isinstance(creation, QDate):  # or QDateTime
                creation = creation.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
            else:
                creation = str(creation)

            self.table.setItem(row, 0, QTableWidgetItem(str(id)))
            self.table.setItem(row, 1, QTableWidgetItem(customer))
            self.table.setItem(row, 2, QTableWidgetItem(salesman))
            self.table.setItem(row, 3, QTableWidgetItem(creation))

            detail = QPushButton('Details')
            detail.setStyleSheet("""
                    background-color: #777;
                    color: blue;              
                    font-weight: 600;
                
            """)
            
            self.table.setCellWidget(row, 4, detail)
            detail.clicked.connect(partial(self.detailpagesignal.emit, id))
            
            row += 1
        




            
        

