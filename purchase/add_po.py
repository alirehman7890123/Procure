from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QDateEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QFrame, QHeaderView,
    QSizePolicy, QGridLayout, QCheckBox, QDialog
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QIntValidator, QDoubleValidator
from utilities.stylus import load_stylesheets
from utilities.activity_logger import log_activity
from utilities.session_gate import require_open_session
from utilities.session_service import get_active_session_id
from utilities.permissions import Permissions
from utilities.app_messagebox import AppMessageBox
from utilities.product_search_widget import ProductSearchBox
from services.purchase_order_service import (
    build_purchase_order_header_payload,
    compute_reorder_suggestion,
    fetch_last_purchase_order_cost,
    fetch_low_stock_products,
    fetch_next_purchase_order_number,
    fetch_pack_size,
    fetch_product_reorder_level,
    fetch_recent_sales_units,
    insert_purchase_order_header,
    insert_purchase_order_line,
    normalize_po_number,
    normalize_purchase_order_line_row,
)


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


class LowStockProductsDialog(QDialog):
    def __init__(self, rows, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Low Stock Products")
        self.resize(980, 620)
        self.selected_rows = set()
        self._data_rows = rows or []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel("Low Stock Products", objectName="SectionTitle")
        hint = QLabel(
            "Used products only. Click any product row to toggle it, then add the selected lines to the purchase order."
        )
        hint.setStyleSheet("font-size: 11px; color: #666; padding-left: 0;")
        layout.addWidget(title)
        layout.addWidget(hint)

        self.table = QTableWidget(0, 7, self)
        self.table.setHorizontalHeaderLabels([
            "Pick", "Product", "Stock", "Reorder", "Suggested Qty", "Last Cost", "Reason"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.cellClicked.connect(self._handle_cell_clicked)
        self.table.setStyleSheet("QTableWidget::item { padding: 6px; }")
        layout.addWidget(self.table, 1)

        footer = QHBoxLayout()
        self.summary = QLabel("0 products selected")
        self.summary.setStyleSheet("font-size: 11px; color: #555; padding-left: 0;")
        footer.addWidget(self.summary)
        footer.addStretch()
        cancel_btn = QPushButton("Cancel", objectName="TopRightButton")
        add_btn = QPushButton("Add to Purchase Order", objectName="SaveButton")
        cancel_btn.clicked.connect(self.reject)
        add_btn.clicked.connect(self.accept)
        footer.addWidget(cancel_btn)
        footer.addWidget(add_btn)
        layout.addLayout(footer)

        self._populate_table()

    def _populate_table(self):
        current_manufacturer = None
        visual_row = 0
        for data in self._data_rows:
            manufacturer_name = data.get("manufacturer_name") or "Unassigned Manufacturer"
            if manufacturer_name != current_manufacturer:
                self.table.insertRow(visual_row)
                group_item = QTableWidgetItem(f"Manufacturer: {manufacturer_name}")
                group_item.setFlags(Qt.ItemIsEnabled)
                group_item.setData(Qt.UserRole, "group")
                group_item.setData(Qt.UserRole + 1, None)
                group_item.setForeground(QColor("#21435D"))
                group_item.setBackground(QColor("#E8EFF5"))
                for col in range(self.table.columnCount()):
                    item = group_item if col == 1 else QTableWidgetItem("")
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setData(Qt.UserRole, "group")
                    item.setData(Qt.UserRole + 1, None)
                    item.setBackground(QColor("#E8EFF5"))
                    item.setForeground(QColor("#21435D"))
                    self.table.setItem(visual_row, col, item)
                self.table.setSpan(visual_row, 1, 1, self.table.columnCount() - 1)
                self.table.setRowHeight(visual_row, 28)
                current_manufacturer = manufacturer_name
                visual_row += 1

            self.table.insertRow(visual_row)
            pick_item = QTableWidgetItem("○")
            pick_item.setTextAlignment(Qt.AlignCenter)
            pick_item.setData(Qt.UserRole, "data")
            pick_item.setData(Qt.UserRole + 1, data)

            values = [
                pick_item,
                QTableWidgetItem(str(data.get("product_name") or "")),
                QTableWidgetItem(str(data.get("stock_qty") or 0)),
                QTableWidgetItem(str(data.get("reorder_level") or 0)),
                QTableWidgetItem(str(data.get("suggested_qty") or 1)),
                QTableWidgetItem(f"{float(data.get('last_cost') or 0.0):.2f}"),
                QTableWidgetItem(str(data.get("status_reason") or "Low Stock")),
            ]
            for col, item in enumerate(values):
                item.setData(Qt.UserRole, "data")
                item.setData(Qt.UserRole + 1, data)
                if col in (2, 3, 4, 5):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(visual_row, col, item)
            self.table.setRowHeight(visual_row, 34)
            visual_row += 1

        self._refresh_selection_ui()

    def _handle_cell_clicked(self, row, _column):
        item = self.table.item(row, 0)
        if item is None:
            return
        if item.data(Qt.UserRole) != "data":
            return
        if row in self.selected_rows:
            self.selected_rows.remove(row)
        else:
            self.selected_rows.add(row)
        self._refresh_selection_ui()

    def _refresh_selection_ui(self):
        count = 0
        normal_bg = QColor("#FFFFFF")
        selected_bg = QColor("#EAF4FF")
        selected_fg = QColor("#173F5F")
        for row in range(self.table.rowCount()):
            row_type = self.table.item(row, 0).data(Qt.UserRole) if self.table.item(row, 0) else None
            if row_type != "data":
                continue
            selected = row in self.selected_rows
            pick = self.table.item(row, 0)
            if pick:
                pick.setText("●" if selected else "○")
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item is None:
                    continue
                item.setBackground(selected_bg if selected else normal_bg)
                item.setForeground(selected_fg if selected else QColor("#222222"))
            if selected:
                count += 1
        self.summary.setText(f"{count} product{'s' if count != 1 else ''} selected")

    def selected_products(self):
        rows = []
        for row in sorted(self.selected_rows):
            item = self.table.item(row, 0)
            if item is None:
                continue
            data = item.data(Qt.UserRole + 1)
            if data:
                rows.append(data)
        return rows


class AddPOWidget(QWidget):
    """Create New Purchase Order Widget"""

    po_list_signal = Signal()
    _default_reorder_hint = "When enabled, qty is suggested from product sales in the last 30 days."

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

        self._low_stock_btn = QPushButton("Low Stock Picker", objectName="TopRightButton")
        self._low_stock_btn.setCursor(Qt.PointingHandCursor)
        self._low_stock_btn.clicked.connect(self._open_low_stock_dialog)
        reorder_row.addWidget(self._low_stock_btn)

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
            self._reorder_hint.setText(self._default_reorder_hint)

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

        cost, source = self._get_last_cost(product_id)
        if cost is not None:
            self._entry_price.setText(f"{cost:.2f}")
            self._last_cost_hint.setText(f"Last cost: {cost:.2f} ({source})")
            self._update_entry_total()
            return

        self._entry_price.clear()
        self._last_cost_hint.setText("Last cost: no history")

    def _get_last_cost(self, product_id):
        if product_id is None:
            return None, None
        return fetch_last_purchase_order_cost(product_id)

    def _get_reorder_level(self, product_id):
        return fetch_product_reorder_level(product_id)

    def _suggest_reorder_qty(self, product_id):
        if not self._suggest_reorder_checkbox.isChecked():
            self._reorder_hint.setText(self._default_reorder_hint)
            return

        if product_id is None:
            self._entry_qty.clear()
            self._reorder_hint.setText("Suggested qty: -")
            return

        try:
            suggestion = compute_reorder_suggestion(
                suggested_units=fetch_recent_sales_units(product_id),
                pack_size=fetch_pack_size(product_id),
                reorder_level=self._get_reorder_level(product_id),
            )
        except Exception:
            self._reorder_hint.setText("Suggested qty unavailable.")
            return

        if suggestion["suggested_qty"] > 0 and suggestion["source"] == "sales_30d":
            self._entry_qty.setText(str(suggestion["suggested_qty"]))
            self._reorder_hint.setText(
                f"Suggested qty: {suggestion['suggested_qty']} pack(s) from {suggestion['suggested_units']} unit sales in last 30 days | Avg/day: {suggestion['average_per_day']:.1f} unit(s)"
            )
            return

        if suggestion["suggested_qty"] > 0 and suggestion["source"] == "reorder_level":
            self._entry_qty.setText(str(suggestion["suggested_qty"]))
            self._reorder_hint.setText(
                f"Suggested qty: {suggestion['suggested_qty']} pack(s) from reorder level | Avg/day: 0.0 unit(s)"
            )
        else:
            self._entry_qty.clear()
            self._reorder_hint.setText("Suggested qty: no 30-day sales or reorder level found.")

    def _focus_next(self, widget):
        widget.setFocus()
        if hasattr(widget, "selectAll"):
            widget.selectAll()

    def _reset_entry_line(self):
        self._entry_product.setCurrentIndex(-1)
        self._entry_product.lineEdit().clear()
        self._entry_qty.clear()
        self._entry_price.clear()
        self._entry_total.setText("0.00")
        self._reorder_hint.setText(self._default_reorder_hint)

    def _collect_entry_line_values(self):
        product_name = self._entry_product.currentText().strip()
        product_id = self._entry_product.currentData()
        qty_text = self._entry_qty.text().strip()
        price_text = self._entry_price.text().strip()
        return {
            "product_name": product_name,
            "product_id": product_id,
            "qty_text": qty_text,
            "price_text": price_text,
        }

    def _build_entry_line_payload(self):
        entry = self._collect_entry_line_values()
        if not entry["product_name"]:
            raise ValueError("Please select a product first.")
        if entry["product_id"] is None:
            raise ValueError("Product not found. Please add it to the product list first.")
        if not entry["qty_text"] or entry["qty_text"] == "0":
            raise ValueError("Packs cannot be empty or zero.")
        if not entry["price_text"] or entry["price_text"] == "0":
            raise ValueError("Cost per pack cannot be empty or zero.")

        try:
            return {
                "product_id": entry["product_id"],
                "product_name": entry["product_name"],
                "qty": int(entry["qty_text"]),
                "price": float(entry["price_text"]),
            }
        except ValueError:
            raise ValueError("Packs must be whole numbers and cost must be numeric.")

    def _row_widget(self, row, column):
        return self.items_table.cellWidget(row, column)

    def _collect_po_header_values(self):
        return {
            "supplier_id": self.supplier_combo.currentData(),
            "po_date": self.po_date.date().toString("yyyy-MM-dd"),
            "expected_delivery_date": self.delivery_date.date().toString("yyyy-MM-dd"),
            "total_value": float(self.total_value_label.text() or 0.0),
            "notes": (self.notes_edit.text() or "").strip(),
        }

    def _persist_po_lines(self, po_id, row_payloads):
        for row_payload in row_payloads:
            insert_purchase_order_line(po_id, row_payload)

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
        try:
            payload = self._build_entry_line_payload()
        except ValueError as exc:
            AppMessageBox.information(self, "Error", str(exc))
            if "product" in str(exc).lower():
                self._entry_product.setFocus()
            elif "pack" in str(exc).lower():
                self._entry_qty.setFocus()
            else:
                self._entry_price.setFocus()
            return

        self._upsert_po_item_row(
            payload["product_id"],
            payload["product_name"],
            payload["qty"],
            payload["price"],
        )
        self._reset_entry_line()
        self._entry_product.setFocus()

    def _find_existing_po_row(self, product_id):
        for row in range(self.items_table.rowCount()):
            product_combo = self._row_widget(row, 1)
            if product_combo and product_combo.currentData() == product_id:
                return row
        return -1

    def _append_po_item_row(self, product_id, product_name, qty, price):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self.items_table.setRowHeight(row, self.row_height)

        counter = QLabel(str(row + 1))
        counter.setAlignment(Qt.AlignCenter)
        self.items_table.setCellWidget(row, 0, counter)

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

        qty_edit = QLineEdit(str(qty))
        qty_edit.setValidator(QIntValidator(0, 999999, self.items_table))
        qty_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        qty_edit.textChanged.connect(lambda _, r=row: self._recalc_row(r))
        self.items_table.setCellWidget(row, 2, qty_edit)

        price_edit = QLineEdit(f"{price:.2f}")
        price_edit.setReadOnly(True)
        price_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.items_table.setCellWidget(row, 3, price_edit)

        total_edit = QLineEdit(f"{qty * price:.2f}")
        total_edit.setReadOnly(True)
        total_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.items_table.setCellWidget(row, 4, total_edit)

        del_btn = QPushButton("X")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("color: #c0392b; font-weight: bold;")
        del_btn.clicked.connect(lambda _, r=row: self._remove_row(r))
        self.items_table.setCellWidget(row, 5, del_btn)

    def _upsert_po_item_row(self, product_id, product_name, qty, price):
        existing_row = self._find_existing_po_row(product_id)
        if existing_row >= 0:
            qty_edit = self._row_widget(existing_row, 2)
            if isinstance(qty_edit, QLineEdit):
                try:
                    current_qty = int(qty_edit.text() or 0)
                except ValueError:
                    current_qty = 0
                qty_edit.setText(str(current_qty + qty))
            price_edit = self._row_widget(existing_row, 3)
            if isinstance(price_edit, QLineEdit):
                price_edit.setText(f"{price:.2f}")
            self._recalc_row(existing_row)
        else:
            self._append_po_item_row(product_id, product_name, qty, price)

        self._update_grand_total()

    def _fetch_low_stock_products(self):
        return fetch_low_stock_products()

    def _open_low_stock_dialog(self):
        try:
            rows = self._fetch_low_stock_products()
        except Exception as exc:
            AppMessageBox.error(self, "Load Failed", f"Could not load low stock products: {exc}")
            return

        if not rows:
            AppMessageBox.information(
                self,
                "Nothing To Add",
                "No used products are currently at zero stock or below their reorder level.",
            )
            return

        dialog = LowStockProductsDialog(rows, self)
        if dialog.exec() != QDialog.Accepted:
            return

        selected_rows = dialog.selected_products()
        if not selected_rows:
            AppMessageBox.information(self, "No Selection", "Select at least one product to add.")
            return

        added_count = 0
        for data in selected_rows:
            product_id = data.get("product_id")
            product_name = str(data.get("product_name") or "").strip()
            qty = max(1, int(data.get("suggested_qty") or 1))
            price = float(data.get("last_cost") or 0.0)
            self._upsert_po_item_row(product_id, product_name, qty, price)
            added_count += 1

        self._entry_product.setFocus()
        AppMessageBox.success(
            self,
            "Products Added",
            f"Added {added_count} low stock product{'s' if added_count != 1 else ''} to the purchase order.",
        )

    def _recalc_row(self, row):
        qty_w = self._row_widget(row, 2)
        price_w = self._row_widget(row, 3)
        total_w = self._row_widget(row, 4)
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
            counter = self._row_widget(row, 0)
            if isinstance(counter, QLabel):
                counter.setText(str(row + 1))
            qty_w = self._row_widget(row, 2)
            if isinstance(qty_w, QLineEdit):
                try:
                    qty_w.textChanged.disconnect()
                except RuntimeError:
                    pass
                qty_w.textChanged.connect(lambda _, r=row: self._recalc_row(r))
            del_btn = self._row_widget(row, 5)
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
            w = self._row_widget(row, 4)
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
        return fetch_next_purchase_order_number()

    def _collect_po_rows(self):
        rows = []
        for row in range(self.items_table.rowCount()):
            product_combo = self._row_widget(row, 1)
            qty_widget = self._row_widget(row, 2)
            price_widget = self._row_widget(row, 3)

            rows.append(
                normalize_purchase_order_line_row(
                    product_id=product_combo.currentData() if product_combo else None,
                    qty=qty_widget.text() if qty_widget else "",
                    unit_price=price_widget.text() if price_widget else "",
                    row_number=row + 1,
                )
            )
        return rows

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
            try:
                po_number = normalize_po_number(po_number)
            except ValueError as exc:
                AppMessageBox.warning(self, "Invalid PO Number", str(exc))
                return

        header_values = self._collect_po_header_values()

        try:
            row_payloads = self._collect_po_rows()
        except ValueError as exc:
            AppMessageBox.warning(self, "Invalid Line Item", str(exc))
            return

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.error(self, "Error", "Could not start transaction.")
            return

        try:
            session_id = get_active_session_id(strict=True)
            header_payload = build_purchase_order_header_payload(
                po_number=po_number,
                supplier_id=header_values["supplier_id"],
                po_date=header_values["po_date"],
                expected_delivery_date=header_values["expected_delivery_date"],
                total_value=header_values["total_value"],
                notes=header_values["notes"],
                session_id=session_id,
            )
            po_id = insert_purchase_order_header(header_payload)
            self._persist_po_lines(po_id, row_payloads)

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
        self._reset_entry_line()

    def on_back_clicked(self):
        self.po_list_signal.emit()
