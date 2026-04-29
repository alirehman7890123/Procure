from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QTableWidget,
    QTableWidgetItem, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QLineEdit, QMessageBox,
    QHeaderView, QGridLayout, QCheckBox, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtSql import QSqlDatabase
import re
from PySide6.QtWidgets import QApplication

from medic.utilities.activity_logger import log_activity
from medic.utilities.payment_handler import PaymentMethodHandler
from medic.utilities.permissions import Permissions
from medic.utilities.session_gate import require_open_session
from medic.utilities.session_service import get_active_session_id
from medic.utilities.stylus import load_stylesheets
from medic.utilities.app_messagebox import AppMessageBox
from medic.features.purchase.services.grn_posting_service import (
    build_goods_receipt_payload,
    collect_grn_billing_data,
    collect_grn_totals_payload,
    normalize_grn_receipt_line,
)
from medic.features.purchase.services.grn_transaction_service import (
    fetch_next_grn_number,
    fetch_open_po_option_rows,
    fetch_po_receipt_line_rows,
    fetch_po_supplier_rep_context,
    insert_goods_receipt_header,
    insert_goods_receipt_line,
    recompute_po_status_from_receipts,
    resolve_po_supplier_id,
    insert_goods_receipt_header,
    insert_goods_receipt_line,
    update_goods_receipt_status,
)
from medic.features.purchase.services.purchase_transaction_service import (
    fetch_product_pack_size,
    insert_batch_record,
    fetch_supplier_balances,
    insert_purchase_header,
    insert_purchase_item,
    insert_supplier_transaction,
    mark_product_used,
    update_supplier_balances,
)
from medic.features.purchase.services.purchase_posting_service import build_purchase_header_payload, build_supplier_transaction_payload
from medic.features.purchase.services.grn_draft_service import (
    delete_grn_draft,
    load_latest_grn_draft,
    save_grn_draft,
)


class MyTable(QTableWidget):
    """Responsive table with column ratio scaling on widget resize."""
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


class SelectAllLineEdit(QLineEdit):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)


class SelectAllSpinBox(QSpinBox):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        editor = self.lineEdit()
        if editor is not None:
            QTimer.singleShot(0, editor.selectAll)


class SelectAllDoubleSpinBox(QDoubleSpinBox):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        editor = self.lineEdit()
        if editor is not None:
            QTimer.singleShot(0, editor.selectAll)


