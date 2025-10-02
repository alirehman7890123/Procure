from PySide6.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtSql import QSqlQuery
from functools import partial
from utilities.stylus import load_stylesheets





class CustomerListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Customer Information", objectName="SectionTitle")
        self.addcustomer = QPushButton("Add Customer", objectName="TopRightButton")
        self.addcustomer.setCursor(Qt.PointingHandCursor)
        self.addcustomer.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.addcustomer)

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
        self.layout.addSpacing(10)
        
        # Search Field
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search Customer...")
        search_edit.textChanged.connect(self.search_rows)
        search_layout.addWidget(search_edit)
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)
        
        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.20, 0.10, 0.20, 0.15, 0.10, 0.10, 0.10])
        headers = ["No.", "Name", "Contact", "Email", "Status", "Payable", "Receiveable", "Detail"]
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
        self.load_customers_into_table()
        



    def load_customers_into_table(self):
        
        
        query = QSqlQuery()
        query.exec("SELECT id, name, contact, email, status, payable, receiveable FROM customer")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            self.table.insertRow(row)
            
            row_no = int(row + 1)
            cust_id = int(query.value(0))
            name = query.value(1)
            contact = query.value(2)
            email = query.value(3)
            status = query.value(4)
            payable = query.value(5)
            receiveable = query.value(6)
            
            
            row_no_item = QTableWidgetItem(str(row_no))
            name = QTableWidgetItem(name)
            contact = QTableWidgetItem(contact)
            email = QTableWidgetItem(email)
            status = QTableWidgetItem(status)
            payable = QTableWidgetItem(str(payable))
            receiveable = QTableWidgetItem(str(receiveable))
            
            self.table.setItem(row, 0, row_no_item)
            self.table.setItem(row, 1, name)
            self.table.setItem(row, 2, contact)
            self.table.setItem(row, 3, email)
            self.table.setItem(row, 4, status)
            self.table.setItem(row, 5, payable)
            self.table.setItem(row, 6, receiveable)

            detail = QPushButton('Details')
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
            
            self.table.setCellWidget(row, 7, detail)
            detail.clicked.connect(partial(self.detailpagesignal.emit, cust_id))
            
            row += 1
        

    
    
    def search_rows(self, text):
        
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
            
            
    # from PySide6.QtCore import Qt
    # from PySide6.QtGui import QTextDocument
    # from PySide6.QtWidgets import QTableWidgetItem

    # def search_customers(self, text):
    #     # Reset formatting first
    #     for row in range(self.table.rowCount()):
    #         for col in range(self.table.columnCount() - 1):
    #             item = self.table.item(row, col)
    #             if item:
    #                 item.setText(item.text())  # reset to plain text

    #     if not text.strip():
    #         # show all if search is empty
    #         for row in range(self.table.rowCount()):
    #             self.table.setRowHidden(row, False)
    #         return

    #     text_lower = text.lower()

    #     for row in range(self.table.rowCount()):
    #         match = False
    #         for col in range(self.table.columnCount() - 1):
    #             item = self.table.item(row, col)
    #             if item:
    #                 cell_text = item.text()
    #                 cell_text_lower = cell_text.lower()
    #                 if text_lower in cell_text_lower:
    #                     match = True
    #                     # highlight by wrapping the match in <b> tags
    #                     start = cell_text_lower.find(text_lower)
    #                     end = start + len(text)
    #                     highlighted = (
    #                         cell_text[:start]
    #                         + "<b>" + cell_text[start:end] + "</b>"
    #                         + cell_text[end:]
    #                     )
    #                     item.setData(Qt.DisplayRole, highlighted)
    #                     item.setData(Qt.TextFormat, Qt.RichText)
    #                 else:
    #                     item.setData(Qt.DisplayRole, cell_text)
    #                     item.setData(Qt.TextFormat, Qt.PlainText)
    #         self.table.setRowHidden(row, not match)

            



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



        

