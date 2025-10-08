from PySide6.QtWidgets import QWidget, QComboBox, QGridLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtSql import QSqlQuery
from functools import partial
from utilities.stylus import load_stylesheets





class SupplierTransactionWidget(QWidget):
    
    transaction_page_signal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        layout = QVBoxLayout(self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)


        heading = QLabel("Supplier List", objectName='myheading')
        self.addsupplier = QPushButton('Add Supplier', objectName='supplierlist')

        grid_layout.addWidget(heading, 0,0)
        grid_layout.addWidget(self.addsupplier, 0,2)

        layout.addWidget(grid_widget)

        

        self.table = QTableWidget()
        
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "Name", "Contact", "Email", "Payable", "Receiveable", "Pay / Receive"
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
        self.load_suppliers_transactions()
        



    def load_suppliers_transactions(self):
        
        query = QSqlQuery()
        query.exec("SELECT id, name, contact, email, payable, receiveable FROM supplier")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            suppid = int(query.value(0))
            name = str(query.value(1))
            contact = str(query.value(2))
            email = str(query.value(3))
            payable = str(query.value(4))
            receiveable = str(query.value(5))
            
            counter = str(row + 1)
            counter = QTableWidgetItem(counter)
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
            pay.clicked.connect(partial(self.transaction_page_signal.emit, suppid))
            
            row += 1
        




            
        

