from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QLineEdit, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtSql import QSqlQuery
from functools import partial
from utilities.stylus import load_stylesheets




class SalesRepListWidget(QWidget):
    
    detailpagesignal = Signal(int)

    def __init__(self, parent=None):

        super().__init__(parent)


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Rep Information", objectName="SectionTitle")
        self.addsalesrep = QPushButton("Add Sales Rep", objectName="TopRightButton")
        self.addsalesrep.setCursor(Qt.PointingHandCursor)
        self.addsalesrep.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.addsalesrep)

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

        self.table = MyTable(column_ratios=[0.05, 0.20, 0.20, 0.10, 0.15, 0.10])
        headers = ['Sr. No.', 'Sales Rep', 'Supplier', 'Contact', 'Status', 'Detail']
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
        self.load_salesreps_into_table()
        


      
    def load_salesreps_into_table(self):
        print("Loading Sales Reps")

        query = QSqlQuery()
        sql = "SELECT id, name, supplier_id, contact, status FROM rep"
        if not query.exec(sql):
            print("Error Loading Sales Reps:", query.lastError().text())
            return

        self.table.setRowCount(0)  # clear existing rows
        row = 0

        while query.next():
            rep_id = int(query.value(0))
            name = query.value(1)
            supplier_id = query.value(2)
            contact = query.value(3)
            status = query.value(4)

            # Resolve supplier name
            supplier_name = self.get_supplier_name(supplier_id)

            # Insert row
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(str(name)))
            self.table.setItem(row, 2, QTableWidgetItem(str(supplier_name)))
            self.table.setItem(row, 3, QTableWidgetItem(str(contact)))
            self.table.setItem(row, 4, QTableWidgetItem(str(status)))

            # Detail button
            detail = QPushButton("Details")
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
            detail.clicked.connect(partial(self.detailpagesignal.emit, rep_id))
            self.table.setCellWidget(row, 5, detail)

            row += 1
            


    def get_supplier_name(self, supplier_id):
        
        query = QSqlQuery()
        
        query.prepare("SELECT name FROM supplier WHERE id = :id")
        query.bindValue(":id", supplier_id)
        
        if query.exec() and query.next():
            
            return query.value(0)
        
        return "Unknown"



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






            
        



