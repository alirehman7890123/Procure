import re

from PySide6.QtWidgets import QWidget, QApplication, QCompleter,QAbstractItemView, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget, QStyledItemDelegate
from PySide6.QtCore import QFile, Qt, QStringListModel, QDate, QTimer, Signal, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent
from functools import partial
from PySide6.QtGui import QKeySequence, QShortcut

from utilities.session_gate import require_open_session
from utilities.session_service import get_active_session_id

from utilities.stylus import load_stylesheets
from utilities.payment_handler import PaymentMethodHandler
from utilities.activity_logger import log_activity
from utilities.permissions import Permissions
from utilities.app_messagebox import AppMessageBox
from utilities.product_search_widget import ProductSearchBox
from services.purchase_posting_service import (
    build_purchase_header_payload,
    build_supplier_transaction_payload,
    compute_purchase_settlement,
)
from services.purchase_items_service import (
    build_batch_payload,
    compute_purchase_distribution_factor,
    normalize_purchase_item_row,
    parse_expiry_to_db_date,
)
from services.purchase_transaction_service import (
    fetch_product_pack_size,
    fetch_supplier_balances,
    insert_batch_record,
    insert_purchase_header,
    insert_purchase_item,
    insert_supplier_transaction,
    mark_product_used,
    update_supplier_balances,
)
from services.purchase_draft_service import (
    delete_purchase_draft,
    load_latest_purchase_draft,
    save_purchase_draft,
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

    def mousePressEvent(self, event):
        if not self.hasFocus():
            self._select_on_release = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._select_on_release:
            self._select_on_release = False
            self.selectAll()


class LivePriceDelegate(QStyledItemDelegate):
    def __init__(self, on_text_changed, parent=None):
        super().__init__(parent)
        self.on_text_changed = on_text_changed

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)

        if isinstance(editor, QLineEdit):
            editor.textChanged.connect(self.on_text_changed)

        return editor


