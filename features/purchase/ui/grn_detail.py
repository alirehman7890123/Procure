from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Signal, Qt

from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from medic.features.purchase.services.grn_transaction_service import fetch_grn_detail, fetch_grn_line_rows


class MyTable(QTableWidget):
    def __init__(self, column_ratios=None, parent=None):
        super().__init__(parent)
        self.column_ratios = column_ratios or []
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        if total <= 0:
            return
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            self.setColumnWidth(i, int(width * (ratio / total)))


class GRNDetailWidget(QWidget):
    grn_list_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_grn_id = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header = QHBoxLayout()
        heading = QLabel("Goods Receipt Detail", objectName="SectionTitle")
        self.back_btn = QPushButton("Back", objectName="TopRightButton")
        self.back_btn.clicked.connect(self.grn_list_signal.emit)
        header.addWidget(heading)
        header.addStretch()
        header.addWidget(self.back_btn)
        self.layout.addLayout(header)

        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        self.layout.addWidget(line)

        # Header summary block
        self.summary_frame = QFrame()
        self.summary_frame.setObjectName("sectionCard")
        self.summary_layout = QGridLayout(self.summary_frame)
        self.summary_layout.setContentsMargins(10, 10, 10, 10)
        self.summary_layout.setHorizontalSpacing(18)
        self.summary_layout.setVerticalSpacing(8)

        self.grn_number_value = QLabel("-")
        self.grn_date_value = QLabel("-")
        self.po_number_value = QLabel("-")
        self.supplier_value = QLabel("-")
        self.status_value = QLabel("-")
        self.session_value = QLabel("-")

        self.subtotal_value = QLabel("0.00")
        self.discount_value = QLabel("0.00")
        self.taxable_value = QLabel("0.00")
        self.tax_236g_value = QLabel("0.00")
        self.tax_236h_value = QLabel("0.00")
        self.sales_tax_value = QLabel("0.00")

        self.header_tax_value = QLabel("0.00")
        self.net_amount_value = QLabel("0.00")
        self.cn_adjust_value = QLabel("0.00")
        self.total_value = QLabel("0.00")
        self.bill_id_value = QLabel("-")

        row_1 = [
            ("GRN Number", self.grn_number_value),
            ("GRN Date", self.grn_date_value),
            ("PO Number", self.po_number_value),
            ("Supplier", self.supplier_value),
            ("Status", self.status_value),
            ("Session", self.session_value),
        ]
        row_2 = [
            ("Subtotal", self.subtotal_value),
            ("Discount", self.discount_value),
            ("Taxable", self.taxable_value),
            ("Tax 236(G)", self.tax_236g_value),
            ("Tax 236(H)", self.tax_236h_value),
            ("Sales Tax", self.sales_tax_value),
        ]
        row_3 = [
            ("Header Tax", self.header_tax_value),
            ("Net Amount", self.net_amount_value),
            ("CN Adjust", self.cn_adjust_value),
            ("Total Value", self.total_value),
            ("Bill ID", self.bill_id_value),
        ]

        def add_summary_row(row_index, pairs):
            col = 0
            for label_text, value_widget in pairs:
                label = QLabel(f"{label_text}:")
                label.setStyleSheet("font-weight: 600; padding-left: 0;")
                value_widget.setStyleSheet("padding-left: 0;")
                if label_text in ("Total Value", "Net Amount"):
                    label.setStyleSheet("font-weight: 600; color: #2F5D7C; padding-left: 0;")
                    value_widget.setStyleSheet("font-weight: 600; color: #2F5D7C; padding-left: 0;")

                self.summary_layout.addWidget(label, row_index, col)
                self.summary_layout.addWidget(value_widget, row_index, col + 1)
                col += 2

        add_summary_row(0, row_1)
        add_summary_row(1, row_2)
        add_summary_row(2, row_3)

        for stretch_col in (1, 3, 5, 7, 9, 11):
            self.summary_layout.setColumnStretch(stretch_col, 1)

        self.layout.addWidget(self.summary_frame)

        notes_row = QHBoxLayout()
        notes_label = QLabel("Notes:")
        notes_label.setStyleSheet("font-weight: 600; padding-left: 0;")
        self.notes_value = QLabel("-")
        self.notes_value.setWordWrap(True)
        self.notes_value.setStyleSheet("padding-left: 0;")
        notes_row.addWidget(notes_label)
        notes_row.addWidget(self.notes_value, 1)
        self.layout.addLayout(notes_row)

        self.table = MyTable(column_ratios=[0.22, 0.12, 0.12, 0.08, 0.10, 0.08, 0.08, 0.10, 0.10])
        headers = ["Product", "Batch", "Expiry", "Qty", "Unit Price", "Discount", "Tax", "Line Total", "Landing Cost"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget::item { color: #333; border: none; }")
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.table.setMinimumWidth(700)
        self.table.setFixedHeight(360)
        self.layout.addWidget(self.table)

        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())

    def load_grn_data(self, grn_id):
        self.current_grn_id = int(grn_id)
        header = fetch_grn_detail(self.current_grn_id)
        if header is None:
            AppMessageBox.critical(self, "Error", "Could not load GRN details.")
            return

        self.grn_number_value.setText(str(header["grn_number"] or "-"))
        self.grn_date_value.setText(str(header["grn_date"] or "-"))
        self.po_number_value.setText(str(header["po_number"] or "-"))
        self.supplier_value.setText(str(header["supplier_name"] or "-"))
        self.status_value.setText(str(header["status"] or "-"))
        self.session_value.setText(str(header["session_id"] or "-"))

        self.subtotal_value.setText(f"{float(header['subtotal'] or 0):.2f}")
        self.discount_value.setText(f"{float(header['header_discount'] or 0):.2f}")
        self.taxable_value.setText(f"{float(header['taxable'] or 0):.2f}")
        self.tax_236g_value.setText(f"{float(header['tax_236g'] or 0):.2f}")
        self.tax_236h_value.setText(f"{float(header['tax_236h'] or 0):.2f}")
        self.sales_tax_value.setText(f"{float(header['sales_tax'] or 0):.2f}")
        self.header_tax_value.setText(f"{float(header['header_tax'] or 0):.2f}")
        self.net_amount_value.setText(f"{float(header['net_amount'] or 0):.2f}")
        self.cn_adjust_value.setText(f"{float(header['cn_adjustment'] or 0):.2f}")
        self.total_value.setText(f"{float(header['total_value'] or 0):.2f}")
        self.bill_id_value.setText(header["bill_id"] if header["bill_id"] else "-")
        self.notes_value.setText(header["notes"] if header["notes"] else "-")

        self.table.setRowCount(0)
        for row, row_data in enumerate(fetch_grn_line_rows(self.current_grn_id)):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(row_data["product_name"] or "")))
            self.table.setItem(row, 1, QTableWidgetItem(str(row_data["batch_no"] or "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(row_data["expiry_date"] or "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(int(row_data["qty_received"] or 0))))
            self.table.setItem(row, 4, QTableWidgetItem(f"{float(row_data['unit_price_received'] or 0):.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{float(row_data['discount'] or 0):.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{float(row_data['tax'] or 0):.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{float(row_data['total_received'] or 0):.2f}"))
            self.table.setItem(row, 8, QTableWidgetItem(f"{float(row_data['landing_cost'] or 0):.2f}"))
