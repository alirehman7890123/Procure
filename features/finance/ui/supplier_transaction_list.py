from functools import partial

from PySide6.QtWidgets import QWidget, QFrame, QLineEdit, QHBoxLayout, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt, Signal

from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from features.finance.services.party_transaction_service import fetch_supplier_transaction_list_rows


class SupplierTransactionListWidget(QWidget):
    transaction_detail_signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("All Transactions", objectName="SectionTitle")
        self.transaction_list = QPushButton("All Supplier Transactions", objectName="TopRightButton")
        self.transaction_list.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.transaction_list)
        self.layout.addLayout(header_layout)

        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(
            """
                QFrame#lineSeparator {
                    border: none;
                    border-top: 2px solid #333;
                }
            """
        )
        self.layout.addWidget(line)
        self.layout.addSpacing(10)

        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search Supplier...")
        search_edit.textChanged.connect(self.search_rows)
        search_layout.addWidget(search_edit)
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)

        self.row_height = 35
        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.20, 0.15, 0.10, 0.10])
        headers = ["#", "Supplier", "Type", "Paid", "Received", "Date", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        detail_col = headers.index("Detail")
        self.table.horizontalHeaderItem(detail_col).setTextAlignment(Qt.AlignCenter)
        self.table.setStyleSheet("QTableWidget::item { color: #333; }")
        self.table.verticalHeader().setFixedWidth(0)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumWidth(700)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

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
        self.load_supplier_transactions()

    def load_supplier_transactions(self):
        try:
            rows = fetch_supplier_transaction_list_rows()
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))
            return

        self.table.setRowCount(0)
        row = 0
        for row_data in rows:
            self.table.insertRow(row)
            transaction_id = int(row_data["transaction_id"] or 0)
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(str(row_data["supplier_name"] or "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(row_data["transaction_type"] or "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(row_data["paid"] or "0")))
            self.table.setItem(row, 4, QTableWidgetItem(str(row_data["received"] or "0")))
            self.table.setItem(row, 5, QTableWidgetItem(str(row_data["creation_date"] or "")))

            detail = QPushButton("Details")
            detail.setStyleSheet(
                """
                    background-color: #333;
                    color: #fff;
                    font-weight: 600;
            """
            )
            detail.setCursor(Qt.PointingHandCursor)
            self.table.setCellWidget(row, 6, detail)
            detail.clicked.connect(partial(self.transaction_detail_signal.emit, transaction_id))
            row += 1


class MyTable(QTableWidget):
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            self.setColumnWidth(i, int(width * (ratio / total)))
