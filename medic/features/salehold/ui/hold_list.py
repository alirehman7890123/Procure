from functools import partial

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QGridLayout,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from medic.services.sales_detail_service import fetch_hold_sale_list_rows
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.stylus import load_stylesheets


class SaleHoldListWidget(QWidget):
    holddetailsignal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)

        heading = QLabel("On-Hold Sales Order", objectName="SectionTitle")
        grid_layout.addWidget(heading, 0, 0)
        layout.addWidget(grid_widget)

        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(6)
        self.supplier_table.setHorizontalHeaderLabels([
            "#", "Customer", "User", "Status", "Date", "Details"
        ])
        self.supplier_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.supplier_table.horizontalHeader().setSectionResizeMode(self.supplier_table.horizontalHeader().Stretch)
        self.supplier_table.setStyleSheet("QTableWidget::item { color: #333; }")
        self.supplier_table.verticalHeader().setFixedWidth(0)
        header = self.supplier_table.horizontalHeader()
        header.setFixedHeight(30)
        header.setStyleSheet(
            """
                background-color: #333;
                color: white;
                font-weight: 600;
            """
        )

        layout.addWidget(self.supplier_table)
        self.setLayout(layout)
        self.setStyleSheet(load_stylesheets())

    def showEvent(self, event):
        super().showEvent(event)
        self.load_sales_into_table()

    def load_sales_into_table(self):
        try:
            rows = fetch_hold_sale_list_rows()
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))
            return

        self.supplier_table.setRowCount(0)

        for row_index, record in enumerate(rows):
            self.supplier_table.insertRow(row_index)

            created_at = record.get("created_at") or "-"
            if isinstance(created_at, QDate):
                created_at = created_at.toString("dd-MM-yyyy")

            items = [
                QTableWidgetItem(str(record["id"])),
                QTableWidgetItem(str(record.get("customer") or "Walk-in Customer")),
                QTableWidgetItem(str(record.get("user") or "-")),
                QTableWidgetItem(str(record.get("status") or "hold")),
                QTableWidgetItem(str(created_at)),
            ]

            for column, item in enumerate(items):
                self.supplier_table.setItem(row_index, column, item)

            detail = QPushButton("Details")
            detail.setObjectName("EntryButton")
            detail.setCursor(Qt.PointingHandCursor)
            detail.clicked.connect(partial(self.holddetailsignal.emit, int(record["id"])))
            self.supplier_table.setCellWidget(row_index, 5, detail)
