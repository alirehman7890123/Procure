from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QGridLayout,
    QWidget,
)

from medic.services.sales_detail_service import (
    fetch_hold_sale_detail,
    fetch_hold_sale_item_rows,
)
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.stylus import load_stylesheets


class HoldSalesDetailWidget(QWidget):
    reload_order_signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)

        heading = QLabel("Sales Orders - On Hold", objectName="SectionTitle")
        self.holdinglist = QPushButton("Hold Sales", objectName="TopRightButton")
        self.holdinglist.setCursor(Qt.PointingHandCursor)

        grid_layout.addWidget(heading, 0, 0, 1, 7)
        grid_layout.addWidget(self.holdinglist, 0, 7, 1, 1)

        orderlabel = QLabel("Hold Sale Id")
        statuslabel = QLabel("Order Status")
        customerlabel = QLabel("Customer")
        salesman = QLabel("User")
        datelabel = QLabel("Date")

        grid_layout.addWidget(orderlabel, 1, 0)
        grid_layout.addWidget(statuslabel, 2, 0)
        grid_layout.addWidget(customerlabel, 3, 0)
        grid_layout.addWidget(salesman, 4, 0)
        grid_layout.addWidget(datelabel, 5, 0)

        self.orderid = QLabel()
        self.status = QLabel()
        self.customer = QLabel()
        self.salesman = QLabel()
        self.orderdate = QLabel()

        grid_layout.addWidget(self.orderid, 1, 1)
        grid_layout.addWidget(self.status, 2, 1)
        grid_layout.addWidget(self.customer, 3, 1)
        grid_layout.addWidget(self.salesman, 4, 1)
        grid_layout.addWidget(self.orderdate, 5, 1)

        layout.addWidget(grid_widget)

        self.supplier_table = MyTable()
        self.supplier_table.setColumnCount(8)
        self.supplier_table.setHorizontalHeaderLabels([
            "##", "Product", "Qty", "Rate", "Disc (%)", "Disc", "Tax %", "Total"
        ])
        self.supplier_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.supplier_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header = self.supplier_table.horizontalHeader()
        header.setStretchLastSection(False)
        self.supplier_table.setStyleSheet("QTableWidget::item { color: #333; }")
        self.supplier_table.verticalHeader().setFixedWidth(0)
        header.setFixedHeight(30)
        header.setStyleSheet(
            """
                background-color: #333;
                color: white;
                font-weight: 600;
            """
        )

        grid_layout.addWidget(self.supplier_table, 6, 0, 1, 8)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid_layout.addItem(spacer, 10, 0)

        self.reload_data_btn = QPushButton("Reload Sale Order")
        self.reload_data_btn.setObjectName("TopRightButton")
        self.reload_data_btn.setCursor(Qt.PointingHandCursor)
        grid_layout.addWidget(self.reload_data_btn, 8, 2, 1, 1)

        self.setLayout(layout)
        self.setStyleSheet(load_stylesheets())

    def load_holdsales_data(self, hold_id):
        try:
            self.hold_id = int(hold_id)
            header = fetch_hold_sale_detail(self.hold_id)
            if not header:
                AppMessageBox.warning(self, "Not Found", "Hold sale record not found.")
                return

            created_at = header.get("created_at") or "-"
            if isinstance(created_at, QDate):
                created_at = created_at.toString("dd-MM-yyyy")

            self.orderid.setText(str(self.hold_id))
            self.status.setText(str(header.get("status") or "hold"))
            self.customer.setText(str(header.get("customer_name") or "Walk-in Customer"))
            self.salesman.setText(str(header.get("user_name") or "-"))
            self.orderdate.setText(str(created_at))

            self.load_items_into_table(self.hold_id)
        except Exception as exc:
            AppMessageBox.critical(self, "Error", f"Error loading sales data: {exc}")

    def load_items_into_table(self, hold_id):
        try:
            rows = fetch_hold_sale_item_rows(hold_id)
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))
            return

        self.supplier_table.setRowCount(0)

        for row_index, row_data in enumerate(rows):
            self.supplier_table.insertRow(row_index)
            values = [
                str(row_index + 1),
                str(row_data.get("product_name") or "-"),
                str(row_data.get("qty") or 0),
                str(row_data.get("unitrate") or 0),
                str(row_data.get("discount_percent") or 0),
                str(row_data.get("discount_amount") or 0),
                str(row_data.get("tax_percent") or 0),
                str(row_data.get("total") or 0),
            ]
            for column, value in enumerate(values):
                self.supplier_table.setItem(row_index, column, QTableWidgetItem(value))

        try:
            self.reload_data_btn.clicked.disconnect()
        except Exception:
            pass
        self.reload_data_btn.clicked.connect(lambda: self.reload_order_signal.emit(hold_id))


class MyTable(QTableWidget):
    pass
