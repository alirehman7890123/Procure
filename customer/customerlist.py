from PySide6.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from functools import partial
from medic.utilities.stylus import load_stylesheets
from medic.utilities.table_helpers import centered_cell_widget, style_table_action_button
from medic.utilities.app_messagebox import AppMessageBox
from services.customer_service import fetch_customer_list_rows





class CustomerListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Customer Information", objectName="SectionTitle")
        self.addcustomer = QPushButton("Add Customer", objectName="TopRightButton")
        self.addcustomer.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
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
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search Customer...")
        search_edit.textChanged.connect(self.search_rows)
        search_layout.addWidget(search_edit)
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)
        
        self.row_height = 35

        self.table = MyTable(column_ratios=[0.05, 0.18, 0.10, 0.18, 0.11, 0.10, 0.10, 0.10, 0.08])
        headers = ["No.", "Name", "Contact", "Email", "Status", "Payable", "Receiveable", "Credit Limit", "Detail"]
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
        self.load_customers_into_table()
        



    def load_customers_into_table(self):
        try:
            rows = fetch_customer_list_rows()
        except Exception as exc:
            AppMessageBox.critical(self, "Customer List", str(exc))
            return

        self.table.setRowCount(0)

        for row_index, customer in enumerate(rows):
            self.table.insertRow(row_index)

            values = [
                QTableWidgetItem(str(row_index + 1)),
                QTableWidgetItem(customer["name"]),
                QTableWidgetItem(customer["contact"]),
                QTableWidgetItem(customer["email"]),
                QTableWidgetItem(customer["status"]),
                QTableWidgetItem(f"{customer['payable']:.2f}"),
                QTableWidgetItem(f"{customer['receiveable']:.2f}"),
                QTableWidgetItem(f"{customer['credit_limit']:.2f}"),
            ]

            for col_index, item in enumerate(values):
                self.table.setItem(row_index, col_index, item)

            detail = style_table_action_button(QPushButton('Details'))
            self.table.setCellWidget(row_index, 8, centered_cell_widget(detail))
            detail.clicked.connect(partial(self.detailpagesignal.emit, customer["id"]))
        

    
    
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



        
