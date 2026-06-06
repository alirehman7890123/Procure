from PySide6.QtWidgets import QApplication, QWidget, QDateEdit, QVBoxLayout, QHBoxLayout, QDialog, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget, QFileDialog
from PySide6.QtCore import QFile, Qt, QDate, Signal, QTimer, QEvent, QRectF, QSizeF, QObject
from medic.utilities.product_search_widget import ProductSearchBox
import os
import sys
import platform
import subprocess

from PySide6.QtGui import QPalette, QColor, QKeyEvent, QPdfWriter, QKeySequence, QPainter, QPageSize, QFont, QTextOption, QPen, QFontMetrics
from functools import partial
import math
from medic.utilities.stylus import load_stylesheets
from medic.utilities.session_gate import require_open_session
from medic.utilities.session_service import get_active_session_id
from PySide6.QtGui import QShortcut

from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.utilities.app_theme import get_theme_palette
from medic.utilities.file_preview import preview_file
from medic.utilities.payment_handler import PaymentMethodHandler
from medic.utilities.product_form_options import get_product_form_options
from medic.utilities.activity_logger import log_activity
from medic.features.sales.ui.pricing_logic import compute_header_totals, compute_line_pricing
from medic.services.product_media_service import ensure_product_media_schema
from medic.services.product_catalog_service import (
    fetch_available_product_quantity,
    fetch_hold_row_product_data,
    fetch_sales_product_by_code,
    fetch_sales_product_detail,
    find_product_id_by_display_name,
    search_sales_products,
)
from medic.services.product_write_service import (
    DEFAULT_MARGIN_PERCENT as PRODUCT_DEFAULT_MARGIN_PERCENT,
    fetch_dormant_product_record,
    find_existing_product_id_by_display_name,
    save_product_with_opening_stock,
)
from medic.services.accounting_settings_service import load_sales_policy_settings
from medic.services.sales_defaults_service import resolve_sales_header_pricing
from medic.services.sales_detail_service import (
    create_sales_customer,
    ensure_sales_manufacturer,
    fetch_active_customer_option_rows,
    fetch_active_manufacturer_option_rows,
    fetch_hold_sale_detail,
    fetch_hold_sale_item_rows,
    fetch_hold_sale_list_rows,
    fetch_sales_receipt_render_context,
    fetch_saved_sale_tax_breakdown,
    insert_sales_customer_quick,
)
from medic.services.sales_posting_service import (
    build_sales_header_payload,
    compute_due_date_from_option,
    resolve_sales_settlement,
)
from medic.services.sales_items_service import (
    normalize_sales_item_row,
)
from medic.services.sales_transaction_service import (
    delete_hold_sale,
    ensure_prescription_schema,
    fetch_prescription_required_products,
    fetch_customer_credit_position,
    persist_sales_receipt_header_and_prescription,
    persist_sales_customer_transaction,
    persist_sales_item_with_fifo,
    resolve_salesman_id,
    run_sales_write_transaction,
    save_hold_sale,
)





class KeyUpLineEdit(QLineEdit):
    keyReleased = Signal(QKeyEvent)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.keyReleased.emit(event)




class SelectAllLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._select_on_release = False

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if event.reason() != Qt.PopupFocusReason:
            QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event):
        if not self.hasFocus():
            self._select_on_release = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._select_on_release:
            self._select_on_release = False
            self.selectAll()


class SalesQuickProductDialog(QDialog):
    DEFAULT_MARGIN_PERCENT = PRODUCT_DEFAULT_MARGIN_PERCENT

    def __init__(self, parent=None, initial_name=""):
        super().__init__(parent)
        ensure_prescription_schema()
        ensure_product_media_schema()
        self.saved_product_id = None
        self.saved_visible_name = ""
        self.existing_product_id = None
        self.selected_media_path = ""
        self.selected_media_info = None
        self.media_removed = False
        self.setWindowTitle("Quick Add Product")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setMinimumHeight(420)

        self.setStyleSheet("""
            QDialog {
                background: #EEF4F8;
            }
            QFrame#quickAddHeader {
                background-color: #325D7B;
                border: 1px solid #284B63;
                border-radius: 8px;
            }
            QFrame#quickAddContent, QFrame#quickAddFooter {
                background: #FFFFFF;
                border: 1px solid #D3DEE7;
                border-radius: 8px;
            }
            QLineEdit, QComboBox {
                min-height: 26px;
                padding: 2px 6px;
                border: 1px solid #C7D4DF;
                border-radius: 6px;
                background: #FFFFFF;
                color: #223746;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #5A9EC9;
                background: #F7FBFF;
                color: #16364B;
            }
            QComboBox QAbstractItemView {
                background: white;
                color: #223746;
                selection-background-color: #5A9EC9;
                selection-color: white;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header_frame = QFrame()
        header_frame.setObjectName("quickAddHeader")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 9, 10, 9)
        header_layout.setSpacing(2)

        header = QLabel("Add Product With Opening Stock")
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        header_layout.addWidget(header)

        header_note = QLabel("Create a new sellable item or revive a dormant product by assigning opening stock, pricing, batch, and expiry.")
        header_note.setWordWrap(True)
        header_note.setStyleSheet("font-size: 11px; color: #DDEAF3;")
        header_layout.addWidget(header_note)
        layout.addWidget(header_frame)

        content_frame = QFrame()
        content_frame.setObjectName("quickAddContent")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(12, 10, 12, 10)
        content_layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(11)

        def form_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #4B5563;")
            return lbl

        initial_name = str(initial_name or "").strip().upper()

        self.product_name_input = SelectAllLineEdit()
        self.product_name_input.setPlaceholderText("Product")
        self.product_name_input.setText(initial_name)
        self.product_name_input.textEdited.connect(lambda text: self.force_uppercase_line_edit(self.product_name_input, text))

        self.dose_input = SelectAllLineEdit()
        self.dose_input.setPlaceholderText("Dose")
        self.dose_input.textEdited.connect(lambda text: self.force_uppercase_line_edit(self.dose_input, text))

        self.form_input = QComboBox()
        self.form_input.setEditable(True)
        self.form_input.setLineEdit(SelectAllLineEdit())
        self.form_input.setInsertPolicy(QComboBox.NoInsert)
        self.form_input.addItems(get_product_form_options())
        self.form_input.setPlaceholderText("Form")
        if self.form_input.lineEdit() is not None:
            self.form_input.lineEdit().textEdited.connect(
                lambda text: self.force_uppercase_line_edit(self.form_input.lineEdit(), text)
            )

        self.formula_input = SelectAllLineEdit()
        self.formula_input.setPlaceholderText("Formula / generic name")
        self.prescription_required_check = QCheckBox("Prescription Required")

        self.manufacturer_combo = QComboBox()
        self.manufacturer_combo.setEditable(True)
        self.manufacturer_combo.setLineEdit(SelectAllLineEdit())
        self.manufacturer_combo.setInsertPolicy(QComboBox.NoInsert)
        self.populate_manufacturer_combo()
        self.manufacturer_combo.lineEdit().editingFinished.connect(self.handle_new_manufacturer_entry)

        self.pack_size_input = SelectAllLineEdit()
        self.pack_size_input.setPlaceholderText("Pack size")

        self.sale_price_input = SelectAllLineEdit()
        self.sale_price_input.setPlaceholderText("Sale price")

        self.margin_input = SelectAllLineEdit()
        self.margin_input.setPlaceholderText("Margin %")
        self.margin_input.setText(f"{self.DEFAULT_MARGIN_PERCENT:.1f}")

        self.cost_price_input = SelectAllLineEdit()
        self.cost_price_input.setPlaceholderText("Cost price (derived)")
        self.cost_price_input.setReadOnly(True)

        self.qty_input = SelectAllLineEdit()
        self.qty_input.setPlaceholderText("Opening qty")

        self.batch_input = SelectAllLineEdit()
        self.batch_input.setPlaceholderText("Batch")
        self.batch_input.textEdited.connect(lambda text: self.force_uppercase_line_edit(self.batch_input, text))

        self.expiry_input = SelectAllLineEdit()
        self.expiry_input.setPlaceholderText("MM-YY (optional)")
        self.expiry_input.setInputMask("99-99;_")

        row = 0
        grid.addWidget(form_label("Product"), row, 0)
        grid.addWidget(self.product_name_input, row, 1)
        grid.addWidget(self.dose_input, row, 2, 1, 2)
        grid.addWidget(self.form_input, row, 4, 1, 2)
        row += 1
        grid.addWidget(form_label("Formula"), row, 0)
        grid.addWidget(self.formula_input, row, 1, 1, 5)
        row += 1
        grid.addWidget(self.prescription_required_check, row, 1, 1, 2)
        media_label = form_label("Product File")
        self.media_value = QLabel("No file selected")
        self.media_value.setStyleSheet("font-size: 11px; color: #5D6E7D; font-weight: 600;")
        self.media_browse_btn = QPushButton("Select File", objectName="TopRightButton")
        self.media_preview_btn = QPushButton("Preview", objectName="TopRightButton")
        self.media_clear_btn = QPushButton("Clear", objectName="TopRightButton")
        self.media_browse_btn.clicked.connect(self.browse_media_file)
        self.media_preview_btn.clicked.connect(self.preview_media_file)
        self.media_clear_btn.clicked.connect(self.clear_media_file)
        media_row = QHBoxLayout()
        media_row.setContentsMargins(0, 0, 0, 0)
        media_row.setSpacing(7)
        media_row.addWidget(self.media_value, 1)
        media_row.addWidget(self.media_browse_btn)
        media_row.addWidget(self.media_preview_btn)
        media_row.addWidget(self.media_clear_btn)
        grid.addWidget(media_label, row, 3)
        grid.addLayout(media_row, row, 4, 1, 2)
        row += 1
        grid.addWidget(form_label("Manufacturer"), row, 0)
        grid.addWidget(self.manufacturer_combo, row, 1, 1, 3)
        grid.addWidget(form_label("Pack Size"), row, 4)
        grid.addWidget(self.pack_size_input, row, 5)
        row += 1
        grid.addWidget(form_label("Sale Price"), row, 0)
        grid.addWidget(self.sale_price_input, row, 1)
        grid.addWidget(form_label("Margin %"), row, 2)
        grid.addWidget(self.margin_input, row, 3)
        grid.addWidget(form_label("Cost Price"), row, 4)
        grid.addWidget(self.cost_price_input, row, 5)
        row += 1
        grid.addWidget(form_label("Opening Qty"), row, 0)
        grid.addWidget(self.qty_input, row, 1)
        grid.addWidget(form_label("Batch"), row, 2)
        grid.addWidget(self.batch_input, row, 3)
        grid.addWidget(form_label("Expiry"), row, 4)
        grid.addWidget(self.expiry_input, row, 5)

        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(3, 2)
        grid.setColumnStretch(5, 2)
        content_layout.addLayout(grid)
        layout.addWidget(content_frame)

        footer_frame = QFrame()
        footer_frame.setObjectName("quickAddFooter")
        footer = QHBoxLayout(footer_frame)
        footer.setContentsMargins(10, 7, 10, 7)
        footer.setSpacing(7)
        footer.addStretch()
        cancel_btn = QPushButton("Cancel", objectName="TopRightButton")
        save_btn = QPushButton("Save Product", objectName="TopRightButton")
        cancel_btn.setAutoDefault(False)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        self.save_btn = save_btn
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.save_product)
        footer.addWidget(cancel_btn)
        footer.addWidget(save_btn)
        layout.addWidget(footer_frame)

        self.try_prefill_existing_product(initial_name)
        self.update_media_display()
        self.sale_price_input.textChanged.connect(self.calculate_pack_cost_from_margin)
        self.margin_input.textChanged.connect(self.calculate_pack_cost_from_margin)
        self.calculate_pack_cost_from_margin()
        self.setup_enter_navigation()
        self._prime_item_field_focus()

    def showEvent(self, event):
        super().showEvent(event)
        # Run after dialog is shown so button/default focus does not override item focus.
        self._prime_item_field_focus()

    def _prime_item_field_focus(self):
        QTimer.singleShot(0, self._focus_item_field)

    def _focus_item_field(self):
        if getattr(self, "product_name_input", None) is None:
            return
        self.product_name_input.setFocus(Qt.OtherFocusReason)
        self.product_name_input.selectAll()

    def focus_next_field(self, widget):
        line_edit = widget.lineEdit() if isinstance(widget, QComboBox) and widget.isEditable() else None
        if line_edit is not None:
            line_edit.setFocus()
            line_edit.selectAll()
            return

        widget.setFocus()
        if isinstance(widget, QLineEdit):
            widget.selectAll()

    def setup_enter_navigation(self):
        self._enter_nav_order = []
        self._enter_nav_next = {}

        watched_widgets = (
            self.product_name_input,
            self.dose_input,
            self.form_input,
            self.form_input.lineEdit(),
            self.formula_input,
            self.manufacturer_combo,
            self.manufacturer_combo.lineEdit(),
            self.pack_size_input,
            self.sale_price_input,
            self.margin_input,
            self.qty_input,
            self.cost_price_input,
            self.batch_input,
            self.expiry_input,
        )
        for widget in watched_widgets:
            if widget is None:
                continue
            widget.installEventFilter(self)
            self._enter_nav_order.append(widget)

        self._enter_nav_next = {
            self.product_name_input: self.dose_input,
            self.dose_input: self.form_input,
            self.form_input: self.formula_input,
            self.form_input.lineEdit(): self.formula_input,
            self.formula_input: self.manufacturer_combo,
            self.manufacturer_combo: self.pack_size_input,
            self.manufacturer_combo.lineEdit(): self.pack_size_input,
            self.pack_size_input: self.sale_price_input,
            self.sale_price_input: self.margin_input,
            self.margin_input: self.qty_input,
            self.qty_input: self.batch_input,
            self.cost_price_input: self.batch_input,
            self.batch_input: self.expiry_input,
        }

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if watched in getattr(self, "_enter_nav_order", []):
                if watched is self.manufacturer_combo or watched is self.manufacturer_combo.lineEdit():
                    self.handle_new_manufacturer_entry()

                if watched is self.expiry_input:
                    self.save_product()
                    return True

                next_widget = self._enter_nav_next.get(watched)
                if next_widget is not None:
                    self.focus_next_field(next_widget)
                    return True

        return super().eventFilter(watched, event)

    def force_uppercase_line_edit(self, line_edit, text):
        cursor_position = line_edit.cursorPosition()
        line_edit.blockSignals(True)
        line_edit.setText((text or "").upper())
        line_edit.setCursorPosition(cursor_position)
        line_edit.blockSignals(False)

    def populate_manufacturer_combo(self):
        self.manufacturer_combo.clear()
        try:
            rows = fetch_active_manufacturer_option_rows()
        except Exception:
            rows = []
        for row_data in rows:
            self.manufacturer_combo.addItem(row_data["name"], row_data["manufacturer_id"])

    def handle_new_manufacturer_entry(self):
        combo = self.manufacturer_combo
        name = combo.currentText().strip()
        if not name:
            return
        for index in range(combo.count()):
            if combo.itemText(index).strip().lower() == name.lower():
                combo.setCurrentIndex(index)
                return
        try:
            manufacturer = ensure_sales_manufacturer(name)
        except Exception:
            return
        if not manufacturer:
            return
        combo.addItem(manufacturer["name"], manufacturer["manufacturer_id"])
        combo.setCurrentIndex(combo.count() - 1)

    def parse_expiry_month_year(self, text):
        raw = str(text or "").strip()
        collapsed = raw.replace("_", "").replace(" ", "")
        if not collapsed or collapsed in {"-", "--"}:
            return None
        match = re.fullmatch(r"(\d{2})-(\d{2})", raw)
        if not match:
            return None
        month = int(match.group(1))
        year = 2000 + int(match.group(2))
        if month < 1 or month > 12:
            return None
        parsed = QDate(year, month, 1)
        if not parsed.isValid():
            return None
        return parsed

    def _float_or_default(self, value, default=0.0):
        try:
            text = str(value or "").strip()
            if not text:
                return float(default)
            return float(re.sub(r"[^0-9.\\-]", "", text))
        except Exception:
            return float(default)

    def calculate_pack_cost_from_margin(self):
        sale_price = self._float_or_default(self.sale_price_input.text(), 0.0)
        margin_percent = self._float_or_default(self.margin_input.text(), self.DEFAULT_MARGIN_PERCENT)
        if sale_price <= 0:
            self.cost_price_input.clear()
            return
        margin_percent = max(0.0, min(99.99, margin_percent))
        pack_cost = sale_price * (1 - (margin_percent / 100.0))
        self.cost_price_input.setText(f"{pack_cost:.2f}")

    def browse_media_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Product File",
            "",
            "Images and PDF Files (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.pdf);;Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;PDF Files (*.pdf);;All Files (*)",
        )
        if not file_path:
            return
        self.selected_media_path = file_path
        self.selected_media_info = None
        self.media_removed = False
        self.update_media_display()

    def preview_media_file(self):
        media_path = str(self.selected_media_path or "").strip()
        mime_type = ""
        if not media_path and self.selected_media_info:
            media_path = str(self.selected_media_info.get("absolute_path") or "").strip()
            mime_type = str(self.selected_media_info.get("mime_type") or "").strip()
        if not media_path:
            AppMessageBox.information(self, "Preview File", "No product file is attached yet.")
            return
        preview_file(self, media_path, mime_type=mime_type)

    def clear_media_file(self):
        self.selected_media_path = ""
        self.selected_media_info = None
        self.media_removed = True
        self.update_media_display()

    def update_media_display(self):
        media_name = "No file selected"
        if str(self.selected_media_path or "").strip():
            media_name = f"Selected: {self.selected_media_path.split('/')[-1]}"
        elif self.selected_media_info:
            media_name = f"Stored: {self.selected_media_info.get('original_filename') or 'Attached file'}"
        elif self.media_removed:
            media_name = "Existing file will be cleared"
        self.media_value.setText(media_name)
        has_media = bool(str(self.selected_media_path or "").strip() or self.selected_media_info)
        self.media_preview_btn.setEnabled(has_media)
        self.media_clear_btn.setEnabled(has_media or self.media_removed)

    def _find_existing_product_id(self, display_name):
        return find_existing_product_id_by_display_name(display_name)

    def _find_dormant_product_record(self, display_name):
        return fetch_dormant_product_record(display_name)

    def try_prefill_existing_product(self, initial_name):
        record = self._find_dormant_product_record(initial_name)
        if not record:
            return

        self.existing_product_id = record["product_id"]
        if record["brand"]:
            self.product_name_input.setText(record["brand"].upper())
        if record["strength"]:
            self.dose_input.setText(record["strength"].upper())
        if record["form"]:
            self.form_input.setEditText(record["form"].title())
        if record["generic_name"]:
            self.formula_input.setText(record["generic_name"])
        if record["manufacturer_id"] is not None:
            for index in range(self.manufacturer_combo.count()):
                if self.manufacturer_combo.itemData(index) == record["manufacturer_id"]:
                    self.manufacturer_combo.setCurrentIndex(index)
                    break
        if record["pack_size"] > 0:
            pack_size = record["pack_size"]
            if float(pack_size).is_integer():
                self.pack_size_input.setText(str(int(pack_size)))
            else:
                self.pack_size_input.setText(f"{pack_size:.2f}")
        if record["pack_price"] > 0:
            self.sale_price_input.setText(f"{record['pack_price']:.2f}")
        self.margin_input.setText(f"{float(record.get('margin_percent', self.DEFAULT_MARGIN_PERCENT) or self.DEFAULT_MARGIN_PERCENT):.2f}")
        self.prescription_required_check.setChecked(bool(record.get("prescription_required")))
        self.selected_media_info = record.get("media_info")
        self.selected_media_path = ""
        self.media_removed = False
        self.update_media_display()
        self.calculate_pack_cost_from_margin()

    def save_product(self):
        product_name = str(self.product_name_input.text() or "").strip()
        dose = str(self.dose_input.text() or "").strip()
        form = str(self.form_input.currentText() or "").strip()
        display_name = " ".join(part for part in [product_name, form, dose] if part).strip()
        formula = str(self.formula_input.text() or "").strip() or None
        manufacturer_id = self.manufacturer_combo.currentData()
        manufacturer_id = int(manufacturer_id) if manufacturer_id not in (None, "") else None
        pack_size_text = str(self.pack_size_input.text() or "").strip()
        sale_price_text = str(self.sale_price_input.text() or "").strip()
        margin_text = str(self.margin_input.text() or "").strip()
        qty_text = str(self.qty_input.text() or "").strip()
        batch_no = str(self.batch_input.text() or "").strip() or None
        expiry_text = str(self.expiry_input.text() or "").strip()

        if not product_name:
            AppMessageBox.information(self, "Missing Data", "Product name is required.")
            self.product_name_input.setFocus()
            return

        if not pack_size_text:
            AppMessageBox.information(self, "Missing Data", "Pack size is required.")
            self.pack_size_input.setFocus()
            return

        if not sale_price_text:
            AppMessageBox.information(self, "Missing Data", "Sale price is required.")
            self.sale_price_input.setFocus()
            return

        if not qty_text:
            AppMessageBox.information(self, "Missing Data", "Opening qty is required.")
            self.qty_input.setFocus()
            return

        pack_size = self._float_or_default(pack_size_text, 0.0)
        sale_price = self._float_or_default(sale_price_text, 0.0)
        opening_qty = self._float_or_default(qty_text, 0.0)
        margin_percent = self._float_or_default(margin_text, self.DEFAULT_MARGIN_PERCENT)
        pack_cost = sale_price * (1 - (margin_percent / 100.0)) if sale_price > 0 else None

        if pack_size <= 0:
            AppMessageBox.information(self, "Missing Data", "Pack size must be greater than 0.")
            self.pack_size_input.setFocus()
            return
        if sale_price <= 0:
            AppMessageBox.information(self, "Missing Data", "Sale price must be greater than 0.")
            self.sale_price_input.setFocus()
            return
        if opening_qty <= 0:
            AppMessageBox.information(self, "Missing Data", "Opening qty must be greater than 0.")
            self.qty_input.setFocus()
            return
        if margin_percent < 0 or margin_percent >= 100:
            AppMessageBox.information(self, "Missing Data", "Margin % must be between 0 and 99.99.")
            self.margin_input.setFocus()
            self.margin_input.selectAll()
            return
        if pack_cost is not None and pack_cost < 0:
            AppMessageBox.information(self, "Missing Data", "Cost price cannot be negative.")
            self.cost_price_input.setFocus()
            return

        expiry_date = None
        if expiry_text.replace("_", "").replace(" ", "") not in {"", "-", "--"}:
            parsed_expiry = self.parse_expiry_month_year(expiry_text)
            if parsed_expiry is None:
                AppMessageBox.information(self, "Missing Data", "Expiry must be in MM-YY format, for example 04-26.")
                self.expiry_input.setFocus()
                self.expiry_input.selectAll()
                return
            expiry_date = parsed_expiry.toString("yyyy-MM-dd")

        ensure_prescription_schema()
        ensure_product_media_schema()

        try:
            result = save_product_with_opening_stock(
                existing_product_id=self.existing_product_id or self._find_existing_product_id(display_name),
                display_name=display_name,
                manufacturer_id=manufacturer_id,
                discount_group_id=None,
                tax_group_id=None,
                generic_name=formula,
                code=None,
                rack="",
                qty_text=qty_text,
                batch_no=batch_no,
                pack_size=pack_size_text,
                pack_price_text=sale_price_text,
                margin_text=margin_text,
                reorder_level_text="0",
                expiry_date=expiry_date,
                form=form or None,
                strength=dose or None,
                prescription_required=self.prescription_required_check.isChecked(),
                media_removed=self.media_removed,
                selected_media_path=self.selected_media_path,
            )

            self.saved_product_id = int(result["product_id"])
            self.saved_visible_name = ProductSearchBox.format_product_label(display_name, pack_size)
            self.selected_media_info = result.get("media_info") or (
                None if self.media_removed else self.selected_media_info
            )
            self.selected_media_path = ""
            self.media_removed = False
            self.accept()
        except Exception as exc:
            AppMessageBox.critical(self, "Error", f"Failed to save product.\n\n{exc}")


class PrescriptionInfoDialog(QDialog):
    def __init__(self, parent=None, *, product_names=None, existing_payload=None):
        super().__init__(parent)
        self.ignore_requested = False
        self.setWindowTitle("Prescription Information")
        self.setModal(True)
        self.setMinimumWidth(520)

        product_names = [str(name or "").strip() for name in (product_names or []) if str(name or "").strip()]

        self.setStyleSheet("""
            QDialog {
                background: #EEF4F8;
            }
            QFrame#prescriptionHeader {
                background-color: #325D7B;
                border: 1px solid #284B63;
                border-radius: 8px;
            }
            QFrame#prescriptionBody, QFrame#prescriptionFooter {
                background: #FFFFFF;
                border: 1px solid #D3DEE7;
                border-radius: 8px;
            }
            QLineEdit, QDateEdit {
                min-height: 28px;
                padding: 3px 6px;
                border: 1px solid #C7D4DF;
                border-radius: 6px;
                background: #FFFFFF;
                color: #223746;
            }
            QLineEdit:focus, QDateEdit:focus {
                border: 1px solid #5A9EC9;
                background: #F7FBFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header_frame = QFrame()
        header_frame.setObjectName("prescriptionHeader")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(3)

        title = QLabel("Prescription Required")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        header_layout.addWidget(title)

        helper = QLabel("This invoice includes prescription-only medicines. Capture the prescriber details before saving the sale.")
        helper.setWordWrap(True)
        helper.setStyleSheet("font-size: 11px; color: #DDEAF3;")
        header_layout.addWidget(helper)
        layout.addWidget(header_frame)

        body_frame = QFrame()
        body_frame.setObjectName("prescriptionBody")
        body_layout = QVBoxLayout(body_frame)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(10)

        if product_names:
            product_label = QLabel("Prescription items in this invoice")
            product_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #4B5563;")
            body_layout.addWidget(product_label)

            product_value = QLabel(", ".join(product_names))
            product_value.setWordWrap(True)
            product_value.setStyleSheet("font-size: 12px; color: #223746;")
            body_layout.addWidget(product_value)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(10)

        def field_label(text):
            label = QLabel(text)
            label.setStyleSheet("font-size: 11px; font-weight: 700; color: #4B5563;")
            return label

        self.doctor_name_input = QLineEdit()
        self.doctor_name_input.setPlaceholderText("Doctor name")

        self.clinic_name_input = QLineEdit()
        self.clinic_name_input.setPlaceholderText("Clinic / hospital (optional)")

        self.doctor_license_input = QLineEdit()
        self.doctor_license_input.setPlaceholderText("PMDC / license no. (optional)")

        self.prescription_date_input = QDateEdit()
        self.prescription_date_input.setCalendarPopup(True)
        self.prescription_date_input.setDate(QDate.currentDate())
        self.prescription_date_input.setDisplayFormat("dd MMM yyyy")

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Notes (optional)")
        self.attachment_paths = list((existing_payload or {}).get("attachment_source_paths") or [])
        browse_button = QPushButton("Attach Image/PDF")
        browse_button.clicked.connect(self._choose_attachment)
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self._remove_selected_attachment)

        self.attachment_table = QTableWidget()
        self.attachment_table.setColumnCount(1)
        self.attachment_table.setHorizontalHeaderLabels(["Attachment"])
        self.attachment_table.verticalHeader().setVisible(False)
        self.attachment_table.horizontalHeader().setStretchLastSection(True)
        self.attachment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.attachment_table.setSelectionMode(QTableWidget.SingleSelection)
        self.attachment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.attachment_table.setMinimumHeight(110)

        grid.addWidget(field_label("Doctor"), 0, 0)
        grid.addWidget(self.doctor_name_input, 0, 1)
        grid.addWidget(field_label("Prescription Date"), 0, 2)
        grid.addWidget(self.prescription_date_input, 0, 3)
        grid.addWidget(field_label("Clinic"), 1, 0)
        grid.addWidget(self.clinic_name_input, 1, 1, 1, 3)
        grid.addWidget(field_label("License No."), 2, 0)
        grid.addWidget(self.doctor_license_input, 2, 1, 1, 3)
        grid.addWidget(field_label("Notes"), 3, 0)
        grid.addWidget(self.notes_input, 3, 1, 1, 3)
        grid.addWidget(field_label("Attachment"), 4, 0)
        grid.addWidget(self.attachment_table, 4, 1, 1, 2)
        attachment_actions = QVBoxLayout()
        attachment_actions.addWidget(browse_button)
        attachment_actions.addWidget(remove_button)
        attachment_actions.addStretch(1)
        grid.addLayout(attachment_actions, 4, 3)
        body_layout.addLayout(grid)

        layout.addWidget(body_frame)

        footer_frame = QFrame()
        footer_frame.setObjectName("prescriptionFooter")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(12, 10, 12, 10)
        footer_layout.setSpacing(8)
        footer_layout.addStretch(1)

        cancel_button = QPushButton("Cancel")
        ignore_button = QPushButton("Ignore Prescription")
        save_button = QPushButton("Save Prescription Info")
        save_button.setDefault(True)
        footer_layout.addWidget(cancel_button)
        footer_layout.addWidget(ignore_button)
        footer_layout.addWidget(save_button)
        layout.addWidget(footer_frame)

        cancel_button.clicked.connect(self.reject)
        ignore_button.clicked.connect(self._ignore_prescription)
        save_button.clicked.connect(self._submit)

        if existing_payload:
            self.doctor_name_input.setText(str(existing_payload.get("doctor_name") or ""))
            self.clinic_name_input.setText(str(existing_payload.get("clinic_name") or ""))
            self.doctor_license_input.setText(str(existing_payload.get("doctor_license_no") or ""))
            existing_date = str(existing_payload.get("prescription_date") or "").strip()
            if existing_date:
                parsed = QDate.fromString(existing_date, "yyyy-MM-dd")
                if parsed.isValid():
                    self.prescription_date_input.setDate(parsed)
            self.notes_input.setText(str(existing_payload.get("notes") or ""))
        self._refresh_attachment_table()

    def _submit(self):
        if not str(self.doctor_name_input.text() or "").strip():
            AppMessageBox.warning(self, "Missing Data", "Doctor name is required for prescription medicines.")
            self.doctor_name_input.setFocus()
            return
        self.accept()

    def _ignore_prescription(self):
        _, accepted = AppMessageBox.confirm(
            self,
            "Ignore Prescription",
            (
                "Continue without prescription info or attachment?\n\n"
                "This will be logged in the activity log for audit history."
            ),
            confirm_label="Ignore And Continue",
            cancel_label="Cancel",
            kind="warning",
        )
        if not accepted:
            return
        self.ignore_requested = True
        self.accept()

    def _choose_attachment(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Prescription Attachment(s)",
            "",
            "Prescription Files (*.png *.jpg *.jpeg *.webp *.bmp *.pdf);;All Files (*)",
        )
        if not file_paths:
            return
        for file_path in file_paths:
            if file_path and file_path not in self.attachment_paths:
                self.attachment_paths.append(file_path)
        self._refresh_attachment_table()

    def _refresh_attachment_table(self):
        self.attachment_table.setRowCount(0)
        for row_index, file_path in enumerate(self.attachment_paths):
            self.attachment_table.insertRow(row_index)
            self.attachment_table.setItem(row_index, 0, QTableWidgetItem(os.path.basename(file_path)))

    def _remove_selected_attachment(self):
        row = self.attachment_table.currentRow()
        if row < 0 or row >= len(self.attachment_paths):
            return
        self.attachment_paths.pop(row)
        self._refresh_attachment_table()

    def get_payload(self):
        return {
            "doctor_name": str(self.doctor_name_input.text() or "").strip(),
            "clinic_name": str(self.clinic_name_input.text() or "").strip(),
            "doctor_license_no": str(self.doctor_license_input.text() or "").strip(),
            "prescription_date": self.prescription_date_input.date().toString("yyyy-MM-dd"),
            "notes": str(self.notes_input.text() or "").strip(),
            "attachment_source_paths": list(self.attachment_paths),
        }