class AddPurchaseWidget(QWidget):


    def __init__(self, parent=None):

        super().__init__(parent)
        
        
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop)
        self.current_purchase_draft_id = None
        self._purchase_draft_resume_checked = False
        self._suspend_purchase_draft_autosave = False
        self._draft_save_in_progress = False
        self._draft_autosave_timer = QTimer(self)
        self._draft_autosave_timer.setSingleShot(True)
        self._draft_autosave_timer.timeout.connect(self._save_purchase_draft_snapshot)
        
        
        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Invoice", objectName="SectionTitle")
        heading.setStyleSheet('color: #2F5D7C')
        self.invoicelist = QPushButton("Invoice List", objectName="TopRightButton")
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.invoicelist)

        self.layout.addLayout(header_layout)
        
        
        # Add Supplier Section 
        self.add_supplier_section()
       
        
        
        
        
        
        ### Populate Labels & Entry Line
        self.populate_label_line()
        
        
        self.populate_totals_section()
        self._install_select_all_focus_behavior()
        self._setup_purchase_draft_autosave()

        
        
        
        
        
        self.setStyleSheet(load_stylesheets())
        QTimer.singleShot(0, self.update_purchase_table_height)
        
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.add_row)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, activated=self.remove_row)
        
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.save_purchase)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.save_purchase)

        
    
    def add_supplier_section(self):
        
        # ---------------------------
        # Supplier Section Frame
        # ---------------------------
        supplier_frame = QFrame()
        supplier_frame.setObjectName("sectionCard")
        self.supplier_frame = supplier_frame
        supplier_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        supplier_layout = QVBoxLayout(supplier_frame)
        supplier_layout.setContentsMargins(10, 10, 10, 10)
        supplier_layout.setSpacing(10)

        # Top Row Layout
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        supplier = QLabel("Supplier")
        rep = QLabel("Seller Rep")
        seller_invoice = QLabel("Seller Invoice")

        self.supplier_edit = QComboBox()
        self.new_supplier_btn = QPushButton("+")
        
        
        self.rep_edit = QComboBox()
        self.new_rep_btn = QPushButton("+")
        
        self.invoice_edit = QLineEdit()

        # Optional placeholders
        self.supplier_edit.setPlaceholderText("Select supplier")
        self.rep_edit.setPlaceholderText("Select rep")
        self.invoice_edit.setPlaceholderText("Invoice number")

        # Add widgets
        top_row.addWidget(supplier, 1)
        top_row.addWidget(self.supplier_edit, 2)
        top_row.addWidget(self.new_supplier_btn, 1)
        
        
        spacer = QLabel()
        top_row.addWidget(spacer)
           
        
        top_row.addWidget(rep, 1)
        top_row.addWidget(self.rep_edit, 2)
        top_row.addWidget(self.new_rep_btn, 1)
        
        spacer = QLabel()
        
        top_row.addWidget(spacer, 3)
        top_row.addWidget(seller_invoice, 1)
        top_row.addWidget(self.invoice_edit, 2)

        supplier_layout.addLayout(top_row)

        # Add frame to main layout
        self.layout.addWidget(supplier_frame)
        
        supplier.setStyleSheet("font-weight: 600;")
        rep.setStyleSheet("font-weight: 600;")
        seller_invoice.setStyleSheet("font-weight: 600;")
        
        btn_style = """
        QPushButton {
            background-color: #2d2d2d;
            color: white;
            border: 1px solid #444;
            border-radius: 4px;
            font-weight: bold;
            padding: 2px;
        }

        QPushButton:hover {
            background-color: #3a3a3a;
        }

        QPushButton:pressed {
            background-color: #1f1f1f;
        }
        """

        self.new_supplier_btn.setStyleSheet(btn_style)
        self.new_rep_btn.setStyleSheet(btn_style)
        
        self.new_supplier_btn.setFixedSize(28, 28)
        self.new_rep_btn.setFixedSize(28, 28)
        
        self.new_supplier_btn.clicked.connect(self.open_supplier_dialog)
        self.new_rep_btn.clicked.connect(self.open_rep_dialog)
        
        self.setup_supplier_rep_signals()
    
    
    
    
    
        

    def open_supplier_dialog(self):
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Supplier")
        dialog.setMinimumWidth(350)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("New Supplier")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        name_label = QLabel("Supplier Name")
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Enter supplier name")

        contact_label = QLabel("Contact")
        contact_edit = QLineEdit()
        contact_edit.setPlaceholderText("Enter contact")

        layout.addWidget(name_label)
        layout.addWidget(name_edit)
        layout.addWidget(contact_label)
        layout.addWidget(contact_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        def save_supplier():
            name = name_edit.text().strip()
            contact = contact_edit.text().strip()

            if not name:
                AppMessageBox.warning(dialog, "Validation Error", "Supplier name is required.")
                return

            query = QSqlQuery()
            query.prepare("""
                INSERT INTO supplier (
                    name,
                    contact
                )
                VALUES (?, ?)
            """)
            query.addBindValue(name)
            query.addBindValue(contact if contact else None)

            if not query.exec():
                AppMessageBox.critical(
                    dialog,
                    "Database Error",
                    f"Failed to save supplier:\n{query.lastError().text()}"
                )
                return

            supplier_id = query.lastInsertId()
            try:
                supplier_id = int(supplier_id)
            except Exception:
                supplier_id = None

            AppMessageBox.information(dialog, "Success", "Supplier added successfully.")
            dialog.accept()

            if hasattr(self, "populate_suppliers"):
                self.populate_suppliers(selected_supplier_id=supplier_id)


        save_btn.clicked.connect(save_supplier)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()



    def open_rep_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Sales Rep")
        dialog.setMinimumWidth(380)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("New Sales Rep")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        supplier_label = QLabel("Supplier")
        supplier_combo = QComboBox()

        # load suppliers
        query = QSqlQuery("""
            SELECT id, name
            FROM supplier
            ORDER BY name
        """)
        while query.next():
            supplier_id = query.value(0)
            supplier_name = query.value(1)
            supplier_combo.addItem(f"{supplier_id} - {supplier_name}", supplier_id)

        name_label = QLabel("Rep Name")
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Enter rep name")

        contact_label = QLabel("Contact")
        contact_edit = QLineEdit()
        contact_edit.setPlaceholderText("Enter contact")

        layout.addWidget(supplier_label)
        layout.addWidget(supplier_combo)
        layout.addWidget(name_label)
        layout.addWidget(name_edit)
        layout.addWidget(contact_label)
        layout.addWidget(contact_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        
        def save_rep():
            supplier_id = supplier_combo.currentData()
            name = name_edit.text().strip()
            contact = contact_edit.text().strip()

            if supplier_id is None:
                AppMessageBox.warning(dialog, "Validation Error", "Supplier is required.")
                return

            if not name:
                AppMessageBox.warning(dialog, "Validation Error", "Rep name is required.")
                return

            query = QSqlQuery()
            query.prepare("""
                INSERT INTO rep (
                    name,
                    supplier_id,
                    contact
                )
                VALUES (?, ?, ?)
            """)
            query.addBindValue(name)
            query.addBindValue(supplier_id)
            query.addBindValue(contact if contact else None)

            if not query.exec():
                AppMessageBox.critical(
                    dialog,
                    "Database Error",
                    f"Failed to save rep:\n{query.lastError().text()}"
                )
                return

            rep_id = query.lastInsertId()
            try:
                rep_id = int(rep_id)
            except Exception:
                rep_id = None

            AppMessageBox.information(dialog, "Success", "Rep added successfully.")
            dialog.accept()

            if hasattr(self, "populate_suppliers"):
                self.populate_suppliers(selected_supplier_id=supplier_id, selected_rep_id=rep_id)
                
                
                
        save_btn.clicked.connect(save_rep)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()
    
    
    
    
    
    
    def setup_supplier_rep_signals(self):
        
        self.supplier_edit.currentIndexChanged.connect(self.populate_reps)    

    def force_uppercase_line_edit(self, line_edit, text):
        cursor_pos = line_edit.cursorPosition()
        upper_text = str(text or "").upper()
        if line_edit.text() == upper_text:
            return
        line_edit.blockSignals(True)
        line_edit.setText(upper_text)
        line_edit.setCursorPosition(min(cursor_pos, len(upper_text)))
        line_edit.blockSignals(False)
            
        
        
    def update_line_total(self):
        
        qty = self.qty_edit.text()
        rate = self.rate_edit.text()
        
        
        qty_value = max(0.0, self._float_or_default(qty, 0.0))
        rate_value = max(0.0, self._float_or_default(rate, 0.0))
        discount_value = max(0.0, self._float_or_default(self.discount_edit.text(), 0.0))
        tax_value = max(0.0, self._float_or_default(self.tax_edit.text(), 0.0))

        subtotal = qty_value * rate_value
        flat_discount = min(subtotal, (subtotal * discount_value) / 100.0)
        taxable_amount = max(0.0, subtotal - flat_discount)
        tax_amount = (taxable_amount * tax_value) / 100.0

        # update the total label
        total = taxable_amount + tax_amount
        self.amount_edit.setText(f"{total:.2f}")

    def populate_totals_section(self):
        
        field_style = """
            QLabel {
                margin: 0;
                padding-left: 0;
                font-size: 12px;
            }

            QLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                background-color: #f9f9f9;
                color: #333333;
            }

            QComboBox {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                background-color: #f9f9f9;
                color: #333333;
            }
            
            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus {
                border: 2px solid #5B8FB8;
                background: #F2F8FC;
                color: #333333;
            }

            KeyUpLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                background-color: #f9f9f9;
                color: #333333;
            }
        """

    
        totals_frame = QFrame()
        totals_frame.setObjectName("sectionCard")
        self.totals_frame = totals_frame
        totals_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setContentsMargins(10, 10, 10, 10)
        totals_layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        # -----------------------------
        # Row 1: Invoice math
        # -----------------------------
        gross_label = QLabel("Gross Amount")
        self.gross_entry = QLineEdit("0.00")
        self.gross_entry.setReadOnly(True)
        self.gross_entry.setStyleSheet(field_style)

        discount_label = QLabel("Discount")
        self.discount_entry = QLineEdit()
        self.discount_entry.setStyleSheet(field_style)

        taxable_label = QLabel("Taxable")
        self.taxable_entry = QLineEdit("0.00")
        self.taxable_entry.setReadOnly(True)
        self.taxable_entry.setStyleSheet(field_style)

        tax_236g_label = QLabel("Tax 236(G)")
        self.tax_236g_entry = QLineEdit()
        self.tax_236g_entry.setStyleSheet(field_style)

        tax_236h_label = QLabel("Tax 236(H)")
        self.tax_236h_entry = QLineEdit()
        self.tax_236h_entry.setStyleSheet(field_style)

        sales_tax_label = QLabel("Sales Tax")
        self.sales_tax_entry = QLineEdit()

        net_amount_label = QLabel("Net Amount")
        self.net_amount_entry = QLineEdit("0.00")
        self.net_amount_entry.setReadOnly(True)
        
        payment_method_label = QLabel("Payment Method")
        payment_method_label.setMinimumWidth(180)
        
        self.payment_handler = PaymentMethodHandler(self)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)

        self.due_date_combo = QComboBox()
        self.due_date_combo.addItems(["None", "+15 days", "+30 days", "+45 days", "+60 days", "+90 days"])
        self.due_date_combo.setCurrentText("None")
        self.due_date_combo.setEnabled(False)
        

        grid.addWidget(gross_label,        0, 0)
        grid.addWidget(discount_label,     0, 1)
        grid.addWidget(taxable_label,      0, 2)
        grid.addWidget(tax_236g_label,     0, 3)
        grid.addWidget(tax_236h_label,     0, 4)
        grid.addWidget(sales_tax_label,    0, 5)
        grid.addWidget(net_amount_label,   0, 6)
        grid.addWidget(payment_method_label, 0, 7)
        grid.addWidget(self.payment_method, 0 , 8)

        grid.addWidget(self.gross_entry,       1, 0)
        grid.addWidget(self.discount_entry,    1, 1)
        grid.addWidget(self.taxable_entry,     1, 2)
        grid.addWidget(self.tax_236g_entry,    1, 3)
        grid.addWidget(self.tax_236h_entry,    1, 4)
        grid.addWidget(self.sales_tax_entry,   1, 5)
        grid.addWidget(self.net_amount_entry,  1, 6)

        # -----------------------------
        # Row 2: Settlement
        # -----------------------------
        cn_adjust_label = QLabel("CN Adjustment")
        self.cn_adjustment_entry = QLineEdit()

        final_label = QLabel("Final Amount")
        self.final_amount = QLineEdit("0.00")
        self.final_amount.setReadOnly(True)

        self.paid_label = QLabel("Paid Amount")
        self.paid_amount = QLineEdit()

        self.remaining_label = QLabel("Remaining Amount")
        self.remainingdata = QLineEdit("0.00")
        self.remainingdata.setReadOnly(True)

        self.writeoff_check = QCheckBox("Write-off Remaining")
        self.writeoff_check.setStyleSheet("QCheckBox { color: #333; }")

        grid.addWidget(cn_adjust_label,    2, 4)
        grid.addWidget(final_label,        2, 5)
        grid.addWidget(self.paid_label,    2, 6)
        grid.addWidget(self.remaining_label, 2, 7)

        due_date_label = QLabel("Due Date")
        grid.addWidget(due_date_label, 2, 0)

        grid.addWidget(self.cn_adjustment_entry, 3, 4)
        grid.addWidget(self.final_amount,        3, 5)
        grid.addWidget(self.paid_amount,         3, 6)
        grid.addWidget(self.remainingdata,       3, 7)
        grid.addWidget(self.due_date_combo,      3, 0)

        grid.addWidget(self.writeoff_check,      3, 8)

        # -----------------------------
        # Stretch
        # -----------------------------
        for col in range(9):
            grid.setColumnStretch(col, 1)

        totals_layout.addLayout(grid)

        # -----------------------------
        # Signals
        # -----------------------------
        self.discount_entry.textChanged.connect(self.update_total_amount)
        self.tax_236g_entry.textChanged.connect(self.update_total_amount)
        self.tax_236h_entry.textChanged.connect(self.update_total_amount)
        self.sales_tax_entry.textChanged.connect(self.update_total_amount)
        self.cn_adjustment_entry.textChanged.connect(self.update_total_amount)

        self.paid_amount.textChanged.connect(self.calculate_payment)
        self.paid_amount.textChanged.connect(self.update_due_date_availability)
        self.writeoff_check.toggled.connect(self.update_due_date_availability)

        # -----------------------------
        # Add totals frame
        # -----------------------------
        self.layout.addWidget(totals_frame)

        # -----------------------------
        # Save button
        # -----------------------------
        save_row = QHBoxLayout()
        save_row.addStretch()
        self.clear_purchase_button = QPushButton("Clear Invoice", objectName="TopRightButton")
        self.clear_purchase_button.setCursor(Qt.PointingHandCursor)
        save_row.addWidget(self.clear_purchase_button)

        addpurchase = QPushButton("Save Purchase Invoice", objectName="SaveButton")
        addpurchase.setCursor(Qt.PointingHandCursor)
        addpurchase.setMinimumWidth(220)
        save_row.addWidget(addpurchase)
        self.save_purchase_button = addpurchase

        self.layout.addLayout(save_row)

        self.clear_purchase_button.clicked.connect(self.confirm_clear_purchase)
        addpurchase.clicked.connect(self.save_purchase)
    
    
    
    
    
    
    def add_table(self):
        
         # Purchse Table
        self.row_height = 30
        self.min_visible_rows = 5
    
        self.table = MyTable(column_ratios=[0.03, 0.25, 0.07, 0.10, 0.05, 0.05, 0.07, 0.07, 0.05, 0.10, 0.05])
        headers = ["#", "Product", "Batch", "Expiry (MM-YY)", "Qty", "Bonus", "Rate", "Disc % ", "Tax %", "Total", "X"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setTabKeyNavigation(False)
        
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.table.verticalHeader().setFixedWidth(0)
        remove_col = headers.index("X")
        self.table.horizontalHeaderItem(remove_col).setTextAlignment(Qt.AlignCenter)
        
        self.table.setStyleSheet("QTableWidget::item { color: #333; border: none;}")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   
        
        self.table.setMinimumWidth(900)
        self.table.setMinimumHeight(0)
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)
        

        # Alternating row colors
        self.table.setAlternatingRowColors(True)

        # Selection behaviour
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        return self.table
        
        
        
        
    def populate_label_line(self):
    
        label_entry_frame = QFrame()
        
        label_entry_frame.setObjectName("sectionCard")
        label_entry_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.label_entry_frame = label_entry_frame

        label_entry_layout = QVBoxLayout(label_entry_frame)
        label_entry_layout.setContentsMargins(10, 10, 10, 10)
        label_entry_layout.setSpacing(10)
        self.label_entry_layout = label_entry_layout

        field_style = """
            QLabel {
                margin: 0;
                padding-left: 0;
                font-size: 12px;
            }

            QLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                background-color: #f9f9f9;
                color: #333333;
            }

            QComboBox {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                background-color: #f9f9f9;
                color: #333333;
            }
            
            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus {
                border: 2px solid #5B8FB8;
                background: #F2F8FC;
                color: #333333;
            }

            KeyUpLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                background-color: #f9f9f9;
                color: #333333;
            }
        """

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(10, 10, 10, 10)
        self.entry_grid = grid

        # -----------------------------
        # Labels
        # -----------------------------
        product_label = QLabel("Product")
        product_label.setStyleSheet(field_style)

        batch_label = QLabel("Batch")
        batch_label.setStyleSheet(field_style)

        expiry_label = QLabel("Expiry (MM-YY)")
        expiry_label.setStyleSheet(field_style)

        qty_label = QLabel("Packs")
        qty_label.setStyleSheet(field_style)

        bonus_label = QLabel("Bonus")
        bonus_label.setStyleSheet(field_style)

        rate_label = QLabel("Cost")
        rate_label.setStyleSheet(field_style)

        discount_label = QLabel("Disc %")
        discount_label.setStyleSheet(field_style)

        tax_label = QLabel("Tax %")
        tax_label.setStyleSheet(field_style)

        total_label = QLabel("Total")
        total_label.setStyleSheet(field_style)

        add_button_label = QLabel("Action")
        add_button_label.setStyleSheet(field_style)

        # -----------------------------
        # Entry widgets
        # -----------------------------
        self.item = ProductSearchBox(self, placeholder="select product")
        self.item.wheelEvent = lambda event: event.ignore()
        self.item.setLineEdit(SelectAllLineEdit())
        self.item.lineEdit().editingFinished.connect(
            lambda c=self.item: self.handle_editing_finished(c)
        )
        self.item.product_selected.connect(
            lambda pid, name: self.on_completer_selected(name, self.item)
        )
        self.item.setStyleSheet(field_style)

        self.batch_edit = QLineEdit()
        self.batch_edit.setPlaceholderText("batch")
        self.batch_edit.setStyleSheet(field_style)
        self.batch_edit.textEdited.connect(lambda text: self.force_uppercase_line_edit(self.batch_edit, text))

        self.expiry_edit = SelectAllLineEdit()
        self.expiry_edit.setPlaceholderText("MM-YY")
        self.expiry_edit.setInputMask("00-00;_")
        self.expiry_edit.setStyleSheet(field_style)

        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText("qty")
        self.qty_edit.setStyleSheet(field_style)

        self.bonus_edit = QLineEdit()
        self.bonus_edit.setPlaceholderText("bonus")
        self.bonus_edit.setStyleSheet(field_style)

        self.rate_edit = QLineEdit()
        self.rate_edit.setPlaceholderText("rate")
        self.rate_edit.setStyleSheet(field_style)

        self.discount_edit = KeyUpLineEdit()
        self.discount_edit.setPlaceholderText("Disc %")
        self.discount_edit.setStyleSheet(field_style)

        self.tax_edit = KeyUpLineEdit()
        self.tax_edit.setPlaceholderText("Tax %")
        self.tax_edit.setStyleSheet(field_style)

        self.amount_edit = QLineEdit()
        self.amount_edit.setReadOnly(True)
        self.amount_edit.setText("0.00")
        self.amount_edit.setStyleSheet("""
            QLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                background-color: #f9f9f9;
                font-weight: bold;
            }
        """)

        add_button = QPushButton("Add", objectName="EntryButton")

        # -----------------------------
        # Add labels to row 0
        # -----------------------------
        grid.addWidget(product_label,    0, 0)
        grid.addWidget(batch_label,      0, 1)
        grid.addWidget(expiry_label,     0, 2)
        grid.addWidget(qty_label,        0, 3)
        grid.addWidget(bonus_label,      0, 4)
        grid.addWidget(rate_label,       0, 5)
        grid.addWidget(discount_label,   0, 6)
        grid.addWidget(tax_label,        0, 7)
        grid.addWidget(total_label,      0, 8)
        grid.addWidget(add_button_label, 0, 9)

        # -----------------------------
        # Add entries to row 1
        # -----------------------------
        grid.addWidget(self.item,         1, 0)
        grid.addWidget(self.batch_edit,   1, 1)
        grid.addWidget(self.expiry_edit,  1, 2)
        grid.addWidget(self.qty_edit,     1, 3)
        grid.addWidget(self.bonus_edit,   1, 4)
        grid.addWidget(self.rate_edit,    1, 5)
        grid.addWidget(self.discount_edit,1, 6)
        grid.addWidget(self.tax_edit,     1, 7)
        grid.addWidget(self.amount_edit,  1, 8)
        grid.addWidget(add_button,        1, 9)

        # -----------------------------
        # Stretch factors
        # -----------------------------
        grid.setColumnStretch(0, 3)
        for col in range(1, 10):
            grid.setColumnStretch(col, 1)

        # -----------------------------
        # Signals
        # -----------------------------
        self.qty_edit.textChanged.connect(self.update_total_amount)

        self.rate_edit.textChanged.connect(self.update_line_total)
        self.qty_edit.textChanged.connect(self.update_line_total)
        self.discount_edit.textChanged.connect(self.update_line_total)
        self.tax_edit.textChanged.connect(self.update_line_total)

        add_button.clicked.connect(self.add_row)

        # -----------------------------
        # Focus flow
        # -----------------------------
        QWidget.setTabOrder(self.item, self.batch_edit)

        self.item.lineEdit().returnPressed.connect(lambda: self.handle_item_return_pressed(self.item))
        self.batch_edit.returnPressed.connect(lambda: self.focus_next_field(self.expiry_edit))
        self.expiry_edit.returnPressed.connect(lambda: self.focus_next_field(self.qty_edit))
        self.qty_edit.returnPressed.connect(lambda: self.focus_next_field(self.bonus_edit))
        self.bonus_edit.returnPressed.connect(lambda: self.focus_next_field(self.rate_edit))
        self.rate_edit.returnPressed.connect(lambda: self.focus_next_field(self.discount_edit))
        self.discount_edit.returnPressed.connect(lambda: self.focus_next_field(self.tax_edit))
        self.tax_edit.returnPressed.connect(lambda: self.focus_next_field(add_button))

        # -----------------------------
        # Final layout
        # -----------------------------
        label_entry_layout.addLayout(grid)
        
        
        
        # add table
        table = self.add_table()
        
        label_entry_layout.addSpacing(10)
        label_entry_layout.addWidget(table)
        
        self.layout.addWidget(label_entry_frame)
            
        
    
    def on_payment_method_changed(self, method):
        
        success = self.payment_handler.handle_method_change(method)

        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)
            self.payment_handler.payment_data = self._normalize_payment_data({"payment_method": "Cash"})
        
        self.schedule_purchase_draft_save()
            
        
    
        
    def focus_next_field(self, widget):
        widget.setFocus()

        if hasattr(widget, "selectAll"):
            widget.selectAll()

    def _install_select_all_focus_behavior(self):
        widgets = [
            getattr(self, "supplier_edit", None),
            getattr(self, "rep_edit", None),
            getattr(self, "invoice_edit", None),
            getattr(self, "item", None),
            getattr(self, "batch_edit", None),
            getattr(self, "expiry_edit", None),
            getattr(self, "qty_edit", None),
            getattr(self, "bonus_edit", None),
            getattr(self, "rate_edit", None),
            getattr(self, "discount_edit", None),
            getattr(self, "tax_edit", None),
            getattr(self, "discount_entry", None),
            getattr(self, "tax_236g_entry", None),
            getattr(self, "tax_236h_entry", None),
            getattr(self, "sales_tax_entry", None),
            getattr(self, "cn_adjustment_entry", None),
            getattr(self, "paid_amount", None),
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

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            if isinstance(obj, QLineEdit) and not obj.isReadOnly():
                QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)

    def _setup_purchase_draft_autosave(self):
        self.invoice_edit.textChanged.connect(self.schedule_purchase_draft_save)
        self.supplier_edit.currentIndexChanged.connect(self.schedule_purchase_draft_save)
        self.rep_edit.currentIndexChanged.connect(self.schedule_purchase_draft_save)
        self.discount_entry.textChanged.connect(self.schedule_purchase_draft_save)
        self.tax_236g_entry.textChanged.connect(self.schedule_purchase_draft_save)
        self.tax_236h_entry.textChanged.connect(self.schedule_purchase_draft_save)
        self.sales_tax_entry.textChanged.connect(self.schedule_purchase_draft_save)
        self.cn_adjustment_entry.textChanged.connect(self.schedule_purchase_draft_save)
        self.paid_amount.textChanged.connect(self.schedule_purchase_draft_save)
        self.writeoff_check.toggled.connect(self.schedule_purchase_draft_save)
        self.due_date_combo.currentIndexChanged.connect(self.schedule_purchase_draft_save)

    def _current_purchase_draft_user_id(self):
        app = QApplication.instance()
        if app is None:
            return None
        return app.property("user_id")

    def _set_combo_current_data(self, combo, value):
        if combo is None:
            return False
        if value in (None, ""):
            return False
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return True
        return False

    def _format_draft_text(self, value, decimals=2):
        if value in (None, ""):
            return ""
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if decimals == 0:
            return str(int(number))
        return f"{number:.{decimals}f}"

    def _draft_has_meaningful_content(self):
        if self.table.rowCount() > 0:
            return True
        if self.invoice_edit.text().strip():
            return True
        if any(
            str(widget.text()).strip()
            for widget in [
                self.discount_entry,
                self.tax_236g_entry,
                self.tax_236h_entry,
                self.sales_tax_entry,
                self.cn_adjustment_entry,
                self.paid_amount,
            ]
            if widget is not None
        ):
            return True
        return False

    def _collect_purchase_draft_header(self):
        return {
            "supplier": self.supplier_edit.currentData(),
            "rep": self.rep_edit.currentData(),
            "sellerinvoice": self.invoice_edit.text().strip(),
            "discount": self.discount_entry.text().strip(),
            "tax_236g": self.tax_236g_entry.text().strip(),
            "tax_236h": self.tax_236h_entry.text().strip(),
            "sales_tax": self.sales_tax_entry.text().strip(),
            "cn_adjustment": self.cn_adjustment_entry.text().strip(),
            "paid": self.paid_amount.text().strip(),
            "writeoff_enabled": self.writeoff_check.isChecked(),
            "due_date_option": self.due_date_combo.currentText().strip(),
            "user_id": self._current_purchase_draft_user_id(),
            "session_id": get_active_session_id(strict=False),
            "payment_data": self._normalize_payment_data(self.payment_handler.payment_data.copy()),
        }

    def _collect_purchase_draft_rows(self):
        rows = []
        for row in range(self.table.rowCount()):
            product_combo = self.table.cellWidget(row, 1)
            batch_edit = self.table.cellWidget(row, 2)
            expiry_edit = self.table.cellWidget(row, 3)
            qty_edit = self.table.cellWidget(row, 4)
            bonus_edit = self.table.cellWidget(row, 5)
            rate_edit = self.table.cellWidget(row, 6)
            discount_edit = self.table.cellWidget(row, 7)
            tax_edit = self.table.cellWidget(row, 8)
            total_edit = self.table.cellWidget(row, 9)

            if product_combo is None:
                continue

            rows.append(
                {
                    "product": product_combo.currentData(),
                    "product_name": product_combo.currentText().strip(),
                    "batch": batch_edit.text().strip() if batch_edit else "",
                    "expiry": expiry_edit.text().strip() if expiry_edit else "",
                    "qty": qty_edit.text().strip() if qty_edit else "",
                    "bonus": bonus_edit.text().strip() if bonus_edit else "",
                    "rate": rate_edit.text().strip() if rate_edit else "",
                    "discount": discount_edit.text().strip() if discount_edit else "",
                    "tax": tax_edit.text().strip() if tax_edit else "",
                    "total": total_edit.text().strip() if total_edit else "",
                }
            )
        return rows

    def schedule_purchase_draft_save(self):
        if self._suspend_purchase_draft_autosave or self._draft_save_in_progress:
            return
        self._draft_autosave_timer.start(700)

    def _save_purchase_draft_snapshot(self):
        if self._suspend_purchase_draft_autosave or self._draft_save_in_progress:
            return

        if not self._draft_has_meaningful_content():
            return

        self._draft_save_in_progress = True
        try:
            self.current_purchase_draft_id = save_purchase_draft(
                self._collect_purchase_draft_header(),
                self._collect_purchase_draft_rows(),
                draft_id=self.current_purchase_draft_id,
            )
            print(f"Purchase draft autosaved successfully. Draft ID: {self.current_purchase_draft_id}")
        except Exception as exc:
            print(f"Purchase draft autosave failed: {exc}")
        finally:
            self._draft_save_in_progress = False

    def _discard_current_purchase_draft(self):
        if self.current_purchase_draft_id in (None, ""):
            return
        try:
            delete_purchase_draft(self.current_purchase_draft_id)
        except Exception as exc:
            print(f"Failed to delete purchase draft {self.current_purchase_draft_id}: {exc}")
            return
        print(f"Deleted purchase draft {self.current_purchase_draft_id}")
        self.current_purchase_draft_id = None

    def _restore_purchase_draft(self, draft_record):
        header = dict((draft_record or {}).get("header") or {})
        rows = list((draft_record or {}).get("rows") or [])

        self._suspend_purchase_draft_autosave = True
        try:
            self.clear_fields(reset_draft_state=False)
            self.current_purchase_draft_id = (draft_record or {}).get("id")

            self._set_combo_current_data(self.supplier_edit, header.get("supplier"))
            self.populate_reps()
            self._set_combo_current_data(self.rep_edit, header.get("rep"))

            self.invoice_edit.setText(str(header.get("sellerinvoice") or ""))
            self.discount_entry.setText(str(header.get("discount") or ""))
            self.tax_236g_entry.setText(str(header.get("tax_236g") or ""))
            self.tax_236h_entry.setText(str(header.get("tax_236h") or ""))
            self.sales_tax_entry.setText(str(header.get("sales_tax") or ""))
            self.cn_adjustment_entry.setText(str(header.get("cn_adjustment") or ""))
            self.paid_amount.setText(str(header.get("paid") or ""))
            self.writeoff_check.setChecked(bool(header.get("writeoff_enabled")))

            due_date_option = str(header.get("due_date_option") or "None")
            due_date_index = self.due_date_combo.findText(due_date_option, Qt.MatchFixedString)
            self.due_date_combo.setCurrentIndex(due_date_index if due_date_index >= 0 else 0)

            payment_data = dict(header.get("payment_data") or {})
            payment_method = str(payment_data.get("payment_method") or "Cash")
            payment_index = self.payment_method.findText(payment_method, Qt.MatchFixedString)
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentIndex(payment_index if payment_index >= 0 else 0)
            self.payment_method.blockSignals(False)
            self.payment_handler.payment_data = self._normalize_payment_data(payment_data)

            self.table.setRowCount(0)
            for row in rows:
                self._insert_purchase_table_row(
                    product_id=row.get("product"),
                    product_name=row.get("product_name") or "",
                    batch_data=row.get("batch") or "",
                    expiry_data=row.get("expiry") or "",
                    qty_data=str(row.get("qty") or ""),
                    bonus_data=str(row.get("bonus") or "0"),
                    rate_data=self._format_draft_text(row.get("rate"), 2),
                    discount_data=self._format_draft_text(row.get("discount"), 2),
                    tax_data=self._format_draft_text(row.get("tax"), 2),
                    total_data=self._format_draft_text(row.get("total"), 2),
                )

            self.update_total_amount()
            self.calculate_payment()
            self.update_due_date_availability()
            self.update_purchase_table_height()
            self.item.setFocus()
        finally:
            self._suspend_purchase_draft_autosave = False

    def prompt_resume_purchase_draft(self):
        if self._purchase_draft_resume_checked:
            return
        if self.table.rowCount() > 0:
            return

        self._purchase_draft_resume_checked = True
        try:
            draft_record = load_latest_purchase_draft(
                user_id=self._current_purchase_draft_user_id(),
                session_id=get_active_session_id(strict=False),
            )
        except Exception as exc:
            print(f"Could not load purchase draft for recovery: {exc}")
            return

        if not draft_record:
            return

        _, accepted = AppMessageBox.confirm(
            self,
            "Resume Draft Purchase",
            "An unfinished purchase invoice draft was found. Would you like to resume it?",
            confirm_label="Resume Draft",
            cancel_label="Discard Draft",
            kind="question",
        )

        if accepted:
            self._restore_purchase_draft(draft_record)
            return

        self.current_purchase_draft_id = draft_record.get("id")
        self._discard_current_purchase_draft()
        
        
    
        
    def update_total_amount(self):
        
        
        subtotal = 0.00
        for row in range(self.table.rowCount()):
            line_total_widget = self.table.cellWidget(row, 9)
            if line_total_widget is None:
                continue

            subtotal += max(0.0, self._float_or_default(line_total_widget.text(), 0.0))

        self.gross_entry.setText(f"{subtotal:.2f}")
        discount = min(max(0.0, self._float_or_default(self.discount_entry.text(), 0.0)), subtotal)
        taxable = subtotal - discount
        self.taxable_entry.setText(f"{taxable:.2f}")

        tax_236g = max(0.0, self._float_or_default(self.tax_236g_entry.text(), 0.0))
        tax_236h = max(0.0, self._float_or_default(self.tax_236h_entry.text(), 0.0))
        sales_tax = max(0.0, self._float_or_default(self.sales_tax_entry.text(), 0.0))
        tax_amount = tax_236h + sales_tax - tax_236g
        net_amount = max(0.0, taxable + tax_amount)
        self.net_amount_entry.setText(f"{net_amount:.2f}")

        cn_adjust = max(0.0, self._float_or_default(self.cn_adjustment_entry.text(), 0.0))
        final_amount = max(0.0, net_amount - cn_adjust)
        self.final_amount.setText(f"{final_amount:.2f}")
        
        self.final_amount.setStyleSheet("font-weight: bold;")
        
    


    def calculate_payment(self):
        finalamount = self._float_or_default(self.final_amount.text(), 0.0)
        paid = max(0.0, self._float_or_default(self.paid_amount.text(), 0.0))
        remaining = finalamount - paid
        self.remainingdata.setText(f"{remaining:.2f}")

    def update_due_date_availability(self):
        """Enable due date only when there is an unpaid payable balance and not written off."""
        remaining = self._float_or_default(self.remainingdata.text(), 0.0)
        should_enable = remaining > 0 and not self.writeoff_check.isChecked()

        self.due_date_combo.setEnabled(should_enable)
        if not should_enable:
            self.due_date_combo.setCurrentText("None")

    def compute_due_date(self):
        """Return due date string (yyyy-MM-dd) based on selected offset, or None."""
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

    def parse_expiry_month_year(self, text):
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

    def expiry_month_year_text(self, date_value):
        if date_value is None or not date_value.isValid():
            return ""
        return date_value.toString("MM-yy")

    def _text_or_none(self, value):
        text = str(value).strip() if value is not None else ""
        return text if text else None

    def _text_or_default(self, value, default=""):
        text = str(value).strip() if value is not None else ""
        return text if text else default

    def _int_or_default(self, value, default=0):
        try:
            if value is None or str(value).strip() == "":
                return int(default)
            return int(value)
        except (TypeError, ValueError):
            return int(default)

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

    def _normalize_payment_data(self, payment):
        payment = dict(payment or {})
        return {
            "payment_method": self._text_or_default(payment.get("payment_method"), "Cash"),
            "bank_name": self._text_or_none(payment.get("bank_name")),
            "account_no": self._text_or_none(payment.get("account_no")),
            "transaction_mode": self._text_or_none(payment.get("transaction_mode")),
            "wallet_provider": self._text_or_none(payment.get("wallet_provider")),
            "wallet_no": self._text_or_none(payment.get("wallet_no")),
            "payment_reference": self._text_or_none(payment.get("payment_reference")),
        }
        
    


    
    def handle_editing_finished(self, combo):
        
        print("Handling Editing Finished")

        text = combo.currentText().strip()
        if not text:
            return

        if text.isdigit():
            match = combo.lookup_product_by_code(text)
            if match:
                product_id, display_name = match
                combo.select_result(display_name, product_id)
                self.focus_next_field(self.batch_edit)
                return

        index = combo.findText(text, Qt.MatchFixedString)

        print(f"Editing finished text: {text}, matched index: {index}")

        if index >= 0:
            combo.setCurrentIndex(index)
            self.focus_next_field(self.batch_edit)
            return

        self.new_product = text
        self.add_new_product_dialog(combo, new_product=text)


    def handle_item_return_pressed(self, combo):
        text = combo.currentText().strip()
        if not text:
            return

        if text.isdigit():
            match = combo.lookup_product_by_code(text)
            if match:
                product_id, display_name = match
                combo.select_result(display_name, product_id)
                self.focus_next_field(self.batch_edit)
                return

        index = combo.findText(text, Qt.MatchFixedString)

        if index >= 0:
            combo.setCurrentIndex(index)
            self.focus_next_field(self.batch_edit)
            return

        self.new_product = text
        self.add_new_product_dialog(combo, new_product=text)
    
    

       
   
    
    def _insert_purchase_table_row(
        self,
        *,
        product_id,
        product_name,
        batch_data,
        expiry_data,
        qty_data,
        bonus_data,
        rate_data,
        discount_data,
        tax_data,
        total_data,
    ):
        row = self.table.rowCount()
        
        self.table.setRowHeight(row, self.row_height)
        
        counter = QLabel(str(row + 1))
        counter.setAlignment(Qt.AlignCenter)

        remove_btn = QPushButton("X")
        remove_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        remove_btn.setStyleSheet("color: #333;")
        
        product_combo = QComboBox()
        product_combo.setEditable(True)
        product_combo.lineEdit().setReadOnly(True)
        product_combo.setInsertPolicy(QComboBox.NoInsert)

        product_combo.addItem(product_name, product_id)

        product_combo.setStyleSheet("""
        QComboBox::drop-down {
            border: 0px;
        }
        QComboBox::down-arrow {
            image: none;
        }
        """)
        
        qty_edit = QLineEdit()
        qty_edit.setReadOnly(True)
        qty_edit.setText(qty_data)
        
        
        bonus_edit = QLineEdit()
        bonus_edit.setReadOnly(True)
        bonus_edit.setText(bonus_data)
        
        rate_edit = QLineEdit()
        rate_edit.setReadOnly(True)
        rate_edit.setText(rate_data)
        
        batch_edit = QLineEdit()
        batch_edit.setReadOnly(True)
        batch_edit.setText(batch_data)  
        
        expiry_edit = QLineEdit()
        expiry_edit.setReadOnly(True)
        expiry_edit.setText(expiry_data)
        
        discount_edit = QLineEdit()
        discount_edit.setReadOnly(True)
        discount_edit.setText(discount_data)
        
        tax_edit = QLineEdit()
        tax_edit.setReadOnly(True)
        tax_edit.setText(tax_data)
        
        total_edit = QLineEdit()
        total_edit.setReadOnly(True)
        total_edit.setText(total_data)
        
        
        remove_btn = QPushButton("X")
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setStyleSheet("color: #333;")
        
        self.table.insertRow(row)
        
        
        self.table.setCellWidget(row, 0, counter)
        self.table.setCellWidget(row, 1, product_combo)
        
        self.table.setCellWidget(row, 2, batch_edit)
        self.table.setCellWidget(row, 3, expiry_edit)
       
        self.table.setCellWidget(row, 4, qty_edit)
        self.table.setCellWidget(row, 5, bonus_edit)
        self.table.setCellWidget(row, 6, rate_edit)
        
        self.table.setCellWidget(row, 7, discount_edit)
        self.table.setCellWidget(row, 8, tax_edit)
        self.table.setCellWidget(row, 9, total_edit)
        self.table.setCellWidget(row, 10, remove_btn)
        
        
        
        remove_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        return row

    def add_row(self):
        
        product_name = self.item.currentText()
        product_id = self.item.currentData()
        
        print(f"Product Name: {product_name}, Product ID: {product_id}")
        
        if product_name == '':
            print("Please Select a product first")
            AppMessageBox.information(self, 'Error', "Please Select a product first")
            self.item.setFocus()
            return
        elif product_id is None:
            print("Entered product is not available... Please Add this product first")
            AppMessageBox.information(self, 'Error', "Entered product is not available... Please Add this product first")
            self.item.setFocus()
            return

        qty_data = self.qty_edit.text()
        bonus_data = self.bonus_edit.text()
        rate_data = self.rate_edit.text()
        batch_data = self.batch_edit.text()
        expiry_data = self.expiry_edit.text().strip()
        expiry_collapsed = expiry_data.replace("_", "").replace(" ", "")
        if not expiry_collapsed or expiry_collapsed in {"-", "--"}:
            expiry_data = ""
        if expiry_data:
            parsed_expiry = self.parse_expiry_month_year(expiry_data)
            if parsed_expiry is None:
                AppMessageBox.information(
                    self,
                    'Error',
                    "Please enter expiry in MM-YY format, for example 04-26."
                )
                self.expiry_edit.setFocus()
                self.expiry_edit.selectAll()
                return
            expiry_data = self.expiry_month_year_text(parsed_expiry)
        discount_data = self.discount_edit.text() or "0.0"
        tax_data = self.tax_edit.text() or "0.0"
        total_data = self.amount_edit.text()
        bonus_data = bonus_data or "0"

        if qty_data == "" or qty_data == "0" or rate_data == "" or rate_data == "0":
            print("Quantity or Rate cannot be empty or zero.")
            AppMessageBox.information(self, 'Error', "Quantity or Rate cannot be empty or zero.")
            return

        self._insert_purchase_table_row(
            product_id=product_id,
            product_name=product_name,
            batch_data=batch_data,
            expiry_data=expiry_data,
            qty_data=qty_data,
            bonus_data=bonus_data,
            rate_data=rate_data,
            discount_data=discount_data,
            tax_data=tax_data,
            total_data=total_data,
        )
        
        self.item.setFocus()
        
        self.update_total_amount()
        self.calculate_payment()
        self.update_due_date_availability()
        
        self.qty_edit.clear()
        self.bonus_edit.clear()
        self.rate_edit.clear()
        self.batch_edit.clear()
        self.expiry_edit.clear()
        self.discount_edit.clear()
        self.tax_edit.clear()
        
        # clear combo field
        self.item.setCurrentIndex(-1)
        self.update_purchase_table_height()
        self.schedule_purchase_draft_save()
        
        

    
    
        

    def remove_row(self, target_row):
        
        self.table.removeRow(target_row)

        # Reconnect all remove buttons with updated row numbers
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 10)
            if isinstance(widget, QPushButton):
                widget.clicked.disconnect()
                widget.clicked.connect(lambda _, r=row: self.remove_row(r))

        
        self.update_total_amount()
        self.calculate_payment()
        self.update_due_date_availability()
        self.update_purchase_table_height()
        self.schedule_purchase_draft_save()
        
        

    def showEvent(self, event):
        super().showEvent(event)
        self.populate_suppliers()
        QTimer.singleShot(0, self.update_purchase_table_height)
        QTimer.singleShot(0, self.prompt_resume_purchase_draft)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_purchase_table_height()


    def update_purchase_table_height(self):
        if not hasattr(self, "table") or not hasattr(self, "label_entry_frame"):
            return

        margins = self.layout.contentsMargins()
        vertical_spacing = self.layout.spacing() * max(0, self.layout.count() - 1)

        header_height = self.layout.itemAt(0).sizeHint().height() if self.layout.count() > 0 else 0
        supplier_height = self.supplier_frame.sizeHint().height() if hasattr(self, "supplier_frame") else 0
        totals_height = self.totals_frame.sizeHint().height() if hasattr(self, "totals_frame") else 0
        save_height = self.save_purchase_button.sizeHint().height() if hasattr(self, "save_purchase_button") else 0

        available_label_frame_height = (
            self.height()
            - margins.top()
            - margins.bottom()
            - vertical_spacing
            - header_height
            - supplier_height
            - totals_height
            - save_height
        )

        frame_height = max(240, available_label_frame_height)
        frame_height = min(frame_height, 500)
        self.label_entry_frame.setMaximumHeight(frame_height)

        frame_margins = self.label_entry_layout.contentsMargins()
        controls_height = self.entry_grid.sizeHint().height() if hasattr(self, "entry_grid") else 0
        spacer_height = 10
        table_height = (
            frame_height
            - frame_margins.top()
            - frame_margins.bottom()
            - controls_height
            - spacer_height
            - self.label_entry_layout.spacing()
        )

        min_table_height = self.table.horizontalHeader().height() + (self.row_height * self.min_visible_rows) + 8
        table_height = max(min_table_height, table_height)
        table_height = min(table_height, 360)

        self.table.setMinimumHeight(table_height)
        self.table.setMaximumHeight(table_height)
        


    def populate_suppliers(self, selected_supplier_id=None, selected_rep_id=None):
        
        self.supplier_edit.blockSignals(True)
        self.supplier_edit.clear()

        query = QSqlQuery()
        if not query.exec("SELECT id, name FROM supplier WHERE status = 'active' ORDER BY name;"):
            AppMessageBox.information(self, "Error", query.lastError().text())
            self.supplier_edit.blockSignals(False)
            self.rep_edit.clear()
            return

        while query.next():
            supplier_id = query.value(0)
            supplier_name = query.value(1)
            self.supplier_edit.addItem(supplier_name, supplier_id)

        self.supplier_edit.blockSignals(False)

        if self.supplier_edit.count() > 0:
            target_index = 0
            if selected_supplier_id is not None:
                found_index = self.supplier_edit.findData(selected_supplier_id)
                if found_index >= 0:
                    target_index = found_index
            self.supplier_edit.setCurrentIndex(target_index)
            self.populate_reps(selected_rep_id=selected_rep_id)
        else:
            self.rep_edit.clear()
        
        
        
        
    def populate_reps(self, selected_rep_id=None):
        
        self.rep_edit.clear()

        supplier_id = self.supplier_edit.currentData()

        print("Current supplier id:", supplier_id)
        print("Current supplier text:", self.supplier_edit.currentText())
        print("Current supplier index:", self.supplier_edit.currentIndex())

        if supplier_id is None:
            return

        query = QSqlQuery()
        query.prepare("""
            SELECT id, name
            FROM rep
            WHERE supplier_id = ?
            ORDER BY name;
        """)
        query.addBindValue(int(supplier_id))

        if not query.exec():
            AppMessageBox.information(self, "Error", query.lastError().text())
            return

        found = False
        while query.next():
            found = True
            rep_id = query.value(0)
            rep_name = query.value(1)
            self.rep_edit.addItem(rep_name, rep_id)

        if not found:
            print(f"No reps found for supplier_id = {supplier_id}")
            
        # select the first rep automatically
        if self.rep_edit.count() > 0:
            target_index = 0
            if selected_rep_id is not None:
                found_index = self.rep_edit.findData(selected_rep_id)
                if found_index >= 0:
                    target_index = found_index
            self.rep_edit.setCurrentIndex(target_index)
    
    
    
    
    
    
    
    
    
    
    
    
    
    @Permissions.require_permission('purchase.create')
    def save_purchase(self):
        if not require_open_session(self):
            return

        self.show_price_review_dialog()

        # ------------------------------------------------------------
        # 1) Ask user whether they really want to save the purchase
        # ------------------------------------------------------------
        _, accepted = AppMessageBox.confirm(
            self,
            "Confirm Save",
            "Would you like to save the Purchase Invoice?",
            confirm_label="Save Purchase",
            cancel_label="Cancel",
            kind="question",
        )

        if not accepted:
            return

        # ------------------------------------------------------------
        # 2) Get current database connection and start transaction
        # ------------------------------------------------------------
        db = QSqlDatabase.database()

        if not db.transaction():
            AppMessageBox.error(self, "Database Error", "Could not start database transaction.")
            return

        try:
            # --------------------------------------------------------
            # 3) Collect and validate all purchase data from the form
            # --------------------------------------------------------
            
            purchase_data = self._collect_purchase_data()

            print("Purchase data collected successfully")
            print("Purchase data:", purchase_data)

            # --------------------------------------------------------
            # 4) Save purchase header
            # --------------------------------------------------------
            #
            # This helper should insert into the purchase table
            # and return the new purchase_id.
            #
            purchase_id = self._save_purchase_header(purchase_data)

            print(f"Purchase header saved successfully with ID: {purchase_id}")

            # --------------------------------------------------------
            # 5) Save purchase items and related batch records
            # --------------------------------------------------------
            #
            # This helper should:
            # - loop through table rows
            # - validate item rows
            # - insert purchaseitem rows
            # - calculate unit cost
            # - insert batch rows
            # - raise exception if no valid items found
            #
            self._save_purchase_items(purchase_id)

            print("Purchase items saved successfully")

            # --------------------------------------------------------
            # 6) Save supplier transaction and update supplier balance
            # --------------------------------------------------------
            #
            # This helper should:
            # - insert into supplier_transaction
            # - update supplier payable / receivable in supplier table
            #
            self._save_purchase_transaction(purchase_id, purchase_data)

            print("Purchase transaction saved successfully")

        except Exception as e:
            # --------------------------------------------------------
            # 7) Roll back everything if any step fails
            # --------------------------------------------------------
            db.rollback()
            print("Transaction rolled back due to error:", str(e))
            error_text = str(e)
            if error_text == "Please enter sales invoice.":
                AppMessageBox.error(self, "Error", error_text)
            else:
                AppMessageBox.error(
                    self,
                    "Error",
                    f"An error occurred while saving the purchase:\n{error_text}"
                )
            return

        # ------------------------------------------------------------
        # 8) Commit transaction if all steps succeed
        # ------------------------------------------------------------
        if not db.commit():
            db.rollback()
            AppMessageBox.error(self, "Database Error", "Could not commit the purchase transaction.")
            return

        print("Transaction committed successfully")
        self._discard_current_purchase_draft()
        AppMessageBox.success(self, "Success", "Purchase saved successfully.")
        self.clear_fields()
        
        
        
    def _collect_purchase_data(self):

        # ------------------------------------------------------------
        # 1) Read header values from UI
        # ------------------------------------------------------------
        supplier = self.supplier_edit.currentData()
        rep = self.rep_edit.currentData()
        sellerinvoice = self.invoice_edit.text().strip()

        subtotal = self.gross_entry.text().strip()
        discount = self.discount_entry.text().strip()

        taxable = self.taxable_entry.text().strip()

        tax_236g = self.tax_236g_entry.text().strip()
        tax_236h = self.tax_236h_entry.text().strip()
        sales_tax = self.sales_tax_entry.text().strip()

        netamount = self.net_amount_entry.text().strip()
        cn_adjustment = self.cn_adjustment_entry.text().strip()
        final_amount = self.final_amount.text().strip()

        paid = self.paid_amount.text().strip()
        remaining = self.remainingdata.text().strip()

        # ------------------------------------------------------------
        # 2) Basic validation
        # ------------------------------------------------------------
        if supplier is None:
            raise Exception("Please select a supplier.")

        if not sellerinvoice:
            raise Exception("Please enter sales invoice.")

        # rep can be optional if your system allows it
        # if rep is None:
        #     raise Exception("Please select a rep.")

        # ------------------------------------------------------------
        # 3) Convert numbers using your same style
        # ------------------------------------------------------------
        subtotal = max(0.0, self._float_or_default(subtotal, 0.0))
        discount = min(max(0.0, self._float_or_default(discount, 0.0)), subtotal)
        taxable = max(0.0, self._float_or_default(taxable, subtotal - discount))
        tax_236g = max(0.0, self._float_or_default(tax_236g, 0.0))
        tax_236h = max(0.0, self._float_or_default(tax_236h, 0.0))
        sales_tax = max(0.0, self._float_or_default(sales_tax, 0.0))

        netamount = max(0.0, self._float_or_default(netamount, taxable + tax_236h + sales_tax - tax_236g))
        cn_adjustment = max(0.0, self._float_or_default(cn_adjustment, 0.0))
        total = max(0.0, self._float_or_default(final_amount, netamount - cn_adjustment))
        paid = max(0.0, self._float_or_default(paid, 0.0))
        remaining = self._float_or_default(remaining, total - paid)

        # ------------------------------------------------------------
        # 4) Calculate header net amount exactly in your style
        # ------------------------------------------------------------
        header_net_amount = (-discount - tax_236g + tax_236h + sales_tax - cn_adjustment)

        print("Header Net Amount: ", header_net_amount)

        # ------------------------------------------------------------
        # 5) Visualize data
        # ------------------------------------------------------------
        print("Supplier ID:", supplier)
        print("Rep ID:", rep)
        print("Seller Invoice:", sellerinvoice)
        print("Subtotal:", subtotal)
        print("Discount:", discount)
        print("Taxable:", taxable)
        print("Tax 236G:", tax_236g)
        print("Tax 236H:", tax_236h)
        print("Sales Tax:", sales_tax)
        print("Net Amount:", netamount)
        print("CN Adjustment:", cn_adjustment)
        print("Final Amount:", total)
        print("Paid:", paid)
        print("Remaining:", remaining)

        # ------------------------------------------------------------
        # 6) Validate your financial logic
        # ------------------------------------------------------------
        if total < 0:
            raise Exception("Final amount cannot be negative.")

        if paid < 0:
            raise Exception("Paid amount cannot be negative.")

        # Since your UI already gives remaining,
        # we can still validate it against total - paid if you want.
        calculated_remaining = total - paid

        # optional float tolerance check
        if abs(calculated_remaining - remaining) > 0.01:
            raise Exception("Remaining amount does not match total - paid.")

        # ------------------------------------------------------------
        # 7) Same writeoff / payable / receivable logic as your code
        # ------------------------------------------------------------
        due_date = self.compute_due_date() if remaining > 0 and not self.writeoff_check.isChecked() else None
        settlement = compute_purchase_settlement(
            remaining=remaining,
            writeoff_enabled=self.writeoff_check.isChecked(),
            due_date=due_date,
        )

        if settlement["payable"] > 0 and due_date is None:
            print("No due date selected for payable purchase. It will be tracked in No Due Date bucket.")

        session_id = get_active_session_id(strict=True)
        if session_id is None:
            raise Exception("No active session found.")

        # ------------------------------------------------------------
        # 9) Return data in your own naming style
        # ------------------------------------------------------------
        return {
            "supplier": supplier,
            "rep": rep,
            "sellerinvoice": sellerinvoice,
            "subtotal": subtotal,
            "discount": discount,
            "taxable": taxable,
            "tax_236g": tax_236g,
            "tax_236h": tax_236h,
            "sales_tax": sales_tax,
            "netamount": netamount,
            "cn_adjustment": cn_adjustment,
            "final_amount": final_amount,   # kept as your original field
            "total": total,                 # useful for calculations
            "paid": paid,
            "remaining": remaining,
            "writeoff": settlement["writeoff"],
            "payable": settlement["payable"],
            "receivable": settlement["receivable"],
            "due_date": settlement["due_date"],
            "session_id": session_id,
            "header_net_amount": header_net_amount,
        }
        
        
    
    def _save_purchase_header(self, data):
        normalized = build_purchase_header_payload(
            supplier=self._int_or_default(data.get("supplier"), 0),
            rep=self._int_or_default(data.get("rep"), 0) if data.get("rep") not in (None, "") else None,
            sellerinvoice=self._text_or_default(data.get("sellerinvoice"), ""),
            subtotal=self._float_or_default(data.get("subtotal"), 0.0),
            discount=self._float_or_default(data.get("discount"), 0.0),
            taxable=self._float_or_default(data.get("taxable"), 0.0),
            tax_236g=self._float_or_default(data.get("tax_236g"), 0.0),
            tax_236h=self._float_or_default(data.get("tax_236h"), 0.0),
            sales_tax=self._float_or_default(data.get("sales_tax"), 0.0),
            netamount=self._float_or_default(data.get("netamount"), 0.0),
            cn_adjustment=self._float_or_default(data.get("cn_adjustment"), 0.0),
            total=self._float_or_default(data.get("total"), 0.0),
            paid=self._float_or_default(data.get("paid"), 0.0),
            remaining=self._float_or_default(data.get("remaining"), 0.0),
            session_id=self._int_or_default(data.get("session_id"), 0),
            settlement={
                "writeoff": self._float_or_default(data.get("writeoff"), 0.0),
                "payable": self._float_or_default(data.get("payable"), 0.0),
                "receivable": self._float_or_default(data.get("receivable"), 0.0),
                "due_date": self._text_or_none(data.get("due_date")),
            },
        )

        purchase_id = insert_purchase_header(normalized)

        print("Purchase header saved successfully.")
        print("Purchase ID:", purchase_id)

        return purchase_id
    
    
    
    def _save_purchase_items(self, purchase_id):
    
        # ------------------------------------------------------------
        # 1) Basic sanity check
        # ------------------------------------------------------------
        if purchase_id is None:
            raise Exception("Invalid purchase_id received in _save_purchase_items().")

        row_count = self.table.rowCount()
        print("Total rows in purchase table:", row_count)

        if row_count == 0:
            raise Exception("Purchase table is empty. Cannot save purchase without items.")

        saved_rows = 0
        distribution = self._collect_purchase_distribution_context()

        # ------------------------------------------------------------
        # 2) Loop through each row
        # ------------------------------------------------------------
        for row in range(row_count):

            print(f"\nProcessing row {row + 1}")

            # --------------------------------------------------------
            # 3) Get row widgets
            # --------------------------------------------------------
            product_combo = self.table.cellWidget(row, 1)
            batch_edit = self.table.cellWidget(row, 2)
            expiry_edit = self.table.cellWidget(row, 3)
            qty_edit = self.table.cellWidget(row, 4)
            bonus_edit = self.table.cellWidget(row, 5)
            rate_edit = self.table.cellWidget(row, 6)
            discount_edit = self.table.cellWidget(row, 7)
            tax_edit = self.table.cellWidget(row, 8)
            total_edit = self.table.cellWidget(row, 9)

            # --------------------------------------------------------
            # 4) Validate widget presence
            # --------------------------------------------------------
            if product_combo is None:
                raise Exception(f"Missing product widget in row {row + 1}.")
            if batch_edit is None:
                raise Exception(f"Missing batch widget in row {row + 1}.")
            if expiry_edit is None:
                raise Exception(f"Missing expiry widget in row {row + 1}.")
            if qty_edit is None:
                raise Exception(f"Missing qty widget in row {row + 1}.")
            if bonus_edit is None:
                raise Exception(f"Missing bonus widget in row {row + 1}.")
            if rate_edit is None:
                raise Exception(f"Missing rate widget in row {row + 1}.")
            if discount_edit is None:
                raise Exception(f"Missing discount widget in row {row + 1}.")
            if tax_edit is None:
                raise Exception(f"Missing tax widget in row {row + 1}.")
            if total_edit is None:
                raise Exception(f"Missing total widget in row {row + 1}.")

            # --------------------------------------------------------
            # 5) Read raw row values
            # --------------------------------------------------------
            product = product_combo.currentData()
            product_name = product_combo.currentText().strip()

            batch = batch_edit.text().strip()
            expiry = expiry_edit.text().strip()
            if expiry:
                expiry = parse_expiry_to_db_date(expiry)

            qty = qty_edit.text().strip()
            bonus = bonus_edit.text().strip()
            rate = rate_edit.text().strip()
            item_discount = discount_edit.text().strip()
            item_tax = tax_edit.text().strip()
            item_total = total_edit.text().strip()

            print("Product ID:", product)
            print("Product Name:", product_name)
            print("Batch:", batch)
            print("Expiry:", expiry)
            print("Qty:", qty)
            print("Bonus:", bonus)
            print("Rate:", rate)
            print("Discount:", item_discount)
            print("Tax:", item_tax)
            print("Item Total:", item_total)

            # --------------------------------------------------------
            # 6) Skip completely blank rows
            # --------------------------------------------------------
            #
            # Sometimes table may contain an empty editable row.
            #
            if (
                product is None
                and not batch
                and not expiry
                and not qty
                and not bonus
                and not rate
                and not item_discount
                and not item_tax
                and not item_total
            ):
                print(f"Row {row + 1} is completely blank. Skipping.")
                continue

            # --------------------------------------------------------
            # 7) Validate required row fields
            # --------------------------------------------------------
            if product is None:
                raise Exception(f"Please select a product in row {row + 1}.")

            if not qty:
                raise Exception(f"Please enter quantity in row {row + 1}.")

            if not rate:
                raise Exception(f"Please enter rate in row {row + 1}.")

            # --------------------------------------------------------
            # 8) Convert numeric values
            # --------------------------------------------------------
            try:
                normalized_row = normalize_purchase_item_row(
                    row_number=row + 1,
                    product_id=self._int_or_default(product, 0),
                    batch_text=batch,
                    expiry_text=expiry,
                    qty_text=qty,
                    bonus_text=bonus,
                    rate_text=rate,
                    discount_text=item_discount,
                    tax_text=item_tax,
                    total_text=item_total,
                    distribution_factor=distribution["distribution_factor"],
                )
            except ValueError as exc:
                raise Exception(str(exc))

            purchase_item_id = self._persist_purchase_row(purchase_id, normalized_row, row + 1)
            self._persist_purchase_batch(normalized_row, purchase_item_id, row + 1)

            saved_rows += 1

        # ------------------------------------------------------------
        # 13) Final validation
        # ------------------------------------------------------------
        if saved_rows == 0:
            raise Exception("No valid purchase items were found to save.")

        print(f"Total purchase item rows saved: {saved_rows}")
        
        
        
    def _save_purchase_transaction(self, purchase_id, data):

        if purchase_id is None:
            raise Exception("Invalid purchase_id received in _save_purchase_transaction().")

        supplier = self._int_or_default(data.get("supplier"), 0)
        rep = self._int_or_default(data.get("rep"), 0) if data.get("rep") not in (None, "") else None
        session_id = self._int_or_default(data.get("session_id"), 0)

        paid = self._float_or_default(data.get("paid"), 0.0)
        payable = self._float_or_default(data.get("payable"), 0.0)
        receivable = self._float_or_default(data.get("receivable"), 0.0)
        total = self._float_or_default(data.get("total"), 0.0)

        # ------------------------------------------------------------
        # 1) Get supplier balances BEFORE transaction
        # ------------------------------------------------------------
        balances = fetch_supplier_balances(supplier)
        payable_before = balances["payable_before"]
        receiveable_before = balances["receiveable_before"]

        # ------------------------------------------------------------
        # 2) Calculate purchase transaction values
        # ------------------------------------------------------------
        payment = self._normalize_payment_data(self.payment_handler.payment_data.copy())
        payload = build_supplier_transaction_payload(
            purchase_id=purchase_id,
            supplier_id=supplier,
            rep_id=rep,
            session_id=session_id,
            total=total,
            paid=paid,
            settlement={
                "payable": payable,
                "receivable": receivable,
            },
            payable_before=payable_before,
            receiveable_before=receiveable_before,
            payment=payment,
        )

        print(payment)

        insert_supplier_transaction(payload)

        # ------------------------------------------------------------
        # 5) Update supplier table balances
        # ------------------------------------------------------------
        update_supplier_balances(
            supplier,
            payable_after=payload["payable_after"],
            receiveable_after=payload["receiveable_after"],
        )

        print("Supplier transaction saved successfully.")    

    def _collect_purchase_distribution_context(self):
        row_count = self.table.rowCount()
        line_subtotal = 0.0

        for row in range(row_count):
            product_combo = self.table.cellWidget(row, 1)
            if product_combo is None or product_combo.currentData() is None:
                continue
            total_edit = self.table.cellWidget(row, 9)
            if total_edit is None:
                continue
            line_subtotal += max(0.0, self._float_or_default(total_edit.text(), 0.0))

        return compute_purchase_distribution_factor(
            line_subtotal=line_subtotal,
            header_discount=self._float_or_default(self.discount_entry.text(), 0.0),
            header_tax_236g=self._float_or_default(self.tax_236g_entry.text(), 0.0),
            header_tax_236h=self._float_or_default(self.tax_236h_entry.text(), 0.0),
            header_sales_tax=self._float_or_default(self.sales_tax_entry.text(), 0.0),
            cn_adjustment=self._float_or_default(self.cn_adjustment_entry.text(), 0.0),
        )

    def _persist_purchase_row(self, purchase_id, normalized_row, row_number):
        try:
            purchase_item_id = insert_purchase_item(purchase_id, normalized_row)
        except Exception as exc:
            raise Exception(f"Failed to save purchase item in row {row_number}: {exc}")

        print("Purchase item saved with ID:", purchase_item_id)
        return purchase_item_id

    def _persist_purchase_batch(self, normalized_row, purchase_item_id, row_number):
        pack_size = fetch_product_pack_size(normalized_row["product"])
        batch_payload = build_batch_payload(
            product_id=normalized_row["product"],
            purchase_item_id=purchase_item_id,
            qty=normalized_row["qty"],
            bonus=normalized_row["bonus"],
            pack_size=pack_size,
            landing_cost=normalized_row["landing_cost"],
            batch=normalized_row["batch"],
            expiry=normalized_row["expiry"],
        )

        print("Batch payload:", batch_payload)
        print("Product:", normalized_row["product"])
        print("Purchase Item ID:", purchase_item_id)
        print("Received:", normalized_row["qty"] + normalized_row["bonus"])
        print("Qty:", normalized_row["qty"])
        print("Rate:", normalized_row["rate"])

        try:
            insert_batch_record(batch_payload)
        except Exception as exc:
            raise Exception(f"Failed to save batch in row {row_number}: {exc}")

        print(f"Batch saved successfully for row {row_number}")

        try:
            mark_product_used(normalized_row["product"])
        except Exception as exc:
            raise Exception(f"Failed to update product status in row {row_number}: {exc}")
            
            
    
    
    
    
    def on_completer_selected(self, text, item):
        
        text = text.strip()

        index = item.findText(text, Qt.MatchFixedString)
        if index < 0:
            return

        item.setCurrentIndex(index)
        item.lineEdit().setText(text)
        
        # move to next field
        self.focus_next_field(self.batch_edit)
    
    
    
    


    def on_cell_focus(self, row, column):
        
        index = self.table.model().index(row, column)
        self.table.edit(index)  # Start editing cell

        QTimer.singleShot(0, lambda: self._select_all_in_focus_widget())
    
    

    def _select_all_in_focus_widget(self):
        
        editor = self.table.focusWidget()
        if isinstance(editor, QLineEdit):
            editor.selectAll()
        elif isinstance(editor, QComboBox) and editor.isEditable():
            editor.lineEdit().selectAll()
    
    
    def clear_fields(self, reset_draft_state=True):
        
        self._draft_autosave_timer.stop()
        self._suspend_purchase_draft_autosave = True
        
        try:
            self.supplier_edit.clear()
            
            self.invoice_edit.clear()
            
            self.rep_edit.clear()
            self.gross_entry.clear()
            self.discount_entry.clear()
            
            self.tax_236g_entry.clear()
            self.tax_236h_entry.clear()
            self.sales_tax_entry.clear()
            self.net_amount_entry.clear()
            self.final_amount.clear()
            self.paid_amount.clear()
            self.remainingdata.clear()
            
            self.writeoff_check.setChecked(False)        

            self.due_date_combo.setCurrentText("None")
            self.due_date_combo.setEnabled(False)
            
            self.table.setRowCount(0)

            self.qty_edit.clear()
            self.bonus_edit.clear()
            self.rate_edit.clear()
            self.batch_edit.clear()
            self.expiry_edit.clear()
            self.discount_edit.clear()
            self.tax_edit.clear()
            self.item.setCurrentIndex(-1)
            
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentIndex(0)
            self.payment_method.blockSignals(False)
            self.payment_handler.payment_data = self._normalize_payment_data({"payment_method": "Cash"})
            
            self.populate_suppliers()
            self.item.setFocus()

            if reset_draft_state:
                self.current_purchase_draft_id = None
                self._purchase_draft_resume_checked = False
        finally:
            self._suspend_purchase_draft_autosave = False

    def confirm_clear_purchase(self):
        _, accepted = AppMessageBox.confirm(
            self,
            "Clear Purchase Invoice",
            "Clear the current purchase invoice and remove all entered rows?",
            confirm_label="Clear Invoice",
            cancel_label="Keep Editing",
            kind="question",
        )
        if not accepted:
            return
        self._discard_current_purchase_draft()
        self.clear_fields()
        
       


    def add_new_product_dialog(self, combo, new_product=None):
        
        dialog = ImportDialog(self)
        
        dialog.name_input.setText(new_product)
        
        if dialog.exec() == QDialog.Accepted:
            
            print("New Product is: ", new_product)
            
            
            item_name = self._text_or_default(dialog.name_input.text(), "")
            item_form = self._text_or_none(dialog.form_input.currentText())
            item_packing = self._text_or_none(dialog.packing_input.text())
            
            display_name_parts = [item_name]
            if item_form:
                display_name_parts.append(item_form)
            if item_packing:
                display_name_parts.append(item_packing)
            display_name = " ".join(display_name_parts).strip()
            print("The display name is: ", display_name)
            
            manufacturer = dialog.brand_input.currentData()
            manufacturer = self._int_or_default(manufacturer, 0) if manufacturer not in (None, "") else None
            packsize = self._int_or_default(dialog.packsize_input.text(), 1)
            saleprice = self._float_or_default(dialog.saleprice_input.text(), 0.0)
            
            # Insert Data into Database
            
            brand_name = self._text_or_none(item_name)
            if brand_name is None:
                raise Exception("Brand is required for a new product.")

            product_query = QSqlQuery()
            product_query.prepare("""
                INSERT INTO product (
                    display_name,
                    code,
                    reg_no,
                    generic_name,
                    brand,
                    form,
                    strength,
                    packing,
                    rack,
                    manufacturer_id,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
            
            code = None
            reg_no = None
            generic_name = None
            packing = None

            product_query.addBindValue(display_name)
            product_query.addBindValue(code)
            product_query.addBindValue(reg_no)
            product_query.addBindValue(generic_name)
            product_query.addBindValue(brand_name)
            product_query.addBindValue(item_form)
            product_query.addBindValue(item_packing)
            product_query.addBindValue(packing)
            product_query.addBindValue("")
            product_query.addBindValue(manufacturer)
            product_query.addBindValue("used")

            if not product_query.exec():
                raise Exception(product_query.lastError().text())

            else:
                
                AppMessageBox.information(None, "Success", "Product added successfully")
                product_id = product_query.lastInsertId()
                print("New Product ID is: ", product_id)
                
                # Create Empty Stock Record
                price_query = QSqlQuery()
                price_query.prepare("""
                    INSERT INTO price_pack (product_id, pack_size, pack_price)
                    VALUES (?, ?, ?)
                """)
                
                price_query.addBindValue(product_id)
                price_query.addBindValue(packsize)  # initial packsize
                price_query.addBindValue(saleprice)  # initial saleprice

                if not price_query.exec():
                    print("Error inserting price_pack:", price_query.lastError().text())
                else:
                    print("Price pack record created successfully for new product")
                

            # clear combo box
            combo.setCurrentIndex(-1)
            combo.setFocus()
            print("Import Dialog Accepted")
            
        else:
            print("Import Dialog Cancelled")


    def force_uppercase(self, text):
        line_edit = self.name_input.lineEdit()
        line_edit.blockSignals(True)
        line_edit.setText(text.upper())
        line_edit.blockSignals(False)




    def get_previous_price(self, product_id):
        query = QSqlQuery()
        query.prepare("""
            SELECT COALESCE(pack_price, 0)
            FROM price_pack
            WHERE product_id = ?
            ORDER BY is_default DESC, id ASC
            LIMIT 1
        """)
        query.addBindValue(product_id)

        if not query.exec():
            raise Exception(f"Failed to fetch previous price: {query.lastError().text()}")

        if query.next():
            return query.value(0) or 0

        return 0


    def get_price_review_rows(self):
        rows = []
        seen_product_ids = set()

        for row in range(self.table.rowCount()):
            product_combo = self.table.cellWidget(row, 1)

            if product_combo is None:
                continue

            product_id = product_combo.currentData()
            product_name = product_combo.currentText().strip()

            if product_id is None or not product_name:
                continue

            if product_id in seen_product_ids:
                continue

            seen_product_ids.add(product_id)
            previous_price = self.get_previous_price(product_id)
            rows.append((product_id, product_name, previous_price, ""))

        return rows


    def populate_price_review_table(self, table):
        data = self.get_price_review_rows()
        table.setRowCount(len(data))

        for row, (product_id, name, prev_price, new_price) in enumerate(data):
            values = [str(product_id), str(name), str(prev_price), str(new_price)]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)

                if col == 3:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                else:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                table.setItem(row, col, item)

        return len(data)


    def show_price_review_dialog(self):
    
        dialog = QDialog(self)
        dialog.setWindowTitle("Review Selling Prices")
        dialog.resize(700, 400)

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        title = QLabel("Review Sale Price")
        title.setObjectName("SectionTitle")
        title.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([
            "ID", "Medicine Name", "Previous Price", "New Price"
        ])
        table.setItemDelegateForColumn(3, LivePriceDelegate(self.reveal_price_save_button, table))

        table.setEditTriggers(
            QAbstractItemView.CurrentChanged |
            QAbstractItemView.EditKeyPressed |
            QAbstractItemView.AnyKeyPressed
        )
        table.setStyleSheet("""
            QTableWidget {
                padding: 10px;
            }
        """)
        table.verticalHeader().setVisible(False)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        ratios = [1, 5, 2, 2]
        total = sum(ratios)
        table_width = 640

        for col, ratio in enumerate(ratios):
            header.resizeSection(col, int(table_width * ratio / total))

        row_count = self.populate_price_review_table(table)

        if row_count == 0:
            AppMessageBox.information(
                self,
                "No Items",
                "No purchased items were found to review prices for."
            )
            return

        main_layout.addWidget(table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("Save Changes")
        self.skip_btn = QPushButton("Skip")

        self.save_btn.hide()

        self.save_btn.clicked.connect(lambda: self.save_price_review_changes(dialog, table))
        self.skip_btn.clicked.connect(dialog.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.skip_btn)

        main_layout.addLayout(btn_layout)

        table.itemChanged.connect(self.on_price_changed)

        dialog.exec() 


    def save_price_review_changes(self, dialog, table):
        db = QSqlDatabase.database()

        if not db.transaction():
            AppMessageBox.critical(self, "Database Error", "Could not start price update transaction.")
            return

        try:
            updated_rows = 0
            app = QApplication.instance()
            change_user_id = app.property("user_id") if app else None
            change_username = (app.property("username") or "") if app else ""

            for row in range(table.rowCount()):
                product_id_item = table.item(row, 0)
                product_name_item = table.item(row, 1)
                previous_price_item = table.item(row, 2)
                new_price_item = table.item(row, 3)

                if product_id_item is None or new_price_item is None:
                    continue

                new_price_text = new_price_item.text().strip()
                if not new_price_text:
                    continue

                product_id = int(product_id_item.text().strip())
                product_name = product_name_item.text().strip() if product_name_item else f"Product {product_id}"
                previous_price = float(previous_price_item.text().strip() or 0)

                try:
                    new_price = float(new_price_text)
                except ValueError:
                    raise Exception(f"Invalid new price in row {row + 1}.")

                if new_price < 0:
                    raise Exception(f"New price cannot be negative in row {row + 1}.")

                price_query = QSqlQuery()
                price_query.prepare("""
                    UPDATE price_pack
                    SET pack_price = ?
                    WHERE id = (
                        SELECT id
                        FROM price_pack
                        WHERE product_id = ?
                        ORDER BY is_default DESC, id ASC
                        LIMIT 1
                    )
                """)
                price_query.addBindValue(new_price)
                price_query.addBindValue(product_id)

                if not price_query.exec():
                    raise Exception(f"Failed to update price in row {row + 1}: {price_query.lastError().text()}")

                if price_query.numRowsAffected() == 0:
                    raise Exception(f"No price_pack row found for product ID {product_id}.")

                change_query = QSqlQuery()
                change_query.prepare("""
                    INSERT INTO price_changes (
                        product_id,
                        previous_price,
                        new_price,
                        source,
                        user_id,
                        username
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """)
                change_query.addBindValue(product_id)
                change_query.addBindValue(previous_price)
                change_query.addBindValue(new_price)
                change_query.addBindValue("purchase_price_review")
                change_query.addBindValue(change_user_id)
                change_query.addBindValue(change_username)

                if not change_query.exec():
                    raise Exception(f"Failed to log price change in row {row + 1}: {change_query.lastError().text()}")

                log_activity(
                    category="price",
                    action="price_updated",
                    entity_type="product",
                    entity_id=product_id,
                    note=(
                        f"Selling price updated for {product_name} (Product ID {product_id}). "
                        f"Pack price changed from {previous_price} to {new_price} during purchase price review."
                    ),
                    previous_value=str(previous_price),
                    new_value=str(new_price)
                )

                updated_rows += 1

            if updated_rows == 0:
                raise Exception("Enter at least one new price before saving changes.")

            if not db.commit():
                raise Exception("Could not commit price changes.")

            dialog.accept()

        except Exception as e:
            db.rollback()
            AppMessageBox.critical(self, "Error", str(e))
             


    def on_price_changed(self, item):
        NEW_PRICE_COL = 3

        if item.column() == NEW_PRICE_COL:
            self.reveal_price_save_button()


    def reveal_price_save_button(self):
        if hasattr(self, "save_btn") and self.save_btn is not None:
            self.save_btn.show()

        if hasattr(self, "skip_btn") and self.skip_btn is not None:
            self.skip_btn.setDisabled(True)



class MyTable(QTableWidget):
    
    def __init__(self, rows=0, cols=0, column_ratios=None, parent=None):
        super().__init__(rows, cols, parent)
        self.column_ratios = column_ratios or []
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # user can drag
        header.setMinimumSectionSize(10)  # let it shrink smaller

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.column_ratios:
            return
        total = sum(self.column_ratios)
        width = self.viewport().width()
        for i, ratio in enumerate(self.column_ratios):
            col_width = int(width * (ratio / total))
            self.setColumnWidth(i, col_width)



        
        
      
            
import math
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDateEdit

class ImportDialog(QDialog):
    
    # ... your __init__ / UI methods ...
    def __init__(self, parent=None):
        
        super().__init__(parent)
        self.setWindowTitle("Add New Product")
        self.resize(600, 332)
        self.setMinimumWidth(560)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(14, 12, 14, 12)
        self.layout.setSpacing(10)
        self.indicators = {}
        self.insert_subheading("PRODUCT Does Not Exist... Add INFORMATION")

        self.form_card = QFrame()
        self.form_card.setObjectName("ImportProductCard")
        self.form_layout = QVBoxLayout(self.form_card)
        self.form_layout.setContentsMargins(16, 14, 16, 14)
        self.form_layout.setSpacing(10)

        self.populate_product_fields()
        self.layout.addWidget(self.form_card)

        self.setLayout(self.layout)
        
        # Buttons
        self.footer_card = QFrame()
        self.footer_card.setObjectName("ImportDialogFooter")
        self.footer_layout = QHBoxLayout(self.footer_card)
        self.footer_layout.setContentsMargins(14, 10, 14, 10)
        self.footer_layout.setSpacing(10)

        self.footer_hint = QLabel("This product will be available immediately in Purchase Invoice.")
        self.footer_hint.setObjectName("ImportDialogFooterHint")
        self.footer_hint.setWordWrap(True)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.setCenterButtons(False)
        save_button = button_box.button(QDialogButtonBox.Save)
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        if save_button is not None:
            save_button.setText("Save Product")
            save_button.setObjectName("SaveButton")
            save_button.setCursor(Qt.PointingHandCursor)
            save_button.setMinimumHeight(34)
            save_button.setMinimumWidth(124)
        if cancel_button is not None:
            cancel_button.setText("Cancel")
            cancel_button.setObjectName("TopRightButton")
            cancel_button.setCursor(Qt.PointingHandCursor)
            cancel_button.setMinimumHeight(34)
            cancel_button.setMinimumWidth(92)
        button_box.accepted.connect(self.accept)   # Save → dialog.accept()
        button_box.rejected.connect(self.reject)   # Cancel → dialog.reject()
        self.footer_layout.addWidget(self.footer_hint, 1)
        self.footer_layout.addWidget(button_box, 0, Qt.AlignRight)
        self.layout.addWidget(self.footer_card)
        self.setStyleSheet(load_stylesheets() + """
            QDialog {
                background-color: #F5F7FB;
            }
            QFrame#ImportDialogHeader {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #264B68, stop: 1 #315D7D
                );
                border: 1px solid #1D4058;
                border-radius: 12px;
            }
            QLabel#ImportDialogBadge {
                background-color: rgba(255, 255, 255, 0.14);
                color: #FFFFFF;
                border-radius: 13px;
                font-family: montserrat;
                font-size: 11px;
                font-weight: 800;
                min-width: 26px;
                min-height: 26px;
                max-width: 26px;
                max-height: 26px;
                qproperty-alignment: AlignCenter;
            }
            QWidget#ImportDialogTitleWrap {
                background: transparent;
            }
            QLabel#ImportDialogTitle {
                color: #FFFFFF;
                font-family: montserrat;
                font-size: 16px;
                font-weight: 800;
            }
            QLabel#ImportDialogHint {
                color: rgba(255, 255, 255, 0.78);
                font-family: montserrat;
                font-size: 10px;
                font-weight: 600;
            }
            QFrame#ImportProductCard {
                background-color: #FFFFFF;
                border: 1px solid #D6E0E8;
                border-radius: 12px;
            }
            QLabel#ImportFieldLabel {
                color: #30485C;
                font-family: montserrat;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.2px;
            }
            QLineEdit#importField,
            QComboBox#importField {
                min-height: 34px;
                background-color: #F9FBFD;
                border: 1px solid #C9D7E3;
                border-radius: 9px;
                padding: 0 10px;
                color: #22313F;
                font-family: montserrat;
                font-size: 12px;
            }
            QLineEdit#importField:focus,
            QComboBox#importField:focus {
                border: 1px solid #7EA4C1;
                background-color: #FFFFFF;
            }
            QComboBox#importField::drop-down {
                width: 28px;
                border: none;
                background: transparent;
            }
            QFrame#ImportDialogFooter {
                background-color: #FFFFFF;
                border: 1px solid #D6E0E8;
                border-radius: 12px;
            }
            QLabel#ImportDialogFooterHint {
                color: #5D6E7D;
                font-family: montserrat;
                font-size: 10px;
                font-weight: 600;
            }
        """)
    
    

    def insert_subheading(self, title):
        self.header_card = QFrame()
        self.header_card.setObjectName("ImportDialogHeader")
        subheader_layout = QHBoxLayout(self.header_card)
        subheader_layout.setContentsMargins(14, 10, 14, 10)
        subheader_layout.setSpacing(10)

        badge = QLabel("P")
        badge.setObjectName("ImportDialogBadge")

        title_wrap = QWidget()
        title_wrap.setObjectName("ImportDialogTitleWrap")
        title_layout = QVBoxLayout(title_wrap)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(1)
        heading = QLabel("Add New Product")
        heading.setObjectName("ImportDialogTitle")

        subheading = QLabel(title)
        subheading.setObjectName("ImportDialogHint")
        
        title_layout.addWidget(heading)
        title_layout.addWidget(subheading)

        subheader_layout.addWidget(badge, 0, Qt.AlignTop)
        subheader_layout.addWidget(title_wrap, 1)
        self.layout.addWidget(self.header_card)
        
        
        
    
    def populate_product_fields(self):
        item_label = QLabel("Item")
        item_label.setObjectName("ImportFieldLabel")

        brand_label = QLabel("Brand")
        brand_label.setObjectName("ImportFieldLabel")

        packsize_label = QLabel("Pack Size")
        packsize_label.setObjectName("ImportFieldLabel")

        price_label = QLabel("Pack Sale Price")
        price_label.setObjectName("ImportFieldLabel")

        self.name_input = QLineEdit()
        self.name_input.setObjectName("importField")
        self.name_input.setPlaceholderText("Product name")

        forms = [
            "AEROSOL","BALM","BUBBLE GUM","CAP","CAPLET","CAPS SR","CREAM","DRAGEES","DROPS",
            "DRY SUSP","E AND E DROPS","EAR DROPS","ELIXIR","EMUL","ENEMA","EXPC","EYE DROPS",
            "EYE GEL","EYE OINT","EYE SUSP","FORM","GEL","GRANULES","INF","INHALER","INJ",
            "INJ CS","INJ DS","INJ IM/IV","INJ SC","INJ SR","INJ-IM","INJ-IV","LINCTUS",
            "LINIMENT","LIQUID","LOTION","LOZENGES","MIXTURE","MOUTH SPRAY","MOUTH WASH",
            "NASAL DROPS","NASAL SPRAY","NEBULISER","OIL","OINT","ORAL SOLN","PAINT",
            "PASTE","PATCHES","PELLETS","POULTICE","POWDER","ROTA CAPS","SACHET","SCRUB",
            "SHAMPOO","SOAP","SOFT CAPS","SOLN","SPRAY","SUPPOSITORIES","SUSP","SUSP DS",
            "SYP","SYRINGE","TAB","TAB ENTERIC COATED","TABS CHEWABLE","TABS DS","TABS EFR",
            "TABS SL","TABS SR","TINC","TOOTH PASTE","VAG CREAM","VAG OVULE","VAG PESSARIES","VAG TABS"
        ]

        forms = sorted([f.title() for f in forms])
        self.form_input = QComboBox()
        self.form_input.setObjectName("importField")
        self.form_input.setEditable(True)
        self.form_input.lineEdit().setObjectName("importField")
        self.form_input.addItems(forms)

        self.packing_input = QLineEdit()
        self.packing_input.setObjectName("importField")
        self.packing_input.setPlaceholderText("Strength / dose")

        self.brand_input = QComboBox()
        self.brand_input.setObjectName("importField")
        self.setup_manufacturer_combobox(self.brand_input)
        self.brand_input.lineEdit().setObjectName("importField")

        self.packsize_input = QLineEdit()
        self.packsize_input.setObjectName("importField")
        self.packsize_input.setPlaceholderText("Units per pack")

        self.saleprice_input = QLineEdit()
        self.saleprice_input.setObjectName("importField")
        self.saleprice_input.setPlaceholderText("Sale price")

        item_row = QHBoxLayout()
        item_row.setSpacing(10)
        item_row.addWidget(self.name_input, 3)
        item_row.addWidget(self.form_input, 2)
        item_row.addWidget(self.packing_input, 2)

        self.form_layout.addWidget(item_label)
        self.form_layout.addLayout(item_row)
        self.form_layout.addWidget(brand_label)
        self.form_layout.addWidget(self.brand_input)
        self.form_layout.addWidget(packsize_label)
        self.form_layout.addWidget(self.packsize_input)
        self.form_layout.addWidget(price_label)
        self.form_layout.addWidget(self.saleprice_input)
        
        
    def populate_manufacturer_combobox(self, combo: QComboBox):
        
        combo.clear()

        query = QSqlQuery("""
            SELECT id, name
            FROM manufacturer
            WHERE status = 'active'
            ORDER BY name
        """)

        while query.next():
            manufacturer_id = query.value(0)
            manufacturer_name = query.value(1)
            combo.addItem(manufacturer_name, manufacturer_id)
    
        
         
    def setup_manufacturer_combobox(self, combo: QComboBox):
        
        combo.setEditable(True)
        combo.lineEdit().focusInEvent = lambda event, le=combo.lineEdit(): (
            le.selectAll(),
            QLineEdit.focusInEvent(le, event)
        )
        combo.setInsertPolicy(QComboBox.NoInsert)

        self.populate_manufacturer_combobox(combo)

        # avoid duplicate connections if method is called again
        try:
            combo.lineEdit().editingFinished.disconnect()
        except (RuntimeError, TypeError):
            pass

        combo.lineEdit().editingFinished.connect(
            lambda: self.handle_new_manufacturer_entry(combo)
        )


    def handle_new_manufacturer_entry(self, combo: QComboBox):
        
        name = combo.currentText().strip()

        if not name:
            return

        # check if already exists in combobox
        for i in range(combo.count()):
            if combo.itemText(i).strip().lower() == name.lower():
                combo.setCurrentIndex(i)
                return

        # insert new manufacturer
        query = QSqlQuery()
        query.prepare("""
            INSERT INTO manufacturer (name)
            VALUES (?)
        """)
        query.addBindValue(name)

        if not query.exec():
            print("Failed to insert manufacturer:", query.lastError().text())
            return

        new_id = query.lastInsertId()

        # add directly instead of reloading everything
        combo.addItem(name, new_id)
        combo.setCurrentIndex(combo.count() - 1)
        print("New Manufacturer added .. right about now...")
