from PySide6.QtWidgets import QWidget, QComboBox, QHBoxLayout, QFrame, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal, QDate, QDateTime
from PySide6.QtSql import QSqlQuery
from functools import partial
from utilities.stylus import load_stylesheets





class PurchaseReturnListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Return List", objectName="SectionTitle")
        self.addPurchaseReturn = QPushButton("Purchase Returns List", objectName="TopRightButton")
        self.addPurchaseReturn.setCursor(Qt.PointingHandCursor)
        self.addPurchaseReturn.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.addPurchaseReturn)

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
        self.min_visible_rows = 5
        
    
        self.table = MyTable(column_ratios=[0.05, 0.25, 0.10, 0.10, 0.05])
        headers = ["Id", "Supplier", "Rep", "Date", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.table.verticalHeader().setFixedWidth(0)
        remove_col = headers.index("Detail")
        self.table.horizontalHeaderItem(remove_col).setTextAlignment(Qt.AlignCenter)
        
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
                    
                    
            joining_date = creation
            
            if isinstance(joining_date, QDateTime):
                joining_date = joining_date.date().toString("dd-MM-yyyy")
            elif isinstance(joining_date, QDate):
                joining_date = joining_date.toString("dd-MM-yyyy")
            else:
                joining_date = str(joining_date)
                
            creation = joining_date

            self.table.setItem(row, 0, QTableWidgetItem(str(id)))
            self.table.setItem(row, 1, QTableWidgetItem(supplier))
            self.table.setItem(row, 2, QTableWidgetItem(rep))
            self.table.setItem(row, 3, QTableWidgetItem(creation))

            detail = QPushButton('Details')
            detail.setStyleSheet("""
                QPushButton {
                    color: #333;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #333;
                    color: #fff;
                }
            """)
            
            self.table.setCellWidget(row, 4, detail)
            detail.clicked.connect(partial(self.detailpagesignal.emit, id))
            
            row += 1
        




    
class MyTable(QTableWidget):
    
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # user can drag
        header.setMinimumSectionSize(10)  # let it shrink smaller

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)




            
        

