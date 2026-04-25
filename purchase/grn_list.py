from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QDateEdit, QFrame, QTableWidget, QTableWidgetItem, QSizePolicy, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtSql import QSqlQuery

from medic.utilities.stylus import load_stylesheets
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.table_helpers import centered_cell_widget, style_table_action_button


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


class GRNListWidget(QWidget):
    add_grn_signal = Signal()
    detail_grn_signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        header_layout = QHBoxLayout()
        heading = QLabel("Goods Receipt Notes", objectName="SectionTitle")
        self.add_grn_btn = QPushButton("Create GRN", objectName="TopRightButton")
        self.add_grn_btn.setCursor(Qt.PointingHandCursor)
        self.add_grn_btn.clicked.connect(self.add_grn_signal.emit)
        self.health_check_btn = QPushButton("PO/GRN Health Check", objectName="TopRightButton")
        self.health_check_btn.setCursor(Qt.PointingHandCursor)
        self.health_check_btn.clicked.connect(self.run_health_check)
        self.health_check_btn.setVisible(Permissions.has_permission("grn.audit"))
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.health_check_btn)
        header_layout.addWidget(self.add_grn_btn)
        self.layout.addLayout(header_layout)

        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        self.layout.addWidget(line)

        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(10)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search GRN number / PO number / supplier...")
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.load_grn_list)
        self.search_edit.textChanged.connect(lambda: self.search_timer.start(400))

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-90))

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())

        get_btn = QPushButton("Get Data", objectName="TopRightButton")
        get_btn.setCursor(Qt.PointingHandCursor)
        get_btn.clicked.connect(self.load_grn_list)

        filter_layout.addWidget(self.search_edit, 3)
        filter_layout.addWidget(QLabel("From"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("To"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(get_btn)

        self.layout.addLayout(filter_layout)

        self.table = MyTable(column_ratios=[0.06, 0.15, 0.15, 0.23, 0.12, 0.11, 0.10, 0.08])
        headers = ["ID", "GRN", "PO", "Supplier", "GRN Date", "Status", "Total", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setMinimumWidth(700)
        self.table.setFixedHeight(400)
        self.layout.addWidget(self.table)
        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())

    def showEvent(self, event):
        super().showEvent(event)
        self.load_grn_list()

    def load_grn_list(self):
        query = QSqlQuery()
        search = (self.search_edit.text() or "").strip()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        sql = """
            SELECT
                gr.id,
                gr.grn_number,
                po.po_number,
                s.name,
                gr.grn_date,
                gr.status,
                gr.total_value
            FROM goods_receipt gr
            JOIN purchase_order po ON gr.po_id = po.id
            JOIN supplier s ON po.supplier = s.id
            WHERE gr.grn_date BETWEEN ? AND ?
        """

        params = [date_from, date_to]
        if search:
            sql += " AND (gr.grn_number LIKE ? OR po.po_number LIKE ? OR s.name LIKE ?)"
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard])

        sql += " ORDER BY gr.id DESC"

        query.prepare(sql)
        for param in params:
            query.addBindValue(param)

        if not query.exec():
            self.table.setRowCount(0)
            print("GRN list load failed:", query.lastError().text())
            return

        self.table.setRowCount(0)
        row = 0
        while query.next():
            self.table.insertRow(row)

            grn_id = int(query.value(0) or 0)
            self.table.setItem(row, 0, QTableWidgetItem(str(grn_id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(query.value(1) or "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(query.value(2) or "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(query.value(3) or "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(query.value(4) or "")))
            self.table.setItem(row, 5, QTableWidgetItem(str(query.value(5) or "")))
            self.table.setItem(row, 6, QTableWidgetItem(f"{float(query.value(6) or 0):.2f}"))

            detail_btn = style_table_action_button(QPushButton("Details"))
            detail_btn.setCursor(Qt.PointingHandCursor)
            detail_btn.clicked.connect(lambda _=False, gid=grn_id: self.detail_grn_signal.emit(gid))
            self.table.setCellWidget(row, 7, centered_cell_widget(detail_btn))

            row += 1

    def _count_from_query(self, sql):
        query = QSqlQuery()
        if not query.exec(sql) or not query.next():
            return None
        return int(query.value(0) or 0)

    def run_health_check(self):
        checks = []

        checks.append((
            "GRN without lines",
            self._count_from_query("""
                SELECT COUNT(*)
                FROM goods_receipt gr
                WHERE NOT EXISTS (
                    SELECT 1 FROM goods_receipt_line grl WHERE grl.grn_id = gr.id
                )
            """)
        ))

        checks.append((
            "Receipt lines with missing PO line",
            self._count_from_query("""
                SELECT COUNT(*)
                FROM goods_receipt_line grl
                LEFT JOIN purchase_order_line pol ON pol.id = grl.po_line_id
                WHERE pol.id IS NULL
            """)
        ))

        checks.append((
            "Billed GRNs missing purchase bill",
            self._count_from_query("""
                SELECT COUNT(*)
                FROM goods_receipt gr
                WHERE gr.status = 'billed'
                  AND NOT EXISTS (
                    SELECT 1 FROM purchase p WHERE p.sellerinvoice = gr.grn_number
                  )
            """)
        ))

        checks.append((
            "GRN without stock batches",
            self._count_from_query("""
                SELECT COUNT(*)
                FROM goods_receipt gr
                WHERE EXISTS (
                    SELECT 1 FROM goods_receipt_line grl WHERE grl.grn_id = gr.id
                )
                  AND NOT EXISTS (
                    SELECT 1
                    FROM batch b
                    LEFT JOIN purchaseitem pi ON pi.id = b.purchaseitem_id
                    LEFT JOIN purchase p ON p.id = pi.purchase
                    WHERE b.source = ('GRN:' || gr.grn_number)
                       OR p.sellerinvoice = gr.grn_number
                  )
            """)
        ))

        checks.append((
            "PO status inconsistent with received quantity",
            self._count_from_query("""
                WITH po_totals AS (
                    SELECT
                        po.id,
                        po.status,
                        COALESCE((SELECT SUM(qty_ordered) FROM purchase_order_line WHERE po_id = po.id), 0) AS ordered_qty,
                        COALESCE((
                            SELECT SUM(grl.qty_received)
                            FROM goods_receipt_line grl
                            JOIN goods_receipt gr ON gr.id = grl.grn_id
                            JOIN purchase_order_line pol ON pol.id = grl.po_line_id
                            WHERE gr.po_id = po.id
                        ), 0) AS received_qty
                    FROM purchase_order po
                    WHERE po.status != 'closed'
                )
                SELECT COUNT(*)
                FROM po_totals
                WHERE (
                    received_qty <= 0 AND status NOT IN ('draft', 'sent')
                ) OR (
                    received_qty > 0 AND received_qty < ordered_qty AND status != 'partial_received'
                ) OR (
                    received_qty >= ordered_qty AND ordered_qty > 0 AND status != 'received'
                )
            """)
        ))

        checks.append((
            "GRN total not matching receipt + header adjustments",
            self._count_from_query("""
                SELECT COUNT(*)
                FROM goods_receipt gr
                LEFT JOIN (
                    SELECT
                        grn_id,
                        ROUND(SUM(COALESCE(total_received, 0) - COALESCE(discount, 0) + COALESCE(tax, 0)), 2) AS lines_total
                    FROM goods_receipt_line
                    GROUP BY grn_id
                ) x ON x.grn_id = gr.id
                WHERE ABS(
                    COALESCE(gr.total_value, 0) - (
                        COALESCE(x.lines_total, 0)
                        - COALESCE(gr.header_discount, 0)
                        + COALESCE(gr.tax_236g, 0)
                        + COALESCE(gr.tax_236h, 0)
                        + COALESCE(gr.salestax, 0)
                        - COALESCE(gr.cn_adjustment, 0)
                    )
                ) > 0.01
            """)
        ))

        lines = []
        total_issues = 0
        for label, count in checks:
            if count is None:
                lines.append(f"- {label}: error while checking")
                total_issues += 1
                continue
            lines.append(f"- {label}: {count}")
            total_issues += count

        report = "\n".join(lines)
        if total_issues == 0:
            AppMessageBox.information(
                self,
                "PO/GRN Health Check",
                "No inconsistencies found.\n\n" + report,
            )
        else:
            AppMessageBox.warning(
                self,
                "PO/GRN Health Check",
                f"Detected {total_issues} issue(s).\n\n" + report,
            )
