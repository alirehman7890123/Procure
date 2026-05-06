from PySide6.QtWidgets import QWidget, QLineEdit,QFrame, QVBoxLayout, QDialog, QHBoxLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from functools import partial

from medic.utilities.stylus import load_stylesheets
from medic.utilities.table_helpers import centered_cell_widget, style_table_action_button
from medic.utilities.app_messagebox import AppMessageBox
from medic.services.supplier_service import fetch_supplier_list_rows



class SupplierListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)
        
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Supplier Information", objectName="SectionTitle")
        self.addsupplier = QPushButton("Add Supplier", objectName="TopRightButton")
        self.addsupplier.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.addsupplier)

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
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search Supplier...")
        search_edit.textChanged.connect(self.search_rows)
        search_layout.addWidget(search_edit)
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)





        # table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        # table.setColumnCount(7)
        # table.setHorizontalHeaderLabels(["No.", "Name", "Contact", "Email", "Website", "Status", "Detail"])
        # table.verticalHeader().setVisible(False)
        # table.setAlternatingRowColors(True)
        # table.setStyleSheet("""
        #     QTableWidget {
        #         background: white;
        #         alternate-background-color: #f9f9f9;
        #         border: 1px solid #ddd;
        #         gridline-color: #ddd;
        #     }
        #     QHeaderView::section {
        #         background-color: #34495e;
        #         color: white;
        #         font-weight: bold;
        #         border: none;
        #         padding: 6px;
        #     }
        # """)
        # header = table.horizontalHeader()
        # self.layout.addWidget(table)


        self.row_height = 35

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        headers = ["No.", "Name", "Contact", "Email", "Website", "Status", "Detail"]
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
        self.load_suppliers_into_table()
        



    def load_suppliers_into_table(self):
        try:
            rows = fetch_supplier_list_rows()
        except Exception as exc:
            AppMessageBox.critical(self, "Supplier List", str(exc))
            return

        self.table.setRowCount(0)

        for row_index, supplier in enumerate(rows):
            self.table.insertRow(row_index)

            values = [
                QTableWidgetItem(str(row_index + 1)),
                QTableWidgetItem(supplier["name"]),
                QTableWidgetItem(supplier["contact"]),
                QTableWidgetItem(supplier["email"]),
                QTableWidgetItem(supplier["website"]),
                QTableWidgetItem(supplier["status"]),
            ]

            for col_index, item in enumerate(values):
                self.table.setItem(row_index, col_index, item)

            detail = style_table_action_button(QPushButton('Details'))
            detail.setCursor(Qt.PointingHandCursor)
            self.table.setCellWidget(row_index, 6, centered_cell_widget(detail))
            detail.clicked.connect(partial(self.detailpagesignal.emit, supplier["id"]))
        


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


    
