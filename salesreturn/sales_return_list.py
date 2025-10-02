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


        heading = QLabel("purchase Return List", objectName='myheading')
        self.addSalesReturn = QPushButton('Add purchase Return', objectName='supplierslit')

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
        self.load_purchases_into_table()
        



    def load_purchases_into_table(self):
        
        
        query = QSqlQuery()
        query.exec("SELECT id, supplier, rep, creation_date FROM purchase_return")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            id = int(query.value(0))
            supplier = query.value(1)
            rep = query.value(2)
            creation = query.value(3)
            
            
            # Get Supplier
            supplier = int(supplier)
            
            supplier_query = QSqlQuery()
            supplier_query.prepare("SELECT name FROM supplier WHERE id = ?")
            supplier_query.addBindValue(supplier)        
            
            if supplier_query.exec():
                
                while supplier_query.next():
                    
                    supplier = supplier_query.value(0)
                    

            rep_query = QSqlQuery()
            rep_query.prepare("SELECT name FROM rep WHERE id = ?")
            rep_query.addBindValue(rep)
            
            if rep_query.exec():
                while rep_query.next():
                    rep = rep_query.value(0)
                    
                    
            if isinstance(creation, QDate):  # or QDateTime
                creation = creation.toString("dd-MM-yyyy")  # or "yyyy-MM-dd"
            else:
                creation = str(creation)

            self.table.setItem(row, 0, QTableWidgetItem(str(id)))
            self.table.setItem(row, 1, QTableWidgetItem(supplier))
            self.table.setItem(row, 2, QTableWidgetItem(rep))
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
        




            
        

