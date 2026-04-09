from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QDateEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QFrame, QMessageBox, QHeaderView,
    QCompleter, QSizePolicy, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QStringListModel
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from PySide6.QtGui import QKeySequence, QShortcut, QIntValidator, QDoubleValidator
from utilities.stylus import load_stylesheets
from utilities.activity_logger import log_activity
from utilities.session_gate import require_open_session
from utilities.session_service import get_active_session_id
from utilities.permissions import Permissions
from utilities.app_messagebox import AppMessageBox
from utilities.product_search_widget import ProductSearchBox
import re


class SelectAllLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._select_on_release = False

    def mousePressEvent(self, event):
        if not self.hasFocus():
            self._select_on_release = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._select_on_release:
            self._select_on_release = False
            self.selectAll()


class MyTable(QTableWidget):
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(10)

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


class AddPOWidget(QWidget):
    """Create New Purchase Order Widget"""

    po_list_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header ===
        header_layout = QHBoxLayout()
        heading = QLabel("Create Purchase Order", objectName="SectionTitle")
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

        # === PO Header Details ===
        header_frame = QFrame()
        header_frame.setObjectName("sectionCard")
        header_layout2 = QVBoxLayout(header_frame)
        header_layout2.setContentsMargins(10, 10, 10, 10)
        header_layout2.setSpacing(10)

        row1 = QHBoxLayout()
        supplier_label = QLabel("Supplier")
        supplier_label.setStyleSheet("font-weight: 600;")
        self.supplier_combo = QComboBox()
        self.supplier_combo.setPlaceholderText("Select supplier")
        self.load_suppliers()
        row1.addWidget(supplier_label, 1)
        row1.addWidget(self.supplier_combo, 2)

        po_number_label = QLabel("PO Number")
        po_number_label.setStyleSheet("font-weight: 600;")
        self.po_number_edit = QLineEdit()
        self.po_number_edit.setPlaceholderText("Auto-generated (PO-1001+) or enter manually")
        row1.addWidget(po_number_label, 1)
        row1.addWidget(self.po_number_edit, 2)

        po_date_label = QLabel("PO Date")
        po_date_label.setStyleSheet("font-weight: 600;")
        self.po_date = QDateEdit()
        self.po_date.setCalendarPopup(True)
        self.po_date.setDate(QDate.currentDate())
        row1.addWidget(po_date_label, 1)
        row1.addWidget(self.po_date, 2)
        header_layout2.addLayout(row1)

        row2 = QHBoxLayout()
        delivery_label = QLabel("Expected Delivery Date")
        delivery_label.setStyleSheet("font-weight: 600;")
        self.delivery_date = QDateEdit()
        self.delivery_date.setCalendarPopup(True)
        self.delivery_date.setDate(QDate.currentDate().addDays(7))
        row2.addWidget(delivery_label, 1)
        row2.addWidget(self.delivery_date, 2)

        notes_label = QLabel("Notes")
        notes_label.setStyleSheet("font-weight: 600;")
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Any special instructions...")
        row2.addWidget(notes_label, 1)
        row2.addWidget(self.notes_edit, 2)
        header_layout2.addLayout(row2)
        self.layout.addWidget(header_frame)

        # === Line Items Section (entry line + table) ===
        self._build_line_items_section()

        # === Totals Section ===
        totals_frame = QFrame()
        totals_frame.setObjectName("sectionCard")
        totals_layout = QHBoxLayout(totals_frame)
        totals_layout.setContentsMargins(10, 10, 10, 10)
        totals_layout.setSpacing(20)
        totals_layout.addStretch()
        total_label = QLabel("Total Value:")
        total_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        self.total_value_label = QLabel("0.00")
        self.total_value_label.setStyleSheet("font-size: 14px; color: #2F5D7C;")
        totals_layout.addWidget(total_label)
        totals_layout.addWidget(self.total_value_label)
        self.layout.addWidget(totals_frame)

        # === Action Buttons ===
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        self.save_btn = QPushButton("Save PO")
        self.save_btn.setObjectName("TopRightButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedWidth(150)
        self.save_btn.clicked.connect(self.save_po)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("CancelButton")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedWidth(150)
        cancel_btn.clicked.connect(self.on_back_clicked)
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(cancel_btn)
        self.layout.addLayout(action_layout)
        self.layout.addStretch()

        self.setStyleSheet(load_stylesheets())
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.save_po)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.save_po)

    # ─────────────────────────────────────────────────────────────
    # UI builders
    # ─────────────────────────────────────────────────────────────

    def _build_line_items_section(self):
        """Entry-line + responsive table inside a sectionCard frame."""
        self._items_frame = QFrame()
        self._items_frame.setObjectName("sectionCard")
        self._items_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        frame_layout = QVBoxLayout(self._items_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(10)
        self._frame_layout = frame_layout

        reorder_row = QHBoxLayout()
        reorder_row.setContentsMargins(0, 0, 0, 0)
        reorder_row.setSpacing(8)

        self._suggest_reorder_checkbox = QCheckBox("Suggest reorder qty")
        self._suggest_reorder_checkbox.setCursor(Qt.PointingHandCursor)
        self._suggest_reorder_checkbox.setChecked(False)
        self._suggest_reorder_checkbox.toggled.connect(self._on_reorder_toggle_changed)
        reorder_row.addWidget(self._suggest_reorder_checkbox)

        self._reorder_hint = QLabel("When enabled, qty is suggested from product sales in the last 30 days.")
        self._reorder_hint.setStyleSheet("font-size: 11px; color: #666; padding-left: 0;")
        reorder_row.addWidget(self._reorder_hint)
        reorder_row.addStretch()

        frame_layout.addLayout(reorder_row)

        field_style = """
            QLabel  { font-size: 12px; padding-left: 0; }
            QLineEdit {
                padding: 5px; border: 1px solid #ccc; border-radius: 4px;
                font-size: 12px; background-color: #f9f9f9;
            }
            QLineEdit:focus { border: 2px solid #5B8FB8; background: #F2F8FC; }
            QComboBox {
                padding: 5px; border: 1px solid #ccc; border-radius: 4px;
                font-size: 12px; background-color: #f9f9f9;
            }
            QComboBox:focus { border: 2px solid #5B8FB8; background: #F2F8FC; }
        """

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)
        self._entry_grid = grid

        for col, text in enumerate(["Product", "Qty (Packs)", "Cost / Pack", "Total", "Action"]):
            lbl = QLabel(text)
            lbl.setStyleSheet(field_style)
            grid.addWidget(lbl, 0, col)

        # product combo with live autocomplete
        self._entry_product = ProductSearchBox(self, placeholder="search product...", defer_numeric_to_enter=True)
        self._entry_product.wheelEvent = lambda e: e.ignore()
        self._entry_product.setLineEdit(SelectAllLineEdit())
        self._entry_product.lineEdit().editingFinished.connect(
            lambda c=self._entry_product: self._handle_editing_finished(c)
        )
        self._entry_product.lineEdit().returnPressed.connect(
            lambda: self._handle_item_return_pressed(self._entry_product)
        )
        self._entry_product.product_selected.connect(
            lambda pid, name: self._on_completer_selected(name, self._entry_product)
        )
        self._entry_product.setStyleSheet(field_style)

        self._entry_qty = QLineEdit()
        self._entry_qty.setPlaceholderText("packs")
        self._entry_qty.setValidator(QIntValidator(0, 999999, self))
        self._entry_qty.setStyleSheet(field_style)

        self._entry_price = QLineEdit()
        self._entry_price.setPlaceholderText("cost/pack")
        price_validator = QDoubleValidator(0.0, 999999999.99, 2, self)
        price_validator.setNotation(QDoubleValidator.StandardNotation)
        self._entry_price.setValidator(price_validator)
        self._entry_price.setStyleSheet(field_style)

        self._last_cost_hint = QLabel("Last cost: -")
        self._last_cost_hint.setStyleSheet("font-size: 11px; color: #666; padding-left: 4px;")

        self._entry_total = QLineEdit("0.00")
        self._entry_total.setReadOnly(True)
        self._entry_total.setStyleSheet("""
            QLineEdit {
                padding: 5px; border: 1px solid #ccc; border-radius: 4px;
                font-size: 12px; background-color: #f9f9f9; font-weight: bold;
            }
        """)

        add_btn = QPushButton("Add", objectName="EntryButton")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_row)

        grid.addWidget(self._entry_product, 1, 0)
        grid.addWidget(self._entry_qty,     1, 1)
        grid.addWidget(self._entry_price,   1, 2)
        grid.addWidget(self._entry_total,   1, 3)
        grid.addWidget(add_btn,             1, 4)
        grid.addWidget(self._last_cost_hint, 2, 2)

        grid.setColumnStretch(0, 3)
        for c in range(1, 5):
            grid.setColumnStretch(c, 1)

        self._entry_qty.textChanged.connect(self._update_entry_total)
        self._entry_price.textChanged.connect(self._update_entry_total)
        self._entry_qty.returnPressed.connect(lambda: self._focus_next(self._entry_price))
        self._entry_price.returnPressed.connect(lambda: self._focus_next(add_btn))

        frame_layout.addLayout(grid)
        frame_layout.addSpacing(6)

        # table
        self.row_height = 30
        self.min_visible_rows = 5
        self.items_table = MyTable(
            column_ratios=[0.04, 0.38, 0.14, 0.16, 0.16, 0.12]
        )
        headers = ["#", "Product", "Qty (Packs)", "Cost/Pack", "Total", ""]
        self.items_table.setColumnCount(len(headers))
        self.items_table.setHorizontalHeaderLabels(headers)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.verticalHeader().setFixedWidth(0)
        self.items_table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.items_table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.items_table.setTabKeyNavigation(False)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setSelectionMode(QTableWidget.SingleSelection)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.items_table.setStyleSheet("""
            QTableWidget::item { color: #333; border: none; }
            QLineEdit { color: #333; background: #f9f9f9; border: 1px solid #ccc; border-radius: 3px; padding: 2px 4px; }
            QLineEdit:read-only { background: #efefef; }
        """)
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setMinimumWidth(900)
        self.items_table.setFixedHeight(400)

        frame_layout.addWidget(self.items_table)
        frame_layout.setStretch(3, 1)

        self.layout.addWidget(self._items_frame)

    # ─────────────────────────────────────────────────────────────
    # Product autocomplete
    # ─────────────────────────────────────────────────────────────

    def _on_completer_selected(self, text, combo):
        text = text.strip()
        index = combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            combo.setCurrentIndex(index)
            combo.lineEdit().setText(text)
            product_id = combo.currentData()
            self._autofill_cost_from_history(product_id)
            self._suggest_reorder_qty(product_id)
        self._focus_next(self._entry_qty)

    def _on_reorder_toggle_changed(self, checked):
        product_id = self._entry_product.currentData()
        if checked:
            self._suggest_reorder_qty(product_id)
        else:
            self._reorder_hint.setText("When enabled, qty is suggested from product sales in the last 30 days.")

    def _handle_item_return_pressed(self, combo):
        text = combo.currentText().strip()
        if not text:
            return
        if text.isdigit():
            match = combo.lookup_product_by_code(text)
            if match:
                product_id, display_name = match
                combo.select_result(display_name, product_id)
                self._autofill_cost_from_history(product_id)
                self._suggest_reorder_qty(product_id)
                self._focus_next(self._entry_qty)
                return
        index = combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            combo.setCurrentIndex(index)
            product_id = combo.currentData()
            self._autofill_cost_from_history(product_id)
            self._suggest_reorder_qty(product_id)
        self._focus_next(self._entry_qty)

    def _handle_editing_finished(self, combo):
        text = combo.currentText().strip()
        if not text:
            return
        if text.isdigit():
            match = combo.lookup_product_by_code(text)
            if match:
                product_id, display_name = match
                combo.select_result(display_name, product_id)
                self._autofill_cost_from_history(product_id)
                self._suggest_reorder_qty(product_id)
                self._focus_next(self._entry_qty)
                return
        index = combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            combo.setCurrentIndex(index)
            product_id = combo.currentData()
            self._autofill_cost_from_history(product_id)
            self._suggest_reorder_qty(product_id)
        self._focus_next(self._entry_qty)

    def _autofill_cost_from_history(self, product_id):
        """Auto-fill cost from latest purchase history; user can still edit it."""
        if product_id is None:
            self._last_cost_hint.setText("Last cost: -")
            return

        # 1) Prefer latest actual purchase invoice rate (direct purchases)
        query = QSqlQuery()
        query.prepare("""
            SELECT rate
            FROM purchaseitem
            WHERE product = ?
            ORDER BY id DESC
            LIMIT 1
        """)
        query.addBindValue(product_id)

        if query.exec() and query.next():
            cost = float(query.value(0) or 0.0)
            self._entry_price.setText(f"{cost:.2f}")
            self._last_cost_hint.setText(f"Last cost: {cost:.2f} (invoice)")
            self._update_entry_total()
            return

        # 2) Fallback to latest purchase-order line cost
        query2 = QSqlQuery()
        query2.prepare("""
            SELECT unit_price
            FROM purchase_order_line
            WHERE product = ?
            ORDER BY id DESC
            LIMIT 1
        """)
        query2.addBindValue(product_id)

        if query2.exec() and query2.next():
            cost = float(query2.value(0) or 0.0)
            self._entry_price.setText(f"{cost:.2f}")
            self._last_cost_hint.setText(f"Last cost: {cost:.2f} (po)")
            self._update_entry_total()
            return

        self._entry_price.clear()
        self._last_cost_hint.setText("Last cost: no history")

    def _suggest_reorder_qty(self, product_id):
        if not self._suggest_reorder_checkbox.isChecked():
            self._reorder_hint.setText("When enabled, qty is suggested from product sales in the last 30 days.")
            return

        if product_id is None:
            self._entry_qty.clear()
            self._reorder_hint.setText("Suggested qty: -")
            return

        query = QSqlQuery()
        pack_query = QSqlQuery()
        pack_query.prepare(
            """
            SELECT COALESCE(pack_size, 1)
            FROM price_pack
            WHERE product_id = ?
            ORDER BY is_default DESC, id ASC
            LIMIT 1
            """
        )
        pack_query.addBindValue(product_id)

        pack_size = 1
        if pack_query.exec() and pack_query.next():
            try:
                pack_size = max(1, int(float(pack_query.value(0) or 1)))
            except (TypeError, ValueError):
                pack_size = 1

        query.prepare(
            """
            SELECT COALESCE(SUM(COALESCE(si.qty_sold, 0)), 0)
            FROM salesitem si
            JOIN sales s ON s.id = si.sales_id
            WHERE si.product_id = ?
              AND DATE(s.creation_date) >= DATE('now', '-30 days')
            """
        )
        query.addBindValue(product_id)

        if not query.exec():
            self._reorder_hint.setText("Suggested qty unavailable.")
            return

        suggested_units = 0
        if query.next():
            try:
                suggested_units = int(float(query.value(0) or 0))
            except (TypeError, ValueError):
                suggested_units = 0

        suggested_qty = 0
        average_per_day = 0.0
        if suggested_units > 0:
            suggested_qty = max(1, (suggested_units + pack_size - 1) // pack_size)
            average_per_day = suggested_units / 30.0

        if suggested_qty > 0:
            self._entry_qty.setText(str(suggested_qty))
            self._reorder_hint.setText(
                f"Suggested qty: {suggested_qty} pack(s) from {suggested_units} unit sales in last 30 days | Avg/day: {average_per_day:.1f} unit(s)"
            )
            return

        reorder_query = QSqlQuery()
        reorder_query.prepare(
            """
            SELECT COALESCE(MAX(COALESCE(reorder_level, 0)), 0)
            FROM price_pack
            WHERE product_id = ?
            """
        )
        reorder_query.addBindValue(product_id)

        reorder_level = 0
        if reorder_query.exec() and reorder_query.next():
            try:
                reorder_level = int(float(reorder_query.value(0) or 0))
            except (TypeError, ValueError):
                reorder_level = 0

        if reorder_level > 0:
            self._entry_qty.setText(str(reorder_level))
            self._reorder_hint.setText(
                f"Suggested qty: {reorder_level} pack(s) from reorder level | Avg/day: 0.0 unit(s)"
            )
        else:
            self._entry_qty.clear()
            self._reorder_hint.setText("Suggested qty: no 30-day sales or reorder level found.")

    def _focus_next(self, widget):
        widget.setFocus()
        if hasattr(widget, "selectAll"):
            widget.selectAll()

    # ─────────────────────────────────────────────────────────────
    # Entry line helpers
    # ─────────────────────────────────────────────────────────────

    def _update_entry_total(self):
        try:
            qty = int(self._entry_qty.text()) if self._entry_qty.text() else 0
            price = float(self._entry_price.text()) if self._entry_price.text() else 0.0
            self._entry_total.setText(f"{qty * price:.2f}")
        except ValueError:
            self._entry_total.setText("0.00")

    # ─────────────────────────────────────────────────────────────
    # Table row operations
    # ─────────────────────────────────────────────────────────────

    def _add_row(self):
        product_name = self._entry_product.currentText().strip()
        product_id = self._entry_product.currentData()

        if not product_name:
            AppMessageBox.information(self, "Error", "Please select a product first.")
            self._entry_product.setFocus()
            return
        if product_id is None:
            AppMessageBox.information(
                self, "Error",
                "Product not found. Please add it to the product list first."
            )
            self._entry_product.setFocus()
            return

        qty_text = self._entry_qty.text().strip()
        price_text = self._entry_price.text().strip()

        if not qty_text or qty_text == "0":
            AppMessageBox.information(self, "Error", "Packs cannot be empty or zero.")
            self._entry_qty.setFocus()
            return
        if not price_text or price_text == "0":
            AppMessageBox.information(self, "Error", "Cost per pack cannot be empty or zero.")
            self._entry_price.setFocus()
            return

        try:
            qty = int(qty_text)
            price = float(price_text)
        except ValueError:
            AppMessageBox.information(self, "Error", "Packs must be whole numbers and cost must be numeric.")
            return

        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self.items_table.setRowHeight(row, self.row_height)

        # col 0 — row counter
        counter = QLabel(str(row + 1))
        counter.setAlignment(Qt.AlignCenter)
        self.items_table.setCellWidget(row, 0, counter)

        # col 1 — product (read-only display combo)
        product_combo = QComboBox()
        product_combo.addItem(product_name, product_id)
        product_combo.setStyleSheet("""
            QComboBox::drop-down { border: 0px; }
            QComboBox::down-arrow { image: none; }
        """)
        product_combo.setEditable(True)
        product_combo.lineEdit().setReadOnly(True)
        product_combo.setInsertPolicy(QComboBox.NoInsert)
        self.items_table.setCellWidget(row, 1, product_combo)

        # col 2 — qty (editable, recalculates total)
        qty_edit = QLineEdit(str(qty))
        qty_edit.setValidator(QIntValidator(0, 999999, self.items_table))
        qty_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        qty_edit.textChanged.connect(lambda _, r=row: self._recalc_row(r))
        self.items_table.setCellWidget(row, 2, qty_edit)

        # col 3 — unit price (read-only)
        price_edit = QLineEdit(f"{price:.2f}")
        price_edit.setReadOnly(True)
        price_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.items_table.setCellWidget(row, 3, price_edit)

        # col 4 — total (read-only, computed)
        total_edit = QLineEdit(f"{qty * price:.2f}")
        total_edit.setReadOnly(True)
        total_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.items_table.setCellWidget(row, 4, total_edit)

        # col 5 — delete
        del_btn = QPushButton("X")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("color: #c0392b; font-weight: bold;")
        del_btn.clicked.connect(lambda _, r=row: self._remove_row(r))
        self.items_table.setCellWidget(row, 5, del_btn)

        # reset entry line
        self._entry_product.setCurrentIndex(-1)
        self._entry_product.lineEdit().clear()
        self._entry_qty.clear()
        self._entry_price.clear()
        self._entry_total.setText("0.00")
        self._reorder_hint.setText(
            "When enabled, qty is suggested from product sales in the last 30 days."
        )
        self._entry_product.setFocus()

        self._update_grand_total()

    def _recalc_row(self, row):
        qty_w  = self.items_table.cellWidget(row, 2)
        price_w = self.items_table.cellWidget(row, 3)
        total_w = self.items_table.cellWidget(row, 4)
        if not (qty_w and price_w and total_w):
            return
        try:
            qty = int(qty_w.text()) if qty_w.text() else 0
            price = float(price_w.text()) if price_w.text() else 0.0
            total_w.setText(f"{qty * price:.2f}")
        except ValueError:
            total_w.setText("0.00")
        self._update_grand_total()

    def _remove_row(self, target_row):
        self.items_table.removeRow(target_row)
        for row in range(self.items_table.rowCount()):
            counter = self.items_table.cellWidget(row, 0)
            if isinstance(counter, QLabel):
                counter.setText(str(row + 1))
            qty_w = self.items_table.cellWidget(row, 2)
            if isinstance(qty_w, QLineEdit):
                try:
                    qty_w.textChanged.disconnect()
                except RuntimeError:
                    pass
                qty_w.textChanged.connect(lambda _, r=row: self._recalc_row(r))
            del_btn = self.items_table.cellWidget(row, 5)
            if isinstance(del_btn, QPushButton):
                try:
                    del_btn.clicked.disconnect()
                except RuntimeError:
                    pass
                del_btn.clicked.connect(lambda _, r=row: self._remove_row(r))
        self._update_grand_total()

    def _update_grand_total(self):
        total = 0.0
        for row in range(self.items_table.rowCount()):
            w = self.items_table.cellWidget(row, 4)
            if w:
                try:
                    total += float(w.text())
                except ValueError:
                    pass
        self.total_value_label.setText(f"{total:.2f}")

    # ─────────────────────────────────────────────────────────────
    # DB helpers
    # ─────────────────────────────────────────────────────────────

    def load_suppliers(self):
        query = QSqlQuery()
        if not query.exec("SELECT id, name FROM supplier ORDER BY name ASC"):
            print("Error loading suppliers:", query.lastError().text())
            return
        while query.next():
            self.supplier_combo.addItem(str(query.value(1)), query.value(0))

    def get_next_po_number(self):
        query = QSqlQuery()
        if not query.exec(
            """
            SELECT MAX(CAST(SUBSTR(po_number, 4) AS INTEGER))
            FROM purchase_order
            WHERE po_number LIKE 'PO-%'
            """
        ):
            return "PO-1001"

        next_no = 1001
        if query.next() and query.value(0) is not None:
            try:
                next_no = max(int(query.value(0)) + 1, 1001)
            except (TypeError, ValueError):
                next_no = 1001

        return f"PO-{next_no}"

    # ─────────────────────────────────────────────────────────────
    # Save PO
    # ─────────────────────────────────────────────────────────────

    @Permissions.require_permission('po.create')
    def save_po(self):
        if not require_open_session(self):
            return
        if self.supplier_combo.currentIndex() < 0:
            AppMessageBox.warning(self, "Invalid Input", "Please select a supplier.")
            return
        if self.items_table.rowCount() == 0:
            AppMessageBox.warning(self, "Invalid Input", "Please add at least one line item.")
            return

        po_number = (self.po_number_edit.text() or "").strip()
        if not po_number:
            po_number = self.get_next_po_number()
        else:
            po_number = po_number.upper()
            if not re.fullmatch(r"PO-\d+", po_number):
                AppMessageBox.warning(
                    self,
                    "Invalid PO Number",
                    "PO number must follow format PO-<digits>, e.g. PO-1001.",
                )
                return

        supplier_id = self.supplier_combo.currentData()
        po_date = self.po_date.date().toString("yyyy-MM-dd")
        expected_delivery = self.delivery_date.date().toString("yyyy-MM-dd")
        total_value = float(self.total_value_label.text())
        notes = (self.notes_edit.text() or "").strip()

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.error(self, "Error", "Could not start transaction.")
            return

        try:
            po_query = QSqlQuery()
            session_id = get_active_session_id(strict=True)

            po_query.prepare("""
                INSERT INTO purchase_order (po_number, supplier, po_date, expected_delivery_date, status, total_value, notes, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """)
            po_query.addBindValue(po_number)
            po_query.addBindValue(supplier_id)
            po_query.addBindValue(po_date)
            po_query.addBindValue(expected_delivery)
            po_query.addBindValue("draft")
            po_query.addBindValue(total_value)
            po_query.addBindValue(notes)
            po_query.addBindValue(session_id)

            if not po_query.exec():
                raise Exception(f"PO insert failed: {po_query.lastError().text()}")

            po_id = po_query.lastInsertId()

            for row in range(self.items_table.rowCount()):
                product_combo = self.items_table.cellWidget(row, 1)
                qty_widget    = self.items_table.cellWidget(row, 2)
                price_widget  = self.items_table.cellWidget(row, 3)

                product_id = product_combo.currentData()
                try:
                    qty = int(qty_widget.text())
                    unit_price = float(price_widget.text())
                except ValueError:
                    raise Exception(f"Invalid numeric data on row {row + 1}.")
                total_price = qty * unit_price

                line_query = QSqlQuery()
                line_query.prepare("""
                    INSERT INTO purchase_order_line (po_id, product, qty_ordered, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                """)
                line_query.addBindValue(po_id)
                line_query.addBindValue(product_id)
                line_query.addBindValue(qty)
                line_query.addBindValue(unit_price)
                line_query.addBindValue(total_price)

                if not line_query.exec():
                    raise Exception(f"Line item insert failed: {line_query.lastError().text()}")

            if not db.commit():
                raise Exception("Failed to commit PO.")

            try:
                log_activity(
                    category="procurement",
                    action="po_created",
                    entity_type="purchase_order",
                    entity_id=po_id,
                    note=f"Created PO {po_number} with {self.items_table.rowCount()} items"
                )
            except Exception as e:
                print("Activity log failed (non-blocking):", e)

            AppMessageBox.success(self, "Success", f"Purchase Order {po_number} created successfully.")
            self.clear_form()
            self.po_list_signal.emit()

        except Exception as e:
            db.rollback()
            AppMessageBox.error(self, "Error", f"Failed to save PO: {str(e)}")

    # ─────────────────────────────────────────────────────────────
    # Form reset
    # ─────────────────────────────────────────────────────────────

    def clear_form(self):
        self.supplier_combo.setCurrentIndex(-1)
        self.po_number_edit.clear()
        self.po_date.setDate(QDate.currentDate())
        self.delivery_date.setDate(QDate.currentDate().addDays(7))
        self.notes_edit.clear()
        self.items_table.setRowCount(0)
        self.total_value_label.setText("0.00")
        self._entry_product.setCurrentIndex(-1)
        self._entry_product.lineEdit().clear()
        self._entry_qty.clear()
        self._entry_price.clear()
        self._entry_total.setText("0.00")
        self._reorder_hint.setText(
            "When enabled, qty is suggested from product sales in the last 30 days."
        )

    def on_back_clicked(self):
        self.po_list_signal.emit()