from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QLineEdit, QCheckBox, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt
import re


class CreateSalesWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # === Main Vertical Layout ===
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(8)
        
        self.scan_timer = QTimer(self)
        self.scan_timer.setSingleShot(True)
        self._pending_scan = None
        self._suppress_enter_once = False
        self.scan_timer.timeout.connect(lambda: self._run_pending_scan())
        self.current_line_product_defaults = {}
        self.line_discount_manual_override = False
        self.line_tax_manual_override = False
        self.current_line_pricing_summary_text = "Line Pricing: Waiting for product selection"
        self.current_sale_prescription_payload = None
        self.current_sale_prescription_ignored = False
        self.minimum_margin_percent = 15.0
        self.pricing_details_dialog = None
        self.pricing_details_line_label = None
        self.pricing_details_header_label = None
        self.pricing_details_global_label = None
        
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reloading_sale = False
        self.order_modified = False
        self.current_hold_sale_id = None
        self.row_height = 40

        

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Receipt", objectName='SectionTitle')
        
        
        clear_btn = QPushButton('Clear Sale', objectName='TopRightButton')
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_fields)
        
        self.heldsales_btn = QPushButton('Held Sales', objectName='TopRightButton')
        self.heldsales_btn.setCursor(Qt.PointingHandCursor)
        self.heldsales_btn.clicked.connect(self.load_hold_orders)
        
        self.invoicelist = QPushButton('SO List', objectName='TopRightButton')
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.heldsales_btn)
        header_layout.addWidget(clear_btn)
        header_layout.addWidget(self.invoicelist)
        
        self.layout.addLayout(header_layout)

        

        # === Customer + Salesman Row ===
        
        self.add_customer_section()
        

        self.add_product_section()
        
        

        self.add_totals_section()
        self._install_select_all_focus_behavior()
        self.layout.addStretch()
        

        
        QShortcut(
            QKeySequence("F12"),
            self,
            activated=lambda: (
                self.received_entry.setFocus(),
                QTimer.singleShot(0, self.received_entry.selectAll)
            )
        )
        
        
        
        QShortcut(QKeySequence("Ctrl+Numpad+"), self, activated=self.add_row)
        


        QShortcut(QKeySequence("Ctrl+Return"), self, activated=lambda: self.save_receipt())
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=lambda: self.save_receipt())  

        
        self.setStyleSheet(load_stylesheets())
        
    
    
    
    
    def clear_product_field(self):
         
        self.item.blockSignals(True)

        self.item.setCurrentIndex(-1)
        self.item.lineEdit().clear()
        self.item.hidePopup()
        self.item.blockSignals(False)
        self.item.setFocus()
       
    
    
    def add_customer_section(self):
        
        # ---------------------------
        # Customer Section Frame
        # ---------------------------
        customer_frame = QFrame()
        customer_frame.setObjectName("sectionCard")
        self.customer_frame = customer_frame

        customer_layout = QVBoxLayout(customer_frame)
        customer_layout.setContentsMargins(12, 8, 12, 4)
        customer_layout.setSpacing(2)

        # Top Row Layout
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        top_row = QHBoxLayout()
        customerlabel = QLabel("CUSTOMER")
        
        self.customer = QComboBox()
        self.customer.setMinimumWidth(170)
               
        self.customer.setEditable(True)
        self.customer.setLineEdit(SelectAllLineEdit())
        self.customer.completer().setCaseSensitivity(Qt.CaseInsensitive)
        self.customer.completer().setFilterMode(Qt.MatchContains)
        
        self.customer.lineEdit().selectionChanged.connect(lambda: None)  # prevents some focus quirks
        self.customer.lineEdit().installEventFilter(self)
        
        self.customer.setInsertPolicy(QComboBox.NoInsert)
        
        self.new_customer_btn = QPushButton("+")
        btn_style = """
        QPushButton {
            background-color: #2d2d2d;
            color: white;
            border: 1px solid #444;
            border-radius: 4px;
            font-weight: 500;
            padding: 2px;
        }

        QPushButton:hover {
            background-color: #3a3a3a;
        }

        QPushButton:pressed {
            background-color: #1f1f1f;
        }
        """

        self.new_customer_btn.setStyleSheet(btn_style)
        self.new_customer_btn.setFixedSize(28, 28)
        
        spacer = QLabel()

        # Add widgets
        top_row.addWidget(customerlabel, 1)
        top_row.addWidget(self.customer, 2)
        top_row.addWidget(self.new_customer_btn)
        top_row.addWidget(spacer, 5)
        
        main_final_label = QLabel("Final Amount")
        main_final_label.setStyleSheet("font-weight: 500; font-size: 13px;")   
        
             
        self.main_final_amount = QLabel("0.00")
        self.main_final_amount.setStyleSheet("font-weight: 700; font-size: 18px;")
        top_row.addWidget(main_final_label)
        top_row.addWidget(self.main_final_amount)
        
        self.new_customer_btn.clicked.connect(self.open_customer_dialog)
        self.customer.currentIndexChanged.connect(self.update_customer_credit_summary)
        self.customer.currentIndexChanged.connect(self.apply_customer_pricing_groups)

        self.active_discount_group_id = None
        self.active_discount_group_name = ""
        self.active_discount_percent = 0.0
        self.active_discount_fixed_amount = 0.0
        self.active_discount_apply_on_sale = False
        self.active_discount_source = "none"
        self.active_tax_group_id = None
        self.active_tax_group_name = ""
        self.active_tax_percent = 0.0
        self.current_sale_prescription_payload = None
        self.active_tax_fixed_amount = 0.0
        self.active_tax_apply_on_sale = False
        self.active_tax_source = "none"
        self.active_tax_fixed_amount = 0.0
        self.active_tax_apply_on_sale = False
        self.active_tax_source = "none"
        self.sales_discount_policy = "both"
        self.sales_tax_policy = "both"
        self.discount_group_manual_override = False
        self.tax_group_manual_override = False
        
        
        customer_layout.addLayout(top_row)

        self.global_pricing_status = QLabel()
        self.global_pricing_status.setWordWrap(False)
        self.global_pricing_status.setStyleSheet(
            "color: #3F5F75; font-size: 10px; font-weight: 700; padding-left: 0; margin: 0;"
        )
        self.global_pricing_status.setContentsMargins(0, 0, 0, 0)
        self.global_pricing_status.hide()

        self.update_customer_credit_summary()
        self.apply_customer_pricing_groups()

        # Add frame to main layout
        self.layout.addWidget(customer_frame, 0, Qt.AlignTop)
        
        self.customer.setStyleSheet("font-weight: 600;")
        
        

        
    def open_customer_dialog(self):
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Customer")
        dialog.setMinimumWidth(350)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("New Customer")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        name_label = QLabel("Customer Name")
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Enter customer name")

        contact_label = QLabel("Contact")
        contact_edit = QLineEdit()
        contact_edit.setPlaceholderText("Enter contact")

        layout.addWidget(name_label)
        layout.addWidget(name_edit)
        layout.addWidget(contact_label)
        layout.addWidget(contact_edit)

        btn_row = QHBoxLayout()

        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        def save_customer():
            name = name_edit.text().strip()
            contact = contact_edit.text().strip()

            if not name:
                AppMessageBox.warning(dialog, "Validation Error", "Customer name is required.")
                return

            try:
                customer_id = create_sales_customer(name=name, contact=contact)
            except ValueError as exc:
                AppMessageBox.warning(dialog, "Validation Error", str(exc))
                return
            except Exception as exc:
                AppMessageBox.critical(
                    dialog,
                    "Database Error",
                    str(exc)
                )
                return

            AppMessageBox.information(dialog, "Success", "Customer added successfully.")
            dialog.accept()

            if hasattr(self, "populate_customers"):
                self.populate_customers(selected_customer_id=customer_id)


        save_btn.clicked.connect(save_customer)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()


    
    def add_table(self):
        
        self.row_height = 30

        self.table = MyTable(column_ratios=[0.05, 0.35, 0.08, 0.08, 0.08, 0.08, 0.08, 0.03])
        headers = ["#", " Product ", " Qty", "Rate", "Disc", "Tax %", "Total", "X"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        self.table.setTabKeyNavigation(False)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumWidth(780)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        visible_rows = 6
        header_height = self.table.horizontalHeader().height()

        table_height = header_height + (self.row_height * visible_rows) + 2
        self.table.setMinimumHeight(table_height)

        return self.table 
        
    
    def add_product_section(self):
        
        product_frame = QFrame()
        product_frame.setObjectName("sectionCard")
        self.product_frame = product_frame
        
        product_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        
        product_entry_layout = QVBoxLayout(product_frame)
        product_entry_layout.setContentsMargins(12, 8, 12, 8)
        product_entry_layout.setSpacing(2)
        self.product_entry_layout = product_entry_layout
        
        product_entry_layout.setAlignment(Qt.AlignTop)
        
        field_style = """
            QLabel {
                margin: 0;
                font-size: 12px;
                letter-spacing: 0.2px;
                margin-right: 5px;
            }

            QLineEdit {
                margin: 0;
                padding: 5px 4px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 12px;
                letter-spacing: 0.2px;
                background-color: #fbfcfd;
                color: #223746;
            }

            QComboBox {
                margin: 0;
                padding: 5px 4px;
                padding-right: 24px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 12px;
                letter-spacing: 0.2px;
                background-color: #fbfcfd;
                color: #223746;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border: none;
                border-left: 1px solid #d8e0e6;
                background-color: #f1f5f8;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }

            QComboBox::down-arrow {
                image: url(res/rail_icons/chevron_down.svg);
                width: 12px;
                height: 12px;
            }
            
            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus {
                border: 1px solid #5B8FB8;
                background: #F2F8FC;
            }

            KeyUpLineEdit {
                margin: 0;
                padding: 5px 4px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 12px;
                letter-spacing: 0.2px;
                background-color: #fbfcfd;
                color: #223746;
            }
        """

        
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(2)
        grid.setContentsMargins(0, 8, 0, 8)
        self.entry_grid = grid

        palette = get_theme_palette()
        info_bg = palette.get("primary_main", "#2F5D7C")
        info_bg = palette.get("primary_light", "#DCEAF5")
        info_border = palette.get("primary_soft_border", "#B7CCDD")
        info_text = palette.get("primary_deep_text", "#1F445D")

        info_strip = QFrame()
        info_strip.setObjectName("LineInfoStrip")
        info_strip.setStyleSheet(
            f"""
            QFrame#LineInfoStrip {{
                background-color: {info_bg};
                border: 1px solid {info_border};
                border-radius: 6px;
            }}
            """
        )
        info_strip_layout = QHBoxLayout(info_strip)
        info_strip_layout.setContentsMargins(10, 7, 10, 7)
        info_strip_layout.setSpacing(12)

        self.line_info_formula_label = QLabel("Formula: Waiting for product selection")
        self.line_info_formula_label.setWordWrap(False)
        self.line_info_formula_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.line_info_formula_label.setStyleSheet(
            f"color: {info_text}; font-size: 11px; font-weight: 700; padding-left: 0; margin: 0;"
        )
        self.line_info_cost_sale_label = QLabel("Cost: - | Sale: -")
        self.line_info_cost_sale_label.setWordWrap(False)
        self.line_info_cost_sale_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.line_info_cost_sale_label.setStyleSheet(
            f"color: {info_text}; font-size: 11px; font-weight: 700; padding-left: 0; margin: 0;"
        )
        self.line_info_profit_label = QLabel("Profit: -")
        self.line_info_profit_label.setWordWrap(False)
        self.line_info_profit_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.line_info_profit_label.setStyleSheet(
            f"color: {info_text}; font-size: 11px; font-weight: 700; padding-left: 0; margin: 0;"
        )
        self.line_info_margin_label = QLabel("Margin: -")
        self.line_info_margin_label.setWordWrap(False)
        self.line_info_margin_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.line_info_margin_label.setStyleSheet(
            f"color: {info_text}; font-size: 11px; font-weight: 700; padding-left: 0; margin: 0;"
        )
        self.line_info_prescription_badge = QLabel("RX REQUIRED")
        self.line_info_prescription_badge.setVisible(False)
        self.line_info_prescription_badge.setStyleSheet(
            "background-color: #FFF1F2; color: #B42318; border: 1px solid #FECACA; "
            "border-radius: 10px; padding: 3px 8px; font-size: 11px; font-weight: 700;"
        )

        info_strip_layout.addWidget(self.line_info_formula_label, 4)
        info_strip_layout.addSpacing(6)
        info_strip_layout.addWidget(self.line_info_cost_sale_label, 2)
        info_strip_layout.addSpacing(6)
        info_strip_layout.addWidget(self.line_info_profit_label, 1)
        info_strip_layout.addSpacing(6)
        info_strip_layout.addWidget(self.line_info_margin_label, 2)
        info_strip_layout.addSpacing(6)
        info_strip_layout.addWidget(self.line_info_prescription_badge, 0)
        product_entry_layout.addWidget(info_strip)
        product_entry_layout.addSpacing(4)

        # -----------------------------
        # Labels
        # -----------------------------
        
        info_box_layout = QHBoxLayout()
        
        info_btn = QPushButton("?")
        info_btn.setObjectName("PricingInfoButton")
        info_btn.setFixedSize(32, 32)
        info_btn.setCursor(Qt.PointingHandCursor)
        info_btn.setStyleSheet(
            """
            QPushButton#PricingInfoButton {
                background-color: #EFF5FA;
                color: #2F5D7C;
                border: 1px solid #C8D8E5;
                border-radius: 16px;
                font-size: 13px;
                font-weight: 700;
                padding: 0;
            }
            QPushButton#PricingInfoButton:hover {
                background-color: #DDECF7;
                border-color: #9FBCD3;
                color: #1F445D;
            }
            QPushButton#PricingInfoButton:pressed {
                background-color: #CFE3F2;
            }
            """
        )
        info_btn.setToolTip("Show pricing details")
        info_btn.clicked.connect(self.show_pricing_details_dialog)
        self.line_pricing_info_btn = info_btn
        
        info_box_layout.addWidget(info_btn)
        self.entry_info_box_layout = info_box_layout
        
        grid.addLayout(info_box_layout, 0 , 0)

        
        product_box_layout = QHBoxLayout()
        product_box_layout.setContentsMargins(0, 0, 6, 0)
        product_box_layout.setSpacing(6)
        
        product_label = QLabel("PRODUCT")
        product_label.setStyleSheet(field_style)
        
        
        self.item = ProductSearchBox(self, query_fn=self._sales_product_query_fn, placeholder="select product", defer_numeric_to_enter=True)
        self.item.wheelEvent = lambda event: event.ignore()
        self.item.setLineEdit(SelectAllLineEdit())
        self.item.lineEdit().textEdited.connect(self.force_uppercase)
        self.item.lineEdit().returnPressed.connect(
            lambda: QTimer.singleShot(0, self.handle_product_enter)
        )
        QShortcut(
            QKeySequence(Qt.Key_Escape),
            self.item,
            activated=self.clear_product_field
        )
        self.item.product_selected_with_data.connect(
            lambda pid, name, data, c=self.item: self.on_completer_selected(name, c, data)
        )
        self.item.setStyleSheet(field_style)
        self.quick_add_product_btn = QPushButton("+", objectName="EntryButton")
        self.quick_add_product_btn.setMinimumSize(38, 34)
        self.quick_add_product_btn.setStyleSheet(
            """
            QPushButton#EntryButton {
                font-size: 18px;
                font-weight: 900;
                padding: 0 8px 2px 8px;
            }
            """
        )
        self.quick_add_product_btn.setToolTip("Quick add product with opening stock")
        self.quick_add_product_btn.clicked.connect(
            lambda: self.open_sales_product_quick_add_dialog(self.item.lineEdit().text())
        )
        
        product_box_layout.addWidget(product_label, 0)
        product_box_layout.addWidget(self.item, 1)
        product_box_layout.addWidget(self.quick_add_product_btn, 0)
        
        grid.addLayout(product_box_layout, 0, 1)
        
        
        
        
        qty_box_layout = QHBoxLayout()
        
        qty_label = QLabel("QTY")
        qty_label.setStyleSheet(field_style)
        
        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText("qty")
        self.qty_edit.setStyleSheet(field_style)
        qty_box_layout.addWidget(qty_label)
        qty_box_layout.addWidget(self.qty_edit)
        
        grid.addLayout(qty_box_layout, 0, 2)
        
        
        
        
        rate_box_layout = QHBoxLayout()

        rate_label = QLabel("PRICE")
        rate_label.setStyleSheet(field_style)
        
        self.rate_edit = QLineEdit()
        self.rate_edit.setPlaceholderText("rate")
        self.rate_edit.setStyleSheet(field_style)
        rate_box_layout.addWidget(rate_label)
        rate_box_layout.addWidget(self.rate_edit)
        
        grid.addLayout(rate_box_layout, 0, 3)
        

        # ---- DISC % ----
        discount_box_layout = QHBoxLayout()
        discount_box_layout.setSpacing(6)

        discount_label = QLabel("DISC %")
        discount_label.setStyleSheet(field_style)
        self.entry_discount_label = discount_label

        self.discount = KeyUpLineEdit()
        self.discount.setPlaceholderText("Disc %")
        self.discount.setStyleSheet(field_style)
        self.discount_mode_combo = QComboBox()
        self.discount_mode_combo.addItem("%", "percent")
        self.discount_mode_combo.addItem("Amt", "amount")
        self.discount_mode_combo.setStyleSheet(field_style)
        self.discount_mode_combo.setFixedWidth(62)

        discount_box_layout.addWidget(discount_label)
        discount_box_layout.addWidget(self.discount)
        discount_box_layout.addWidget(self.discount_mode_combo)
        self.discount_box_layout = discount_box_layout

        grid.addLayout(discount_box_layout, 0, 4)



        # ---- TAX % ----
        tax_box_layout = QHBoxLayout()
        tax_box_layout.setSpacing(6)

        tax_label = QLabel("TAX %")
        tax_label.setStyleSheet(field_style)
        self.entry_tax_label = tax_label

        self.tax = KeyUpLineEdit()
        self.tax.setPlaceholderText("Tax %")
        self.tax.setStyleSheet(field_style)
        tax_box_layout.addWidget(tax_label)
        tax_box_layout.addWidget(self.tax)
        self.tax_box_layout = tax_box_layout

        grid.addLayout(tax_box_layout, 0, 5)


        # ---- TOTAL ----
        total_box_layout = QHBoxLayout()
        total_box_layout.setSpacing(6)

        total_label = QLabel("TOTAL")
        total_label.setStyleSheet(field_style)
        self.entry_total_label = total_label

        self.amount_edit = QLineEdit()
        self.amount_edit.setReadOnly(True)
        self.amount_edit.setText("0.00")
        self.amount_edit.setStyleSheet(field_style)
        total_box_layout.addWidget(total_label)
        total_box_layout.addWidget(self.amount_edit)
        self.total_box_layout = total_box_layout

        grid.addLayout(total_box_layout, 0, 6)


        # ---- ACTION ----
        add_button = QPushButton("+", objectName="EntryButton")
        add_button.setMinimumHeight(34)
        add_button.setMinimumWidth(92)
        add_button.setStyleSheet(
            """
            QPushButton#EntryButton {
                font-size: 20px;
                font-weight: 800;
                padding: 0 12px 2px 12px;
            }
            """
        )
        add_button.clicked.connect(self.add_row)
        self.add_line_button = add_button

        self.reset_line_defaults_btn = QPushButton("Reset", objectName="EntryButton")
        self.reset_line_defaults_btn.clicked.connect(self.reset_current_line_defaults)

        action_box_layout = QHBoxLayout()
        action_box_layout.setContentsMargins(8, 6, 6, 6)
        action_box_layout.setSpacing(6)
        action_box_layout.addWidget(add_button)
        action_box_layout.addWidget(self.reset_line_defaults_btn)
        self.action_box_layout = action_box_layout

        grid.addLayout(action_box_layout, 0, 7)

        qty_filter = QtyValidationFilter(self, self.qty_edit, self.item)
        self.qty_edit.installEventFilter(qty_filter)

        # important: keep reference
        if not hasattr(self, "qty_filters"):
            self.qty_filters = []
        self.qty_filters.append(qty_filter)
        
        
        
        
        self.qty_edit.returnPressed.connect(self.advance_after_qty_entry)
        self.rate_edit.returnPressed.connect(lambda: self.focus_next_field(self.add_line_button))
        self.discount.returnPressed.connect(lambda: self.focus_next_field(self.tax))
        self.tax.returnPressed.connect(lambda: self.focus_next_field(self.add_line_button))
        

        self.qty_edit.textChanged.connect(self.update_line_total)
        self.rate_edit.textChanged.connect(self.update_line_total)

        self.discount.textChanged.connect(self.update_line_total)
        self.tax.textChanged.connect(self.update_line_total)
        self.discount.textEdited.connect(self.on_line_discount_edited)
        self.tax.textEdited.connect(self.on_line_tax_edited)
        self.discount_mode_combo.currentIndexChanged.connect(self.on_discount_mode_changed)
        
        
        
        
        
        # -----------------------------
        # Stretch factors
        # -----------------------------
        ratios = [5, 35, 8, 8, 8, 8, 8, 3]

        for col, r in enumerate(ratios):
            grid.setColumnStretch(col, r)

        

        product_entry_layout.addLayout(grid)
        product_entry_layout.addSpacing(0)
        self.apply_fast_entry_layout()

        table = self.add_table()
        product_entry_layout.addWidget(table)

        self.layout.addWidget(product_frame)
    
    
    
    
    def clear_product_field(self):
        
        self.item.blockSignals(True)

        self.item.setCurrentIndex(-1)
        self.item.lineEdit().clear()
        self.item.hidePopup()
        self.item.blockSignals(False)
        self.item.setFocus()
        self.current_line_product_defaults = {}
        self.line_discount_manual_override = False
        self.line_tax_manual_override = False
        self.current_line_pricing_summary_text = "Line Pricing: Waiting for product selection"
        if hasattr(self, "line_info_formula_label"):
            self._set_line_info_labels(
                formula_text="Formula: Waiting for product selection",
                cost_sale_text="Cost: - | Sale: -",
                profit_text="Profit: -",
                margin_text=f"Margin: - (Target: {self.minimum_margin_percent:.0f}%)",
            )
        self.refresh_pricing_details_dialog()
    
    
    
    
    def add_totals_section(self):
    
        totals_frame = QFrame()
        totals_frame.setObjectName("sectionCard")
        self.totals_frame = totals_frame

        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setContentsMargins(6, 8, 6, 8)
        totals_layout.setSpacing(6)

        main_grid = QGridLayout()
        main_grid.setHorizontalSpacing(12)
        main_grid.setVerticalSpacing(8)

        label_style = """
        QLabel {
            font-size: 11px;
            color: #555;
            font-weight: 600;
            padding-left: 0;
        }
        """

        # -----------------------------
        # Create labels
        # -----------------------------
        gross_label = QLabel("Subtotal")
        discount_label = QLabel("Discount")
        tax_label = QLabel("Tax")
        additional_label = QLabel("Extra Charges")
        taxable_label = QLabel("Taxable")
        net_amount_label = QLabel("Net")
        line_discount_label = QLabel("Line Disc")
        line_tax_label = QLabel("Line Tax")

        received_label = QLabel("Received")
        received_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        received_label.setStyleSheet("font-size: 14px; font-weight: 600;")

        payment_method_label = QLabel("Payment Method")
        due_date_label = QLabel("Due Date")
        remaining_label = QLabel("Remaining")
        change_label = QLabel("Change")

        gross_label.setStyleSheet(label_style)
        discount_label.setStyleSheet(label_style)
        taxable_label.setStyleSheet(label_style)
        tax_label.setStyleSheet(label_style)
        net_amount_label.setStyleSheet(label_style)
        additional_label.setStyleSheet(label_style)
        line_discount_label.setStyleSheet(label_style)
        line_tax_label.setStyleSheet(label_style)
        payment_method_label.setStyleSheet(label_style)
        due_date_label.setStyleSheet(label_style)
        remaining_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        remaining_label.setStyleSheet(label_style)
        change_label.setStyleSheet(label_style)

        # Top-row alignment: first label remains left, next three align right.
        discount_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tax_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        additional_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Second-row alignment: keep first label left, right-align the next three.
        line_tax_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        taxable_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        net_amount_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Keep a consistent footprint across the left 700px section.
        for lbl in (
            gross_label,
            discount_label,
            tax_label,
            additional_label,
            line_discount_label,
            line_tax_label,
            taxable_label,
            net_amount_label,
            due_date_label,
            payment_method_label,
        ):
            lbl.setMinimumWidth(72)

        # -----------------------------
        # Create fields
        # -----------------------------
        self.gross_entry = QLineEdit("0.00")
        self.gross_entry.setReadOnly(True)

        self.discount_entry = QLineEdit()

        self.tax_entry = QLineEdit()

        self.additional_entry = QLineEdit()

        self.gross_entry.setMinimumWidth(60)
        self.discount_entry.setMinimumWidth(60)
        self.tax_entry.setMinimumWidth(60)
        self.additional_entry.setMinimumWidth(60)

        self.taxable_entry = QLineEdit("0.00")
        self.taxable_entry.setReadOnly(True)

        self.net_amount_entry = QLineEdit("0.00")
        self.net_amount_entry.setReadOnly(True)

        self.line_discount_total_entry = QLineEdit("0.00")
        self.line_discount_total_entry.setReadOnly(True)

        self.line_tax_total_entry = QLineEdit("0.00")
        self.line_tax_total_entry.setReadOnly(True)

        self.line_discount_total_entry.setMinimumWidth(60)
        self.line_tax_total_entry.setMinimumWidth(60)
        self.taxable_entry.setMinimumWidth(60)
        self.net_amount_entry.setMinimumWidth(60)

        self.header_discount_source_label = QLabel("Source: Manual / None")
        self.header_discount_source_label.setStyleSheet("color: #6B7F8F; font-size: 10px; font-weight: 600; padding-left: 0;")
        self.header_tax_source_label = QLabel("Source: Manual / None")
        self.header_tax_source_label.setStyleSheet("color: #6B7F8F; font-size: 10px; font-weight: 600; padding-left: 0;")

        self.final_amount_entry = QLabel("0.00")
        self.final_amount_entry.setObjectName("FinalAmount")
        self.final_amount_entry.setAlignment(Qt.AlignCenter)
        self.final_amount_entry.setMinimumHeight(38)
        self.final_amount_entry.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1F2933; "
            "background-color: #EEF4F8; border-radius: 10px; padding: 6px 12px;"
        )

        self.received_entry = QLineEdit("0.00")
        self.received_entry.setObjectName("ReceivedAmount")
        self.received_entry.setMinimumWidth(92)
        
        self.change_entry = QLineEdit("0.00")
        self.change_entry.setReadOnly(True)

        self.remainingdata = QLineEdit("0.00")
        self.remainingdata.setReadOnly(True)
        self.remainingdata.setMinimumWidth(92)

        self.writeoff_check = QCheckBox("Write-off Remaining")
        self.writeoff_check.setStyleSheet("QCheckBox { color: #333; font-size: 11px; }")
        self.writeoff_check.setChecked(True)
        self.auto_print_check = QCheckBox("Auto Print")
        self.auto_print_check.setStyleSheet("QCheckBox { color: #333; font-size: 11px; }")
        self.auto_print_check.setChecked(True)

        self.payment_handler = PaymentMethodHandler(self)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        self.payment_method.setMinimumWidth(60)

        self.due_date_combo = QComboBox()
        self.due_date_combo.addItems(["None", "+15 days", "+30 days", "+45 days", "+60 days", "+90 days"])
        self.due_date_combo.setCurrentText("None")
        self.due_date_combo.setEnabled(False)
        
        self.gross_entry.setAlignment(Qt.AlignRight)
        self.discount_entry.setAlignment(Qt.AlignRight)
        self.tax_entry.setAlignment(Qt.AlignRight)
        self.additional_entry.setAlignment(Qt.AlignRight)
        self.line_discount_total_entry.setAlignment(Qt.AlignRight)
        self.line_tax_total_entry.setAlignment(Qt.AlignRight)
        self.taxable_entry.setAlignment(Qt.AlignRight)
        self.net_amount_entry.setAlignment(Qt.AlignRight)
        self.received_entry.setAlignment(Qt.AlignRight)
        self.remainingdata.setAlignment(Qt.AlignRight)

        # -----------------------------
        # Signals
        # -----------------------------
        self.discount_entry.textChanged.connect(self.update_total_amount)
        self.tax_entry.textChanged.connect(self.update_total_amount)
        self.additional_entry.textChanged.connect(self.update_total_amount)
        self.discount_entry.textEdited.connect(self.on_discount_entry_edited)
        self.tax_entry.textEdited.connect(self.on_tax_entry_edited)
        self.discount_entry.editingFinished.connect(self.on_discount_entry_finished)
        self.tax_entry.editingFinished.connect(self.on_tax_entry_finished)
        self.additional_entry.editingFinished.connect(self.on_additional_entry_finished)
        self.received_entry.textChanged.connect(self.calculate_payment)
        self.received_entry.textChanged.connect(self.update_due_date_availability)
        self.writeoff_check.toggled.connect(self.update_due_date_availability)

        left_grid = QGridLayout()
        left_grid.setContentsMargins(10, 10, 10, 10)
        left_grid.setHorizontalSpacing(6)
        left_grid.setVerticalSpacing(8)
        left_grid.addWidget(gross_label, 0, 0)
        left_grid.addWidget(self.gross_entry, 0, 1)
        left_grid.addWidget(discount_label, 0, 2)
        left_grid.addWidget(self.discount_entry, 0, 3)
        left_grid.addWidget(tax_label, 0, 4)
        left_grid.addWidget(self.tax_entry, 0, 5)
        left_grid.addWidget(additional_label, 0, 6)
        left_grid.addWidget(self.additional_entry, 0, 7)
        left_grid.addWidget(line_discount_label, 1, 0)
        left_grid.addWidget(self.line_discount_total_entry, 1, 1)
        left_grid.addWidget(line_tax_label, 1, 2)
        left_grid.addWidget(self.line_tax_total_entry, 1, 3)
        left_grid.addWidget(taxable_label, 1, 4)
        left_grid.addWidget(self.taxable_entry, 1, 5)
        left_grid.addWidget(net_amount_label, 1, 6)
        left_grid.addWidget(self.net_amount_entry, 1, 7)
        left_grid.addWidget(due_date_label, 2, 4)
        left_grid.addWidget(self.due_date_combo, 2, 5)
        left_grid.addWidget(payment_method_label, 2, 6)
        left_grid.addWidget(self.payment_method, 2, 7)
        left_grid.setColumnMinimumWidth(0, 72)
        left_grid.setColumnMinimumWidth(1, 56)
        left_grid.setColumnMinimumWidth(2, 72)
        left_grid.setColumnMinimumWidth(3, 56)
        left_grid.setColumnMinimumWidth(4, 72)
        left_grid.setColumnMinimumWidth(5, 56)
        left_grid.setColumnMinimumWidth(6, 72)
        left_grid.setColumnMinimumWidth(7, 56)
        left_grid.setColumnStretch(1, 1)
        left_grid.setColumnStretch(3, 1)
        left_grid.setColumnStretch(5, 1)
        left_grid.setColumnStretch(7, 1)

        right_grid = QGridLayout()
        right_grid.setHorizontalSpacing(10)
        right_grid.setVerticalSpacing(8)
        right_grid.addWidget(self.final_amount_entry, 0, 0, 1, 2)
        right_grid.addWidget(received_label, 0, 2)
        right_grid.addWidget(self.received_entry, 0, 3)

        right_grid.addWidget(remaining_label, 1, 2)
        right_grid.addWidget(self.remainingdata, 1, 3)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(10)
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.auto_print_check)
        checkbox_layout.addWidget(self.writeoff_check)
        right_grid.addLayout(checkbox_layout, 2, 0, 1, 4)
        right_grid.setColumnMinimumWidth(0, 84)
        right_grid.setColumnMinimumWidth(2, 104)
        right_grid.setColumnMinimumWidth(3, 92)
        right_grid.setColumnStretch(1, 1)
        right_grid.setColumnStretch(3, 1)

        left_section = QFrame()
        left_section.setObjectName("TotalsLeftSection")
        left_section.setMinimumWidth(0)
        left_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_section_layout = QVBoxLayout(left_section)
        left_section_layout.setContentsMargins(0, 0, 0, 0)
        left_section_layout.setSpacing(0)
        left_section_layout.addLayout(left_grid)
        right_section = QFrame()
        right_section.setObjectName("TotalsRightSection")
        right_section.setMinimumWidth(260)
        right_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_section_layout = QVBoxLayout(right_section)
        right_section_layout.setContentsMargins(8, 10, 8, 10)
        right_section_layout.setSpacing(0)
        right_section_layout.addLayout(right_grid)

        main_grid.addWidget(left_section, 0, 0)
        section_gap = QSpacerItem(4, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        main_grid.addItem(section_gap, 0, 1)
        main_grid.addWidget(right_section, 0, 2)
        main_grid.setColumnStretch(0, 6)
        main_grid.setColumnStretch(2, 4)

        totals_layout.addLayout(main_grid)

        # -----------------------------
        # Add totals frame
        # -----------------------------
        self.layout.addWidget(totals_frame, 0)

        # -----------------------------
        # Save Button
        # -----------------------------
        save_row = QHBoxLayout()
        addreceipt = QPushButton("Save Sales Receipt", objectName="SaveButton")
        addreceipt.setCursor(Qt.PointingHandCursor)
        addreceipt.setMinimumHeight(36)
        addreceipt.clicked.connect(lambda: self.save_receipt())
        save_row.addWidget(addreceipt, 1)

        self.layout.addLayout(save_row, 0)
        
        
    
    
            
        
    def focus_next_field(self, widget):
        widget.setFocus()

        if hasattr(widget, "selectAll"):
            widget.selectAll()

    def apply_fast_entry_layout(self):
        hidden_widgets = [
            getattr(self, "line_pricing_info_btn", None),
            getattr(self, "entry_discount_label", None),
            getattr(self, "discount", None),
            getattr(self, "discount_mode_combo", None),
            getattr(self, "entry_tax_label", None),
            getattr(self, "tax", None),
            getattr(self, "entry_total_label", None),
            getattr(self, "amount_edit", None),
            getattr(self, "reset_line_defaults_btn", None),
        ]

        for widget in hidden_widgets:
            if widget is not None:
                widget.hide()

        for layout in [
            getattr(self, "entry_info_box_layout", None),
            getattr(self, "discount_box_layout", None),
            getattr(self, "tax_box_layout", None),
            getattr(self, "total_box_layout", None),
            getattr(self, "action_box_layout", None),
        ]:
            if layout is not None:
                layout.setContentsMargins(0, 0, 0, 0)

        if hasattr(self, "entry_grid"):
            compact_ratios = [0, 44, 10, 12, 0, 0, 0, 8]
            for col, ratio in enumerate(compact_ratios):
                self.entry_grid.setColumnStretch(col, ratio)

    def _install_select_all_focus_behavior(self):
        widgets = [
            getattr(self, "customer", None),
            getattr(self, "item", None),
            getattr(self, "qty_edit", None),
            getattr(self, "rate_edit", None),
            getattr(self, "discount", None),
            getattr(self, "tax", None),
            getattr(self, "discount_mode_combo", None),
            getattr(self, "discount_entry", None),
            getattr(self, "tax_entry", None),
            getattr(self, "additional_entry", None),
            getattr(self, "received_entry", None),
            getattr(self, "payment_method", None),
            getattr(self, "due_date_combo", None),
        ]

        for widget in widgets:
            if widget is None:
                continue
            widget.installEventFilter(self)
            line_edit = getattr(widget, "lineEdit", None)
            if callable(line_edit):
                child = line_edit()
                if child is not None:
                    child.installEventFilter(self)

    def _clean_numeric_text(self, value):
        text = "" if value is None else str(value).strip()
        if not text:
            return ""

        text = text.replace(",", "")
        text = re.sub(r"[^0-9.\-]", "", text)

        if text.count(".") > 1:
            first_dot = text.find(".")
            text = text[:first_dot + 1] + text[first_dot + 1:].replace(".", "")

        if text in {"", "-", ".", "-."}:
            return ""

        return text

    def _float_or_default(self, value, default=0.0):
        cleaned = self._clean_numeric_text(value)
        if not cleaned:
            return float(default)
        try:
            return float(cleaned)
        except (TypeError, ValueError):
            return float(default)

    def _int_or_default(self, value, default=0):
        return int(self._float_or_default(value, default))

    def _parse_float_field(self, value, field_name, default=0.0, allow_blank=True):
        raw = "" if value is None else str(value).strip()
        cleaned = self._clean_numeric_text(raw)

        if cleaned == "":
            if allow_blank:
                return float(default)
            raise Exception(f"Invalid {field_name}: value is empty.")

        try:
            return float(cleaned)
        except (TypeError, ValueError):
            raise Exception(f"Invalid {field_name}: {raw}")

    def _parse_int_field(self, value, field_name, default=0, allow_blank=True):
        parsed = self._parse_float_field(value, field_name, default=default, allow_blank=allow_blank)
        return int(parsed)

    def _text_or_none(self, value):
        text = str(value).strip() if value is not None else ""
        return text if text else None

    def _normalize_payment_data(self, payment):
        payment = dict(payment or {})
        return {
            "payment_method": self._text_or_none(payment.get("payment_method")) or "Cash",
            "bank_name": self._text_or_none(payment.get("bank_name")),
            "account_no": self._text_or_none(payment.get("account_no")),
            "transaction_mode": self._text_or_none(payment.get("transaction_mode")),
            "wallet_provider": self._text_or_none(payment.get("wallet_provider")),
            "wallet_no": self._text_or_none(payment.get("wallet_no")),
            "payment_reference": self._text_or_none(payment.get("payment_reference")),
        }

    def has_auto_price_for_current_row(self):
        product_data = self.item.currentData()
        if not isinstance(product_data, dict):
            return False

        try:
            unit_price = float(product_data.get("unit_price") or 0.0)
        except (TypeError, ValueError):
            unit_price = 0.0

        return unit_price > 0

    def advance_after_qty_entry(self):
        self.focus_next_field(self.rate_edit)
        

    
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            if isinstance(obj, QLineEdit) and not obj.isReadOnly():
                if event.reason() != Qt.PopupFocusReason:
                    QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)
    
    
    
    
    
    def on_payment_method_changed(self, method):
        
        success = self.payment_handler.handle_method_change(method)

        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)
   




    def update_line_total(self):
        qty_text = self.qty_edit.text().strip() or "0"
        rate_text = self.rate_edit.text().strip() or "0.00"
        discount_text = self.discount.text().strip() or "0.00"
        tax_text = self.tax.text().strip() or "0.00"
        discount_mode = self.discount_mode_combo.currentData() if hasattr(self, "discount_mode_combo") else "percent"

        try:
            qty = float(qty_text)
        except ValueError:
            qty = 0.0

        try:
            rate = float(rate_text)
        except ValueError:
            rate = 0.0

        resolved = self.resolve_line_pricing(
            qty,
            rate,
            discount_text,
            discount_mode,
            tax_text,
            self.current_line_product_defaults.get("discount_fixed_amount", 0.0),
            self.current_line_product_defaults.get("discount_apply_on_sale", True),
            self.current_line_product_defaults.get("tax_fixed_amount", 0.0),
            self.current_line_product_defaults.get("tax_apply_on_sale", True),
        )
        self.amount_edit.setText(f"{resolved['line_total']:.2f}")
        self.update_current_line_margin_indicator()
        self.update_line_pricing_hint()
        
      


    
    
    def keyPressEvent(self, event):
        # Check if Ctrl is pressed AND key is K
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_H:
            self.put_sale_on_hold()
        
        elif event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_L:
            self.load_hold_orders()
        
            
        else:
            super().keyPressEvent(event)  # Propagate if not handled

    def resolve_line_pricing(
        self,
        qty,
        rate,
        discount_text,
        discount_mode,
        tax_text,
        discount_fixed_amount=0.0,
        discount_apply_on_sale=True,
        tax_fixed_amount=0.0,
        tax_apply_on_sale=True,
    ):
        return compute_line_pricing(
            qty=qty,
            rate=rate,
            discount_text=discount_text,
            discount_mode=discount_mode,
            tax_text=tax_text,
            discount_fixed_amount=discount_fixed_amount,
            discount_apply_on_sale=discount_apply_on_sale,
            line_discount_enabled=self._line_discount_enabled_by_policy(),
            tax_fixed_amount=tax_fixed_amount,
            tax_apply_on_sale=tax_apply_on_sale,
            line_tax_enabled=self._line_tax_enabled_by_policy(),
        )

    def on_line_discount_edited(self):
        self.line_discount_manual_override = True
        self.update_line_pricing_hint()

    def on_line_tax_edited(self):
        self.line_tax_manual_override = True
        self.update_line_pricing_hint()

    def show_pricing_details_dialog(self):
        if self.pricing_details_dialog is not None:
            self.refresh_pricing_details_dialog()
            self.pricing_details_dialog.raise_()
            self.pricing_details_dialog.activateWindow()
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Pricing Details")
        dialog.setModal(False)
        dialog.resize(760, 260)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Sales Pricing Breakdown")
        title.setStyleSheet("font-size: 16px; font-weight: 700; padding-left: 0;")
        layout.addWidget(title)

        hint = QLabel(
            "This view explains the current line pricing defaults, header pricing sources, and any active global pricing."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #667788; font-size: 11px; padding-left: 0;")
        layout.addWidget(hint)

        self.pricing_details_line_label = QLabel()
        self.pricing_details_line_label.setWordWrap(True)
        self.pricing_details_line_label.setStyleSheet(
            "background-color: #F6FAFD; border: 1px solid #D6E4EE; border-radius: 8px; padding: 10px; "
            "color: #2A4254; font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(self.pricing_details_line_label)

        self.pricing_details_header_label = QLabel()
        self.pricing_details_header_label.setWordWrap(True)
        self.pricing_details_header_label.setStyleSheet(
            "background-color: #FCFAF4; border: 1px solid #E5D9BA; border-radius: 8px; padding: 10px; "
            "color: #5A4A1F; font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(self.pricing_details_header_label)

        self.pricing_details_global_label = QLabel()
        self.pricing_details_global_label.setWordWrap(True)
        self.pricing_details_global_label.setStyleSheet(
            "background-color: #F4F8F2; border: 1px solid #D7E5D0; border-radius: 8px; padding: 10px; "
            "color: #35533A; font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(self.pricing_details_global_label)

        button_row = QHBoxLayout()
        button_row.addStretch()
        close_btn = QPushButton("Close", objectName="TopRightButton")
        close_btn.clicked.connect(dialog.close)
        button_row.addWidget(close_btn)
        layout.addLayout(button_row)

        def _cleanup():
            self.pricing_details_dialog = None
            self.pricing_details_line_label = None
            self.pricing_details_header_label = None
            self.pricing_details_global_label = None

        dialog.finished.connect(_cleanup)

        self.pricing_details_dialog = dialog
        self.refresh_pricing_details_dialog()
        dialog.show()

    def refresh_pricing_details_dialog(self):
        if self.pricing_details_line_label is not None:
            self.pricing_details_line_label.setText(self.current_line_pricing_summary_text)

        if self.pricing_details_header_label is not None:
            header_discount_source = self.header_discount_source_label.text() if hasattr(self, "header_discount_source_label") else "Source: Unknown"
            header_tax_source = self.header_tax_source_label.text() if hasattr(self, "header_tax_source_label") else "Source: Unknown"
            self.pricing_details_header_label.setText(
                "Header Adjustments\n"
                f"Header Discount: {self.discount_entry.text() if hasattr(self, 'discount_entry') else '0.00'} | {header_discount_source}\n"
                f"Header Tax: {self.tax_entry.text() if hasattr(self, 'tax_entry') else '0.00'} | {header_tax_source}\n"
                f"Additional Charges: {self.additional_entry.text() if hasattr(self, 'additional_entry') else '0.00'}"
            )

        if self.pricing_details_global_label is not None:
            global_status = self.global_pricing_status.text() if hasattr(self, "global_pricing_status") else "Global Promo: Off | Global Tax: Off"
            pricing_defaults = self.customer_pricing_summary.text() if hasattr(self, "customer_pricing_summary") else ""
            self.pricing_details_global_label.setText(
                "Defaults And Global Pricing\n"
                f"{global_status}\n"
                f"{pricing_defaults}"
            )

    def load_sales_discount_policy(self):
        settings = load_sales_policy_settings()
        self.sales_discount_policy = settings["discount_policy"]
        self.minimum_margin_percent = float(settings.get("minimum_margin_percent", self.minimum_margin_percent) or self.minimum_margin_percent)
        return self.sales_discount_policy

    def _line_discount_enabled_by_policy(self):
        return self.sales_discount_policy in ("both", "line_only")

    def _header_discount_enabled_by_policy(self):
        return self.sales_discount_policy in ("both", "header_only")

    def _sales_discount_policy_label(self):
        mapping = {
            "both": "Both",
            "line_only": "Line Only",
            "header_only": "Header Only",
        }
        return mapping.get(self.sales_discount_policy, "Both")

    def load_sales_tax_policy(self):
        self.sales_tax_policy = load_sales_policy_settings()["tax_policy"]
        return self.sales_tax_policy

    def _line_tax_enabled_by_policy(self):
        return self.sales_tax_policy in ("both", "line_only")

    def _header_tax_enabled_by_policy(self):
        return self.sales_tax_policy in ("both", "header_only")

    def _compute_margin_snapshot(self, cost_price, sale_price):
        try:
            cost = float(cost_price or 0.0)
        except (TypeError, ValueError):
            cost = 0.0

        try:
            sale = float(sale_price or 0.0)
        except (TypeError, ValueError):
            sale = 0.0

        if sale <= 0:
            return {
                "cost_price": cost,
                "sale_price": sale,
                "profit_amount": 0.0,
                "margin_percent": None,
            }

        profit_amount = sale - cost
        margin_percent = (profit_amount / sale) * 100.0
        return {
            "cost_price": cost,
            "sale_price": sale,
            "profit_amount": profit_amount,
            "margin_percent": margin_percent,
        }

    def _current_line_target_margin_percent(self):
        product_target = self.current_line_product_defaults.get("target_margin_percent")
        try:
            if product_target not in (None, ""):
                return float(product_target)
        except (TypeError, ValueError):
            pass
        return float(self.minimum_margin_percent or 0.0)

    def _set_line_info_labels(self, *, formula_text, cost_sale_text, profit_text, margin_text):
        if not hasattr(self, "line_info_formula_label"):
            return

        formula_text = str(formula_text or "").strip() or "Formula: -"
        cost_sale_text = str(cost_sale_text or "").strip() or "Cost: - | Sale: -"
        profit_text = str(profit_text or "").strip() or "Profit: -"
        margin_text = str(margin_text or "").strip() or f"Margin: - (Target: {self._current_line_target_margin_percent():.1f}%)"

        metrics = QFontMetrics(self.line_info_formula_label.font())
        available_width = max(self.line_info_formula_label.width() - 6, 220)
        elided_formula = metrics.elidedText(formula_text, Qt.ElideRight, available_width)

        self.line_info_formula_label.setText(elided_formula)
        self.line_info_formula_label.setToolTip(formula_text)
        self.line_info_cost_sale_label.setText(cost_sale_text)
        self.line_info_profit_label.setText(profit_text)
        self.line_info_margin_label.setText(margin_text)
        self._refresh_line_prescription_badge()

    def _refresh_line_prescription_badge(self):
        if not hasattr(self, "line_info_prescription_badge"):
            return

        product_data = self.current_line_product_defaults or {}
        if self.current_sale_prescription_ignored and bool(product_data.get("prescription_required")):
            self.line_info_prescription_badge.setText("RX IGNORED")
            self.line_info_prescription_badge.setStyleSheet(
                "background-color: #FFF7E6; color: #B45309; border: 1px solid #F6C780; "
                "border-radius: 10px; padding: 3px 8px; font-size: 11px; font-weight: 700;"
            )
            self.line_info_prescription_badge.setVisible(True)
            return

        if bool(product_data.get("prescription_required")):
            self.line_info_prescription_badge.setText("RX REQUIRED")
            self.line_info_prescription_badge.setStyleSheet(
                "background-color: #FFF1F2; color: #B42318; border: 1px solid #FECACA; "
                "border-radius: 10px; padding: 3px 8px; font-size: 11px; font-weight: 700;"
            )
            self.line_info_prescription_badge.setVisible(True)
            return

        self.line_info_prescription_badge.setVisible(False)

    def update_current_line_margin_indicator(self):
        if not hasattr(self, "line_info_formula_label"):
            return

        product_data = self.current_line_product_defaults or {}
        formula = str(product_data.get("generic_name") or "").strip()
        cost_price = self._float_or_default(product_data.get("cost_price"), 0.0)
        sale_price = self._float_or_default(self.rate_edit.text(), 0.0)
        target_margin_percent = self._current_line_target_margin_percent()
        formula_text = f"Formula: {formula}" if formula else "Formula: -"

        if cost_price <= 0:
            self._set_line_info_labels(
                formula_text=formula_text,
                cost_sale_text=f"Cost: - | Sale: {sale_price:.2f}" if sale_price > 0 else "Cost: - | Sale: -",
                profit_text="Profit: -",
                margin_text=f"Margin: - (Target: {target_margin_percent:.1f}%)",
            )
            return

        margin = self._compute_margin_snapshot(cost_price, sale_price)
        margin_percent = margin["margin_percent"]
        profit_amount = margin["profit_amount"]

        if margin_percent is None:
            self._set_line_info_labels(
                formula_text=formula_text,
                cost_sale_text=f"Cost: {cost_price:.2f} | Sale: -",
                profit_text="Profit: -",
                margin_text=f"Margin: - (Target: {target_margin_percent:.1f}%)",
            )
            return

        self._set_line_info_labels(
            formula_text=formula_text,
            cost_sale_text=f"Cost: {cost_price:.2f} | Sale: {sale_price:.2f}",
            profit_text=f"Profit: {profit_amount:.2f}",
            margin_text=f"Margin: {margin_percent:.2f}% (Target: {target_margin_percent:.1f}%)",
        )

    def _sales_tax_policy_label(self):
        mapping = {
            "both": "Both",
            "line_only": "Line Only",
            "header_only": "Header Only",
        }
        return mapping.get(self.sales_tax_policy, "Both")

    def get_current_line_tax_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            tax_widget = self.table.cellWidget(row, 5)
            if tax_widget is None:
                continue
            try:
                total += float(tax_widget.property("tax_amount_applied") or 0.0)
            except (TypeError, ValueError):
                pass
        return total

    def get_current_line_discount_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            discount_widget = self.table.cellWidget(row, 4)
            if discount_widget is None:
                continue
            try:
                total += float(discount_widget.property("discount_amount_applied") or 0.0)
            except (TypeError, ValueError):
                pass
        return total

    def on_discount_mode_changed(self):
        if self.current_line_product_defaults:
            self.line_discount_manual_override = True
        self.update_line_total()

    def apply_current_line_product_defaults(self, product_data):
        self.load_sales_discount_policy()
        self.load_sales_tax_policy()
        self.current_line_product_defaults = dict(product_data or {})
        self.line_discount_manual_override = False
        self.line_tax_manual_override = False

        self.discount_mode_combo.blockSignals(True)
        self.discount_mode_combo.setCurrentIndex(self.discount_mode_combo.findData("percent"))
        self.discount_mode_combo.blockSignals(False)

        self.discount.setText(f"{float(self.current_line_product_defaults.get('discount_percent', 0.0) or 0.0):.2f}")
        self.tax.setText(f"{float(self.current_line_product_defaults.get('tax_percent', 0.0) or 0.0):.2f}")
        self.update_current_line_margin_indicator()
        self.update_line_pricing_hint()
        self.update_line_total()

    def reset_current_line_defaults(self):
        if not self.current_line_product_defaults:
            self.discount_mode_combo.blockSignals(True)
            self.discount_mode_combo.setCurrentIndex(self.discount_mode_combo.findData("percent"))
            self.discount_mode_combo.blockSignals(False)
            self.discount.setText("0.00")
            self.tax.setText("0.00")
            self.line_discount_manual_override = False
            self.line_tax_manual_override = False
            if hasattr(self, "line_info_formula_label"):
                self._set_line_info_labels(
                    formula_text="Formula: Waiting for product selection",
                    cost_sale_text="Cost: - | Sale: -",
                    profit_text="Profit: -",
                    margin_text=f"Margin: - (Target: {self.minimum_margin_percent:.0f}%)",
                )
            self.update_line_pricing_hint()
            self.update_line_total()
            return

        self.apply_current_line_product_defaults(self.current_line_product_defaults)
    
    
    
    def writeoffcheck(self):
        
        remaining = self.remainingdata.text()
        remaining = float(remaining) if remaining else 0
        
        if remaining > 0:
            
            if self.writeoff_check.isChecked():
                
                self.note.setText(f"Amount {remaining} will be wrote-off / Cleared")
            else:
                self.note.setText(f"Amount {remaining} will be added to receiveable")
        
        else:
            
            self.note.setText(f"Amount {remaining} is excessive and will be added to payable")    
    
    
    
    
    def calculate_percentage_discount(self):
        
        print("Running Percentage Discount")
        
        subtotal = self.gross_entry.text()
        subtotal = float(subtotal) if subtotal else 0
        
        discount = self.discount_entry.text()
        discount = float(discount) if discount else 0
        
        print("Subtotal is: ", subtotal, " percentage discount is; ", discount )
        amount = subtotal * discount / 100
        print("Flat Dsicout is: ", amount)
        self.flatdiscount.setText(f"{amount:.2f}")
        
        self.update_total_amount()
        
        
        
    def calculate_flat_discount(self):
        
        print("Running Flat Discount")
        
        subtotal = self.subtotaldata.text()
        subtotal = float(subtotal) if subtotal else 0
        
        
        discount = self.flatdiscount.text()
        discount = float(discount) if discount else 0
        
        percentage = ( discount / subtotal ) * 100
        self.percentage.setText(f"{percentage:.2f}")
        self.update_total_amount()
        
       
    
    
    def calculate_payment(self):
        
        finalamount = self.final_amount_entry.text()
        finalamount = float(finalamount) if finalamount else 0.00

        received = self.received_entry.text()
        received = float(received) if received else 0.00
        
        change =  max(received - finalamount, 0)
        self.change_entry.setText(str(change))

        remaining = finalamount - received
        self.remainingdata.setText(str(remaining))
        
    
        
    

    def calculate_tax(self):
        
        net_amount = self.net_amount_entry.text()
        net_amount = float(net_amount) if net_amount else 0
        
        tax = self.tax_entry.text()
        tax = float(tax) if tax else 0
        
        tax_amount = net_amount * tax / 100
        self.tax_entry.setText(f"{tax_amount:.2f}")
        
        self.update_total_amount()
        
        



        
    def add_row(self):
        
        row = self.table.rowCount()
        
        self.table.setRowHeight(row, self.row_height)
        
        
        
        counter = QLabel()
        counter.setStyleSheet('font-weight: 500;')
        counter.setText(str(row + 1))
        

        
        remove_btn = QPushButton("X")
        remove_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        remove_btn.setStyleSheet("color: #333; ")

        product_name = self.item.currentText()
        product_id = self.item.currentData()
        
        print(f"Product Name: {product_name}, Product ID: {product_id}")
        
        product_combo = QComboBox()
        product_combo.setEditable(True)
        product_combo.lineEdit().setStyleSheet("font-weight: 700;")
        product_combo.lineEdit().setReadOnly(True)
        product_combo.setInsertPolicy(QComboBox.NoInsert)
        
        
        if product_name == '':
            print("Please Select a product first")
            AppMessageBox.information(self, 'Error', "Please Select a product first")
            QTimer.singleShot(0, lambda: self.item.lineEdit().setFocus())
            return
        
        elif product_id is None:
            print("Entered product is not available... Please Add this product first")
            AppMessageBox.information(self, 'Error', "Entered product is not available... Please Add this product first")
            QTimer.singleShot(0, lambda: self.item.lineEdit().setFocus())
            return

        self.table.insertRow(row)
        product_combo.addItem(product_name, product_id)

        product_combo.setStyleSheet("""
        QComboBox {font-weight: 600; padding: 0;}
        QComboBox::drop-down {
            border: 0px;
        }
        QComboBox::down-arrow {
            image: none;
        }
        """)
        
        
        
        
        
        
        
        
        
        
        qty_data = self.qty_edit.text()
        rate_data = self.rate_edit.text()
        discount_data = self.discount.text() or "0"
        tax_data = self.tax.text() or "0"
        total_data = self.amount_edit.text()
        discount_mode = self.discount_mode_combo.currentData() if hasattr(self, "discount_mode_combo") else "percent"
        resolved = self.resolve_line_pricing(
            qty_data or 0,
            rate_data or 0,
            discount_data or 0,
            discount_mode,
            tax_data or 0,
            self.current_line_product_defaults.get("discount_fixed_amount", 0.0),
            self.current_line_product_defaults.get("discount_apply_on_sale", True),
            self.current_line_product_defaults.get("tax_fixed_amount", 0.0),
            self.current_line_product_defaults.get("tax_apply_on_sale", True),
        )
        discount_source = "manual_override" if self.line_discount_manual_override else "product_default"
        tax_source = "manual_override" if self.line_tax_manual_override else "product_default"
        
        if discount_data == '':
            discount_data = '0'
        
        if tax_data == '':
            tax_data = '0'    
        
        
        qty_edit = QLineEdit()
        qty_edit.setText(qty_data)
        qty_edit.setPlaceholderText("qty")
        qty_edit.setStyleSheet("font-weight: 600;")
        
        
        
        
        
        
        
        rate_edit = QLineEdit()
        rate_edit.setText(rate_data)
        rate_edit.setStyleSheet("font-weight: 600;")
        discount = QLineEdit()
        discount.setText(discount_data)
        discount.setProperty("discount_input_mode", discount_mode)
        discount.setProperty("discount_percent_applied", resolved["discount_percent"])
        discount.setProperty("discount_fixed_amount_applied", resolved["discount_fixed_amount"])
        discount.setProperty("discount_amount_applied", resolved["discount_amount"])
        discount.setProperty(
            "discount_apply_on_sale",
            self.current_line_product_defaults.get("discount_apply_on_sale", True)
        )
        discount.setProperty(
            "default_discount_group_id",
            self.current_line_product_defaults.get("discount_group_id")
        )
        discount.setProperty(
            "discount_group_id",
            self.current_line_product_defaults.get("discount_group_id") if not self.line_discount_manual_override else None
        )
        discount.setProperty("discount_source", discount_source)
        
        tax = QLineEdit()
        tax.setText(tax_data)
        tax.setProperty("tax_percent_applied", resolved["tax_percent"])
        tax.setProperty("tax_fixed_amount_applied", resolved["tax_fixed_amount"])
        tax.setProperty("tax_amount_applied", resolved["tax_amount"])
        tax.setProperty(
            "tax_apply_on_sale",
            self.current_line_product_defaults.get("tax_apply_on_sale", True)
        )
        tax.setProperty(
            "default_tax_group_id",
            self.current_line_product_defaults.get("tax_group_id")
        )
        tax.setProperty(
            "tax_group_id",
            self.current_line_product_defaults.get("tax_group_id") if not self.line_tax_manual_override else None
        )
        tax.setProperty("tax_source", tax_source)
        
        amount_edit = QLineEdit()
        amount_edit.setReadOnly(True)
        amount_edit.setText(total_data)
        amount_edit.setStyleSheet("font-weight: 600;")
        self.table.setCellWidget(row, 0, counter)
        self.table.setCellWidget(row, 1, product_combo)
        self.table.setCellWidget(row, 2, qty_edit)
        self.table.setCellWidget(row, 3, rate_edit)
        self.table.setCellWidget(row, 4, discount)
        self.table.setCellWidget(row, 5, tax)
        self.table.setCellWidget(row, 6, amount_edit)
        self.table.setCellWidget(row, 7, remove_btn)
        qty_edit.textChanged.connect(
            lambda _text, current_row=row: self._recalculate_sales_table_row(current_row)
        )
        rate_edit.textChanged.connect(
            lambda _text, current_row=row: self._recalculate_sales_table_row(current_row)
        )
        discount.textChanged.connect(
            lambda _text, current_row=row: self._recalculate_sales_table_row(current_row)
        )
        tax.textChanged.connect(
            lambda _text, current_row=row: self._recalculate_sales_table_row(current_row)
        )
        discount.textEdited.connect(
            lambda _text, widget=discount: (
                widget.setProperty("discount_group_id", None),
                widget.setProperty("discount_source", "manual_override")
            )
        )
        tax.textEdited.connect(
            lambda _text, widget=tax: (
                widget.setProperty("tax_group_id", None),
                widget.setProperty("tax_source", "manual_override")
            )
        )
        
        
        
        self.item.setCurrentIndex(-1)
        self.qty_edit.clear()
        self.rate_edit.clear()
        self.discount.clear()
        self.tax.clear()
        self.amount_edit.setText("0.00")
        self.discount_mode_combo.blockSignals(True)
        self.discount_mode_combo.setCurrentIndex(self.discount_mode_combo.findData("percent"))
        self.discount_mode_combo.blockSignals(False)
        self.current_line_product_defaults = {}
        self.line_discount_manual_override = False
        self.line_tax_manual_override = False
        self.reset_current_line_defaults()
        self.update_line_pricing_hint()
        
        
        
        self.item.lineEdit().setFocus()
        self.item.lineEdit().selectAll()
        self.update_total_amount()
        
       
        

    
    
    
    
    def line_percentage_discount(self, edited_widget):
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            
            qty_text = self.qty_edit.text()
            rate_text = self.rate_edit.text()
            
            
            # get percentage amount
            percentage_discount = self.discount.text()

            qty = float(qty_text) if qty_text else 0
            rate = float(rate_text) if rate_text else 0
            percentage_discount = float(percentage_discount) if percentage_discount else 0
            
            discount_amount =  rate * (percentage_discount / 100)
            self.discount.setText(f"{discount_amount:.2f}")
            price = rate - discount_amount
            
            total = qty * price
            self.amount_edit.setText(f"{total:.2f}")
            
            self.update_total_amount()
            
        except ValueError:
        
            self.amount_edit.setText("0")
            
            
    
    def line_flat_discount(self, edited_widget):
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            
            qty_text = self.qty_edit.text()
            rate_text = self.rate_edit.text()
            # get percentage amount
            flat_discount = self.discount.text()

            qty = float(qty_text) if qty_text else 0
            rate = float(rate_text) if rate_text else 0
            flat_discount = float(flat_discount) if flat_discount else 0

            if flat_discount > 0:
                percentage = ( flat_discount / rate ) * 100
            else:
                percentage = 0.0

            self.discount.setText(f"{percentage:.2f}")

            price = rate - flat_discount
            
            total = price * qty
            
            self.amount_edit.setText(f"{total:.2f}")

            self.update_total_amount()
            
        except ValueError:
        
            self.amount_edit.setText("0")
        
        
        
        
    
    
    
    

    def remove_row(self, target_row):
        self.table.removeRow(target_row)

        # Reconnect all remove buttons with updated row numbers
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 7)
            if isinstance(widget, QPushButton):
                widget.clicked.disconnect()
                widget.clicked.connect(lambda _, r=row: self.remove_row(r))
                
        # update total amount
        self.update_total_amount()

        
        

        
    
    def showEvent(self, event):
        
        super().showEvent(event)
        if not getattr(self, "_customers_loaded_once", False):
            if not self.reloading_sale:
                self.populate_customers()
            self._customers_loaded_once = True




    def populate_customers(self, selected_customer_id=None):
    
        self.customer.clear()
        self.customer.addItem("Walk-in Customer", None)

        try:
            rows = fetch_active_customer_option_rows()
        except Exception as exc:
            AppMessageBox.information(self, "Error", str(exc))
            rows = []

        for row_data in rows:
            self.customer.addItem(row_data["name"], row_data["customer_id"])

        target_index = 0
        if selected_customer_id is not None:
            found_index = self.customer.findData(selected_customer_id)
            if found_index >= 0:
                target_index = found_index
        self.customer.setCurrentIndex(target_index)

        self.update_customer_credit_summary()
    
    
    
    
    
    
    
    
    
    
    
    def insert_customer_quick(self, name):
    
        name = name.strip()
        
        if not name:
            return None

        try:
            return insert_sales_customer_quick(name)
        except Exception as exc:
            print(str(exc))
            return None
    
    
    

    def get_customer_id(self):
        
        customer = self.customer.currentData()
        return customer

    def _collect_selected_product_ids(self):
        product_ids = []
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            if combo is None:
                continue
            product_id = self.extract_product_id(combo.currentData())
            if product_id is None:
                continue
            product_ids.append(product_id)
        return product_ids

    def collect_sales_prescription_payload(self):
        ensure_prescription_schema()
        if self.current_sale_prescription_ignored:
            return None
        if self.current_sale_prescription_payload:
            return dict(self.current_sale_prescription_payload)
        required_products = fetch_prescription_required_products(self._collect_selected_product_ids())
        if not required_products:
            return None

        dialog = PrescriptionInfoDialog(
            self,
            product_names=[row["display_name"] for row in required_products],
        )
        if dialog.exec() != QDialog.Accepted:
            return False

        app = QApplication.instance()
        payload = dialog.get_payload()
        payload["created_by"] = app.property("user_id") if app is not None else None
        self.current_sale_prescription_payload = dict(payload)
        return payload

    def ensure_prescription_for_product(self, product_data):
        if not isinstance(product_data, dict):
            return True
        if not bool(product_data.get("prescription_required")):
            return True
        if self.current_sale_prescription_ignored:
            return True

        app = QApplication.instance()
        payload = None
        if self.current_sale_prescription_payload:
            msg = QMessageBox(self)
            msg.setWindowTitle("Prescription Already Added")
            msg.setIcon(QMessageBox.Question)
            msg.setText("A prescription is already attached to this invoice.")
            msg.setInformativeText(
                "Use the existing prescription for this medicine, or open the prescription dialog again to review details and add more attachments."
            )
            use_existing_btn = msg.addButton("Use Existing", QMessageBox.AcceptRole)
            review_btn = msg.addButton("Review Prescription", QMessageBox.ActionRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec()
            clicked = msg.clickedButton()

            if clicked == cancel_btn:
                return False
            if clicked == use_existing_btn:
                return True
            payload = dict(self.current_sale_prescription_payload)

        dialog = PrescriptionInfoDialog(
            self,
            product_names=[product_data.get("display_name") or product_data.get("visible_name") or "Prescription medicine"],
            existing_payload=payload,
        )
        if dialog.exec() != QDialog.Accepted:
            return False
        if dialog.ignore_requested:
            product_name = str(product_data.get("display_name") or product_data.get("visible_name") or "Prescription medicine").strip()
            self.current_sale_prescription_payload = None
            self.current_sale_prescription_ignored = True
            log_activity(
                category="sales",
                action="prescription_ignored",
                entity_type="sale",
                entity_id=None,
                note=f"Prescription capture was ignored while adding {product_name} to a sales invoice.",
                previous_value="prescription_required",
                new_value="ignored",
            )
            AppMessageBox.information(
                self,
                "Prescription Ignored",
                "Prescription was ignored for this invoice. This decision has been logged, and the sale can continue.",
            )
            return True

        payload = dialog.get_payload()
        payload["created_by"] = app.property("user_id") if app is not None else None
        self.current_sale_prescription_payload = dict(payload)
        self.current_sale_prescription_ignored = False
        return True

    def on_discount_entry_edited(self):
        self.discount_group_manual_override = True
        self.refresh_customer_pricing_summary()

    def on_tax_entry_edited(self):
        self.tax_group_manual_override = True
        self.refresh_customer_pricing_summary()

    def on_discount_entry_finished(self):
        discount_amount = self._float_or_default(self.discount_entry.text(), 0.0)
        self.discount_entry.blockSignals(True)
        self.discount_entry.setText(f"{discount_amount:.2f}")
        self.discount_entry.blockSignals(False)
        self.update_total_amount()

    def on_tax_entry_finished(self):
        tax_amount = self._float_or_default(self.tax_entry.text(), 0.0)
        self.tax_entry.blockSignals(True)
        self.tax_entry.setText(f"{tax_amount:.2f}")
        self.tax_entry.blockSignals(False)
        self.update_total_amount()

    def update_header_adjustment_visuals(self):
        discount_auto = (
            self.active_discount_group_id is not None
            and not self.discount_group_manual_override
            and self._header_discount_enabled_by_policy()
        )
        tax_auto = (
            self.active_tax_group_id is not None
            and not self.tax_group_manual_override
            and self._header_tax_enabled_by_policy()
        )

        auto_style = (
            "QLineEdit {"
            " background-color: #EEF6FF;"
            " border: 1px solid #7AA6C2;"
            " color: #1D425C;"
            " font-weight: 700;"
            " border-radius: 6px;"
            " padding: 6px 8px;"
            "}"
        )
        manual_style = (
            "QLineEdit {"
            " background-color: #FFF8E8;"
            " border: 1px solid #D8B66A;"
            " color: #6B4D12;"
            " font-weight: 700;"
            " border-radius: 6px;"
            " padding: 6px 8px;"
            "}"
        )
        neutral_style = (
            "QLineEdit {"
            " background-color: #F8FAFC;"
            " border: 1px solid #C9D3DC;"
            " color: #334155;"
            " font-weight: 600;"
            " border-radius: 6px;"
            " padding: 6px 8px;"
            "}"
        )

        if hasattr(self, "discount_entry"):
            self.discount_entry.setStyleSheet(
                auto_style if discount_auto else (manual_style if self.discount_group_manual_override else neutral_style)
            )
            self.discount_entry.setToolTip(
                "Auto-applied from pricing defaults." if discount_auto
                else ("Manual override is active." if self.discount_group_manual_override else "No auto header discount is active.")
            )

        if hasattr(self, "tax_entry"):
            self.tax_entry.setStyleSheet(
                auto_style if tax_auto else (manual_style if self.tax_group_manual_override else neutral_style)
            )
            self.tax_entry.setToolTip(
                "Auto-applied from pricing defaults." if tax_auto
                else ("Manual override is active." if self.tax_group_manual_override else "No auto header tax is active.")
            )

    def update_customer_credit_summary(self):
        if not hasattr(self, "customer_credit_summary"):
            return

        customer_id = self.get_customer_id()
        if customer_id is None:
            self.customer_credit_summary.setText(
                "Credit Summary: Walk-in customer | Credit limit not applied"
            )
            return

        try:
            credit_position = fetch_customer_credit_position(customer_id)
        except Exception:
            self.customer_credit_summary.setText("Credit Summary: Unable to load customer credit position")
            return

        customer_name = credit_position["customer_name"]
        receivable = float(credit_position["current_receivable"] or 0.0)
        credit_limit = float(credit_position["credit_limit"] or 0.0)

        if credit_limit <= 0:
            self.customer_credit_summary.setText(
                f"Credit Summary: {customer_name} | Receivable {receivable:,.2f} | No credit limit"
            )
            return

        available_credit = credit_limit - receivable
        utilization_pct = (receivable / credit_limit * 100.0) if credit_limit > 0 else 0.0
        self.customer_credit_summary.setText(
            f"Credit Summary: {customer_name} | Limit {credit_limit:,.2f} | "
            f"Receivable {receivable:,.2f} | Available {available_credit:,.2f} | "
            f"Utilization {utilization_pct:,.1f}%"
        )

    def apply_customer_pricing_groups(self):
        self.load_sales_discount_policy()
        self.load_sales_tax_policy()
        customer_id = self.get_customer_id()
        has_pricing_fields = hasattr(self, "discount_entry") and hasattr(self, "tax_entry")
        self.discount_group_manual_override = False
        self.tax_group_manual_override = False
        resolved = resolve_sales_header_pricing(customer_id)
        self.sales_discount_policy = resolved["policies"]["discount_policy"]
        self.sales_tax_policy = resolved["policies"]["tax_policy"]

        discount_defaults = resolved["discount"]
        tax_defaults = resolved["tax"]
        global_discount_meta = resolved["global_discount_meta"]
        global_tax_meta = resolved["global_tax_meta"]

        self.active_discount_group_id = discount_defaults["group_id"]
        self.active_discount_group_name = discount_defaults["name"]
        self.active_discount_percent = discount_defaults["percent"]
        self.active_discount_fixed_amount = discount_defaults["fixed_amount"]
        self.active_discount_apply_on_sale = discount_defaults["apply_on_sale"]
        self.active_discount_source = discount_defaults["source"]

        self.active_tax_group_id = tax_defaults["group_id"]
        self.active_tax_group_name = tax_defaults["name"]
        self.active_tax_percent = tax_defaults["percent"]
        self.active_tax_fixed_amount = tax_defaults["fixed_amount"]
        self.active_tax_apply_on_sale = tax_defaults["apply_on_sale"]
        self.active_tax_source = tax_defaults["source"]

        if customer_id is None:
            if has_pricing_fields:
                self.discount_entry.blockSignals(True)
                self.tax_entry.blockSignals(True)
                self.tax_entry.setText("0.00")
                self.discount_entry.blockSignals(False)
                self.tax_entry.blockSignals(False)
            self.refresh_customer_pricing_summary()
            if has_pricing_fields:
                self.update_total_amount()
            return

        if has_pricing_fields and (self.active_discount_group_id is None or not self._header_discount_enabled_by_policy()):
            self.discount_entry.blockSignals(True)
            self.discount_entry.setText("0.00")
            self.discount_entry.blockSignals(False)

        if has_pricing_fields and (self.active_tax_group_id is None or not self._header_tax_enabled_by_policy()):
            self.tax_entry.blockSignals(True)
            self.tax_entry.setText("0.00")
            self.tax_entry.blockSignals(False)

        self.refresh_customer_pricing_summary()
        if has_pricing_fields:
            self.update_total_amount()

    def refresh_customer_pricing_summary(self):
        if not hasattr(self, "customer_pricing_summary"):
            return

        discount_label = (
            f"{self.active_discount_group_name} ({self.active_discount_percent:.2f}% + {self.active_discount_fixed_amount:.2f}, {'Auto' if self.active_discount_apply_on_sale else 'Off'})"
            if self.active_discount_group_id is not None and self.active_discount_group_name
            else "None"
        )
        tax_label = (
            f"{self.active_tax_group_name} ({self.active_tax_percent:.2f}% + {self.active_tax_fixed_amount:.2f}, {'Auto' if self.active_tax_apply_on_sale else 'Off'})"
            if self.active_tax_group_id is not None and self.active_tax_group_name
            else "None"
        )

        discount_mode = "Manual Override" if self.discount_group_manual_override else "Auto"
        tax_mode = "Manual Override" if self.tax_group_manual_override else "Auto"
        discount_source_label = (
            "Global Promo"
            if self.active_discount_source == "global_promo"
            else ("Customer Default" if self.active_discount_source == "customer_default" else "None")
        )
        tax_source_label = (
            "Global Tax"
            if self.active_tax_source == "global_tax"
            else ("Customer Default" if self.active_tax_source == "customer_default" else "None")
        )

        self.customer_pricing_summary.setText(
            f"Pricing Defaults: Discount {discount_label} [{discount_mode}, Source {discount_source_label}, Policy {self._sales_discount_policy_label()}] | Tax {tax_label} [{tax_mode}, Source {tax_source_label}, Policy {self._sales_tax_policy_label()}]"
        )

        if hasattr(self, "header_discount_source_label"):
            self.header_discount_source_label.setText(
                f"Source: {discount_source_label} | Policy: {self._sales_discount_policy_label()}"
            )
        if hasattr(self, "header_tax_source_label"):
            self.header_tax_source_label.setText(
                f"Source: {tax_source_label} | Policy: {self._sales_tax_policy_label()}"
            )
        self.update_header_adjustment_visuals()

        if hasattr(self, "global_pricing_status"):
            if self.active_discount_source == "global_promo":
                discount_status = (
                    f"Global Promo: {self.active_discount_group_name} "
                    f"({self.active_discount_percent:.2f}% + {self.active_discount_fixed_amount:.2f})"
                )
            else:
                discount_status = "Global Promo: Off"

            if self.active_tax_source == "global_tax":
                tax_status = (
                    f"Global Tax: {self.active_tax_group_name} "
                    f"({self.active_tax_percent:.2f}% + {self.active_tax_fixed_amount:.2f})"
                )
            else:
                tax_status = "Global Tax: Off"

            self.global_pricing_status.setText(f"{discount_status} | {tax_status}")
        
        
        
    
    
    def get_salesman_id(self):
        
        username = QApplication.instance().property("username")
        try:
            return resolve_salesman_id(username)
        except Exception as exc:
            AppMessageBox.information(None, 'Error', str(exc))
            self.close()
            QApplication.quit()
            return None
    
    
    
    
    def insert_salesreceipt(self, sales_prescription_payload=None):
    
        try:
            self.calculate_payment()
            self.update_due_date_availability()
            # --- Collect Data ---
            customer_id = self.get_customer_id()
            salesman = self.get_salesman_id()

            subtotal = self._parse_float_field(self.gross_entry.text(), "Sub Total", 0.0)
            discount = self._parse_float_field(self.discount_entry.text(), "Discount", 0.0)
            taxable = self._parse_float_field(self.taxable_entry.text(), "Taxable", 0.0)
            tax = self._parse_float_field(self.tax_entry.text(), "Sales Tax", 0.0)
            net_amount = self._parse_float_field(self.net_amount_entry.text(), "Net Amount", 0.0)
            additional_charges = self._parse_float_field(self.additional_entry.text(), "Additional Charges", 0.0)
            total = self._parse_float_field(self.final_amount_entry.text(), "Final Amount", 0.0)
            received = self._parse_float_field(self.received_entry.text(), "Received", 0.0)
            remaining = self._parse_float_field(self.remainingdata.text(), "Remaining Amount", 0.0)
            
            print("[SALES][HEADER] Starting sales receipt insert")
            print(
                "[SALES][HEADER] Raw UI values:",
                {
                    "customer_id": customer_id,
                    "salesman": salesman,
                    "subtotal_text": self.gross_entry.text(),
                    "discount_text": self.discount_entry.text(),
                    "taxable_text": self.taxable_entry.text(),
                    "tax_text": self.tax_entry.text(),
                    "net_amount_text": self.net_amount_entry.text(),
                    "additional_text": self.additional_entry.text(),
                    "final_amount_text": self.final_amount_entry.text(),
                    "received_text": self.received_entry.text(),
                    "remaining_text": self.remainingdata.text(),
                }
            )
            print(
                "[SALES][HEADER] Parsed values:",
                {
                    "subtotal": subtotal,
                    "discount": discount,
                    "taxable": taxable,
                    "tax": tax,
                    "net_amount": net_amount,
                    "additional_charges": additional_charges,
                    "total": total,
                    "received": received,
                    "remaining": remaining,
                }
            )

            # --- Basic Validation ---
            if total < 0:
                AppMessageBox.warning(self, "Validation Error", "Total cannot be negative.")
                return None

            if received < 0:
                AppMessageBox.warning(self, "Validation Error", "Received amount cannot be negative.")
                return None

            session_id = get_active_session_id(strict=True)
            
            if session_id is None:
                AppMessageBox.warning(self, "Validation Error", "No active session found.")
                return None

            try:
                settlement = resolve_sales_settlement(
                    customer_id=customer_id,
                    remaining=remaining,
                    writeoff_enabled=self.writeoff_check.isChecked(),
                    due_date_option_text=self.due_date_combo.currentText(),
                )
            except ValueError as exc:
                AppMessageBox.warning(self, "Error", str(exc))
                return None

            if not self.confirm_customer_credit_limit(customer_id, settlement["receiveable"]):
                return None

            header_payload = build_sales_header_payload(
                customer_id=customer_id,
                salesman_id=salesman,
                subtotal=subtotal,
                discount=discount,
                taxable=taxable,
                tax=tax,
                net_amount=net_amount,
                additional_charges=additional_charges,
                total=total,
                received=received,
                remaining=remaining,
                session_id=session_id,
                settlement=settlement,
            )

            print("[SALES][HEADER] Settlement:", settlement)
            print("[SALES][HEADER] Header payload:", header_payload)
            try:
                sales_id = persist_sales_receipt_header_and_prescription(
                    header_payload,
                    sales_prescription_payload=sales_prescription_payload,
                )
            except Exception as exc:
                AppMessageBox.error(self, "Database Error", str(exc))
                return None
            print("Sales record inserted. ID:", sales_id)
            print(f"[SALES][HEADER] Sales header persisted successfully with sales_id={sales_id}")

            txn_inserted = self.insert_customer_transaction(
                sales_id, customer_id, total, received, remaining, salesman
            )
            if txn_inserted:
                print("Customer transaction inserted for Sales ID:", sales_id)

            return sales_id

        except Exception as e:
            AppMessageBox.error(self, "Error", str(e))
            return None

    def confirm_customer_credit_limit(self, customer_id, additional_receivable):
        if customer_id is None:
            return True

        additional_receivable = float(additional_receivable or 0.0)
        if additional_receivable <= 0:
            return True

        try:
            credit_position = fetch_customer_credit_position(customer_id)
        except Exception as exc:
            AppMessageBox.warning(self, "Credit Limit", str(exc))
            return False

        customer_name = credit_position["customer_name"]
        current_receivable = credit_position["current_receivable"]
        credit_limit = credit_position["credit_limit"]

        if credit_limit <= 0:
            return True

        projected_receivable = current_receivable + additional_receivable
        if projected_receivable <= credit_limit:
            return True

        available_credit = credit_limit - current_receivable
        _, accepted = AppMessageBox.confirm(
            self,
            "Credit Limit Warning",
            (
                f"{customer_name} will exceed the configured credit limit.\n\n"
                f"Credit Limit: {credit_limit:,.2f}\n"
                f"Current Receivable: {current_receivable:,.2f}\n"
                f"Available Credit: {available_credit:,.2f}\n"
                f"New Credit Exposure: {additional_receivable:,.2f}\n"
                f"Projected Receivable: {projected_receivable:,.2f}\n\n"
                "Do you want to continue with this sale?"
            ),
            confirm_label="Save Anyway",
            cancel_label="Cancel",
            kind="warning",
        )
        return accepted
        
    
    
    def insert_customer_transaction(self, sales_id, customer_id,
                                total_amount, received,
                                remaining, salesman_id):

        print("ABOUT TO INSERT CUSTOMER TRANSACTION NOW...")
        print(
            "[SALES][TXN] Inputs:",
            {
                "sales_id": sales_id,
                "customer_id": customer_id,
                "total_amount": total_amount,
                "received": received,
                "remaining": remaining,
                "salesman_id": salesman_id,
            }
        )

        session_id = get_active_session_id(strict=True)
        if session_id is None:
            AppMessageBox.warning(self, "Validation Error", "No active session found.")
            return None

        payment = self._normalize_payment_data(self.payment_handler.payment_data.copy())
        print(payment)
        print("[SALES][TXN] Normalized payment data:", payment)

        result = persist_sales_customer_transaction(
            sales_id=sales_id,
            customer_id=customer_id,
            total_amount=self._float_or_default(total_amount, 0.0),
            received=self._float_or_default(received, 0.0),
            remaining=remaining,
            salesman_id=salesman_id,
            session_id=session_id,
            payment=payment,
        )
        balance_state = result["balance_state"]
        payable_before = result["payable_before"]
        receiveable_before = result["receiveable_before"]
        transaction_id = result["transaction_id"]

        if customer_id is not None:
            print(
                "[SALES][TXN] Customer balances before:",
                {
                    "payable_before": payable_before,
                    "receiveable_before": receiveable_before,
                }
            )
            print(
                "[SALES][TXN] Customer balance movement:",
                {
                    "payable_now": balance_state["payable_now"],
                    "receiveable_now": balance_state["receiveable_now"],
                    "remaining_due": balance_state["remaining_due"],
                    "remaining_now": balance_state["remaining_now"],
                    "payable_after": balance_state["payable_after"],
                    "receiveable_after": balance_state["receiveable_after"],
                }
            )

        print("Transaction Stored with ID:", transaction_id)
        print(f"[SALES][TXN] Customer transaction persisted for sales_id={sales_id}")

        return True

    def _sales_row_widget_text(self, widget, field_name, row):
        if widget is None:
            raise Exception(f"Row {row + 1}: {field_name} widget is missing.")
        return widget.text().strip()

    def _collect_sales_item_header_values(self):
        def safe_text(line_edit):
            return line_edit.text().strip() if line_edit else ""

        subtotal = self._float_or_default(safe_text(self.gross_entry), 0.0)
        header_discount = self._float_or_default(safe_text(self.discount_entry), 0.0)
        header_tax = self._float_or_default(safe_text(self.tax_entry), 0.0)
        additional_charges = self._float_or_default(safe_text(self.additional_entry), 0.0)

        return subtotal, header_discount, header_tax, additional_charges

    def thermal_receipt_printer(self, sales_id):
        filename = "salesinvoice_thermal.pdf"
        return self.export_thermal_pdf(filename=filename, sales_id=sales_id)

    def get_saved_sale_tax_breakdown(self, sales_id):
        return fetch_saved_sale_tax_breakdown(sales_id)
    
    
    def export_thermal_pdf(self, filename=None, sales_id=None, paper_width_mm=80.0):
        
        if sales_id is None:
            print("Cannot export thermal PDF without sales_id.")
            return None

        if filename is None:
            filename = "salesinvoice_thermal.pdf"

        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                print("Could not remove old thermal pdf:", e)

        context = fetch_sales_receipt_render_context(sales_id)
        if not context:
            print("Failed to fetch sales receipt render context.")
            return None

        business = context["business"]
        header = context["header"]
        items = context["items"]
        tax_breakdown = context["tax_breakdown"]

        business_name = business["business_name"] or "Business"
        address = business["business_address"] or "-"
        contact = business["business_contact"] or "-"
        invoice_no = str(header["sales_id"] or sales_id)
        invoice_date = str(header["invoice_date"] or "")
        sales_subtotal = float(header["subtotal"] or 0.0)
        sales_discount = float(header["discount"] or 0.0)
        sales_total = float(header["final_total"] or 0.0)
        customer_name = str(header["customer_name"] or "Walk-In Customer")

        # ---------------------------
        # Build thermal-size PDF
        # ---------------------------
        base_height_mm = 95.0
        per_item_height_mm = 8.0
        page_height_mm = max(120.0, base_height_mm + len(items) * per_item_height_mm)

        pdf = QPdfWriter(filename)
        pdf.setResolution(203)
        pdf.setPageSize(QPageSize(QSizeF(float(paper_width_mm), page_height_mm), QPageSize.Millimeter))

        painter = QPainter(pdf)
        painter.setPen(Qt.black)

        page_width = pdf.width()
        margin = 24
        right = page_width - margin
        y = 34
        line_h = 30

        def center_text(text, font):
            nonlocal y
            painter.setFont(font)
            option = QTextOption()
            option.setAlignment(Qt.AlignHCenter)
            painter.drawText(QRectF(margin, y, page_width - (2 * margin), line_h), text, option)
            y += line_h

        center_text(business_name, QFont("Courier New", 10, QFont.Bold))
        center_text(address, QFont("Courier New", 8))
        center_text(f"Phone: {contact}", QFont("Courier New", 8))
        y += 4

        painter.setFont(QFont("Courier New", 8))
        painter.drawText(margin, y, f"Invoice: {invoice_no}")
        y += line_h - 8
        painter.drawText(margin, y, f"Date: {invoice_date}")
        y += line_h - 8
        painter.drawText(margin, y, f"Customer: {customer_name}")
        y += line_h

        painter.drawLine(margin, y, right, y)
        y += line_h - 8
        painter.drawText(margin, y, "Item")
        painter.drawText(right - 120, y, "Qty")
        painter.drawText(right - 30, y, "Total")
        y += line_h - 8
        painter.drawLine(margin, y, right, y)
        y += line_h - 4

        for row in items:
            name = str(row.get("product_name") or "")[:32]
            qty = row.get("qty", 0)
            total = float(row.get("line_total") or 0.0)
            unit_price = float(row.get("rate") or 0.0)

            painter.drawText(margin, y, name)
            y += line_h - 10
            painter.drawText(margin + 8, y, f"{qty} x {unit_price:.2f}")
            painter.drawText(right - 120, y, str(qty))
            painter.drawText(right - 55, y, f"{total:.2f}")
            y += line_h - 2

        painter.drawLine(margin, y, right, y)
        y += line_h

        painter.setFont(QFont("Courier New", 9))
        painter.drawText(margin, y, "Sub Total")
        painter.drawText(right - 95, y, f"{sales_subtotal:.2f}")
        y += line_h - 6
        painter.drawText(margin, y, "Discount")
        painter.drawText(right - 95, y, f"{sales_discount:.2f}")
        y += line_h - 6
        painter.drawText(margin, y, "Line Tax")
        painter.drawText(right - 95, y, f"{tax_breakdown['line_tax']:.2f}")
        y += line_h - 6
        painter.drawText(margin, y, "Header Tax")
        painter.drawText(right - 95, y, f"{tax_breakdown['header_tax']:.2f}")
        y += line_h - 6
        painter.drawText(margin, y, "Tax Policy")
        painter.drawText(
            right - 95,
            y,
            "Both" if tax_breakdown["policy"] == "both" else ("Line Only" if tax_breakdown["policy"] == "line_only" else "Header Only"),
        )
        y += line_h - 4
        painter.drawLine(margin, y, right, y)
        y += line_h

        painter.setFont(QFont("Courier New", 10, QFont.Bold))
        painter.drawText(margin, y, "Total")
        painter.drawText(right - 95, y, f"{sales_total:.2f}")
        y += line_h

        center_text("Thank you for your purchase", QFont("Courier New", 8))

        painter.end()
        return filename
        
        
      
        
    
    
    def insert_salesitems(self, sales_id):
    
        print("About to INSERT sales items with FIFO allocation for sales ID:", sales_id)
        print(f"[SALES][ITEMS] Starting item processing for sales_id={sales_id}")
        subtotal, header_discount, header_tax, additional_charges = self._collect_sales_item_header_values()
        print(
            "[SALES][ITEMS] Header values for weight distribution:",
            {
                "subtotal": subtotal,
                "header_discount": header_discount,
                "header_tax": header_tax,
                "additional_charges": additional_charges,
            }
        )
        
        
        # check for empty table
        row_count = self.table.rowCount()
        if row_count <= 0:
            QMessageBox
            raise Exception(f"No Items in Table")
        print(f"[SALES][ITEMS] Table row count: {row_count}")
            
        

        for row in range(self.table.rowCount()):
            print(f"[SALES][ROW {row + 1}] --------------------")

            product_widget = self.table.cellWidget(row, 1)
            if product_widget is None:
                print(f"[SALES][ROW {row + 1}] Skipping row because product widget is missing")
                continue

            product_data = product_widget.currentData()
            if not isinstance(product_data, dict):
                print(f"[SALES][ROW {row + 1}] Skipping row because product data is not a dict: {product_data!r}")
                continue

            product_id = product_data.get("product_id")
            if not product_id:
                print(f"[SALES][ROW {row + 1}] Skipping row because product_id is missing in product data")
                continue

            product_id = int(product_id)
            print(f"Processing row {row} with Product ID: {product_id}")
            print(f"[SALES][ROW {row + 1}] Product data snapshot: {product_data}")

            qty_widget = self.table.cellWidget(row, 2)
            rate_widget = self.table.cellWidget(row, 3)
            discount_widget = self.table.cellWidget(row, 4)
            tax_widget = self.table.cellWidget(row, 5)
            total_widget = self.table.cellWidget(row, 6)

            print(
                f"[SALES][ROW {row + 1}] Raw widget texts:",
                {
                    "qty_text": self._sales_row_widget_text(qty_widget, "quantity", row),
                    "rate_text": self._sales_row_widget_text(rate_widget, "rate", row),
                    "discount_text": self._sales_row_widget_text(discount_widget, "discount", row),
                    "tax_text": self._sales_row_widget_text(tax_widget, "tax", row),
                    "total_text": self._sales_row_widget_text(total_widget, "line total", row),
                }
            )

            try:
                normalized_row = normalize_sales_item_row(
                    row_number=row + 1,
                    product_id=product_id,
                    qty_text=self._sales_row_widget_text(qty_widget, "quantity", row),
                    rate_text=self._sales_row_widget_text(rate_widget, "rate", row),
                    discount_text=self._sales_row_widget_text(discount_widget, "discount", row),
                    tax_text=self._sales_row_widget_text(tax_widget, "tax", row),
                    total_text=self._sales_row_widget_text(total_widget, "line total", row),
                    discount_input_mode=discount_widget.property("discount_input_mode"),
                    discount_percent_applied=discount_widget.property("discount_percent_applied"),
                    discount_amount_applied=discount_widget.property("discount_amount_applied"),
                    tax_percent_applied=tax_widget.property("tax_percent_applied"),
                    tax_amount_applied=tax_widget.property("tax_amount_applied"),
                    default_discount_group_id=discount_widget.property("default_discount_group_id"),
                    default_tax_group_id=tax_widget.property("default_tax_group_id"),
                    discount_group_id=discount_widget.property("discount_group_id"),
                    tax_group_id=tax_widget.property("tax_group_id"),
                    discount_source=discount_widget.property("discount_source"),
                    tax_source=tax_widget.property("tax_source"),
                    subtotal=subtotal,
                    header_discount=header_discount,
                    header_tax=header_tax,
                    additional_charges=additional_charges,
                )
            except ValueError as exc:
                raise Exception(str(exc))

            print(
                "Line Weight:", normalized_row["line_weight"],
                "Line Header Discount:", normalized_row["line_header_discount"],
                "Line Header Tax:", normalized_row["line_header_tax"],
                "Line Additional Charges:", normalized_row["line_additional_charges"]
            )

            print(
                "Validated Row Data:",
                "Product ID:", product_id,
                "Qty:", normalized_row["qty"],
                "Rate:", normalized_row["rate"],
                "Discount %:", normalized_row["discount_percent"],
                "Discount Amount:", normalized_row["discount_amount"],
                "Tax %:", normalized_row["tax_percent"],
                "Tax Amount:", normalized_row["tax_amount"],
                "Line Total:", normalized_row["line_total"],
                "Effective Line Total:", normalized_row["effective_line_total"]
            )

            row_payload = {
                    "product_id": normalized_row["product_id"],
                    "qty": normalized_row["qty"],
                    "rate": normalized_row["rate"],
                    "discount_percent": normalized_row["discount_percent"],
                    "tax_percent": normalized_row["tax_percent"],
                    "discount_amount": normalized_row["discount_amount"],
                    "tax_amount": normalized_row["tax_amount"],
                    "discount_input_mode": normalized_row["discount_input_mode"],
                    "default_discount_group_id": normalized_row["default_discount_group_id"],
                    "default_tax_group_id": normalized_row["default_tax_group_id"],
                    "discount_group_id": normalized_row["discount_group_id"],
                    "tax_group_id": normalized_row["tax_group_id"],
                    "discount_source": normalized_row["discount_source"],
                    "tax_source": normalized_row["tax_source"],
                    "line_total": normalized_row["line_total"],
                    "line_weight": normalized_row["line_weight"],
                    "effective_line_total": normalized_row["effective_line_total"],
                }

            result = persist_sales_item_with_fifo(
                sales_id=sales_id,
                row_payload=row_payload,
                row_number=row + 1,
            )
            sale_item_id = result["sale_item_id"]
            total_available = result["total_available"]
            allocation_result = result["allocation_result"]

            print("[SALES][ITEMS] salesitem insert payload:", {"sales_id": sales_id, **row_payload})
            print(f"[SALES][STOCK] Product {product_id} total available stock: {total_available}")
            print("Sales Item ID is:", sale_item_id)
            print(
                f"[SALES][FIFO] FIFO allocation completed for row={row + 1}, "
                f"product_id={product_id}, sale_item_id={sale_item_id}, "
                f"allocations={len(allocation_result['allocations'])}"
            )

        print(f"[SALES][ITEMS] Completed item processing for sales_id={sales_id}")
        return True
    
    
    
    def put_sale_on_hold(self):
        try:
            customer = self.customer.currentData()
            salesman = self.get_salesman_id()
            if customer == 0:
                customer = None

            print("Customer is: ", customer)

            hold_id = save_hold_sale(
                header_payload={
                    "customer": customer,
                    "salesman": salesman,
                    "status": "On Hold",
                    "subtotal": self._parse_float_field(self.gross_entry.text(), "Sub Total", 0.0),
                    "discount_amount": self._parse_float_field(self.discount_entry.text(), "Discount", 0.0),
                    "taxable_amount": self._parse_float_field(self.taxable_entry.text(), "Taxable", 0.0),
                    "tax_amount": self._parse_float_field(self.tax_entry.text(), "Sales Tax", 0.0),
                    "additional_charges": self._parse_float_field(self.additional_entry.text(), "Additional Charges", 0.0),
                    "final_amount": self._parse_float_field(self.final_amount_entry.text(), "Final Amount", 0.0),
                    "received_amount": self._parse_float_field(self.received_entry.text(), "Received", 0.0),
                    "remaining_amount": self._parse_float_field(self.remainingdata.text(), "Remaining Amount", 0.0),
                    "payment_method": self._text_or_none(self.payment_method.currentText()) if hasattr(self, "payment_method") else "Cash",
                    "due_date": self.compute_due_date(),
                },
                item_rows=self._collect_hold_sale_item_rows(),
                hold_id=self.current_hold_sale_id,
            )

            self.current_hold_sale_id = int(hold_id)
            print("Sales ID is: ", hold_id)
        except Exception as exc:
            AppMessageBox.error(self, "Error", f"Database error - rolling back transactions.\n\n{exc}")
        else:
            print("Transaction committed successfully")
            self.clear_fields()
            AppMessageBox.success(self, "Success", "Sales Hold saved successfully")
        
        
        
        
        
    def _collect_hold_sale_item_rows(self):
        item_rows = []
        for row in range(self.table.rowCount()):
            product_widget = self.table.cellWidget(row, 1)
            if not product_widget or not product_widget.currentData():
                print("Row is empty ... ignoring it...")
                continue

            product_id = self.extract_product_id(product_widget.currentData())
            if product_id is None:
                continue

            qty = self._parse_int_field(self.table.cellWidget(row, 2).text(), f"Row {row + 1} Qty", 0)
            rate = self._parse_float_field(self.table.cellWidget(row, 3).text(), f"Row {row + 1} Rate", 0.0)
            discount_widget = self.table.cellWidget(row, 4)
            tax_widget = self.table.cellWidget(row, 5)
            total_widget = self.table.cellWidget(row, 6)
            discount = self._parse_float_field(
                discount_widget.property("discount_percent_applied") or discount_widget.text(),
                f"Row {row + 1} Discount",
                0.0,
            )
            discountamount = self._parse_float_field(
                discount_widget.property("discount_amount_applied"),
                f"Row {row + 1} Discount Amount",
                0.0,
            )
            tax = self._parse_float_field(
                tax_widget.property("tax_percent_applied") or tax_widget.text(),
                f"Row {row + 1} Tax",
                0.0,
            )
            taxamount = self._parse_float_field(
                tax_widget.property("tax_amount_applied"),
                f"Row {row + 1} Tax Amount",
                0.0,
            )
            discount_input_mode = str(discount_widget.property("discount_input_mode") or "percent")
            total = self._parse_float_field(total_widget.text(), f"Row {row + 1} Total", 0.0)
            item_rows.append(
                {
                    "product_id": product_id,
                    "qty": qty,
                    "rate": rate,
                    "discount": discount,
                    "discountamount": discountamount,
                    "tax": tax,
                    "taxamount": taxamount,
                    "discount_input_mode": discount_input_mode,
                    "total": total,
                }
            )
        return item_rows
    
    
    
    
    
    def load_hold_items(self):
        self.load_hold_orders()
        
        
        
        
        
        
    
    #  Saving Sales Receipt
    @Permissions.require_permission('sales.create')
    def save_receipt(self):
        if not require_open_session(self):
            return

        sales_prescription_payload = self.collect_sales_prescription_payload()
        if sales_prescription_payload is False:
            return

        try: 
            def _work():
                sales_id = self.insert_salesreceipt(sales_prescription_payload=sales_prescription_payload)
                if sales_id is None:
                    raise Exception("Sales receipt header was not saved.")
                self.insert_salesitems(sales_id)
                return sales_id

            sales_id = run_sales_write_transaction(_work)
        except Exception as exc:
            AppMessageBox.error(self, "Error", f"Database error - rolling back transactions.\n\n{exc}")
        else:
            print("Transaction committed successfully")

            standard_pdf = self.export_pdf(
                filename="salesinvoice.pdf",
                sales_id=sales_id
            )
            thermal_pdf = self.export_thermal_pdf(
                filename="salesinvoice_thermal.pdf",
                sales_id=sales_id
            )

            if standard_pdf:
                print("Standard invoice PDF generated:", standard_pdf)
            if thermal_pdf:
                print("Thermal invoice PDF generated:", thermal_pdf)

            if not self.auto_print_check.isChecked():
                print("Auto Print is OFF. PDFs generated without printing.")
            else:
                printer_info = self.get_printer_info()
                if not printer_info.get("attached", False):
                    print("No printer detected. PDFs generated but printing skipped.")
                else:
                    is_thermal = printer_info.get("is_thermal", False)
                    printer_name = printer_info.get("name")

                    if is_thermal and thermal_pdf:
                        print("Thermal printer detected:", printer_name)
                        self.print_pdf(thermal_pdf, printer_name=printer_name)
                    elif standard_pdf:
                        print("Standard printer detected:", printer_name)
                        self.print_pdf(standard_pdf, printer_name=printer_name)
                    elif thermal_pdf:
                        # fallback in case standard failed but thermal succeeded
                        self.print_pdf(thermal_pdf, printer_name=printer_name)

            self.delete_current_hold_sale()
            self.clear_fields()
            AppMessageBox.success(self, "Success", "Sales Record saved successfully")
        
        
        
        
    def get_product_via_code(self, code):
        try:
            return fetch_sales_product_by_code(code)
        except Exception as exc:
            print(exc)
            return None


    def find_sale_row_by_product(self, product_id):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            if combo is None:
                continue

            data = combo.currentData()
            row_product_id = self.extract_product_id(data)
            if row_product_id is not None and int(row_product_id) == int(product_id):
                return row

        return -1


    def extract_product_id(self, data):
        if isinstance(data, dict):
            product_id = data.get("product_id")
            if product_id is None:
                return None
            return int(product_id)

        try:
            if data is None:
                return None
            return int(data)
        except (TypeError, ValueError):
            return None


    def get_in_cart_qty_for_product(self, product_id):
        total_qty = 0

        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            qty_widget = self.table.cellWidget(row, 2)
            if combo is None or qty_widget is None:
                continue

            row_product_id = self.extract_product_id(combo.currentData())
            if row_product_id is None or int(row_product_id) != int(product_id):
                continue

            try:
                total_qty += int(float(qty_widget.text() or 0))
            except (TypeError, ValueError):
                pass

        return total_qty


    def apply_scan_to_existing_row(self, row, product):
        qty_widget = self.table.cellWidget(row, 2)
        rate_widget = self.table.cellWidget(row, 3)
        discount_widget = self.table.cellWidget(row, 4)
        tax_widget = self.table.cellWidget(row, 5)
        total_widget = self.table.cellWidget(row, 6)

        if not (qty_widget and rate_widget and discount_widget and tax_widget and total_widget):
            return

        available_stock = int(product.get("available_stock") or 0)
        in_cart_qty = self.get_in_cart_qty_for_product(product["product_id"])
        if in_cart_qty + 1 > available_stock:
            AppMessageBox.information(
                self,
                "Stock Limit",
                f"Cannot add more of {product['display_name']}. Available stock: {available_stock}."
            )
            return

        current_qty = int(float(qty_widget.text() or 0))

        qty = current_qty + 1
        rate = float(rate_widget.text() or product.get("unit_price") or 0.0)
        discount_value = discount_widget.text() or 0.0
        discount_mode = str(discount_widget.property("discount_input_mode") or "percent")
        tax_pct = float(tax_widget.property("tax_percent_applied") or tax_widget.text() or 0.0)
        resolved = self.resolve_line_pricing(
            qty,
            rate,
            discount_value,
            discount_mode,
            tax_pct,
            product.get("discount_fixed_amount", discount_widget.property("discount_fixed_amount_applied") or 0.0),
            product.get("discount_apply_on_sale", True),
            product.get("tax_fixed_amount", tax_widget.property("tax_fixed_amount_applied") or 0.0),
            product.get("tax_apply_on_sale", True),
        )

        qty_widget.setText(str(qty))
        total_widget.setText(f"{resolved['line_total']:.2f}")
        discount_widget.setProperty("discount_percent_applied", resolved["discount_percent"])
        discount_widget.setProperty("discount_fixed_amount_applied", resolved["discount_fixed_amount"])
        discount_widget.setProperty("discount_amount_applied", resolved["discount_amount"])
        tax_widget.setProperty("tax_percent_applied", resolved["tax_percent"])
        tax_widget.setProperty("tax_fixed_amount_applied", product.get("tax_fixed_amount", 0.0))
        tax_widget.setProperty("tax_amount_applied", resolved["tax_amount"])
        self.update_total_amount()


    def process_barcode_code(self, code_text):
        code_text = (code_text or "").strip()
        if not code_text:
            return

        product = self.get_product_via_code(code_text)
        if not product:
            AppMessageBox.information(self, "Not Found", f"No product found for barcode '{code_text}'.")
            self.item.lineEdit().clear()
            self.item.lineEdit().setFocus()
            return

        if str(product.get("status") or "active").strip().lower() != "used":
            self.item.lineEdit().clear()
            self.open_sales_product_quick_add_dialog(product.get("display_name") or code_text)
            self.item.lineEdit().setFocus()
            return

        if int(product.get("available_stock") or 0) <= 0:
            AppMessageBox.information(
                self,
                "Out of Stock",
                f"{product['display_name']} is currently out of stock."
            )
            self.item.lineEdit().clear()
            self.item.lineEdit().setFocus()
            return

        available_stock = int(product.get("available_stock") or 0)
        in_cart_qty = self.get_in_cart_qty_for_product(product["product_id"])
        if in_cart_qty + 1 > available_stock:
            AppMessageBox.information(
                self,
                "Stock Limit",
                f"Cannot add more of {product['display_name']}. Available stock: {available_stock}."
            )
            self.item.lineEdit().clear()
            self.item.lineEdit().setFocus()
            return

        existing_row = self.find_sale_row_by_product(product["product_id"])
        if existing_row >= 0:
            self.apply_scan_to_existing_row(existing_row, product)
            self.item.lineEdit().clear()
            self.item.lineEdit().setFocus()
            return

        product_data = {
            "product_id": product["product_id"],
            "unit_price": product["unit_price"],
            "cost_price": product.get("cost_price", 0.0),
            "discount_group_id": product.get("discount_group_id"),
            "discount_percent": product.get("discount_percent", 0.0),
            "discount_group_name": product.get("discount_group_name", ""),
            "discount_fixed_amount": product.get("discount_fixed_amount", 0.0),
            "discount_apply_on_sale": product.get("discount_apply_on_sale", True),
            "code": product["code"],
            "tax_group_id": product.get("tax_group_id"),
            "tax_percent": product.get("tax_percent", 0.0),
            "tax_fixed_amount": product.get("tax_fixed_amount", 0.0),
            "tax_apply_on_sale": product.get("tax_apply_on_sale", True),
            "tax_group_name": product.get("tax_group_name", ""),
            "prescription_required": product.get("prescription_required", False),
        }

        self.item.blockSignals(True)
        self.item.clear()
        self.item.addItem(product["display_name"], product_data)
        self.item.setCurrentIndex(0)
        if self.item.isEditable():
            self.item.lineEdit().setText(product["display_name"])
        self.item.blockSignals(False)

        self.qty_edit.setText("1")
        self.rate_edit.setText(f"{float(product['unit_price']):.2f}")
        self.apply_current_line_product_defaults(product_data)

        self.add_row()

        self.item.lineEdit().clear()
        self.item.lineEdit().setFocus()


    def handle_product_enter(self):
        if self._suppress_enter_once:
            self._suppress_enter_once = False
            return

        if self.item.popup_is_visible():
            return

        entered_text = (self.item.lineEdit().text() or "").strip()
        if not entered_text:
            return

        looks_like_barcode = entered_text.isdigit() and len(entered_text) >= 1
        if looks_like_barcode:
            self.process_barcode_code(entered_text)
            return

        # For text entry, keep existing behavior intact and move focus to qty only
        # if a valid product has already been selected from completer.
        data = self.item.currentData()
        if isinstance(data, dict) and data.get("product_id"):
            self.qty_edit.setFocus()
            self.qty_edit.selectAll()
            return

        exact_product_id = self.find_sales_product_id_by_name(entered_text)
        if exact_product_id is not None:
            self.select_sales_product_by_id(exact_product_id)
            self.qty_edit.setFocus()
            self.qty_edit.selectAll()
            return

        self.open_sales_product_quick_add_dialog(entered_text)

    
    
    
    def _run_pending_scan(self):
        
        if not self._pending_scan:
            return
        
        code, combo = self._pending_scan
        self._pending_scan = None
        self.process_barcode_code(str(code or ""))


    
        
    
    def _sales_product_query_fn(self, search_text):
        try:
            return search_sales_products(search_text)
        except Exception:
            return []

    def _fetch_sales_product_data(self, product_id):
        return fetch_sales_product_detail(product_id)

    def find_sales_product_id_by_name(self, display_name):
        return find_product_id_by_display_name(display_name)

    def select_sales_product_by_id(self, product_id):
        product_data = self._fetch_sales_product_data(product_id)
        if not product_data:
            return False

        visible_name = product_data.get("visible_name") or product_data.get("display_name") or ""
        self.item.blockSignals(True)
        self.item.clear()
        self.item.addItem(visible_name, product_data)
        self.item.setCurrentIndex(0)
        if self.item.isEditable():
            self.item.lineEdit().setText(visible_name)
        self.item.blockSignals(False)

        self.on_completer_selected(visible_name, self.item, product_data)
        return True

    def open_sales_product_quick_add_dialog(self, initial_name=""):
        dialog = SalesQuickProductDialog(self, initial_name=initial_name)
        if dialog.exec() != QDialog.Accepted or not dialog.saved_product_id:
            return

        if self.select_sales_product_by_id(dialog.saved_product_id):
            self.qty_edit.setFocus()
            self.qty_edit.selectAll()

    def on_completer_selected(self, text, combo, selected_data=None):
        
        index = combo.findText(text.strip(), Qt.MatchExactly)

        if index == -1:
            combo.setCurrentIndex(-1)
            return None

        combo.setCurrentIndex(index)
        if combo.lineEdit() is not None:
            combo.lineEdit().setText(text.strip())
        data = selected_data if isinstance(selected_data, dict) else combo.currentData()

        if not isinstance(data, dict):
            return None

        product_status = str(data.get("status") or "active").strip().lower()
        if product_status != "used":
            combo.blockSignals(True)
            combo.clear()
            combo.setCurrentIndex(-1)
            if combo.lineEdit() is not None:
                combo.lineEdit().clear()
            combo.blockSignals(False)
            combo.hidePopup()
            self.open_sales_product_quick_add_dialog(data.get("display_name") or text)
            return None

        if data.get("search_payload_only"):
            full_product_data = self._fetch_sales_product_data(data.get("product_id"))
            if not isinstance(full_product_data, dict):
                combo.blockSignals(True)
                combo.setCurrentIndex(-1)
                if combo.lineEdit() is not None:
                    combo.lineEdit().clear()
                combo.blockSignals(False)
                combo.hidePopup()
                return None
            data = full_product_data

        if not self.ensure_prescription_for_product(data):
            combo.blockSignals(True)
            combo.setCurrentIndex(-1)
            if combo.lineEdit() is not None:
                combo.lineEdit().clear()
            combo.blockSignals(False)
            combo.hidePopup()
            return None

        product_id = data.get("product_id")
        unit_price = data.get("unit_price", 0)
        discount_percent = data.get("discount_percent", 0)
        tax_percent = data.get("tax_percent", 0)

        try:
            self.rate_edit.setText(f"{float(unit_price):.2f}")
        except (TypeError, ValueError):
            self.rate_edit.clear()

        data["discount_percent"] = discount_percent
        data["tax_percent"] = tax_percent
        self.apply_current_line_product_defaults(data)

        self._suppress_enter_once = True
        self.qty_edit.setFocus()
        self.qty_edit.selectAll()

        combo.hidePopup()

        return product_id

    def update_line_pricing_hint(self, product_data=None):
        product_data = product_data or self.current_line_product_defaults or {}
        discount_name = str(product_data.get("discount_group_name") or "").strip()
        tax_name = str(product_data.get("tax_group_name") or "").strip()
        cost_price = float(product_data.get("cost_price") or 0.0)
        discount_percent = float(product_data.get("discount_percent") or 0.0)
        discount_fixed_amount = float(product_data.get("discount_fixed_amount") or 0.0)
        discount_apply_on_sale = bool(product_data.get("discount_apply_on_sale", True))
        tax_percent = float(product_data.get("tax_percent") or 0.0)
        tax_fixed_amount = float(product_data.get("tax_fixed_amount") or 0.0)
        tax_apply_on_sale = bool(product_data.get("tax_apply_on_sale", True))
        target_margin_percent = self._current_line_target_margin_percent()
        discount_mode = self.discount_mode_combo.currentData() if hasattr(self, "discount_mode_combo") else "percent"
        discount_source = "Manual Override" if self.line_discount_manual_override else "Product Default"
        tax_source = "Manual Override" if self.line_tax_manual_override else "Product Default"
        has_manual_override = self.line_discount_manual_override or self.line_tax_manual_override

        discount_text = (
            f"{discount_name} ({discount_percent:.2f}% + {discount_fixed_amount:.2f}, {'Auto' if discount_apply_on_sale else 'Off'})"
            if discount_name else f"None ({discount_percent:.2f}% + {discount_fixed_amount:.2f})"
        )
        tax_text = (
            f"{tax_name} ({tax_percent:.2f}% + {tax_fixed_amount:.2f}, {'Auto' if tax_apply_on_sale else 'Off'})"
            if tax_name else f"None ({tax_percent:.2f}% + {tax_fixed_amount:.2f})"
        )
        margin_snapshot = self._compute_margin_snapshot(cost_price, self._float_or_default(self.rate_edit.text(), 0.0))
        if cost_price <= 0:
            margin_text = "Margin unavailable (no cost basis)"
        elif margin_snapshot["margin_percent"] is None:
            margin_text = f"Margin waiting for sale price | Cost {cost_price:.2f} | Target {target_margin_percent:.1f}%"
        else:
            margin_text = (
                f"Margin {margin_snapshot['margin_percent']:.2f}% "
                f"(Target {target_margin_percent:.1f}% | Profit {margin_snapshot['profit_amount']:.2f} on Cost {cost_price:.2f})"
            )

        badge = "Manual Override Active" if has_manual_override else "Defaults Active"
        badge_color = "#B45309" if has_manual_override else "#2F5D7C"
        self.current_line_pricing_summary_text = (
            f"Line Pricing [{badge}]: {margin_text} | "
            f"Discount {discount_text} [{discount_source}, Mode: {'Amt' if discount_mode == 'amount' else '%'}, Policy {self._sales_discount_policy_label()}] | "
            f"Tax {tax_text} [{tax_source}, Policy {self._sales_tax_policy_label()}] | Product defaults drive the row, header defaults stay at invoice level"
        )
        if hasattr(self, "line_pricing_info_btn"):
            self.line_pricing_info_btn.setStyleSheet(
                f"font-weight: 700; color: {badge_color};"
            )
            self.line_pricing_info_btn.setToolTip(self.current_line_pricing_summary_text)
        self.refresh_pricing_details_dialog()
            
            




    def update_total_amount(self):
        self.load_sales_discount_policy()
        self.load_sales_tax_policy()
        
        subtotal = 0.00
        for row in range(self.table.rowCount()):
            line_total_widget = self.table.cellWidget(row, 6)
            if line_total_widget is None:
                continue

            subtotal += max(0.0, self._float_or_default(line_total_widget.text(), 0.0))
                
        self.gross_entry.setText(f"{subtotal:.2f}")

        totals = compute_header_totals(
            subtotal=subtotal,
            manual_discount=self._float_or_default(self.discount_entry.text(), 0.0),
            manual_tax=self._float_or_default(self.tax_entry.text(), 0.0),
            additional_charges=self._float_or_default(self.additional_entry.text(), 0.0),
            discount_group_id=self.active_discount_group_id,
            discount_percent=self.active_discount_percent,
            discount_fixed_amount=self.active_discount_fixed_amount,
            discount_apply_on_sale=self.active_discount_apply_on_sale,
            discount_manual_override=self.discount_group_manual_override,
            header_discount_enabled=self._header_discount_enabled_by_policy(),
            tax_group_id=self.active_tax_group_id,
            tax_percent=self.active_tax_percent,
            tax_fixed_amount=self.active_tax_fixed_amount,
            tax_apply_on_sale=self.active_tax_apply_on_sale,
            tax_manual_override=self.tax_group_manual_override,
            header_tax_enabled=self._header_tax_enabled_by_policy(),
        )

        discount = totals["discount"]
        taxable = totals["taxable"]
        tax = totals["tax"]
        net_amount = totals["net_amount"]
        additional_charges = totals["additional_charges"]
        final_amount = totals["final_amount"]
        line_discount_total = self.get_current_line_discount_total()
        line_tax_total = self.get_current_line_tax_total()

        if (
            not self.discount_entry.hasFocus()
            and self.discount_entry.text().strip() != f"{discount:.2f}"
        ):
            self.discount_entry.blockSignals(True)
            self.discount_entry.setText(f"{discount:.2f}")
            self.discount_entry.blockSignals(False)

        self.taxable_entry.setText(f"{taxable:.2f}")

        if (
            not self.tax_entry.hasFocus()
            and self.tax_entry.text().strip() != f"{tax:.2f}"
        ):
            self.tax_entry.blockSignals(True)
            self.tax_entry.setText(f"{tax:.2f}")
            self.tax_entry.blockSignals(False)

        self.net_amount_entry.setText(f"{net_amount:.2f}")

        if (
            not self.additional_entry.hasFocus()
            and self.additional_entry.text().strip() != f"{additional_charges:.2f}"
        ):
            self.additional_entry.blockSignals(True)
            self.additional_entry.setText(f"{additional_charges:.2f}")
            self.additional_entry.blockSignals(False)

        if hasattr(self, "line_discount_total_entry"):
            self.line_discount_total_entry.setText(f"{line_discount_total:.2f}")
        if hasattr(self, "line_tax_total_entry"):
            self.line_tax_total_entry.setText(f"{line_tax_total:.2f}")
        
        self.final_amount_entry.setText(f"{final_amount:.2f}")
        
        self.final_amount_entry.setStyleSheet("font-weight: bold;")
        
        self.main_final_amount.setText(f"{final_amount:.2f}")
        self.calculate_payment()
        self.update_due_date_availability()
        self.refresh_customer_pricing_summary()

    def on_additional_entry_finished(self):
        additional_charges = self._float_or_default(self.additional_entry.text(), 0.0)
        self.additional_entry.blockSignals(True)
        self.additional_entry.setText(f"{additional_charges:.2f}")
        self.additional_entry.blockSignals(False)
        self.update_total_amount()
        
    def build_hold_row_product_data(self, product_id):
        return fetch_hold_row_product_data(product_id)

    def insert_sale_row_widget(
        self,
        product_name,
        product_data,
        qty_data,
        rate_data,
        discount_data,
        tax_data,
        total_data,
        discount_mode="percent",
        discount_manual_override=False,
        tax_manual_override=False,
    ):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, self.row_height)

        counter = QLabel(str(row + 1))
        counter.setStyleSheet("font-weight: 500;")

        remove_btn = QPushButton("X")
        remove_btn.setStyleSheet("color: #333; ")
        remove_btn.clicked.connect(lambda _, r=row: self.remove_row(r))

        product_combo = QComboBox()
        product_combo.setEditable(True)
        product_combo.lineEdit().setStyleSheet("font-weight: 700;")
        product_combo.lineEdit().setReadOnly(True)
        product_combo.setInsertPolicy(QComboBox.NoInsert)
        product_combo.addItem(product_name, product_data)
        product_combo.setCurrentIndex(0)
        product_combo.setStyleSheet("""
        QComboBox {font-weight: 600; padding: 0;}
        QComboBox::drop-down {
            border: 0px;
        }
        QComboBox::down-arrow {
            image: none;
        }
        """)

        resolved = self.resolve_line_pricing(
            qty_data or 0,
            rate_data or 0,
            discount_data or 0,
            discount_mode,
            tax_data or 0,
            product_data.get("discount_fixed_amount", 0.0),
            product_data.get("discount_apply_on_sale", True),
            product_data.get("tax_fixed_amount", 0.0),
            product_data.get("tax_apply_on_sale", True),
        )

        qty_edit = QLineEdit()
        qty_edit.setText(str(qty_data))
        qty_edit.setPlaceholderText("qty")
        qty_edit.setStyleSheet("font-weight: 600;")

        rate_edit = QLineEdit()
        rate_edit.setText(str(rate_data))
        rate_edit.setStyleSheet("font-weight: 600;")

        discount = QLineEdit()
        discount.setText(str(discount_data))
        discount.setProperty("discount_input_mode", discount_mode)
        discount.setProperty("discount_percent_applied", resolved["discount_percent"])
        discount.setProperty("discount_fixed_amount_applied", resolved["discount_fixed_amount"])
        discount.setProperty("discount_amount_applied", resolved["discount_amount"])
        discount.setProperty(
            "discount_apply_on_sale",
            product_data.get("discount_apply_on_sale", True)
        )
        discount.setProperty("default_discount_group_id", product_data.get("discount_group_id"))
        discount.setProperty(
            "discount_group_id",
            None if discount_manual_override else product_data.get("discount_group_id")
        )
        discount.setProperty(
            "discount_source",
            "manual_override" if discount_manual_override else "product_default"
        )

        tax = QLineEdit()
        tax.setText(str(tax_data))
        tax.setProperty("tax_percent_applied", resolved["tax_percent"])
        tax.setProperty("tax_fixed_amount_applied", resolved["tax_fixed_amount"])
        tax.setProperty("tax_amount_applied", resolved["tax_amount"])
        tax.setProperty(
            "tax_apply_on_sale",
            product_data.get("tax_apply_on_sale", True)
        )
        tax.setProperty("default_tax_group_id", product_data.get("tax_group_id"))
        tax.setProperty(
            "tax_group_id",
            None if tax_manual_override else product_data.get("tax_group_id")
        )
        tax.setProperty(
            "tax_source",
            "manual_override" if tax_manual_override else "product_default"
        )

        amount_edit = QLineEdit()
        amount_edit.setReadOnly(True)
        amount_edit.setText(str(total_data))
        amount_edit.setStyleSheet("font-weight: 600;")

        self.table.setCellWidget(row, 0, counter)
        self.table.setCellWidget(row, 1, product_combo)
        self.table.setCellWidget(row, 2, qty_edit)
        self.table.setCellWidget(row, 3, rate_edit)
        self.table.setCellWidget(row, 4, discount)
        self.table.setCellWidget(row, 5, tax)
        self.table.setCellWidget(row, 6, amount_edit)
        self.table.setCellWidget(row, 7, remove_btn)
        qty_edit.textChanged.connect(
            lambda _text, current_row=row: self._recalculate_sales_table_row(current_row)
        )
        rate_edit.textChanged.connect(
            lambda _text, current_row=row: self._recalculate_sales_table_row(current_row)
        )
        discount.textChanged.connect(
            lambda _text, current_row=row: self._recalculate_sales_table_row(current_row)
        )
        tax.textChanged.connect(
            lambda _text, current_row=row: self._recalculate_sales_table_row(current_row)
        )
        discount.textEdited.connect(
            lambda _text, widget=discount: (
                widget.setProperty("discount_group_id", None),
                widget.setProperty("discount_source", "manual_override")
            )
        )
        tax.textEdited.connect(
            lambda _text, widget=tax: (
                widget.setProperty("tax_group_id", None),
                widget.setProperty("tax_source", "manual_override")
            )
        )
        
    

    
    
    def reload_hold_order(self, id):
        
        print("Reloading Hold Data")

        self.clear_fields(reset_hold_reference=False)
        self.reloading_sale = True
        hold_id = int(id)
        self.current_hold_sale_id = hold_id

        try:
            hold_data = fetch_hold_sale_detail(hold_id)
        except Exception as exc:
            self.reloading_sale = False
            AppMessageBox.error(self, "Error", str(exc))
            return
        if not hold_data:
            self.reloading_sale = False
            AppMessageBox.error(self, "Error", "Unable to load held sale.")
            return

        customer_id = hold_data["customer_id"]
        salesman_id = hold_data["salesman_id"]
        stored_discount = hold_data["discount_amount"]
        stored_tax = hold_data["tax_amount"]
        additional_charges = hold_data["additional_charges"]
        received_amount = hold_data["received_amount"]
        payment_method = hold_data["payment_method"]

        customer_index = self.customer.findData(customer_id)
        if customer_index >= 0:
            self.customer.setCurrentIndex(customer_index)
        else:
            self.customer.setCurrentIndex(0)

        self.additional_entry.setText(f"{additional_charges:.2f}")
        self.received_entry.setText(f"{received_amount:.2f}")

        method_index = self.payment_method.findText(payment_method)
        self.payment_method.setCurrentIndex(method_index if method_index >= 0 else 0)

        current_discount = self._float_or_default(self.discount_entry.text(), 0.0)
        current_tax = self._float_or_default(self.tax_entry.text(), 0.0)
        if abs(current_discount - stored_discount) > 0.009:
            self.discount_group_manual_override = True
            self.discount_entry.blockSignals(True)
            self.discount_entry.setText(f"{stored_discount:.2f}")
            self.discount_entry.blockSignals(False)

        if abs(current_tax - stored_tax) > 0.009:
            self.tax_group_manual_override = True
            self.tax_entry.blockSignals(True)
            self.tax_entry.setText(f"{stored_tax:.2f}")
            self.tax_entry.blockSignals(False)

        print("Customer is:", customer_id, "Salesman is:", salesman_id)

        try:
            item_rows = fetch_hold_sale_item_rows(hold_id)
        except Exception as exc:
            self.reloading_sale = False
            AppMessageBox.error(self, "Error", str(exc))
            return

        self.table.setRowCount(0)

        for item_row in item_rows:
            product_id = item_row["product_id"]
            quantity = item_row["qty"]
            rate = item_row["unitrate"]
            discount_percent = item_row["discount_percent"]
            discount_amount = item_row["discount_amount"]
            tax_percent = item_row["tax_percent"]
            discount_mode = item_row["discount_input_mode"]
            total = item_row["total"]

            product_data = self.build_hold_row_product_data(product_id)
            if not product_data:
                continue

            displayed_discount = discount_amount if discount_mode == "amount" else discount_percent
            discount_manual_override = abs(discount_percent - float(product_data.get("discount_percent") or 0.0)) > 0.009
            tax_manual_override = abs(tax_percent - float(product_data.get("tax_percent") or 0.0)) > 0.009

            self.insert_sale_row_widget(
                product_name=product_data["display_name"],
                product_data=product_data,
                qty_data=quantity,
                rate_data=f"{rate:.2f}",
                discount_data=f"{displayed_discount:.2f}",
                tax_data=f"{tax_percent:.2f}",
                total_data=f"{total:.2f}",
                discount_mode=discount_mode,
                discount_manual_override=discount_manual_override,
                tax_manual_override=tax_manual_override,
            )

        self.update_total_amount()
        self.calculate_payment()
        self.refresh_customer_pricing_summary()

        self.reloading_sale = False


    def load_hold_orders(self):
        try:
            rows = fetch_hold_sale_list_rows()
        except Exception as exc:
            AppMessageBox.error(self, "Hold Sales", str(exc))
            return

        if not rows:
            AppMessageBox.information(self, "Hold Sales", "No held sales are currently available.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Held Sales")
        dialog.setModal(True)
        dialog.resize(860, 420)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        heading = QLabel("Held Sales", objectName="SectionTitle")
        subtitle = QLabel("Open a parked sale and continue working on it.")
        subtitle.setStyleSheet("color: #5E7383; font-size: 12px;")

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["ID", "Customer", "User", "Items", "Amount", "Created"])
        table.setRowCount(len(rows))
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("QTableWidget::item { color: #333; }")

        for row_index, row in enumerate(rows):
            values = [
                str(row["id"]),
                row["customer"],
                row["user"],
                str(row["items"]),
                f"{row['final_amount']:.2f}",
                row["created_at"],
            ]
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col_index in (0, 3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                if row["id"] == self.current_hold_sale_id:
                    item.setBackground(QColor("#EAF3F9"))
                table.setItem(row_index, col_index, item)

        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

        button_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh", objectName="TopRightButton")
        open_btn = QPushButton("Open Selected", objectName="TopRightButton")
        close_btn = QPushButton("Close", objectName="TopRightButton")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setCursor(Qt.PointingHandCursor)
        button_row.addStretch()
        button_row.addWidget(refresh_btn)
        button_row.addWidget(open_btn)
        button_row.addWidget(close_btn)

        def open_selected_hold():
            current_row = table.currentRow()
            if current_row < 0:
                AppMessageBox.information(dialog, "Hold Sales", "Please select a held sale first.")
                return

            selected_hold_id = int(table.item(current_row, 0).text())
            has_current_buffer = self.table.rowCount() > 0
            if has_current_buffer:
                _, accepted = AppMessageBox.confirm(
                    dialog,
                    "Open Held Sale",
                    "Opening a held sale will replace the current working sale on screen. Do you want to continue?",
                    confirm_label="Open Hold",
                    cancel_label="Cancel",
                    kind="warning",
                )
                if not accepted:
                    return

            dialog.accept()
            self.reload_hold_order(selected_hold_id)

        refresh_btn.clicked.connect(lambda: (dialog.reject(), self.load_hold_orders()))
        open_btn.clicked.connect(open_selected_hold)
        close_btn.clicked.connect(dialog.reject)
        table.itemDoubleClicked.connect(lambda *_: open_selected_hold())

        layout.addWidget(heading)
        layout.addWidget(subtitle)
        layout.addWidget(table)
        layout.addLayout(button_row)
        dialog.exec()


    def force_uppercase(self, text):
        line_edit = self.item.lineEdit()
        line_edit.blockSignals(True)
        line_edit.setText(text.upper())
        line_edit.blockSignals(False)
    
    

    
    
    def delete_current_hold_sale(self):
        hold_id = self.current_hold_sale_id
        if hold_id is None:
            return

        try:
            delete_hold_sale(hold_id)
        except Exception as exc:
            print("Error deleting hold order")
            print(str(exc))
            return

        self.current_hold_sale_id = None


    def clear_fields(self, reset_hold_reference=True):
        
        self.order_modified = False
        self.reloading_sale = False
        if reset_hold_reference:
            self.current_hold_sale_id = None
        
        self.gross_entry.clear()
        self.discount_entry.clear()
        
        self.net_amount_entry.clear()
        self.tax_entry.clear()
        self.taxable_entry.clear()
        self.received_entry.clear()
        self.remainingdata.clear()
        self.additional_entry.clear()
        self.final_amount_entry.clear()
        self.main_final_amount.clear()

        self.discount_group_manual_override = False
        self.tax_group_manual_override = False
        self.active_discount_group_id = None
        self.active_discount_group_name = ""
        self.active_discount_percent = 0.0
        self.active_discount_fixed_amount = 0.0
        self.active_discount_apply_on_sale = False
        self.active_discount_source = "none"
        self.active_tax_group_id = None
        self.active_tax_group_name = ""
        self.active_tax_percent = 0.0
        self.current_sale_prescription_payload = None
        self.current_sale_prescription_ignored = False
        
        self.payment_method.blockSignals(True); 
        self.payment_method.setCurrentText("Cash"); 
        self.payment_method.blockSignals(False)
        
        
        self.writeoff_check.setChecked(True)
        
        self.table.setRowCount(0)
        
        self.populate_customers()
        self.refresh_customer_pricing_summary()
        
        # set focus back to combobox
        self.item.setCurrentIndex(-1)
        self.item.setFocus()
        
        


    def export_pdf(self, filename="salesinvoice.pdf", sales_id=None):
        
        if sales_id is None:
            print("Cannot export PDF without sales_id.")
            return None

        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                print("Could not remove old invoice pdf:", e)

        context = fetch_sales_receipt_render_context(sales_id)
        if not context:
            print("Failed to fetch sales receipt render context.")
            return None

        business = context["business"]
        header = context["header"]
        tax_breakdown = context["tax_breakdown"]

        business_name = business["business_name"] or "Business"
        address = business["business_address"] or "-"
        contact = business["business_contact"] or "-"
        invoice_no = f"# {int(header['sales_id'])}"
        invoice_date = str(header["invoice_date"] or "")
        sales_subtotal = float(header["subtotal"] or 0.0)
        sales_discount = float(header["discount"] or 0.0)
        sales_total = float(header["final_total"] or 0.0)
        customer_name = str(header["customer_name"] or "Walk-In Customer")

        items = []
        for row in context["items"]:
            product_name = str(row["product_name"] or "")
            qty = float(row["qty"] or 0.0)
            rate = float(row["rate"] or 0.0)
            discount = float(row["discount_amount"] or 0.0)
            total = float(row["line_total"] or 0.0)
            price = rate - discount
            items.append((product_name, qty, rate, discount, price, total))

        
    
        pdf = QPdfWriter(filename)
        pdf.setPageSize(QPageSize(QPageSize.A4))
        pdf.setResolution(300)

        

        painter = QPainter(pdf)
        painter.setFont(QFont("Arial", 12))
        painter.setPen(Qt.black)
        
        
        
        x = 100
        y = 200

        business_font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(business_font)

        painter.drawText(x, y, business_name)

        y += 80
        
        address_font = QFont("Arial", 12)
        painter.setFont(address_font)
        
        painter.drawText(x, y, address)
        
        y += 70
        painter.drawText(x, y, f"Phone: {contact}")
        
        
        invoice_font = QFont("Arial", 36, QFont.Bold)
        painter.setFont(invoice_font)

        invoice_title = "Invoice"
        painter.drawText(1700, 230, invoice_title)
        
        invoice_no_font = QFont("Arial", 12)
        painter.setFont(invoice_no_font)
        
        rect = QRectF(1700, 250, 500, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, invoice_no, option)
        
        
        invoice_date_font = QFont("Arial", 12)
        painter.setFont(invoice_date_font)

        rect = QRectF(1700, 320, 500, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, invoice_date, option)

        y += 150
        
        customer_font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(customer_font)
        customer = f"To : {customer_name}"
        painter.drawText(x, y, customer)
        
        y += 80
        
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)
        
        y += 70
        header_font = QFont("Arial", 11, QFont.Bold)
        painter.setFont(header_font)

        item_name = "Item"
        painter.drawText(x + 20, y, item_name)
        
        item_name = "qty"
        painter.drawText(x + 900, y, item_name)
        
        item_name = "rate"
        painter.drawText(x + 1100, y, item_name)
        
        item_name = "discount"
        painter.drawText(x + 1400, y, item_name)
        
        item_name = "Price"
        painter.drawText(x + 1650, y, item_name)
        
        item_name = "Total"
        painter.drawText(x + 1900, y, item_name)

        
        y += 40
        
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)

        y += 100
        
        items_font = QFont("Arial", 11)
        painter.setFont(items_font)
        
        # Sample items
        # items = [
        #         ("Panadol tab 250mg", 2, 10.00, "2%", 9.80, 18.16), 
        #         ("Amoxil Cap 500mg", 1, 20.00, "0%", 20.00, 20.00), 
        #         ("Floxacin Drops 10ml", 5, 5.00, "5%", 4.75, 23.75),
        #         ("Clementrin Syrup 160ml", 3, 15.00, "10%", 13.50, 40.50),
        #         ("Tibe Cream 75gm", 4, 12.00, "5%", 11.40, 45.60)
        #     ]
        items_total = 0.0
        
        print("Drawing Items into Table")
        
        for item, qty, price, discount, net_price, item_total in items:

            painter.drawText(x + 20, y, item)
            painter.drawText(x + 900, y, str(qty))
            painter.drawText(x + 1100, y, f"{price:.2f}")
            painter.drawText(x + 1400, y, f"{discount:.2f} %")
            painter.drawText(x + 1650, y, f"{net_price:.2f}")
            painter.drawText(x + 1900, y, f"{item_total:.2f}")
            
            items_total += item_total
            y += 80

        y += 40
        
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x, y, pdf.width() - 200, y)
        
        y += 60
        
        rect = QRectF(1500, y, 400, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, "Sub Total", option)
        
        total_font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(total_font)
        rect = QRectF(1950, y, 200, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        painter.drawText(rect, f"{sales_subtotal:.2f}", option)
        
        
        
        y += 100
        painter.drawText(x + 1600, y, f"Discount: ")
        painter.drawText(x + 1900, y, f"{sales_discount:.2f}")
        
        y += 80

        painter.drawText(x + 1600, y, f"Line Tax: ")
        painter.drawText(x + 1900, y, f"{tax_breakdown['line_tax']:.2f}")
        
        y += 80
        painter.drawText(x + 1600, y, f"Header Tax: ")
        painter.drawText(x + 1900, y, f"{tax_breakdown['header_tax']:.2f}")
        
        y += 80
        painter.drawText(x + 1600, y, f"Tax Policy: ")
        painter.drawText(
            x + 1900,
            y,
            "Both" if tax_breakdown["policy"] == "both" else ("Line Only" if tax_breakdown["policy"] == "line_only" else "Header Only"),
        )
        
        y += 80
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x + 1500, y, pdf.width() - 200, y) 
        
        y += 80
        total_font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(total_font)
        painter.drawText(x + 1500, y, f"Total Amount: ")
        painter.drawText(x + 1950, y, f"{sales_total:.2f}")

        painter.end()
        return filename
    


    def get_printer_info(self):
        
        system = platform.system()
        info = {
            "attached": False,
            "name": None,
            "raw_info": "",
            "is_thermal": False,
        }

        # ---------------------------
        # Linux/macOS: use CUPS tools
        # ---------------------------
        if system in ("Linux", "Darwin"):
            default_name = None
            raw_parts = []

            try:
                out = subprocess.run(
                    ["lpstat", "-d"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                raw_parts.append((out.stdout or "") + (out.stderr or ""))

                line = (out.stdout or "").strip()
                if ":" in line:
                    default_name = line.split(":", 1)[1].strip()
            except Exception:
                default_name = None

            printers = []
            try:
                out = subprocess.run(
                    ["lpstat", "-p"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                raw_parts.append((out.stdout or "") + (out.stderr or ""))
                for ln in (out.stdout or "").splitlines():
                    # expected: "printer <name> ..."
                    parts = ln.strip().split()
                    if len(parts) >= 2 and parts[0] == "printer":
                        printers.append(parts[1])
            except Exception:
                printers = []

            selected = default_name or (printers[0] if printers else None)
            info["name"] = selected
            info["attached"] = selected is not None

            if selected:
                # collect extra metadata for thermal detection
                for cmd in (["lpstat", "-v", selected], ["lpoptions", "-p", selected]):
                    try:
                        out = subprocess.run(cmd, capture_output=True, text=True, check=False)
                        raw_parts.append((out.stdout or "") + (out.stderr or ""))
                    except Exception:
                        pass

            raw_blob = "\n".join(part for part in raw_parts if part).lower()
            info["raw_info"] = raw_blob
            info["is_thermal"] = self._is_thermal_printer(
                selected or "",
                raw_blob
            )
            return info

        # ---------------------------
        # Windows fallback
        # ---------------------------
        if system == "Windows":
            name = os.environ.get("PRINTER", "")
            info["name"] = name or None
            info["attached"] = True  # os.startfile print path handles actual availability
            info["raw_info"] = (name or "").lower()
            info["is_thermal"] = self._is_thermal_printer(name or "", info["raw_info"])
            return info

        return info


    def _is_thermal_printer(self, printer_name, metadata=""):
        haystack = f"{printer_name} {metadata}".lower()
        thermal_keywords = [
            "thermal",
            "receipt",
            "pos",
            "xprinter",
            "x-printer",
            "epson tm",
            "bixolon",
            "star tsp",
            "gp-",
            "gprinter",
            "zebra",
        ]
        return any(keyword in haystack for keyword in thermal_keywords)


    def print_pdf(self, filename, printer_name=None):
        
        system = platform.system()
        if system in ("Linux", "Darwin"):
            cmd = ["lp"]
            if printer_name:
                cmd.extend(["-d", printer_name])
            cmd.append(filename)
            subprocess.run(cmd, check=False)
        elif system == "Windows":
            os.startfile(filename, "print")
            
    
    
    def clear_product_field(self):
        
        self.item.blockSignals(True)

        self.item.setCurrentIndex(-1)
        self.item.lineEdit().clear()
        self.item.hidePopup()
        self.item.blockSignals(False)

    
    
    def update_due_date_availability(self):
        """Enable due_date_combo only if there's a receiveable balance"""
        try:
            received = float(self.received_entry.text() or 0.0)
        except (ValueError, AttributeError):
            received = 0.0
        
        try:
            total = float(self.net_amount_entry.text() or 0.0)
        except (ValueError, AttributeError):
            total = 0.0
        
        writeoff_checked = self.writeoff_check.isChecked()

        is_payable = (received < total) and not writeoff_checked
        self.due_date_combo.setEnabled(is_payable)
        
        if not is_payable:
            self.due_date_combo.setCurrentText("None")

    def compute_due_date(self):
        """Compute due date based on selected days from combo box"""
        return compute_due_date_from_option(self.due_date_combo.currentText())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "line_info_formula_label"):
            QTimer.singleShot(0, self.update_current_line_margin_indicator)

    def _recalculate_sales_table_row(self, row):
        qty_widget = self.table.cellWidget(row, 2)
        rate_widget = self.table.cellWidget(row, 3)
        discount_widget = self.table.cellWidget(row, 4)
        tax_widget = self.table.cellWidget(row, 5)
        total_widget = self.table.cellWidget(row, 6)

        if not all([qty_widget, rate_widget, discount_widget, tax_widget, total_widget]):
            return

        qty_value = max(0.0, self._float_or_default(qty_widget.text(), 0.0))
        rate_value = max(0.0, self._float_or_default(rate_widget.text(), 0.0))
        discount_text = discount_widget.text().strip() or "0"
        tax_text = tax_widget.text().strip() or "0"
        discount_mode = str(discount_widget.property("discount_input_mode") or "percent")

        resolved = self.resolve_line_pricing(
            qty_value,
            rate_value,
            discount_text,
            discount_mode,
            tax_text,
            discount_widget.property("discount_fixed_amount_applied") or 0.0,
            bool(discount_widget.property("discount_apply_on_sale") if discount_widget.property("discount_apply_on_sale") is not None else True),
            tax_widget.property("tax_fixed_amount_applied") or 0.0,
            bool(tax_widget.property("tax_apply_on_sale") if tax_widget.property("tax_apply_on_sale") is not None else True),
        )

        total_widget.setText(f"{resolved['line_total']:.2f}")
        discount_widget.setProperty("discount_percent_applied", resolved["discount_percent"])
        discount_widget.setProperty("discount_fixed_amount_applied", resolved["discount_fixed_amount"])
        discount_widget.setProperty("discount_amount_applied", resolved["discount_amount"])
        tax_widget.setProperty("tax_percent_applied", resolved["tax_percent"])
        tax_widget.setProperty("tax_fixed_amount_applied", resolved["tax_fixed_amount"])
        tax_widget.setProperty("tax_amount_applied", resolved["tax_amount"])
        self.update_total_amount()

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
class MyTable(QTableWidget):
    
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # user can drag

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)
            
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # leave table, go to next widget
            self.focusNextChild()
        else:
            super().keyPressEvent(event)
            
    
   
   
   
class QtyValidationFilter(QObject):
    def __init__(self, parent_page, qty_edit, product_combo):
        super().__init__(qty_edit)
        self.parent_page = parent_page
        self.qty_edit = qty_edit
        self.product_combo = product_combo

    def eventFilter(self, obj, event):
        if obj == self.qty_edit and event.type() == QEvent.FocusOut:
            self.validate_qty()
        return super().eventFilter(obj, event)

    def validate_qty(self):
        text = self.qty_edit.text().strip()

        if not text:
            return

        try:
            entered_qty = int(text)
        except ValueError:
            AppMessageBox.warning(
                self.parent_page,
                "Invalid Quantity",
                "Quantity must be a whole number."
            )
            self.qty_edit.clear()
            QTimer.singleShot(0, self.qty_edit.setFocus)
            return

        product_id = (self.product_combo.currentData() or {}).get("product_id")
        if not product_id:
            return
        
        available_qty = self.get_available_qty(product_id)

        if entered_qty > available_qty:
            AppMessageBox.warning(
                self.parent_page,
                "Insufficient Stock",
                f"Entered quantity ( {entered_qty} ) is greater than available stock ( {available_qty} )."
            )
            self.qty_edit.clear()
            QTimer.singleShot(0, self.qty_edit.setFocus)

    def get_available_qty(self, product_id):
        try:
            return fetch_available_product_quantity(product_id)
        except Exception:
            return 0
