from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHeaderView, QLineEdit, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtSql import QSqlQuery
from functools import partial

from utilities.stylus import load_stylesheets



class ProductListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Product Information", objectName="SectionTitle")
        self.addproduct = QPushButton("Add Product", objectName="TopRightButton")
        self.addproduct.setCursor(Qt.PointingHandCursor)
        self.addproduct.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.addproduct)

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
        search_edit.setPlaceholderText("Search Product...")
        search_edit.textChanged.connect(self.search_rows)
        search_layout.addWidget(search_edit)
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)


        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.12, 0.12, 0.10, 0.08, 0.08, 0.05])
        headers = ['No.', 'Product', 'Code/Barcode', 'Category', 'Manufacturer', 'Stock', 'Level', 'Status', 'Detail']
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

        # Selection behaviour
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        
        self.layout.addStretch()


        
        self.setStyleSheet(load_stylesheets())




    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_products_into_table()
        

    def search_rows(self, text):
        
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
    


    def load_products_into_table(self):
        

        query = QSqlQuery()
        query.exec("SELECT id, name, code, category, brand FROM product")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            counter = row + 1
            counter = str(counter)
            self.table.insertRow(row)
            
            product_id = query.value(0)
            name = query.value(1)
            code = query.value(2)
            category = query.value(3)
            brand = query.value(4)
            
            
            counter = QTableWidgetItem(counter)
            name = QTableWidgetItem(name)
            code = QTableWidgetItem(code)
            category = QTableWidgetItem(category)
            brand = QTableWidgetItem(brand)

            
            self.table.setItem(row, 0, counter)
            self.table.setItem(row, 1, name)
            self.table.setItem(row, 2, code)
            self.table.setItem(row, 3, category)
            self.table.setItem(row, 4, brand)
            
            product_id = int(product_id)
            
            
            # bring stock and level from stock table
            stock_query = QSqlQuery()
            stock_query.prepare("SELECT packsize, units, reorder from stock where product = ?")
            stock_query.addBindValue(product_id)
            
            if stock_query.exec() and stock_query.next():
                
                packsize = stock_query.value(0)
                units = stock_query.value(1)
                reorder = stock_query.value(2)
                
                # packsize = int(packsize)
                # units = int(units)
                # reorder = int(reorder)
                
                level = ""
                
                
                if packsize != 0:
                    
                    packs = units // packsize
                    
                    if packs > reorder:
                        level = 'normal'
                    else:
                        level = 'low'
                    
                    
                    rems = units % packsize

                    if packs > 0 and rems > 0:
                        stock = f"{packs} + ({rems})"
                    elif packs > 0:
                        stock = f"{packs}"
                    else:
                        stock = f"    ({rems})"

                
                
                stock = QTableWidgetItem(str(stock))
                # stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                level = QTableWidgetItem(level)
                
                self.table.setItem(row, 5, stock)
                self.table.setItem(row, 6, level)
            
                
            
            
            # inserting product status from batch table
            
            batch_query = QSqlQuery()
            batch_query.prepare("SELECT status, resolved FROM batch WHERE product = :product_id")
            batch_query.bindValue(":product_id", product_id)
            
            status = "Valid"
            
            if batch_query.exec():
                
                while batch_query.next():

                    batch_status = batch_query.value(0)
                    resolved = batch_query.value(1)
                    
                    if resolved:
                        continue
                    
                    if batch_status == 'near-expiry' or batch_status == 'expired':
                        status = 'Near / Expired'
                    
                    
            else:
                
                print("Error executing batch query:", batch_query.lastError().text())
            
            
            status = QTableWidgetItem(status)
            self.table.setItem(row, 7, status)
            
            detail = QPushButton('Details')
            detail.setCursor(Qt.PointingHandCursor)
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
            
            
            self.table.setCellWidget(row, 8, detail)
            detail.clicked.connect(partial(self.detailpagesignal.emit, product_id))
            
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



            
        