class DiscountDisplayEdit(SelectAllLineEdit):
    activate_requested = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.activate_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class DiscountEditDialog(QDialog):
    def __init__(self, parent=None, mode="percent", value=0.0):
        super().__init__(parent)
        self.setWindowTitle("Line Discount")
        self.setModal(True)
        self.setMinimumWidth(332)
        self.setStyleSheet("""
            QDialog {
                background: #FFFFFF;
            }
            QLabel {
                color: #23313F;
            }
            QComboBox QAbstractItemView {
                background: #FFFFFF;
                color: #111111;
                selection-background-color: #DCEAF5;
                selection-color: #111111;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel("Line Discount")
        title.setObjectName("SectionTitle")
        title.setStyleSheet("font-size: 14px; font-weight: 600; padding-left: 0;")
        layout.addWidget(title)
        layout.addStretch()

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        type_label = QLabel("Type")
        type_label.setStyleSheet("font-weight: 600; color: #4A5563; padding-left: 0;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Percentage", "percent")
        self.mode_combo.addItem("Amount", "amount")

        value_label = QLabel("Value")
        value_label.setStyleSheet("font-weight: 600; color: #4A5563; padding-left: 0;")
        self.value_spin = SelectAllDoubleSpinBox()
        self.value_spin.setMinimum(0)
        self.value_spin.setMaximum(10**9)
        self.value_spin.setDecimals(2)
        self.value_spin.setValue(float(value or 0.0))
        if self.value_spin.lineEdit() is not None:
            self.value_spin.lineEdit().setStyleSheet("color: #111111;")

        form.addWidget(type_label, 0, 0)
        form.addWidget(self.mode_combo, 0, 1)
        form.addWidget(value_label, 1, 0)
        form.addWidget(self.value_spin, 1, 1)
        layout.addLayout(form)

        footer = QHBoxLayout()
        footer.setSpacing(10)
        footer.addStretch()
        cancel_btn = QPushButton("Cancel", objectName="TopRightButton")
        save_btn = QPushButton("Apply", objectName="SaveButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        save_btn.setFixedWidth(108)
        footer.addWidget(cancel_btn)
        footer.addWidget(save_btn)
        layout.addLayout(footer)

        mode_index = self.mode_combo.findData(mode or "percent")
        self.mode_combo.setCurrentIndex(mode_index if mode_index >= 0 else 0)

        if self.mode_combo.lineEdit() is not None:
            self.mode_combo.lineEdit().setReadOnly(True)

        self.mode_combo.activated.connect(lambda *_: QTimer.singleShot(0, self.value_spin.setFocus))
        editor = self.value_spin.lineEdit()
        if editor is not None:
            editor.returnPressed.connect(self.accept)

        QTimer.singleShot(0, self.value_spin.setFocus)

    def selected_discount(self):
        return self.mode_combo.currentData(), float(self.value_spin.value())


def parse_expiry_month_year(text):
    raw = str(text or "").strip()
    collapsed = raw.replace("_", "").replace(" ", "")
    if not collapsed or collapsed in {"-", "--"}:
        return None
    if not raw:
        return None

    match = re.fullmatch(r"(\d{2})-(\d{2})", raw)
    if not match:
        return None

    month = int(match.group(1))
    year_two_digits = int(match.group(2))
    if month < 1 or month > 12:
        return None

    year = 2000 + year_two_digits
    normalized = QDate(year, month, 1)
    if not normalized.isValid():
        return None

    current_month_start = QDate.currentDate().addDays(1 - QDate.currentDate().day())
    if normalized < current_month_start:
        return None

    return normalized


class CreateGRNWidget(QWidget):
    grn_list_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._line_refs = []
        self.current_grn_draft_id = None
        self._grn_draft_resume_checked = False
        self._suspend_grn_draft_autosave = False
        self._grn_draft_save_in_progress = False
        self._grn_draft_timer = QTimer(self)
        self._grn_draft_timer.setSingleShot(True)
        self._grn_draft_timer.timeout.connect(self._save_grn_draft_snapshot)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 4, 10, 10)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignTop)

        header = QHBoxLayout()
        heading = QLabel("Create Goods Receipt", objectName="SectionTitle")
        back_btn = QPushButton("Back to List", objectName="TopRightButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.grn_list_signal.emit)
        header.addWidget(heading)
        header.addStretch()
        header.addWidget(back_btn)
        self.layout.addLayout(header)

        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("QFrame#lineSeparator { border: none; border-top: 2px solid #333; }")
        self.layout.addWidget(line)

        header_card = QFrame()
        header_card.setObjectName("sectionCard")
        header_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        header_layout = QVBoxLayout(header_card)
        header_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        notes_row = QHBoxLayout()
        notes_row.setSpacing(12)

        label_style = "font-weight: 600; color: #4A5563; padding-left: 0;"

        self.po_combo = QComboBox()
        self.po_combo.currentIndexChanged.connect(self.load_po_lines)
        self.grn_number_edit = QLineEdit()
        self.grn_number_edit.setPlaceholderText("Auto-generated (GRN-1001+) if empty")
        self.grn_date_edit = QDateEdit()
        self.grn_date_edit.setCalendarPopup(True)
        self.grn_date_edit.setDate(QDate.currentDate())
        self.supplier_value = QLineEdit()
        self.supplier_value.setReadOnly(True)
        self.supplier_value.setPlaceholderText("Supplier from selected PO")
        self.rep_combo = QComboBox()
        self.rep_combo.setPlaceholderText("Select rep")
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Receipt notes...")

        po_label = QLabel("PO")
        po_label.setStyleSheet(label_style)
        po_label.setFixedWidth(72)
        grn_number_label = QLabel("GRN Number")
        grn_number_label.setStyleSheet(label_style)
        grn_number_label.setFixedWidth(92)
        grn_date_label = QLabel("GRN Date")
        grn_date_label.setStyleSheet(label_style)
        grn_date_label.setFixedWidth(72)
        supplier_label = QLabel("Supplier")
        supplier_label.setStyleSheet(label_style)
        supplier_label.setFixedWidth(78)
        rep_label = QLabel("Seller Rep")
        rep_label.setStyleSheet(label_style)
        rep_label.setFixedWidth(84)
        notes_label = QLabel("Notes")
        notes_label.setStyleSheet(label_style)
        notes_label.setFixedWidth(72)

        top_row.addWidget(po_label, 0)
        top_row.addWidget(self.po_combo, 2)
        top_row.addWidget(grn_number_label, 0)
        top_row.addWidget(self.grn_number_edit, 2)
        top_row.addWidget(grn_date_label, 0)
        top_row.addWidget(self.grn_date_edit, 1)
        top_row.addWidget(supplier_label, 0)
        top_row.addWidget(self.supplier_value, 4)
        top_row.addWidget(rep_label, 0)
        top_row.addWidget(self.rep_combo, 2)

        notes_row.addWidget(notes_label, 0)
        notes_row.addWidget(self.notes_edit, 1)

        header_layout.addLayout(top_row)
        header_layout.addLayout(notes_row)
        self.layout.addWidget(header_card)

        # Product, batch, expiry, ordered, previous received, remaining,
        # this GRN receipt qty, unit price, discount, tax, line total
        self.items_table = MyTable(column_ratios=[0.18, 0.10, 0.10, 0.07, 0.07, 0.08, 0.08, 0.10, 0.07, 0.07, 0.08])
        headers = [
            "Product",
            "Batch",
            "Expiry (MM-YY)",
            "Qty Ord",
            "Qty Prev",
            "Qty Rem",
            "Qty This GRN",
            "Unit Price",
            "Discount",
            "Tax",
            "Line Total",
        ]
        self.items_table.setColumnCount(len(headers))
        self.items_table.setHorizontalHeaderLabels(headers)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setMinimumWidth(700)
        self.items_table.setMinimumHeight(360)
        self.items_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.items_table.setStyleSheet("""
            QTableWidget::item { color: #333; border: none; }
            QLineEdit { color: #333; background: #f9f9f9; border: 1px solid #ccc; border-radius: 3px; padding: 2px 4px; }
            QSpinBox, QDoubleSpinBox { color: #333; background: #f9f9f9; border: 1px solid #ccc; border-radius: 3px; padding: 2px 4px; }
            QComboBox { color: #333; background: #f9f9f9; border: 1px solid #ccc; border-radius: 3px; padding: 2px 4px; }
            QDateEdit { color: #333; background: #f9f9f9; border: 1px solid #ccc; border-radius: 3px; padding: 2px 4px; }
        """)
        self.layout.addWidget(self.items_table)

        # ===== ADD TOTALS/BILLING SECTION (matching purchase invoice) =====
        totals_card = QFrame()
        totals_card.setObjectName("sectionCard")
        totals_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        totals_layout = QVBoxLayout(totals_card)
        totals_layout.setContentsMargins(10, 10, 10, 10)
        totals_layout.setSpacing(14)

        totals_title = QLabel("Billing & Settlement")
        totals_title.setStyleSheet("font-weight: 600; color: #2F5D7C; padding-left: 0;")
        totals_layout.addWidget(totals_title)

        totals_grid = QGridLayout()
        totals_grid.setHorizontalSpacing(12)
        totals_grid.setVerticalSpacing(10)

        metric_label_style = "font-weight: 600; color: #4A5563; padding-left: 0;"
        emphasis_style = "font-weight: 600; color: #2F5D7C;"

        self.payment_handler = PaymentMethodHandler(self)

        subtotal_title = QLabel("Subtotal")
        subtotal_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(subtotal_title, 0, 0)
        self.subtotal_label = QLineEdit()
        self.subtotal_label.setReadOnly(True)
        self.subtotal_label.setText("0.00")
        totals_grid.addWidget(self.subtotal_label, 0, 1)

        discount_title = QLabel("Discount")
        discount_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(discount_title, 0, 2)
        self.header_discount_edit = QLineEdit()
        self.header_discount_edit.setText("0.00")
        self.header_discount_edit.textChanged.connect(self.recalculate_landing_costs)
        totals_grid.addWidget(self.header_discount_edit, 0, 3)

        tax_236g_title = QLabel("Tax 236(G)")
        tax_236g_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(tax_236g_title, 0, 4)
        self.tax_236g_edit = QLineEdit()
        self.tax_236g_edit.setText("0.00")
        self.tax_236g_edit.textChanged.connect(self.recalculate_landing_costs)
        totals_grid.addWidget(self.tax_236g_edit, 0, 5)

        tax_236h_title = QLabel("Tax 236(H)")
        tax_236h_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(tax_236h_title, 1, 0)
        self.tax_236h_edit = QLineEdit()
        self.tax_236h_edit.setText("0.00")
        self.tax_236h_edit.textChanged.connect(self.recalculate_landing_costs)
        totals_grid.addWidget(self.tax_236h_edit, 1, 1)

        sales_tax_title = QLabel("Sales Tax")
        sales_tax_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(sales_tax_title, 1, 2)
        self.sales_tax_edit = QLineEdit()
        self.sales_tax_edit.setText("0.00")
        self.sales_tax_edit.textChanged.connect(self.recalculate_landing_costs)
        totals_grid.addWidget(self.sales_tax_edit, 1, 3)

        cn_adjust_title = QLabel("CN Adjustment")
        cn_adjust_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(cn_adjust_title, 1, 4)
        self.cn_adjustment_edit = QLineEdit()
        self.cn_adjustment_edit.setText("0.00")
        self.cn_adjustment_edit.textChanged.connect(self.recalculate_landing_costs)
        totals_grid.addWidget(self.cn_adjustment_edit, 1, 5)

        taxable_title = QLabel("Taxable")
        taxable_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(taxable_title, 2, 0)
        self.taxable_label = QLineEdit()
        self.taxable_label.setReadOnly(True)
        self.taxable_label.setText("0.00")
        totals_grid.addWidget(self.taxable_label, 2, 1)

        net_amount_title = QLabel("Net Amount")
        net_amount_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(net_amount_title, 2, 2)
        self.net_amount_label = QLineEdit()
        self.net_amount_label.setReadOnly(True)
        self.net_amount_label.setText("0.00")
        self.net_amount_label.setStyleSheet(emphasis_style)
        totals_grid.addWidget(self.net_amount_label, 2, 3)

        payment_title = QLabel("Payment Method")
        payment_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(payment_title, 2, 4)
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        totals_grid.addWidget(self.payment_method, 2, 5)

        due_date_title = QLabel("Due Date")
        due_date_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(due_date_title, 3, 0)
        self.due_date_combo = QComboBox()
        self.due_date_combo.addItems(["None", "+15 days", "+30 days", "+45 days", "+60 days", "+90 days"])
        self.due_date_combo.setCurrentText("None")
        self.due_date_combo.setEnabled(False)
        totals_grid.addWidget(self.due_date_combo, 3, 1)

        total_value_title = QLabel("Total Value")
        total_value_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(total_value_title, 3, 2)
        self.total_with_fees_label = QLineEdit()
        self.total_with_fees_label.setReadOnly(True)
        self.total_with_fees_label.setText("0.00")
        self.total_with_fees_label.setStyleSheet(emphasis_style)
        totals_grid.addWidget(self.total_with_fees_label, 3, 3)

        paid_amount_title = QLabel("Paid Amount")
        paid_amount_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(paid_amount_title, 3, 4)
        self.paid_amount = QLineEdit()
        self.paid_amount.setText("0.00")
        totals_grid.addWidget(self.paid_amount, 3, 5)

        remaining_title = QLabel("Remaining Amount")
        remaining_title.setStyleSheet(metric_label_style)
        totals_grid.addWidget(remaining_title, 4, 0)
        self.remaining_amount = QLineEdit()
        self.remaining_amount.setReadOnly(True)
        self.remaining_amount.setText("0.00")
        self.remaining_amount.setStyleSheet(emphasis_style)
        totals_grid.addWidget(self.remaining_amount, 4, 1)

        self.writeoff_check = QCheckBox("Write-off Remaining")
        totals_grid.addWidget(self.writeoff_check, 4, 2, 1, 2)

        for col in range(6):
            if col % 2 == 0:
                totals_grid.setColumnStretch(col, 0)
            else:
                totals_grid.setColumnStretch(col, 1)

        totals_layout.addLayout(totals_grid)
        self.layout.addWidget(totals_card)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("Line Subtotal:"))
        self.total_label = QLabel("0.00")
        footer.addWidget(self.total_label)
        footer.addStretch()

        save_btn = QPushButton("Save GRN", objectName="TopRightButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_grn)

        footer.addSpacing(24)
        footer.addWidget(save_btn)
        self.layout.addLayout(footer)

        self.paid_amount.textChanged.connect(self.calculate_payment)
        self.paid_amount.textChanged.connect(self.update_due_date_availability)
        self.writeoff_check.toggled.connect(self.update_due_date_availability)
        self._setup_grn_draft_autosave()

        self.setStyleSheet(load_stylesheets())

    def _create_discount_editor(self, row):
        editor = DiscountDisplayEdit()
        editor.setReadOnly(True)
        editor.setPlaceholderText("0.00")
        editor.setProperty("discount_input_mode", "percent")
        editor.setProperty("discount_input_value", 0.0)
        editor.setProperty("discount_amount", 0.0)
        editor.activate_requested.connect(lambda r=row: self.open_discount_dialog(r))
        return editor

    def _discount_widget(self, row):
        return self.items_table.cellWidget(row, 8)

    def _format_number(self, value):
        text = f"{float(value):.2f}"
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text

    def _line_discount_amount(self, row, qty, price):
        discount_widget = self._discount_widget(row)
        if discount_widget is None:
            return 0.0

        discount_value = float(discount_widget.property("discount_input_value") or 0.0)
        mode = str(discount_widget.property("discount_input_mode") or "amount")
        base_amount = max(qty * price, 0.0)

        if mode == "percent":
            return max(0.0, min(base_amount, (base_amount * discount_value) / 100.0))
        return max(0.0, min(base_amount, discount_value))

    def update_discount_display(self, row):
        discount_widget = self._discount_widget(row)
        qty_widget = self.items_table.cellWidget(row, 6)
        price_widget = self.items_table.cellWidget(row, 7)
        if discount_widget is None or qty_widget is None or price_widget is None:
            return

        qty = float(qty_widget.value())
        price = float(price_widget.value())
        base_amount = max(qty * price, 0.0)
        discount_amount = self._line_discount_amount(row, qty, price)
        input_value = float(discount_widget.property("discount_input_value") or 0.0)
        mode = str(discount_widget.property("discount_input_mode") or "percent")
        discount_widget.setProperty("discount_amount", discount_amount)

        if discount_amount <= 0:
            discount_widget.setText("0.00")
            return

        if mode == "percent":
            summary = f"{discount_amount:.2f} ({self._format_number(input_value)}%)"
        elif base_amount > 0:
            implied_percent = (discount_amount / base_amount) * 100.0
            summary = f"{discount_amount:.2f} ({self._format_number(implied_percent)}%)"
        else:
            summary = f"{discount_amount:.2f}"

        discount_widget.setText(summary)

    def focus_widget(self, widget):
        if widget is None:
            return
        widget.setFocus()
        if isinstance(widget, QLineEdit):
            widget.selectAll()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            editor = widget.lineEdit()
            if editor is not None:
                editor.selectAll()

    def focus_table_cell_widget(self, row, column):
        if row < 0 or row >= self.items_table.rowCount():
            return
        widget = self.items_table.cellWidget(row, column)
        self.focus_widget(widget)

    def advance_after_tax(self, row):
        next_row = row + 1
        if next_row < self.items_table.rowCount():
            self.focus_table_cell_widget(next_row, 1)
        else:
            self.focus_widget(self.header_discount_edit)

    def open_discount_dialog(self, row):
        discount_widget = self._discount_widget(row)
        qty_widget = self.items_table.cellWidget(row, 6)
        price_widget = self.items_table.cellWidget(row, 7)
        if discount_widget is None or qty_widget is None or price_widget is None:
            return

        dialog = DiscountEditDialog(
            self,
            mode=str(discount_widget.property("discount_input_mode") or "percent"),
            value=float(discount_widget.property("discount_input_value") or 0.0),
        )
        if dialog.exec() == QDialog.Accepted:
            mode, value = dialog.selected_discount()
            discount_widget.setProperty("discount_input_mode", mode)
            discount_widget.setProperty("discount_input_value", value)
            self.update_discount_display(row)
            self.recalculate_totals()
            self.focus_table_cell_widget(row, 9)
        else:
            self.focus_widget(discount_widget)

    def _read_money(self, edit: QLineEdit) -> float:
        raw = ""
        try:
            raw = (edit.text() or "").strip()
        except (AttributeError, TypeError, ValueError):
            return 0.0

        raw = raw.replace(",", "")
        raw = re.sub(r"[^0-9.\-]", "", raw)
        if raw.count(".") > 1:
            first_dot = raw.find(".")
            raw = raw[:first_dot + 1] + raw[first_dot + 1:].replace(".", "")

        if raw in {"", "-", ".", "-."}:
            return 0.0

        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.0

    def on_payment_method_changed(self, method):
        success = self.payment_handler.handle_method_change(method)
        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)
            self.payment_handler.payment_data = {"payment_method": "Cash"}
        self.schedule_grn_draft_save()

    def calculate_payment(self):
        total_value = self._read_money(self.total_with_fees_label)
        paid = self._read_money(self.paid_amount)
        remaining = total_value - paid
        self.remaining_amount.setText(f"{remaining:.2f}")

    def update_due_date_availability(self):
        remaining = self._read_money(self.remaining_amount)
        should_enable = remaining > 0 and not self.writeoff_check.isChecked()
        self.due_date_combo.setEnabled(should_enable)
        if not should_enable:
            self.due_date_combo.setCurrentText("None")

    def compute_due_date(self):
        selected = self.due_date_combo.currentText().strip()
        if selected == "None":
            return None

        offset_map = {
            "+15 days": 15,
            "+30 days": 30,
            "+45 days": 45,
            "+60 days": 60,
            "+90 days": 90,
        }
        days = offset_map.get(selected)
        if days is None:
            return None

        return QDate.currentDate().addDays(days).toString("yyyy-MM-dd")

    def prepare_new_grn(self):
        self._grn_draft_timer.stop()
        self._suspend_grn_draft_autosave = True
        self.notes_edit.clear()
        self.grn_number_edit.clear()
        self.grn_date_edit.setDate(QDate.currentDate())
        self.supplier_value.clear()
        self.rep_combo.clear()
        self.header_discount_edit.setText("0.00")
        self.tax_236g_edit.setText("0.00")
        self.tax_236h_edit.setText("0.00")
        self.sales_tax_edit.setText("0.00")
        self.cn_adjustment_edit.setText("0.00")
        self.subtotal_label.setText("0.00")
        self.taxable_label.setText("0.00")
        self.net_amount_label.setText("0.00")
        self.total_with_fees_label.setText("0.00")
        self.paid_amount.setText("0.00")
        self.remaining_amount.setText("0.00")
        self.writeoff_check.setChecked(False)
        self.due_date_combo.setCurrentText("None")
        self.due_date_combo.setEnabled(False)
        self.payment_method.blockSignals(True)
        self.payment_method.setCurrentText("Cash")
        self.payment_method.blockSignals(False)
        self.payment_handler.handle_method_change("Cash")
        self.load_po_options()
        self.current_grn_draft_id = None
        self._grn_draft_resume_checked = False
        self._suspend_grn_draft_autosave = False
        QTimer.singleShot(0, self.prompt_resume_grn_draft)

    def _setup_grn_draft_autosave(self):
        self.po_combo.currentIndexChanged.connect(self.schedule_grn_draft_save)
        self.rep_combo.currentIndexChanged.connect(self.schedule_grn_draft_save)
        self.grn_number_edit.textChanged.connect(self.schedule_grn_draft_save)
        self.grn_date_edit.dateChanged.connect(lambda *_: self.schedule_grn_draft_save())
        self.notes_edit.textChanged.connect(self.schedule_grn_draft_save)
        self.header_discount_edit.textChanged.connect(self.schedule_grn_draft_save)
        self.tax_236g_edit.textChanged.connect(self.schedule_grn_draft_save)
        self.tax_236h_edit.textChanged.connect(self.schedule_grn_draft_save)
        self.sales_tax_edit.textChanged.connect(self.schedule_grn_draft_save)
        self.cn_adjustment_edit.textChanged.connect(self.schedule_grn_draft_save)
        self.payment_method.currentIndexChanged.connect(self.schedule_grn_draft_save)
        self.paid_amount.textChanged.connect(self.schedule_grn_draft_save)
        self.writeoff_check.toggled.connect(self.schedule_grn_draft_save)
        self.due_date_combo.currentIndexChanged.connect(self.schedule_grn_draft_save)

    def _current_grn_draft_user_id(self):
        app = QApplication.instance()
        if app is None:
            return None
        return app.property("user_id")

    def _set_combo_current_data(self, combo, value):
        if combo is None or value in (None, ""):
            return False
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return True
        return False

    def _grn_draft_has_meaningful_content(self):
        if self.po_combo.currentData() not in (None, ""):
            return True
        if self.notes_edit.text().strip():
            return True
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 6)
            if qty_widget is not None and int(qty_widget.value()) > 0:
                return True
        return False

    def _collect_grn_draft_header(self):
        return {
            "po_id": self.po_combo.currentData(),
            "supplier_name": self.supplier_value.text().strip(),
            "rep": self.rep_combo.currentData(),
            "grn_number": self.grn_number_edit.text().strip(),
            "grn_date": self.grn_date_edit.date().toString("yyyy-MM-dd"),
            "notes": self.notes_edit.text().strip(),
            "header_discount": self.header_discount_edit.text().strip(),
            "tax_236g": self.tax_236g_edit.text().strip(),
            "tax_236h": self.tax_236h_edit.text().strip(),
            "sales_tax": self.sales_tax_edit.text().strip(),
            "cn_adjustment": self.cn_adjustment_edit.text().strip(),
            "paid": self.paid_amount.text().strip(),
            "writeoff_enabled": self.writeoff_check.isChecked(),
            "due_date_option": self.due_date_combo.currentText().strip(),
            "payment_data": dict(self.payment_handler.payment_data or {}),
            "user_id": self._current_grn_draft_user_id(),
            "session_id": get_active_session_id(strict=False),
        }

    def _collect_grn_draft_rows(self):
        rows = []
        for row, line_ref in enumerate(self._line_refs):
            batch_widget = self.items_table.cellWidget(row, 1)
            expiry_widget = self.items_table.cellWidget(row, 2)
            qty_widget = self.items_table.cellWidget(row, 6)
            price_widget = self.items_table.cellWidget(row, 7)
            discount_widget = self.items_table.cellWidget(row, 8)
            tax_widget = self.items_table.cellWidget(row, 9)
            if qty_widget is None or price_widget is None:
                continue

            rows.append(
                {
                    "po_line_id": line_ref.get("po_line_id"),
                    "product_id": line_ref.get("product_id"),
                    "product_name": self.items_table.item(row, 0).text().strip() if self.items_table.item(row, 0) else "",
                    "batch_no": batch_widget.text().strip() if batch_widget else "",
                    "expiry_date": expiry_widget.text().strip() if expiry_widget else "",
                    "qty_received": int(qty_widget.value()),
                    "unit_price": float(price_widget.value()),
                    "discount_mode": str(discount_widget.property("discount_input_mode") or "percent") if discount_widget else "percent",
                    "discount_value": float(discount_widget.property("discount_input_value") or 0.0) if discount_widget else 0.0,
                    "tax": float(tax_widget.value()) if tax_widget else 0.0,
                }
            )
        return rows

    def schedule_grn_draft_save(self):
        if self._suspend_grn_draft_autosave or self._grn_draft_save_in_progress:
            return
        self._grn_draft_timer.start(700)

    def _save_grn_draft_snapshot(self):
        if self._suspend_grn_draft_autosave or self._grn_draft_save_in_progress:
            return
        if not self._grn_draft_has_meaningful_content():
            return
        self._grn_draft_save_in_progress = True
        try:
            header = self._collect_grn_draft_header()
            self.current_grn_draft_id = save_grn_draft(
                header,
                self._collect_grn_draft_rows(),
                draft_id=self.current_grn_draft_id,
            )
            print(f"GRN draft autosaved successfully. Draft ID: {self.current_grn_draft_id}")
        except Exception as exc:
            print(f"GRN draft autosave failed: {exc}")
        finally:
            self._grn_draft_save_in_progress = False

    def _discard_current_grn_draft(self):
        if self.current_grn_draft_id in (None, ""):
            return
        try:
            delete_grn_draft(self.current_grn_draft_id)
        except Exception as exc:
            print(f"Failed to delete GRN draft {self.current_grn_draft_id}: {exc}")
            return
        print(f"Deleted GRN draft {self.current_grn_draft_id}")
        self.current_grn_draft_id = None

    def _restore_grn_draft(self, draft_record):
        header = dict((draft_record or {}).get("header") or {})
        rows = list((draft_record or {}).get("rows") or [])

        self._suspend_grn_draft_autosave = True
        try:
            self._grn_draft_timer.stop()
            self.notes_edit.clear()
            self.grn_number_edit.clear()
            self.grn_date_edit.setDate(QDate.currentDate())
            self.supplier_value.clear()
            self.rep_combo.clear()
            self.header_discount_edit.setText("0.00")
            self.tax_236g_edit.setText("0.00")
            self.tax_236h_edit.setText("0.00")
            self.sales_tax_edit.setText("0.00")
            self.cn_adjustment_edit.setText("0.00")
            self.subtotal_label.setText("0.00")
            self.taxable_label.setText("0.00")
            self.net_amount_label.setText("0.00")
            self.total_with_fees_label.setText("0.00")
            self.paid_amount.setText("0.00")
            self.remaining_amount.setText("0.00")
            self.writeoff_check.setChecked(False)
            self.due_date_combo.setCurrentText("None")
            self.due_date_combo.setEnabled(False)
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)
            self.payment_handler.handle_method_change("Cash")
            self.load_po_options()
            self.current_grn_draft_id = draft_record.get("id")

            self._set_combo_current_data(self.po_combo, header.get("po_id"))
            self.load_po_lines()
            self._set_combo_current_data(self.rep_combo, header.get("rep"))
            self.grn_number_edit.setText(str(header.get("grn_number") or ""))
            grn_date = QDate.fromString(str(header.get("grn_date") or ""), "yyyy-MM-dd")
            if grn_date.isValid():
                self.grn_date_edit.setDate(grn_date)
            self.notes_edit.setText(str(header.get("notes") or ""))
            self.header_discount_edit.setText(str(header.get("header_discount") or "0.00"))
            self.tax_236g_edit.setText(str(header.get("tax_236g") or "0.00"))
            self.tax_236h_edit.setText(str(header.get("tax_236h") or "0.00"))
            self.sales_tax_edit.setText(str(header.get("sales_tax") or "0.00"))
            self.cn_adjustment_edit.setText(str(header.get("cn_adjustment") or "0.00"))
            self.paid_amount.setText(str(header.get("paid") or "0.00"))
            self.writeoff_check.setChecked(bool(header.get("writeoff_enabled")))
            due_date_option = str(header.get("due_date_option") or "None")
            due_index = self.due_date_combo.findText(due_date_option, Qt.MatchFixedString)
            self.due_date_combo.setCurrentIndex(due_index if due_index >= 0 else 0)

            payment_data = dict(header.get("payment_data") or {})
            payment_method = str(payment_data.get("payment_method") or "Cash")
            payment_index = self.payment_method.findText(payment_method, Qt.MatchFixedString)
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentIndex(payment_index if payment_index >= 0 else 0)
            self.payment_method.blockSignals(False)
            self.payment_handler.payment_data = dict(payment_data or {"payment_method": "Cash"})

            rows_by_po_line = {int(row.get("po_line_id") or 0): row for row in rows if int(row.get("po_line_id") or 0) > 0}
            for table_row, line_ref in enumerate(self._line_refs):
                po_line_id = int(line_ref.get("po_line_id") or 0)
                row = rows_by_po_line.get(po_line_id)
                if not row:
                    continue
                batch_widget = self.items_table.cellWidget(table_row, 1)
                expiry_widget = self.items_table.cellWidget(table_row, 2)
                qty_widget = self.items_table.cellWidget(table_row, 6)
                price_widget = self.items_table.cellWidget(table_row, 7)
                discount_widget = self.items_table.cellWidget(table_row, 8)
                tax_widget = self.items_table.cellWidget(table_row, 9)

                if batch_widget:
                    batch_widget.setText(str(row.get("batch_no") or ""))
                if expiry_widget:
                    expiry_widget.setText(str(row.get("expiry_date") or ""))
                if qty_widget:
                    qty_widget.setValue(int(row.get("qty_received") or 0))
                if price_widget:
                    price_widget.setValue(float(row.get("unit_price") or 0.0))
                if discount_widget:
                    discount_widget.setProperty("discount_input_mode", str(row.get("discount_mode") or "percent"))
                    discount_widget.setProperty("discount_input_value", float(row.get("discount_value") or 0.0))
                    self.update_discount_display(table_row)
                if tax_widget:
                    tax_widget.setValue(float(row.get("tax") or 0.0))

            self.recalculate_totals()
            self.recalculate_landing_costs()
        finally:
            self._suspend_grn_draft_autosave = False

    def prompt_resume_grn_draft(self):
        if self._grn_draft_resume_checked:
            return
        self._grn_draft_resume_checked = True
        try:
            draft_record = load_latest_grn_draft(
                user_id=self._current_grn_draft_user_id(),
                session_id=get_active_session_id(strict=False),
            )
        except Exception as exc:
            print(f"Could not load GRN draft for recovery: {exc}")
            return
        if not draft_record:
            return

        _, accepted = AppMessageBox.confirm(
            self,
            "Resume Draft GRN",
            "An unfinished GRN draft was found. Would you like to resume it?",
            confirm_label="Resume Draft",
            cancel_label="Discard Draft",
            kind="question",
        )
        if accepted:
            self._restore_grn_draft(draft_record)
            return
        self.current_grn_draft_id = draft_record.get("id")
        self._discard_current_grn_draft()

    def load_po_options(self):
        self.po_combo.blockSignals(True)
        self.po_combo.clear()
        try:
            rows = fetch_open_po_option_rows()
        except Exception as exc:
            self.po_combo.blockSignals(False)
            print(str(exc))
            return

        for row in rows:
            self.po_combo.addItem(row["po_number"], row["po_id"])

        self.po_combo.blockSignals(False)
        self.load_po_lines()

    def populate_reps_for_po(self, po_id):
        self.supplier_value.clear()
        self.rep_combo.clear()

        if not po_id:
            return

        try:
            context = fetch_po_supplier_rep_context(int(po_id))
        except Exception:
            return

        self.supplier_value.setText(context["supplier_name"])
        for rep in context["reps"]:
            self.rep_combo.addItem(rep["rep_name"], rep["rep_id"])

        if self.rep_combo.count() > 0:
            self.rep_combo.setCurrentIndex(0)

    def load_po_lines(self):
        self.items_table.setRowCount(0)
        self._line_refs = []
        self.total_label.setText("0.00")

        po_id = self.po_combo.currentData()
        self.populate_reps_for_po(po_id)
        if not po_id:
            return

        try:
            rows = fetch_po_receipt_line_rows(int(po_id))
        except Exception as exc:
            print(str(exc))
            return

        row = 0
        for line in rows:
            po_line_id = line["po_line_id"]
            product_id = line["product_id"]
            product_name = line["product_name"]
            qty_ordered = line["qty_ordered"]
            unit_price = line["unit_price"]
            qty_prev_received = line["qty_prev_received"]
            qty_remaining = line["qty_remaining"]
            self.items_table.insertRow(row)
            
            # Column 0: Product name
            self.items_table.setItem(row, 0, QTableWidgetItem(product_name))
            
            # Column 1: Batch Number (editable)
            batch_edit = SelectAllLineEdit()
            batch_edit.setPlaceholderText("Batch #")
            batch_edit.textChanged.connect(self.recalculate_totals)
            self.items_table.setCellWidget(row, 1, batch_edit)
            
            # Column 2: Expiry Date (editable as MM-YY)
            expiry_edit = SelectAllLineEdit()
            expiry_edit.setInputMask("00-00;_")
            expiry_edit.setPlaceholderText("MM-YY")
            expiry_edit.textChanged.connect(self.recalculate_totals)
            self.items_table.setCellWidget(row, 2, expiry_edit)
            
            # Column 3: Qty Ordered (read-only)
            qty_ordered_item = QTableWidgetItem(str(qty_ordered))
            qty_ordered_item.setFlags(qty_ordered_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 3, qty_ordered_item)

            # Column 4: Previously Received (read-only)
            qty_prev_item = QTableWidgetItem(str(qty_prev_received))
            qty_prev_item.setFlags(qty_prev_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 4, qty_prev_item)

            # Column 5: Remaining (read-only)
            qty_remaining_item = QTableWidgetItem(str(qty_remaining))
            qty_remaining_item.setFlags(qty_remaining_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 5, qty_remaining_item)

            # Column 6: Qty Received on this GRN
            qty_received = SelectAllSpinBox()
            qty_received.setMinimum(0)
            qty_received.setMaximum(qty_remaining)
            qty_received.setValue(qty_remaining)
            qty_received.valueChanged.connect(self.recalculate_totals)
            self.items_table.setCellWidget(row, 6, qty_received)

            # Column 7: Unit Price (editable spin box)
            price_box = SelectAllDoubleSpinBox()
            price_box.setMinimum(0)
            price_box.setMaximum(10**9)
            price_box.setDecimals(2)
            price_box.setValue(unit_price)
            price_box.valueChanged.connect(self.recalculate_totals)
            self.items_table.setCellWidget(row, 7, price_box)
            
            # Column 8: Discount (amount or percent via popup editor)
            discount_editor = self._create_discount_editor(row)
            self.items_table.setCellWidget(row, 8, discount_editor)
            
            # Column 9: Tax (editable spin box)
            tax_box = SelectAllDoubleSpinBox()
            tax_box.setMinimum(0)
            tax_box.setMaximum(10**9)
            tax_box.setDecimals(2)
            tax_box.setValue(0.0)
            tax_box.setToolTip("Tax amount on this line")
            tax_box.valueChanged.connect(self.recalculate_totals)
            self.items_table.setCellWidget(row, 9, tax_box)

            # Column 10: Line Total (read-only, calculated)
            total_item = QTableWidgetItem(f"{qty_remaining * unit_price:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 10, total_item)

            self._line_refs.append({
                "po_line_id": po_line_id,
                "product_id": product_id,  # Product ID is stored here for later use in stock batch creation
                "qty_ordered": qty_ordered,
                "qty_prev_received": qty_prev_received,
                "qty_remaining": qty_remaining,
            })

            batch_edit.returnPressed.connect(lambda r=row: self.focus_table_cell_widget(r, 2))
            expiry_edit.returnPressed.connect(lambda r=row: self.focus_table_cell_widget(r, 6))
            qty_received.lineEdit().returnPressed.connect(lambda r=row: self.focus_table_cell_widget(r, 7))
            price_box.lineEdit().returnPressed.connect(lambda r=row: self.focus_table_cell_widget(r, 8))
            tax_box.lineEdit().returnPressed.connect(lambda r=row: self.advance_after_tax(r))

            row += 1

        self.recalculate_totals()

    def recalculate_totals(self):
        total = 0.0
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 6)
            price_widget = self.items_table.cellWidget(row, 7)
            tax_widget = self.items_table.cellWidget(row, 9)
            
            if qty_widget is None or price_widget is None:
                continue
            
            qty = float(qty_widget.value())
            price = float(price_widget.value())
            discount = self._line_discount_amount(row, qty, price)
            tax = float(tax_widget.value()) if tax_widget else 0.0
            
            # Line total = (Qty * Price) - Discount + Tax
            line_total = max(0.0, (qty * price) - discount + tax)
            total += line_total
            
            # Update column 10: Line Total
            item = self.items_table.item(row, 10)
            if item is not None:
                item.setText(f"{line_total:.2f}")
            self.update_discount_display(row)
        
        self.total_label.setText(f"{total:.2f}")
        # Recalculate landing costs whenever totals change
        self.recalculate_landing_costs()

    def recalculate_landing_costs(self):
        """
        Calculate landing cost for each line item by distributing header-level fees.
        Landing Cost = Line Total * (Total with Fees / Line Subtotal)
        
        This matches the sales effective_line_total pattern.
        """
        # Get header adjustments (amount fields, matching purchase invoice)
        header_discount = max(0.0, self._read_money(self.header_discount_edit))
        tax_236g = max(0.0, self._read_money(self.tax_236g_edit))
        tax_236h = max(0.0, self._read_money(self.tax_236h_edit))
        sales_tax = max(0.0, self._read_money(self.sales_tax_edit))
        cn_adjustment = max(0.0, self._read_money(self.cn_adjustment_edit))
        
        # Calculate subtotal and total from all line items
        line_subtotal = 0.0
        for row in range(self.items_table.rowCount()):
            item = self.items_table.item(row, 10)
            if item:
                line_subtotal += max(0.0, self._read_money(item))

        header_discount = min(header_discount, line_subtotal)
        taxable = max(0.0, line_subtotal - header_discount)
        net_amount = max(0.0, taxable + tax_236g + tax_236h + sales_tax)
        # Keep landing-cost distribution aligned with purchase invoice behavior.
        total_with_fees = max(0.0, line_subtotal - header_discount + tax_236g + tax_236h + sales_tax - cn_adjustment)
        
        # Update header displays
        self.subtotal_label.setText(f"{line_subtotal:.2f}")
        self.taxable_label.setText(f"{taxable:.2f}")
        self.net_amount_label.setText(f"{net_amount:.2f}")
        self.total_with_fees_label.setText(f"{total_with_fees:.2f}")
        self.calculate_payment()
        self.update_due_date_availability()
        
        # Calculate distribution factor
        if line_subtotal > 0:
            distribution_factor = total_with_fees / line_subtotal
        else:
            distribution_factor = 1.0
        
        # Store landing costs in _line_refs for later use
        for row in range(len(self._line_refs)):
            item = self.items_table.item(row, 10)
            if item:
                line_total = max(0.0, self._read_money(item))
                landing_cost = max(0.0, line_total * distribution_factor)
                self._line_refs[row]["landing_cost"] = landing_cost
        self.schedule_grn_draft_save()


    def create_stock_batches_from_receipts(self, receipt_rows, grn_number):
        posted_rows = 0

        for row in receipt_rows:
            product_id = int(row.get("product_id") or 0)
            qty_received = int(row.get("qty_received") or 0)
            unit_price = float(row.get("unit_price") or 0.0)
            landing_cost = float(row.get("landing_cost") or unit_price)
            purchaseitem_id = row.get("purchaseitem_id")
            batch_no = row.get("batch_no") or None
            expiry_date = row.get("expiry_date") or None

            if product_id <= 0 or qty_received <= 0:
                continue

            try:
                pack_size = int(fetch_product_pack_size(product_id) or 1)
            except Exception:
                pack_size = 1

            if pack_size <= 0:
                pack_size = 1

            total_received_units = int(qty_received * pack_size)
            # landing_cost is the total allocated cost for the received line.
            # Convert it to an actual per-unit cost for stock valuation / COGS.
            landing_cost_per_unit = round(
                landing_cost / (qty_received * pack_size), 6
            ) if qty_received > 0 and pack_size > 0 else 0.0

            insert_batch_record(
                {
                    "batch_no": batch_no,
                    "expiry_date": expiry_date,
                    "product_id": product_id,
                    "purchaseitem_id": purchaseitem_id if purchaseitem_id else None,
                    "total_received": total_received_units,
                    "paid_qty": total_received_units,
                    "quantity_remaining": total_received_units,
                    "unit_cost": landing_cost_per_unit,
                    "source": "PURCHASE",
                }
            )
            mark_product_used(product_id)

            posted_rows += 1

        return posted_rows

    def _collect_grn_header_amounts(self):
        return {
            "header_discount": self._read_money(self.header_discount_edit),
            "tax_236g": self._read_money(self.tax_236g_edit),
            "tax_236h": self._read_money(self.tax_236h_edit),
            "sales_tax": self._read_money(self.sales_tax_edit),
            "cn_adjustment": self._read_money(self.cn_adjustment_edit),
            "subtotal": self._read_money(self.subtotal_label),
            "taxable": self._read_money(self.taxable_label),
            "netamount": self._read_money(self.net_amount_label),
            "total_value": self._read_money(self.total_with_fees_label),
        }

    def _collect_receipt_rows(self, grn_id):
        line_count = 0
        receipt_rows = []

        for row, line_ref in enumerate(self._line_refs):
            batch_widget = self.items_table.cellWidget(row, 1)
            expiry_widget = self.items_table.cellWidget(row, 2)
            qty_widget = self.items_table.cellWidget(row, 6)
            price_widget = self.items_table.cellWidget(row, 7)
            tax_widget = self.items_table.cellWidget(row, 9)

            if qty_widget is None or price_widget is None:
                continue

            line_payload = normalize_grn_receipt_line(
                row_number=row + 1,
                po_line_id=int(line_ref.get("po_line_id") or 0),
                product_id=int(line_ref.get("product_id") or 0),
                qty_received=int(qty_widget.value()),
                unit_price=float(price_widget.value()),
                batch_no=batch_widget.text().strip() if batch_widget else "",
                expiry_date=expiry_widget.text().strip() if expiry_widget else "",
                discount=self._line_discount_amount(row, int(qty_widget.value()), float(price_widget.value())),
                tax=float(tax_widget.value()) if tax_widget else 0.0,
                landing_cost=line_ref.get("landing_cost") or float(price_widget.value()),
                expiry_parser=parse_expiry_month_year,
            )
            if line_payload is None:
                continue

            insert_goods_receipt_line(grn_id, line_payload)
            line_count += 1
            receipt_rows.append(dict(line_payload))

        return line_count, receipt_rows

    def get_po_supplier(self, po_id):
        return resolve_po_supplier_id(int(po_id))

    def update_po_status_from_receipts(self, po_id):
        new_status = recompute_po_status_from_receipts(int(po_id))
        return new_status

    def create_bill_from_grn(self, po_id, grn_number, receipt_rows, totals, billing_data, payment_data):
        supplier_id = self.get_po_supplier(po_id)
        if supplier_id <= 0:
            raise Exception("Invalid supplier on selected PO.")

        session_id = get_active_session_id(strict=True)
        if session_id is None:
            raise Exception("No active session found for billing.")

        subtotal = float(totals.get("subtotal") or 0.0)
        discount = float(totals.get("discount") or 0.0)
        taxable = float(totals.get("taxable") or 0.0)
        tax_236g = float(totals.get("tax_236g") or 0.0)
        tax_236h = float(totals.get("tax_236h") or 0.0)
        sales_tax = float(totals.get("sales_tax") or 0.0)
        netamount = float(totals.get("netamount") or 0.0)
        cn_adjustment = float(totals.get("cn_adjustment") or 0.0)
        total_value = float(totals.get("total") or 0.0)
        rep_id = billing_data.get("rep")
        paid = float(billing_data.get("paid") or 0.0)
        remaining = float(billing_data.get("remaining") or 0.0)
        writeoff = float(billing_data.get("writeoff") or 0.0)
        payable = float(billing_data.get("payable") or 0.0)
        receivable = float(billing_data.get("receivable") or 0.0)
        due_date = billing_data.get("due_date")
        purchase_header_payload = build_purchase_header_payload(
            supplier=supplier_id,
            rep=rep_id,
            sellerinvoice=grn_number,
            subtotal=subtotal,
            discount=discount,
            taxable=taxable,
            tax_236g=tax_236g,
            tax_236h=tax_236h,
            sales_tax=sales_tax,
            netamount=netamount,
            cn_adjustment=cn_adjustment,
            total=total_value,
            paid=paid,
            remaining=remaining,
            session_id=int(session_id),
            settlement={
                "writeoff": writeoff,
                "payable": payable,
                "receivable": receivable,
                "due_date": due_date,
            },
        )
        purchase_id = insert_purchase_header(purchase_header_payload)

        item_rows = 0
        for row in receipt_rows:
            product_id = int(row.get("product_id") or 0)
            qty_received = float(row.get("qty_received") or 0.0)
            unit_price = float(row.get("unit_price") or 0.0)
            discount = float(row.get("discount") or 0.0)
            tax = float(row.get("tax") or 0.0)
            landing_cost = float(row.get("landing_cost") or unit_price)

            if product_id <= 0 or qty_received <= 0:
                continue

            # Line total = (Qty * Price) - Discount + Tax
            line_total = (qty_received * unit_price) - discount + tax
            purchaseitem_id = insert_purchase_item(
                purchase_id,
                {
                    "product": product_id,
                    "qty": qty_received,
                    "bonus": 0,
                    "rate": unit_price,
                    "item_discount": discount,
                    "item_tax": tax,
                    "item_total": line_total,
                    "landing_cost": landing_cost,
                },
            )
            row["purchaseitem_id"] = purchaseitem_id
            item_rows += 1

        if item_rows == 0:
            raise Exception("Purchase bill creation failed: no bill items were created.")

        balances = fetch_supplier_balances(supplier_id)
        supplier_txn_payload = build_supplier_transaction_payload(
            purchase_id=purchase_id,
            supplier_id=supplier_id,
            rep_id=rep_id,
            session_id=int(session_id),
            total=total_value,
            paid=paid,
            settlement={"payable": payable, "receivable": receivable},
            payable_before=balances["payable_before"],
            receiveable_before=balances["receiveable_before"],
            payment=payment_data,
        )
        insert_supplier_transaction(supplier_txn_payload)
        update_supplier_balances(
            supplier_id,
            payable_after=supplier_txn_payload["payable_after"],
            receiveable_after=supplier_txn_payload["receiveable_after"],
        )
        update_goods_receipt_status(grn_number, "billed")

        return purchase_id

    def validate_receipt_quantities(self):
        under_received_lines = []
        over_received_lines = []
        positive_received_lines = 0

        for row in range(self.items_table.rowCount()):
            product_item = self.items_table.item(row, 0)
            ordered_item = self.items_table.item(row, 3)
            remaining_item = self.items_table.item(row, 5)
            qty_widget = self.items_table.cellWidget(row, 6)

            if qty_widget is None:
                continue

            product_name = str(product_item.text() if product_item else "")
            qty_ordered = int(ordered_item.text() if ordered_item and ordered_item.text() else 0)
            qty_remaining = int(remaining_item.text() if remaining_item and remaining_item.text() else 0)
            qty_received = int(qty_widget.value())

            if qty_received > 0:
                positive_received_lines += 1

            if 0 < qty_received < qty_remaining:
                under_received_lines.append((product_name, qty_remaining, qty_received))
            elif qty_received > qty_remaining:
                over_received_lines.append((product_name, qty_remaining, qty_received))

        if positive_received_lines == 0:
            AppMessageBox.warning(self, "No Receipt", "At least one line must have received quantity greater than zero.")
            return False

        if under_received_lines:
            preview = "\n".join(
                f"- {name}: remaining {remaining}, this GRN {received}"
                for name, remaining, received in under_received_lines[:8]
            )
            if len(under_received_lines) > 8:
                preview += f"\n... and {len(under_received_lines) - 8} more line(s)."

            _, accepted = AppMessageBox.confirm(
                self,
                "Under Receipt Detected",
                "Some lines are received less than the remaining PO quantity.\n"
                "Payment will be based only on received quantities.\n\n"
                f"{preview}\n\n"
                "Do you want to continue?",
                confirm_label="Continue",
                cancel_label="Cancel",
                kind="warning",
            )
            if not accepted:
                return False

        if over_received_lines:
            preview = "\n".join(
                f"- {name}: remaining {remaining}, this GRN {received}"
                for name, remaining, received in over_received_lines[:8]
            )
            if len(over_received_lines) > 8:
                preview += f"\n... and {len(over_received_lines) - 8} more line(s)."

            AppMessageBox.warning(
                self,
                "Over Receipt Detected",
                "Some lines exceed the remaining quantity on the PO.\n"
                "A GRN cannot receive more than the remaining open quantity.\n\n"
                f"{preview}\n\n"
                "Please reduce the received quantity and try again.",
            )
            return False

        return True

    def collect_billing_data(self, supplier_id, grn_number):
        rep = self.rep_combo.currentData()

        subtotal = max(0.0, self._read_money(self.subtotal_label))
        discount = min(max(0.0, self._read_money(self.header_discount_edit)), subtotal)
        taxable = max(0.0, self._read_money(self.taxable_label))
        tax_236g = max(0.0, self._read_money(self.tax_236g_edit))
        tax_236h = max(0.0, self._read_money(self.tax_236h_edit))
        sales_tax = max(0.0, self._read_money(self.sales_tax_edit))
        netamount = max(0.0, self._read_money(self.net_amount_label))
        cn_adjustment = max(0.0, self._read_money(self.cn_adjustment_edit))
        total = max(0.0, self._read_money(self.total_with_fees_label))
        paid = max(0.0, self._read_money(self.paid_amount))
        remaining = self._read_money(self.remaining_amount)

        due_date = self.compute_due_date() if remaining > 0 and not self.writeoff_check.isChecked() else None

        session_id = get_active_session_id(strict=True)
        return collect_grn_billing_data(
            supplier_id=supplier_id,
            rep=rep,
            grn_number=grn_number,
            subtotal=subtotal,
            discount=discount,
            taxable=taxable,
            tax_236g=tax_236g,
            tax_236h=tax_236h,
            sales_tax=sales_tax,
            netamount=netamount,
            cn_adjustment=cn_adjustment,
            total=total,
            paid=paid,
            remaining=remaining,
            writeoff_enabled=self.writeoff_check.isChecked(),
            due_date=due_date,
            session_id=session_id,
        )

    def get_next_grn_number(self):
        return fetch_next_grn_number()

    @Permissions.require_permission('grn.create')
    def save_grn(self):
        if not require_open_session(self):
            return

        po_id = self.po_combo.currentData()
        if not po_id:
            AppMessageBox.warning(self, "Missing PO", "Select a purchase order first.")
            return

        if self.items_table.rowCount() == 0:
            AppMessageBox.warning(self, "No Lines", "Selected PO has no items.")
            return

        if not self.validate_receipt_quantities():
            return

        grn_number = (self.grn_number_edit.text() or "").strip()
        if not grn_number:
            grn_number = self.get_next_grn_number()
        else:
            grn_number = grn_number.upper()
            if not re.fullmatch(r"GRN-\d+", grn_number):
                AppMessageBox.warning(
                    self,
                    "Invalid GRN Number",
                    "GRN number must follow format GRN-<digits>, e.g. GRN-1001.",
                )
                return

        _, accepted = AppMessageBox.confirm(
            self,
            "Confirm Save",
            "Would you like to save the GRN and generate its purchase invoice?",
            confirm_label="Save GRN",
            cancel_label="Cancel",
            kind="question",
        )
        if not accepted:
            return

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.error(self, "Error", "Could not start transaction.")
            return

        try:
            session_id = get_active_session_id(strict=True)
            supplier_id = self.get_po_supplier(int(po_id))
            billing_data = self.collect_billing_data(supplier_id, grn_number)
            payment_data = self.payment_handler.payment_data.copy()
            header_values = self._collect_grn_header_amounts()
            grn_payload = build_goods_receipt_payload(
                grn_number=grn_number,
                po_id=int(po_id),
                grn_date=self.grn_date_edit.date().toString("yyyy-MM-dd"),
                total_value=header_values["total_value"],
                header_discount=header_values["header_discount"],
                tax_236g=header_values["tax_236g"],
                tax_236h=header_values["tax_236h"],
                sales_tax=header_values["sales_tax"],
                cn_adjustment=header_values["cn_adjustment"],
                taxable=header_values["taxable"],
                netamount=header_values["netamount"],
                session_id=session_id,
                notes=(self.notes_edit.text() or "").strip(),
            )
            grn_id = insert_goods_receipt_header(grn_payload)
            line_count, receipt_rows = self._collect_receipt_rows(grn_id)

            if line_count == 0:
                raise Exception("At least one line must have received quantity > 0.")

            totals_payload = collect_grn_totals_payload(
                subtotal=header_values["subtotal"],
                discount=header_values["header_discount"],
                taxable=header_values["taxable"],
                tax_236g=header_values["tax_236g"],
                tax_236h=header_values["tax_236h"],
                sales_tax=header_values["sales_tax"],
                netamount=header_values["netamount"],
                cn_adjustment=header_values["cn_adjustment"],
                total=header_values["total_value"],
            )
            purchase_bill_id = self.create_bill_from_grn(
                po_id=int(po_id),
                grn_number=grn_number,
                receipt_rows=receipt_rows,
                totals=totals_payload,
                billing_data=billing_data,
                payment_data=payment_data,
            )

            stock_batch_count = self.create_stock_batches_from_receipts(receipt_rows, grn_number)
            if stock_batch_count <= 0:
                raise Exception("Stock posting failed: no batch rows were created.")

            po_status = self.update_po_status_from_receipts(int(po_id))

            if not db.commit():
                raise Exception("Could not commit GRN transaction.")

            self._discard_current_grn_draft()

            try:
                log_activity(
                    category="procurement",
                    action="grn_created",
                    entity_type="goods_receipt",
                    entity_id=grn_id,
                    note=f"Created GRN {grn_number} against PO ID {int(po_id)} with {line_count} lines, bill #{purchase_bill_id}, {stock_batch_count} stock batch postings, PO status {po_status}."
                )
            except Exception as exc:
                print("Activity log failed (non-blocking):", exc)

            try:
                log_activity(
                    category="procurement",
                    action="grn_billed",
                    entity_type="purchase",
                    entity_id=purchase_bill_id,
                    note=f"Generated purchase bill #{purchase_bill_id} from GRN {grn_number}."
                )
            except Exception as exc:
                print("GRN billing activity log failed (non-blocking):", exc)

            AppMessageBox.success(self, "Saved", f"GRN {grn_number} created successfully.")
            self.grn_list_signal.emit()

        except Exception as exc:
            db.rollback()
            AppMessageBox.error(self, "Save Failed", str(exc))
