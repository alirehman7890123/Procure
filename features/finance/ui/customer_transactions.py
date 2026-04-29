from functools import partial

from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame, QLabel, QPushButton, QHeaderView, QSizePolicy, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt, Signal

from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from features.finance.services.party_transaction_service import fetch_customer_balance_rows, reconcile_customer_internal_balance


class CustomerTransactionWidget(QWidget):
    transaction_page_signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Customer Transaction List", objectName="SectionTitle")
        self.transactionpage = QPushButton("Main Transactions Page", objectName="TopRightButton")
        self.transactionpage.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.transactionpage)
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

        self.row_height = 35
        self.table = MyTable(column_ratios=[0.05, 0.22, 0.14, 0.18, 0.12, 0.12, 0.09, 0.08])
        headers = ["#", "Name", "Contact", "Email", "Payable", "Receiveable", "Pay / Receive", "Reconcile"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        detail_col = headers.index("Pay / Receive")
        reconcile_col = headers.index("Reconcile")
        self.table.horizontalHeaderItem(detail_col).setTextAlignment(Qt.AlignCenter)
        self.table.horizontalHeaderItem(reconcile_col).setTextAlignment(Qt.AlignCenter)
        self.table.setStyleSheet("QTableWidget::item { color: #333; }")
        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        self.table.setMinimumWidth(700)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self.layout.addWidget(self.table)
        self.layout.addStretch()
        self.setStyleSheet(load_stylesheets())

    def showEvent(self, event):
        super().showEvent(event)
        self.load_customers_into_table()

    def load_customers_into_table(self):
        try:
            rows = fetch_customer_balance_rows()
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))
            return

        self.table.setRowCount(0)
        row = 0
        for row_data in rows:
            self.table.insertRow(row)

            customer_id = int(row_data["party_id"] or 0)
            name_text = str(row_data["name"] or "")
            contact_text = str(row_data["contact"] or "")
            email_text = str(row_data["email"] or "")
            payable_text = str(row_data["payable"] or 0)
            receiveable_text = str(row_data["receiveable"] or 0)

            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(name_text))
            self.table.setItem(row, 2, QTableWidgetItem(contact_text))
            self.table.setItem(row, 3, QTableWidgetItem(email_text))
            self.table.setItem(row, 4, QTableWidgetItem(payable_text))
            self.table.setItem(row, 5, QTableWidgetItem(receiveable_text))

            payable_amount = float(row_data["payable"] or 0.0)
            receiveable_amount = float(row_data["receiveable"] or 0.0)

            pay = QPushButton("Pay / Receive")
            pay.setStyleSheet(
                """
                    background-color: #333;
                    color: #fff;
                    font-weight: 600;
            """
            )
            self.table.setCellWidget(row, 6, pay)
            pay.clicked.connect(partial(self.transaction_page_signal.emit, customer_id))

            reconcile = QPushButton("Reconcile")
            reconcile.setStyleSheet(
                """
                    background-color: #2F5D7C;
                    color: #fff;
                    font-weight: 600;
            """
            )
            can_reconcile = payable_amount > 0 and receiveable_amount > 0
            reconcile.setEnabled(can_reconcile)
            if can_reconcile:
                reconcile.clicked.connect(partial(self.reconcile_customer_balance, customer_id, name_text))
            self.table.setCellWidget(row, 7, reconcile)

            row += 1

    @Permissions.require_permission("transactions.create")
    def reconcile_customer_balance(self, customer_id, customer_name):
        try:
            balance_rows = fetch_customer_balance_rows()
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))
            return

        row = next((item for item in balance_rows if int(item["party_id"] or 0) == int(customer_id)), None)
        if row is None:
            AppMessageBox.warning(self, "Not Found", "Customer could not be loaded for reconciliation.")
            return

        payable_before = float(row["payable"] or 0.0)
        receiveable_before = float(row["receiveable"] or 0.0)
        reconcile_amount = min(payable_before, receiveable_before)
        if reconcile_amount <= 0:
            AppMessageBox.information(self, "Nothing to Reconcile", "This customer has no balances to reconcile.")
            return

        _, accepted = AppMessageBox.confirm(
            self,
            "Internal Reconciliation",
            (
                f"{customer_name} has payable {payable_before:.2f} and receivable {receiveable_before:.2f}.\n"
                f"Reconcile {reconcile_amount:.2f} internally?"
            ),
            confirm_label="Reconcile",
            cancel_label="Cancel",
            kind="warning",
        )

        if not accepted:
            return
        try:
            result = reconcile_customer_internal_balance(customer_id)
            AppMessageBox.success(self, "Reconciled", f"{result['reconcile_amount']:.2f} reconciled for {customer_name}.")
            self.load_customers_into_table()
        except LookupError as exc:
            AppMessageBox.warning(self, "Not Found", str(exc))
        except ValueError as exc:
            AppMessageBox.information(self, "Nothing to Reconcile", str(exc))
        except RuntimeError as exc:
            AppMessageBox.warning(self, "Session Required", str(exc))
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))


class MyTable(QTableWidget):
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            self.setColumnWidth(i, int(width * (ratio / total)))
