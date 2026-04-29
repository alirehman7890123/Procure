from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QMessageBox, QStatusBar, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QPdfWriter, QPainter, QPageSize, QFont, QTextOption, QPen, QColor
import os
import platform
import subprocess
from medic.utilities.activity_logger import log_activity
from medic.utilities.permissions import Permissions
from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from features.purchase.services.purchase_order_service import (
    close_purchase_order,
    fetch_purchase_order_detail,
    fetch_purchase_order_grn_rows,
    fetch_purchase_order_line_rows,
    fetch_purchase_order_print_payload,
    fetch_purchase_order_totals,
)


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

        self.print_po_btn = QPushButton("Print PO")
        self.print_po_btn.setObjectName("TopRightButton")
        self.print_po_btn.setCursor(Qt.PointingHandCursor)
        self.print_po_btn.setFixedWidth(150)
        self.print_po_btn.clicked.connect(self.on_print_po)

        self.close_po_btn = QPushButton("Close PO")
        self.close_po_btn.setObjectName("TopRightButton")
        self.close_po_btn.setCursor(Qt.PointingHandCursor)
        self.close_po_btn.setFixedWidth(150)
        self.close_po_btn.clicked.connect(self.on_close_po)

        action_layout.addWidget(self.print_po_btn)
        action_layout.addWidget(self.update_status_btn)
        action_layout.addWidget(self.close_po_btn)

        self.layout.addLayout(action_layout)
        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())

    def load_po_data(self, po_id):
        """Load PO data from database"""
        self.current_po_id = po_id

        po_data = fetch_purchase_order_detail(po_id)
        if po_data is None:
            AppMessageBox.critical(self, "Error", "PO not found.")
            return

        # Display PO data
        po_status = str(po_data["status"] or "")
        self.po_number_display.setText(str(po_data["po_number"]))
        self.supplier_display.setText(str(po_data["supplier_name"]))
        self.po_date_display.setText(str(po_data["po_date"]))
        self.delivery_display.setText(str(po_data["expected_delivery_date"]))
        self.status_display.setText(po_status)
        self.total_display.setText(f"{float(po_data['total_value'] or 0):.2f}")
        self.notes_display.setText(str(po_data["notes"] or "No notes"))

        # Load line items
        self.load_po_line_items(po_id)
        self.load_po_grn_history(po_id)
        
        # Update close button visibility based on status and GRN association
        self.update_close_button_visibility(po_status)

    def load_po_line_items(self, po_id):
        """Load PO line items"""
        rows = fetch_purchase_order_line_rows(po_id)
        self.items_table.setRowCount(0)
        for row, row_data in enumerate(rows):
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QTableWidgetItem(str(row_data["product_name"])))
            self.items_table.setItem(row, 1, QTableWidgetItem(f"{float(row_data['qty_ordered'] or 0):.2f}"))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{float(row_data['qty_received'] or 0):.2f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{float(row_data['qty_remaining'] or 0):.2f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{float(row_data['unit_price'] or 0):.2f}"))
            self.items_table.setItem(row, 5, QTableWidgetItem(f"{float(row_data['total_price'] or 0):.2f}"))

        totals = fetch_purchase_order_totals(po_id)
        self.received_total_display.setText(f"{totals['received_total']:.2f}")
        self.remaining_total_display.setText(f"{totals['remaining_total']:.2f}")

    def load_po_grn_history(self, po_id):
        rows = fetch_purchase_order_grn_rows(po_id)
        self.grn_table.setRowCount(0)
        for row, row_data in enumerate(rows):
            self.grn_table.insertRow(row)
            grn_id = int(row_data["grn_id"] or 0)

            grn_item = QTableWidgetItem(str(row_data["grn_number"] or ""))
            grn_item.setData(Qt.UserRole, grn_id)

            self.grn_table.setItem(row, 0, grn_item)
            self.grn_table.setItem(row, 1, QTableWidgetItem(str(row_data["grn_date"] or "")))
            self.grn_table.setItem(row, 2, QTableWidgetItem(str(row_data["status"] or "")))
            self.grn_table.setItem(row, 3, QTableWidgetItem(f"{float(row_data['total_value'] or 0):.2f}"))
            self.grn_table.setItem(row, 4, QTableWidgetItem(str(row_data["bill_id"] or "")))

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

    def export_po_pdf(self, filename="purchase_order.pdf"):
        if not self.current_po_id:
            raise Exception("No purchase order is loaded.")
        payload = fetch_purchase_order_print_payload(self.current_po_id)
        business_name = payload["business_name"]
        business_address = payload["business_address"]
        business_contact = payload["business_contact"]
        po_number = payload["po_number"]
        po_date = payload["po_date"]
        expected_delivery = payload["expected_delivery"]
        total_value = payload["total_value"]
        notes = payload["notes"]
        supplier_name = payload["supplier_name"]
        items = payload["items"]

        pdf = QPdfWriter(filename)
        pdf.setPageSize(QPageSize(QPageSize.A4))
        pdf.setResolution(300)

        painter = QPainter(pdf)
        painter.setPen(Qt.black)

        x = 100
        y = 200

        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(x, y, business_name)

        y += 80
        painter.setFont(QFont("Arial", 12))
        painter.drawText(x, y, business_address)
        y += 70
        painter.drawText(x, y, business_contact)

        painter.setFont(QFont("Arial", 30, QFont.Bold))
        painter.drawText(1550, 230, "Purchase Order")

        painter.setFont(QFont("Arial", 12))
        right_option = QTextOption()
        right_option.setAlignment(Qt.AlignRight)
        painter.drawText(QRectF(1550, 250, 650, 100), f"# {po_number}", right_option)
        painter.drawText(QRectF(1550, 320, 650, 100), po_date, right_option)

        y += 150
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(x, y, f"Supplier: {supplier_name}")
        y += 70
        painter.setFont(QFont("Arial", 11))
        painter.drawText(x, y, f"Expected Delivery: {expected_delivery}")

        y += 70
        pen = QPen(QColor("black"))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)

        y += 70
        painter.setFont(QFont("Arial", 11, QFont.Bold))
        painter.drawText(x + 20, y, "Item")
        painter.drawText(x + 1100, y, "Qty")
        painter.drawText(x + 1450, y, "Unit Price")
        painter.drawText(x + 1850, y, "Total")

        y += 40
        painter.drawLine(x, y, pdf.width() - 200, y)
        y += 90

        painter.setFont(QFont("Arial", 11))
        for product_name, qty_ordered, unit_price, total_price in items:
            painter.drawText(x + 20, y, product_name)
            painter.drawText(x + 1100, y, f"{qty_ordered:g}")
            painter.drawText(x + 1450, y, f"{unit_price:.2f}")
            painter.drawText(x + 1850, y, f"{total_price:.2f}")
            y += 80

        y += 30
        painter.drawLine(x + 1450, y, pdf.width() - 200, y)
        y += 80
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(x + 1450, y, "Total Value:")
        painter.drawText(x + 1900, y, f"{total_value:.2f}")

        if notes:
            y += 120
            painter.setFont(QFont("Arial", 11, QFont.Bold))
            painter.drawText(x, y, "Notes:")
            y += 55
            painter.setFont(QFont("Arial", 11))
            painter.drawText(QRectF(x, y, pdf.width() - 300, 220), notes)

        painter.end()
        return filename

    def print_pdf(self, filename):
        system = platform.system()
        if system in ("Linux", "Darwin"):
            subprocess.run(["lp", filename], check=False)
        elif system == "Windows":
            os.startfile(filename, "print")

    def on_print_po(self):
        if not self.current_po_id:
            AppMessageBox.warning(self, "Print PO", "No purchase order is loaded.")
            return
        try:
            filename = self.export_po_pdf(filename=f"purchase_order_{self.current_po_id}.pdf")
            self.print_pdf(filename)
            AppMessageBox.information(self, "Print PO", "Purchase Order sent for printing.")
        except Exception as exc:
            AppMessageBox.error(self, "Print PO", f"Failed to print Purchase Order: {exc}")

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

        try:
            close_purchase_order(self.current_po_id)
        except Exception as exc:
            AppMessageBox.critical(self, "Error", str(exc))
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
