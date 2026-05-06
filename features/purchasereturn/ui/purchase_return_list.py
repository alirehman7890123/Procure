from PySide6.QtWidgets import QWidget, QComboBox, QHBoxLayout, QFrame, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal, QDate, QDateTime
from functools import partial
from medic.services.return_read_service import fetch_purchase_return_list_rows
from medic.utilities.stylus import load_stylesheets





class PurchaseReturnListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Return List", objectName="SectionTitle")
        self.addPurchaseReturn = QPushButton("Purchase Returns List", objectName="TopRightButton")
        self.addPurchaseReturn.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
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
        
        self.row_height = 35
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
        
        self.table.setMinimumWidth(700)
        
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
        rows = fetch_purchase_return_list_rows()
        self.table.setRowCount(0)

        for row, data in enumerate(rows):
            self.table.insertRow(row)
            return_id = data["id"]
            self.table.setItem(row, 0, QTableWidgetItem(str(return_id)))
            self.table.setItem(row, 1, QTableWidgetItem(data["supplier_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["rep_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(data["creation_date"]))

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
            detail.clicked.connect(partial(self.detailpagesignal.emit, return_id))
        




    
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




            
        
