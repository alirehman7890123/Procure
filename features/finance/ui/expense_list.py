from functools import partial

from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt, Signal

from medic.utilities.stylus import load_stylesheets
from medic.utilities.table_helpers import centered_cell_widget, style_table_action_button
from features.finance.services.expense_service import fetch_expense_list_rows


class ExpenseListWidget(QWidget):
    detailpagesignal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

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
        line.setStyleSheet(
            """
                QFrame#lineSeparator {
                    border: none;
                    border-top: 2px solid #333;
                }
            """
        )
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
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumWidth(700)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def showEvent(self, event):
        super().showEvent(event)
        self.load_expenses_into_table()

    def load_expenses_into_table(self):
        try:
            rows = fetch_expense_list_rows()
        except Exception:
            self.table.setRowCount(0)
            return

        self.table.setRowCount(0)
        row = 0
        for row_data in rows:
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(str(row_data.get("category", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(row_data.get("title", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(row_data.get("amount_text", "0.00"))))
            self.table.setItem(row, 4, QTableWidgetItem(str(row_data.get("creation_date_text", ""))))

            detail = style_table_action_button(QPushButton("Details"))
            detail.setCursor(Qt.PointingHandCursor)
            detail.clicked.connect(partial(self.detailpagesignal.emit, int(row_data.get("id", 0) or 0)))
            self.table.setCellWidget(row, 5, centered_cell_widget(detail))
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
