from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtSql import QSqlQuery

from utilities.stylus import load_stylesheets
from utilities.app_messagebox import AppMessageBox


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

        header_q = QSqlQuery()
        header_q.prepare("""
            SELECT
                gr.grn_number,
                gr.grn_date,
                gr.status,
                gr.total_value,
                po.po_number,
                s.name,
                COALESCE(gr.session_id, ''),
                COALESCE(gr.header_discount, 0),
                COALESCE((
                    SELECT SUM(COALESCE(grl.total_received, 0))
                    FROM goods_receipt_line grl
                    WHERE grl.grn_id = gr.id
                ), 0),
                COALESCE(gr.taxable, 0),
                COALESCE(gr.tax_236g, 0),
                COALESCE(gr.tax_236h, 0),
                COALESCE(gr.salestax, 0),
                COALESCE(gr.header_tax, 0),
                COALESCE(gr.netamount, 0),
                COALESCE(gr.cn_adjustment, 0),
                COALESCE(gr.notes, ''),
                COALESCE((SELECT MAX(p.id) FROM purchase p WHERE p.sellerinvoice = gr.grn_number), '') AS bill_id
            FROM goods_receipt gr
            JOIN purchase_order po ON gr.po_id = po.id
            JOIN supplier s ON po.supplier = s.id
            WHERE gr.id = ?
        """)
        header_q.addBindValue(self.current_grn_id)

        if not header_q.exec() or not header_q.next():
            AppMessageBox.critical(self, "Error", "Could not load GRN details.")
            return

        self.grn_number_value.setText(str(header_q.value(0) or "-"))
        self.grn_date_value.setText(str(header_q.value(1) or "-"))
        self.po_number_value.setText(str(header_q.value(4) or "-"))
        self.supplier_value.setText(str(header_q.value(5) or "-"))
        self.status_value.setText(str(header_q.value(2) or "-"))
        self.session_value.setText(str(header_q.value(6) or "-"))

        header_discount = float(header_q.value(7) or 0)
        subtotal = float(header_q.value(8) or 0)
        taxable = float(header_q.value(9) or 0)
        tax_236g = float(header_q.value(10) or 0)
        tax_236h = float(header_q.value(11) or 0)
        sales_tax = float(header_q.value(12) or 0)
        header_tax = float(header_q.value(13) or 0)
        net_amount = float(header_q.value(14) or 0)
        cn_adjustment = float(header_q.value(15) or 0)
        notes = str(header_q.value(16) or "-")
        bill_id = str(header_q.value(17) or "")
        total_value = float(header_q.value(3) or 0)

        self.subtotal_value.setText(f"{subtotal:.2f}")
        self.discount_value.setText(f"{header_discount:.2f}")
        self.taxable_value.setText(f"{taxable:.2f}")
        self.tax_236g_value.setText(f"{tax_236g:.2f}")
        self.tax_236h_value.setText(f"{tax_236h:.2f}")
        self.sales_tax_value.setText(f"{sales_tax:.2f}")
        self.header_tax_value.setText(f"{header_tax:.2f}")
        self.net_amount_value.setText(f"{net_amount:.2f}")
        self.cn_adjust_value.setText(f"{cn_adjustment:.2f}")
        self.total_value.setText(f"{total_value:.2f}")
        self.bill_id_value.setText(bill_id if bill_id else "-")
        self.notes_value.setText(notes if notes else "-")

        lines_q = QSqlQuery()
        lines_q.prepare("""
            SELECT
                p.display_name,
                COALESCE(grl.batch_no, ''),
                COALESCE(grl.expiry_date, ''),
                COALESCE(grl.qty_received, 0),
                COALESCE(grl.unit_price_received, 0),
                COALESCE(grl.discount, 0),
                COALESCE(grl.tax, 0),
                COALESCE(grl.total_received, 0),
                COALESCE(grl.landing_cost, 0)
            FROM goods_receipt_line grl
            JOIN purchase_order_line pol ON grl.po_line_id = pol.id
            JOIN product p ON pol.product = p.id
            WHERE grl.grn_id = ?
            ORDER BY grl.id ASC
        """)
        lines_q.addBindValue(self.current_grn_id)

        if not lines_q.exec():
            self.table.setRowCount(0)
            return

        self.table.setRowCount(0)
        row = 0
        while lines_q.next():
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(lines_q.value(0) or "")))
            self.table.setItem(row, 1, QTableWidgetItem(str(lines_q.value(1) or "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(lines_q.value(2) or "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(int(float(lines_q.value(3) or 0)))))
            self.table.setItem(row, 4, QTableWidgetItem(f"{float(lines_q.value(4) or 0):.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{float(lines_q.value(5) or 0):.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{float(lines_q.value(6) or 0):.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(f"{float(lines_q.value(7) or 0):.2f}"))
            self.table.setItem(row, 8, QTableWidgetItem(f"{float(lines_q.value(8) or 0):.2f}"))
            row += 1
