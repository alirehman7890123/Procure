from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QMessageBox, QStatusBar, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtSql import QSqlQuery
from utilities.activity_logger import log_activity
from utilities.permissions import Permissions
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


class PODetailWidget(QWidget):
    """Purchase Order Detail View"""
    
    po_list_signal = Signal()
    grn_detail_signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.current_po_id = None

        # === Header ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Order Details", objectName="SectionTitle")
        self.back_btn = QPushButton("Back to List", objectName="TopRightButton")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.on_back_clicked)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.back_btn)

        self.layout.addLayout(header_layout)

        # === Separator ===
        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        self.layout.addWidget(line)
        self.layout.addSpacing(10)

        # === PO Summary ===
        summary_frame = QFrame()
        summary_frame.setObjectName("sectionCard")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        summary_layout.setSpacing(10)

        # Ordered 3-column summary grid
        summary_grid = QGridLayout()
        summary_grid.setContentsMargins(0, 0, 0, 0)
        summary_grid.setHorizontalSpacing(24)
        summary_grid.setVerticalSpacing(10)

        po_num_label = QLabel("PO Number:")
        po_num_label.setStyleSheet("font-weight: 600; padding-left: 0;")
        self.po_number_display = QLabel("-")
        self.po_number_display.setStyleSheet("padding-left: 0;")

        supplier_label = QLabel("Supplier:")
        supplier_label.setStyleSheet("font-weight: 600; padding-left: 0;")
        self.supplier_display = QLabel("-")
        self.supplier_display.setStyleSheet("padding-left: 0;")

        po_date_label = QLabel("PO Date:")
        po_date_label.setStyleSheet("font-weight: 600; padding-left: 0;")
        self.po_date_display = QLabel("-")
        self.po_date_display.setStyleSheet("padding-left: 0;")

        delivery_label = QLabel("Expected Delivery:")
        delivery_label.setStyleSheet("font-weight: 600; padding-left: 0;")
        self.delivery_display = QLabel("-")
        self.delivery_display.setStyleSheet("padding-left: 0;")

        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-weight: 600; padding-left: 0;")
        self.status_display = QLabel("-")
        self.status_display.setStyleSheet("padding-left: 0;")

        total_label = QLabel("Total Value:")
        total_label.setStyleSheet("font-weight: 600; color: #2F5D7C; padding-left: 0;")
        self.total_display = QLabel("0.00")
        self.total_display.setStyleSheet("font-weight: 600; color: #2F5D7C; padding-left: 0;")

        received_total_label = QLabel("Received Qty:")
        received_total_label.setStyleSheet("font-weight: 600; padding-left: 0;")
        self.received_total_display = QLabel("0.00")
        self.received_total_display.setStyleSheet("padding-left: 0;")

        remaining_total_label = QLabel("Remaining Qty:")
        remaining_total_label.setStyleSheet("font-weight: 600; padding-left: 0;")
        self.remaining_total_display = QLabel("0.00")
        self.remaining_total_display.setStyleSheet("padding-left: 0;")

        summary_grid.addWidget(po_num_label, 0, 0)
        summary_grid.addWidget(self.po_number_display, 0, 1)
        summary_grid.addWidget(supplier_label, 0, 2)
        summary_grid.addWidget(self.supplier_display, 0, 3)
        summary_grid.addWidget(po_date_label, 0, 4)
        summary_grid.addWidget(self.po_date_display, 0, 5)

        summary_grid.addWidget(delivery_label, 1, 0)
        summary_grid.addWidget(self.delivery_display, 1, 1)
        summary_grid.addWidget(status_label, 1, 2)
        summary_grid.addWidget(self.status_display, 1, 3)
        summary_grid.addWidget(total_label, 1, 4)
        summary_grid.addWidget(self.total_display, 1, 5)
        summary_grid.addWidget(received_total_label, 2, 0)
        summary_grid.addWidget(self.received_total_display, 2, 1)
        summary_grid.addWidget(remaining_total_label, 2, 2)
        summary_grid.addWidget(self.remaining_total_display, 2, 3)

        summary_grid.setColumnStretch(1, 1)
        summary_grid.setColumnStretch(3, 1)
        summary_grid.setColumnStretch(5, 1)

        summary_layout.addLayout(summary_grid)

        self.layout.addWidget(summary_frame)

        # === Line Items ===
        items_label = QLabel("Ordered Items", objectName="SectionTitle")
        self.layout.addWidget(items_label)

        self.items_table = MyTable(column_ratios=[0.32, 0.13, 0.13, 0.13, 0.14, 0.15])
        headers = ["Product", "Qty Ordered", "Qty Received", "Qty Remaining", "Unit Price", "Total Price"]
        self.items_table.setColumnCount(len(headers))
        self.items_table.setHorizontalHeaderLabels(headers)
        self.items_table.setMinimumHeight(200)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setAlternatingRowColors(True)

        self.layout.addWidget(self.items_table)

        grn_label = QLabel("Linked GRNs", objectName="SectionTitle")
        self.layout.addWidget(grn_label)

        self.grn_table = MyTable(column_ratios=[0.22, 0.20, 0.20, 0.20, 0.18])
        grn_headers = ["GRN", "Date", "Status", "Total", "Bill ID"]
        self.grn_table.setColumnCount(len(grn_headers))
        self.grn_table.setHorizontalHeaderLabels(grn_headers)
        self.grn_table.setMinimumHeight(150)
        self.grn_table.verticalHeader().setVisible(False)
        self.grn_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.grn_table.setAlternatingRowColors(True)
        self.grn_table.cellDoubleClicked.connect(self.on_open_linked_grn)
        self.layout.addWidget(self.grn_table)

        # === Notes ===
        notes_label = QLabel("Notes:")
        notes_label.setStyleSheet("font-weight: 600;")
        self.notes_display = QLabel("-")
        self.notes_display.setWordWrap(True)

        self.layout.addWidget(notes_label)
        self.layout.addWidget(self.notes_display)

        # === Action Buttons ===
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.update_status_btn = QPushButton("Update Status")
        self.update_status_btn.setObjectName("TopRightButton")
        self.update_status_btn.setCursor(Qt.PointingHandCursor)
        self.update_status_btn.setFixedWidth(150)
        self.update_status_btn.clicked.connect(self.on_update_status)

        self.close_po_btn = QPushButton("Close PO")
        self.close_po_btn.setObjectName("TopRightButton")
        self.close_po_btn.setCursor(Qt.PointingHandCursor)
        self.close_po_btn.setFixedWidth(150)
        self.close_po_btn.clicked.connect(self.on_close_po)

        action_layout.addWidget(self.update_status_btn)
        action_layout.addWidget(self.close_po_btn)

        self.layout.addLayout(action_layout)
        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())

    def load_po_data(self, po_id):
        """Load PO data from database"""
        self.current_po_id = po_id

        # Load PO header
        po_query = QSqlQuery()
        po_query.prepare("""
            SELECT po.id, po.po_number, s.name, po.po_date, po.expected_delivery_date, po.status, po.total_value, po.notes
            FROM purchase_order po
            JOIN supplier s ON po.supplier = s.id
            WHERE po.id = ?
        """)
        po_query.addBindValue(po_id)

        if not po_query.exec():
            AppMessageBox.critical(self, "Error", f"Failed to load PO: {po_query.lastError().text()}")
            return

        if not po_query.next():
            AppMessageBox.critical(self, "Error", "PO not found.")
            return

        # Display PO data
        po_status = str(po_query.value(5))
        self.po_number_display.setText(str(po_query.value(1)))
        self.supplier_display.setText(str(po_query.value(2)))
        self.po_date_display.setText(str(po_query.value(3)))
        self.delivery_display.setText(str(po_query.value(4)))
        self.status_display.setText(po_status)
        self.total_display.setText(f"{float(po_query.value(6) or 0):.2f}")
        self.notes_display.setText(str(po_query.value(7) or "No notes"))

        # Load line items
        self.load_po_line_items(po_id)
        self.load_po_grn_history(po_id)
        
        # Update close button visibility based on status and GRN association
        self.update_close_button_visibility(po_status)

    def load_po_line_items(self, po_id):
        """Load PO line items"""
        line_query = QSqlQuery()
        line_query.prepare("""
            SELECT
                p.display_name,
                pol.qty_ordered,
                COALESCE(SUM(grl.qty_received), 0) AS qty_received,
                pol.unit_price,
                pol.total_price
            FROM purchase_order_line pol
            JOIN product p ON pol.product = p.id
            LEFT JOIN goods_receipt_line grl ON grl.po_line_id = pol.id
            WHERE pol.po_id = ?
            GROUP BY pol.id, p.display_name, pol.qty_ordered, pol.unit_price, pol.total_price
            ORDER BY pol.id ASC
        """)
        line_query.addBindValue(po_id)

        if not line_query.exec():
            print("Error loading line items:", line_query.lastError().text())
            self.items_table.setRowCount(0)
            return

        self.items_table.setRowCount(0)
        row = 0

        while line_query.next():
            self.items_table.insertRow(row)

            product = line_query.value(0)
            qty = line_query.value(1)
            qty_received = line_query.value(2)
            qty_remaining = max(float(qty or 0) - float(qty_received or 0), 0.0)
            unit_price = line_query.value(3)
            total_price = line_query.value(4)

            self.items_table.setItem(row, 0, QTableWidgetItem(str(product)))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{float(qty_received or 0):.2f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{qty_remaining:.2f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{float(unit_price):.2f}"))
            self.items_table.setItem(row, 5, QTableWidgetItem(f"{float(total_price):.2f}"))

            row += 1

        totals_query = QSqlQuery()
        totals_query.prepare("""
            SELECT
                COALESCE(SUM(pol.qty_ordered), 0),
                COALESCE(SUM(grl.qty_received), 0)
            FROM purchase_order_line pol
            LEFT JOIN goods_receipt_line grl ON grl.po_line_id = pol.id
            WHERE pol.po_id = ?
        """)
        totals_query.addBindValue(int(po_id))
        if totals_query.exec() and totals_query.next():
            ordered_total = float(totals_query.value(0) or 0)
            received_total = float(totals_query.value(1) or 0)
            self.received_total_display.setText(f"{received_total:.2f}")
            self.remaining_total_display.setText(f"{max(ordered_total - received_total, 0.0):.2f}")
        else:
            self.received_total_display.setText("0.00")
            self.remaining_total_display.setText("0.00")

    def load_po_grn_history(self, po_id):
        query = QSqlQuery()
        query.prepare("""
            SELECT
                gr.id,
                gr.grn_number,
                gr.grn_date,
                gr.status,
                gr.total_value,
                COALESCE((SELECT MAX(p.id) FROM purchase p WHERE p.sellerinvoice = gr.grn_number), '') AS bill_id
            FROM goods_receipt gr
            WHERE gr.po_id = ?
            ORDER BY gr.id DESC
        """)
        query.addBindValue(int(po_id))

        if not query.exec():
            self.grn_table.setRowCount(0)
            return

        self.grn_table.setRowCount(0)
        row = 0
        while query.next():
            self.grn_table.insertRow(row)
            grn_id = int(query.value(0) or 0)

            grn_item = QTableWidgetItem(str(query.value(1) or ""))
            grn_item.setData(Qt.UserRole, grn_id)

            self.grn_table.setItem(row, 0, grn_item)
            self.grn_table.setItem(row, 1, QTableWidgetItem(str(query.value(2) or "")))
            self.grn_table.setItem(row, 2, QTableWidgetItem(str(query.value(3) or "")))
            self.grn_table.setItem(row, 3, QTableWidgetItem(f"{float(query.value(4) or 0):.2f}"))
            self.grn_table.setItem(row, 4, QTableWidgetItem(str(query.value(5) or "")))
            row += 1

    def on_open_linked_grn(self, row, _column):
        grn_item = self.grn_table.item(row, 0)
        if grn_item is None:
            return

        grn_id = grn_item.data(Qt.UserRole)
        if grn_id is None:
            return

        self.grn_detail_signal.emit(int(grn_id))

    def update_close_button_visibility(self, po_status):
        """Hide close button if PO is already closed or no GRN is associated"""
        # Hide if status is already 'closed'
        if po_status == 'closed':
            self.close_po_btn.hide()
            return
        
        # Hide if no GRNs are associated
        if self.grn_table.rowCount() == 0:
            self.close_po_btn.hide()
            return
        
        # Show button if both conditions are met
        self.close_po_btn.show()

    def on_update_status(self):
        """Explain PO status behavior now that receipts drive it automatically."""
        AppMessageBox.information(
            self,
            "Status Managed Automatically",
            "PO status is updated automatically from cumulative GRN receipts.\n\n"
            "If some quantity is received, the PO becomes Partial Received.\n"
            "When the ordered quantity is fully received, the PO becomes Received.",
        )

    @Permissions.require_permission('po.update')
    def on_close_po(self):
        """Close PO"""
        if not self.current_po_id:
            return

        _, accepted = AppMessageBox.confirm(
            self,
            "Close PO",
            "Are you sure you want to close this PO?",
            confirm_label="Close PO",
            cancel_label="Cancel",
            kind="warning",
        )
        if not accepted:
            return

        query = QSqlQuery()
        query.prepare("UPDATE purchase_order SET status = ? WHERE id = ?")
        query.addBindValue("closed")
        query.addBindValue(self.current_po_id)

        if not query.exec():
            AppMessageBox.critical(self, "Error", f"Failed to close PO: {query.lastError().text()}")
            return

        try:
            log_activity(
                category="procurement",
                action="po_closed",
                entity_type="purchase_order",
                entity_id=int(self.current_po_id),
                note=f"PO {self.po_number_display.text()} manually set to closed."
            )
        except Exception as exc:
            print("PO close activity log failed (non-blocking):", exc)

        AppMessageBox.information(self, "Success", "PO closed successfully.")
        self.po_list_signal.emit()

    def on_back_clicked(self):
        """Return to list"""
        self.po_list_signal.emit()
