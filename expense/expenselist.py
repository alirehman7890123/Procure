        
from PySide6.QtWidgets import QWidget, QComboBox, QHBoxLayout, QFrame, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal, QDate, QDateTime
from PySide6.QtSql import QSqlQuery
from functools import partial
from utilities.stylus import load_stylesheets
from utilities.table_helpers import centered_cell_widget, style_table_action_button




class ExpenseListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Expense Information", objectName="SectionTitle")
        self.addexpense = QPushButton("Add Expense", objectName="TopRightButton")
        self.addexpense.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.addexpense)

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

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10])
        headers = ["No.", "Category", "Title", "Amount", "Date", "Detail"]
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
        self.load_expenses_into_table()
        



    def load_expenses_into_table(self):
        query = QSqlQuery()
        query.prepare("""
            SELECT id, category, title, amount, creation_date
            FROM expense
            ORDER BY id DESC
        """)

        if not query.exec():
            print("Error loading expenses:", query.lastError().text())
            return

        self.table.setRowCount(0)

        row = 0

        while query.next():
            self.table.insertRow(row)

            exp_id = int(query.value(0))
            category_val = str(query.value(1) or "")
            title_val = str(query.value(2) or "")
            amount_val = query.value(3)
            creation_date_val = query.value(4)

            # format amount safely
            try:
                amount_text = f"{float(amount_val):.2f}"
            except (TypeError, ValueError):
                amount_text = "0.00"

            # format date safely
            if isinstance(creation_date_val, QDateTime):
                creation_date_text = creation_date_val.toString("dd-MM-yyyy")
            elif isinstance(creation_date_val, QDate):
                creation_date_text = creation_date_val.toString("dd-MM-yyyy")
            else:
                creation_date_text = str(creation_date_val or "")

            row_no_item = QTableWidgetItem(str(row + 1))
            category_item = QTableWidgetItem(category_val)
            title_item = QTableWidgetItem(title_val)
            amount_item = QTableWidgetItem(amount_text)
            creation_date_item = QTableWidgetItem(creation_date_text)

            self.table.setItem(row, 0, row_no_item)
            self.table.setItem(row, 1, category_item)
            self.table.setItem(row, 2, title_item)
            self.table.setItem(row, 3, amount_item)
            self.table.setItem(row, 4, creation_date_item)

            detail = style_table_action_button(QPushButton("Details"))
            detail.setCursor(Qt.PointingHandCursor)
            detail.clicked.connect(partial(self.detailpagesignal.emit, exp_id))
            self.table.setCellWidget(row, 5, centered_cell_widget(detail))

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




            
        
