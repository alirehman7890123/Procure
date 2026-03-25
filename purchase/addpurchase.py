from datetime import datetime
from PySide6.QtWidgets import QWidget, QCompleter,QAbstractItemView, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget, QStyledItemDelegate
from PySide6.QtCore import QFile, Qt, QStringListModel, QDate, QTimer, Signal, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent
from functools import partial
from PySide6.QtGui import QKeySequence, QShortcut

from utilities.get_session import get_current_session

from utilities.stylus import load_stylesheets
from utilities.payment_handler import PaymentMethodHandler





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
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)
        
        
        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Invoice", objectName="SectionTitle")
        heading.setStyleSheet('color: #2F5D7C')
        self.invoicelist = QPushButton("Invoice List", objectName="TopRightButton")
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        self.invoicelist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.invoicelist)

        self.layout.addLayout(header_layout)
        
        
        # Add Supplier Section 
        self.add_supplier_section()
       
        
        
        
        
        
        ### Populate Labels & Entry Line
        self.populate_label_line()
        
        
        self.populate_totals_section()

        
        
        
        
        
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

        supplier_layout = QVBoxLayout(supplier_frame)
        supplier_layout.setContentsMargins(15, 10, 15, 10)
        supplier_layout.setSpacing(8)

        # Top Row Layout
        top_row = QHBoxLayout()
        top_row.setSpacing(15)

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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

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
                QMessageBox.warning(dialog, "Validation Error", "Supplier name is required.")
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
                QMessageBox.critical(
                    dialog,
                    "Database Error",
                    f"Failed to save supplier:\n{query.lastError().text()}"
                )
                return

            QMessageBox.information(dialog, "Success", "Supplier added successfully.")
            dialog.accept()

            if hasattr(self, "populate_suppliers"):
                self.populate_suppliers()


        save_btn.clicked.connect(save_supplier)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()



    def open_rep_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Sales Rep")
        dialog.setMinimumWidth(380)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

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
                QMessageBox.warning(dialog, "Validation Error", "Supplier is required.")
                return

            if not name:
                QMessageBox.warning(dialog, "Validation Error", "Rep name is required.")
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
                QMessageBox.critical(
                    dialog,
                    "Database Error",
                    f"Failed to save rep:\n{query.lastError().text()}"
                )
                return

            QMessageBox.information(dialog, "Success", "Rep added successfully.")
            dialog.accept()

            if hasattr(self, "load_reps"):
                self.load_reps()
                
                
                
        save_btn.clicked.connect(save_rep)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()
    
    
    
    
    
    
    def setup_supplier_rep_signals(self):
        
        self.supplier_edit.currentIndexChanged.connect(self.populate_reps)    
            
        
        
    def update_line_total(self):
        
        qty = self.qty_edit.text()
        rate = self.rate_edit.text()
        
        
        if qty == '':
            qty = 0
            
        if rate == '':
            rate = 0.00
        
        
        discount = self.discount_edit.text()
        
        if discount == "":
            discount = 0.00
        
        # turn it into flat discount
        flat_discount = 0.00
        if discount:
            try:
                discount_value = float(discount)
                subtotal = float(qty) * float(rate)
                flat_discount = (subtotal * discount_value) / 100
            except ValueError:
                pass
            
            
        # calculate tax amount
        tax = self.tax_edit.text()
        
        if tax == "":
            tax = 0.00
        
        tax_amount = 0.00
        if tax:
            try:
                tax_value = float(tax)
                taxable_amount = (float(qty) * float(rate)) - flat_discount
                tax_amount = (taxable_amount * tax_value) / 100
            except ValueError:
                pass
        
        # update the total label
        total = float(qty) * float(rate) - flat_discount + tax_amount
        self.amount_edit.setText(f"{total:.2f}")
        
        
    
    
    def populate_totals_section(self):
    
        totals_frame = QFrame()
        totals_frame.setObjectName("sectionCard")
        self.totals_frame = totals_frame

        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setContentsMargins(15, 15, 15, 15)
        totals_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        # -----------------------------
        # Row 1: Invoice math
        # -----------------------------
        gross_label = QLabel("Gross Amount")
        self.gross_entry = QLineEdit("0.00")
        self.gross_entry.setReadOnly(True)

        discount_label = QLabel("Discount")
        self.discount_entry = QLineEdit()

        taxable_label = QLabel("Taxable")
        self.taxable_entry = QLineEdit("0.00")
        self.taxable_entry.setReadOnly(True)

        tax_236g_label = QLabel("Tax 236(G)")
        self.tax_236g_entry = QLineEdit()

        tax_236h_label = QLabel("Tax 236(H)")
        self.tax_236h_entry = QLineEdit()

        sales_tax_label = QLabel("Sales Tax")
        self.sales_tax_entry = QLineEdit()

        net_amount_label = QLabel("Net Amount")
        self.net_amount_entry = QLineEdit("0.00")
        self.net_amount_entry.setReadOnly(True)
        
        payment_method_label = QLabel("Payment Method")
        payment_method_label.setFixedWidth(300)
        
        self.payment_handler = PaymentMethodHandler(self)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        

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

        grid.addWidget(self.cn_adjustment_entry, 3, 4)
        grid.addWidget(self.final_amount,        3, 5)
        grid.addWidget(self.paid_amount,         3, 6)
        grid.addWidget(self.remainingdata,       3, 7)

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

        # -----------------------------
        # Add totals frame
        # -----------------------------
        self.layout.addWidget(totals_frame)

        # -----------------------------
        # Save button
        # -----------------------------
        save_row = QHBoxLayout()
        addpurchase = QPushButton("Save Purchase Invoice", objectName="SaveButton")
        addpurchase.setCursor(Qt.PointingHandCursor)
        save_row.addWidget(addpurchase)
        self.save_purchase_button = addpurchase

        self.layout.addLayout(save_row)

        addpurchase.clicked.connect(self.save_purchase)
    
    
    
    
    
    
    def add_table(self):
        
         # Purchse Table
        self.row_height = 30
        self.min_visible_rows = 5
    
        self.table = MyTable(column_ratios=[0.03, 0.25, 0.07, 0.10, 0.05, 0.05, 0.07, 0.07, 0.05, 0.10, 0.05])
        headers = ["#", "Product", "Batch", "Expiry", "Qty", "Bonus", "Rate", "Disc % ", "Tax %", "Total", "X"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setTabKeyNavigation(False)
        
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.table.verticalHeader().setFixedWidth(0)
        remove_col = headers.index("X")
        self.table.horizontalHeaderItem(remove_col).setTextAlignment(Qt.AlignCenter)
        
        self.table.setStyleSheet("QTableWidget::item { color: #333; border: none;}")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   
        
        self.table.setMinimumWidth(1000)
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
        label_entry_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label_entry_frame = label_entry_frame

        label_entry_layout = QVBoxLayout(label_entry_frame)
        label_entry_layout.setContentsMargins(15, 10, 15, 20)
        label_entry_layout.setSpacing(8)
        self.label_entry_layout = label_entry_layout

        field_style = """
            QLabel {
                margin: 0;
                padding-left: 5px;
                font-size: 12px;
            }

            QLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                background-color: #f9f9f9;
            }

            QComboBox {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                background-color: #f9f9f9;
            }
            
            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus {
                border: 2px solid #5B8FB8;
                background: #F2F8FC;
            }

            KeyUpLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                background-color: #f9f9f9;
            }
        """

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        self.entry_grid = grid

        # -----------------------------
        # Labels
        # -----------------------------
        product_label = QLabel("Product")
        product_label.setStyleSheet(field_style)

        batch_label = QLabel("Batch")
        batch_label.setStyleSheet(field_style)

        expiry_label = QLabel("Expiry")
        expiry_label.setStyleSheet(field_style)

        qty_label = QLabel("Qty")
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
        self.item = QComboBox()
        self.item.wheelEvent = lambda event: event.ignore()
        self.item.setPlaceholderText("select product")
        self.item.setEditable(True)

        line_edit = SelectAllLineEdit()
        self.item.setLineEdit(line_edit)

        self.item.lineEdit().editingFinished.connect(
            lambda c=self.item: self.handle_editing_finished(c)
        )

        completer = QCompleter()
        self.item.setCompleter(completer)
        completer.setCompletionMode(QCompleter.PopupCompletion)

        completer.activated[str].connect(
            lambda text, c=self.item: self.on_completer_selected(text, c)
        )

        self.item.lineEdit().completer().popup().setStyleSheet("""
            QListView {
                padding: 5px;
                background-color: white;
                border: 1px solid gray;
                color: #333;
            }
            QListView::item {
                padding: 6px 10px;
            }
            QListView::item:selected {
                background-color: #5A9EC9;
                color: white;
            }
        """)

        self.item.lineEdit().textEdited.connect(
            lambda text: self.load_product_suggestions(self.item, completer)
        )
        self.item.setStyleSheet(field_style)

        self.batch_edit = QLineEdit()
        self.batch_edit.setPlaceholderText("batch")
        self.batch_edit.setStyleSheet(field_style)

        self.expiry_edit = QDateEdit()
        self.expiry_edit.setCalendarPopup(True)
        self.expiry_edit.setDisplayFormat("dd MMM yyyy")
        self.expiry_edit.setMinimumDate(QDate.currentDate())
        self.expiry_edit.setDate(self.expiry_edit.minimumDate())
        self.expiry_edit.setStyleSheet("""
            QDateEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f9f9f9;
                font-size: 14px;
            }

            QCalendarWidget QWidget {
                background-color: white;
                color: black;
            }

            QCalendarWidget QAbstractItemView {
                selection-background-color: #5A9EC9;
                selection-color: white;
                color: black;
            }

            QCalendarWidget QToolButton {
                background: none;
                color: black;
            }
        """)

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
        QWidget.setTabOrder(self.batch_edit, self.expiry_edit)
        QWidget.setTabOrder(self.expiry_edit, self.qty_edit)
        QWidget.setTabOrder(self.qty_edit, self.bonus_edit)
        QWidget.setTabOrder(self.bonus_edit, self.rate_edit)
        QWidget.setTabOrder(self.rate_edit, self.discount_edit)
        QWidget.setTabOrder(self.discount_edit, self.tax_edit)
        QWidget.setTabOrder(self.tax_edit, self.amount_edit)
        QWidget.setTabOrder(self.amount_edit, add_button)

        self.item.lineEdit().returnPressed.connect(lambda: self.handle_item_return_pressed(self.item))
        self.batch_edit.returnPressed.connect(lambda: self.focus_next_field(self.expiry_edit))
        self.expiry_edit.lineEdit().returnPressed.connect(lambda: self.focus_next_field(self.qty_edit))
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
        label_entry_layout.setStretch(2, 1)
        
        self.layout.addWidget(label_entry_frame)
        self.layout.setStretch(2, 1)
            
        
    
    def on_payment_method_changed(self, method):
        
        success = self.payment_handler.handle_method_change(method)

        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)
            
        
    
        
    def focus_next_field(self, widget):
        widget.setFocus()

        if hasattr(widget, "selectAll"):
            widget.selectAll()
        
        
    
        
    def update_total_amount(self):
        
        
        subtotal = 0.00
        for row in range(self.table.rowCount()):
            
            linetotal = self.table.cellWidget(row, 9).text()
            
            if linetotal:
                try:
                   
                    value = float(linetotal)
                    subtotal = subtotal + value
                    
                except ValueError:
                    pass  # skip empty or invalid cells
                
            else:
                continue
                
        self.gross_entry.setText(f"{subtotal:.2f}")
        discount = self.discount_entry.text()
        discount = float(discount) if discount else 0.00
        
        taxable = subtotal - discount
        self.taxable_entry.setText(f"{taxable:.2f}")
        
        tax_236g = self.tax_236g_entry.text()
        tax_236g = float(tax_236g) if tax_236g else 0.00
        
        tax_236h = self.tax_236h_entry.text()
        tax_236h = float(tax_236h) if tax_236h else 0.00
        
        sales_tax = self.sales_tax_entry.text()
        sales_tax = float(sales_tax) if sales_tax else 0.00
        
        tax_amount = tax_236g + sales_tax - tax_236h
        net_amount = taxable + tax_amount
        
        self.net_amount_entry.setText(f"{net_amount:.2f}")
        
        cn_adjust = self.cn_adjustment_entry.text()
        cn_adjust = float(cn_adjust) if cn_adjust else 0.00
        
        final_amount = net_amount - cn_adjust
        self.final_amount.setText(f"{final_amount:.2f}")
        
        self.final_amount.setStyleSheet("font-weight: bold;")
        
    


    def calculate_payment(self):
        
        finalamount = self.final_amount.text()
        finalamount = float(finalamount) if finalamount else 0.00
        
        paid = self.paid_amount.text()
        paid = float(paid) if paid else 0.00
        
        remaining = finalamount - paid
        self.remainingdata.setText(str(remaining))
        
    


    
    def handle_editing_finished(self, combo):
        
        print("Handling Editing Finished")

        text = combo.currentText().strip()
        if not text:
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

        index = combo.findText(text, Qt.MatchFixedString)

        if index >= 0:
            combo.setCurrentIndex(index)
            self.focus_next_field(self.batch_edit)
            return

        self.new_product = text
        self.add_new_product_dialog(combo, new_product=text)
    
    

       
   
    
    def add_row(self):
        
        row = self.table.rowCount()
        
        self.table.setRowHeight(row, self.row_height)
        
        counter = QLabel(str(row + 1))
        counter.setAlignment(Qt.AlignCenter)

        remove_btn = QPushButton("X")
        remove_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        remove_btn.setStyleSheet("color: #333;")
        
        product_name = self.item.currentText()
        product_id = self.item.currentData()
        
        print(f"Product Name: {product_name}, Product ID: {product_id}")
        
        
        product_combo = QComboBox()
        product_combo.setEditable(True)
        product_combo.lineEdit().setReadOnly(True)
        product_combo.setInsertPolicy(QComboBox.NoInsert)
        
        
        if product_name == '':
            print("Please Select a product first")
            QMessageBox.information(self, 'Error', "Please Select a product first")
            product_combo.setFocus()
            return
        elif product_id is None:
            print("Entered product is not available... Please Add this product first")
            QMessageBox.information(self, 'Error', "Entered product is not available... Please Add this product first")
            product_combo.setFocus()
            return
        
        
        
        product_combo.addItem(product_name, product_id)

        product_combo.setStyleSheet("""
        QComboBox::drop-down {
            border: 0px;
        }
        QComboBox::down-arrow {
            image: none;
        }
        """)
        
        
        ### get data from Entry Line
        
        qty_data = self.qty_edit.text()
        bonus_data = self.bonus_edit.text()
        rate_data = self.rate_edit.text()
        batch_data = self.batch_edit.text()
        expiry_data = self.expiry_edit.date().toString("dd-MM-yyyy")
        discount_data = self.discount_edit.text()
        tax_data = self.tax_edit.text()
        total_data = self.amount_edit.text()
        
        
        if expiry_data:
            try:
                expiry_date = datetime.strptime(expiry_data, "%d-%m-%Y").date()
                if expiry_date <= datetime.now().date():
                    expiry_data = ''  
                    print("Expiry date cannot be in the past. Setting it to empty.")
            except ValueError:
                expiry_data = ''  # If the date is invalid, set it to empty string
        
        
        if discount_data == "":
            discount_data = "0.0"
            
        
        if tax_data == "":
            tax_data = "0.0"
            
        if bonus_data == "":
            bonus_data = "0"
            
        
        # quantity check
        if qty_data == "" or qty_data == "0" or rate_data == "" or rate_data == "0":
            print("Quantity or Rate cannot be empty or zero.")
            QMessageBox.information(self, 'Error', "Quantity or Rate cannot be empty or zero.")
            return
            
        
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
        
        self.item.setFocus()
        
        self.update_total_amount()
        
        self.qty_edit.clear()
        self.bonus_edit.clear()
        self.rate_edit.clear()
        self.batch_edit.clear()
        self.expiry_edit.setDate(QDate.currentDate())
        self.discount_edit.clear()
        self.tax_edit.clear()
        
        # clear combo field
        self.item.setCurrentIndex(-1)
        self.update_purchase_table_height()
        
        

    
    
        

    def remove_row(self, target_row):
        
        self.table.removeRow(target_row)

        # Reconnect all remove buttons with updated row numbers
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 10)
            if isinstance(widget, QPushButton):
                widget.clicked.disconnect()
                widget.clicked.connect(lambda _, r=row: self.remove_row(r))

        
        self.update_total_amount()
        self.update_purchase_table_height()
        
        

    def showEvent(self, event):
        super().showEvent(event)
        self.populate_suppliers()
        QTimer.singleShot(0, self.update_purchase_table_height)


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

        self.table.setMinimumHeight(table_height)
        self.table.setMaximumHeight(table_height)
        


    def populate_suppliers(self):
        
        self.supplier_edit.blockSignals(True)
        self.supplier_edit.clear()

        query = QSqlQuery()
        if not query.exec("SELECT id, name FROM supplier WHERE status = 'active' ORDER BY name;"):
            QMessageBox.information(self, "Error", query.lastError().text())
            self.supplier_edit.blockSignals(False)
            self.rep_edit.clear()
            return

        while query.next():
            supplier_id = query.value(0)
            supplier_name = query.value(1)
            self.supplier_edit.addItem(supplier_name, supplier_id)

        self.supplier_edit.blockSignals(False)

        if self.supplier_edit.count() > 0:
            self.supplier_edit.setCurrentIndex(0)
            self.populate_reps()
        else:
            self.rep_edit.clear()
        
        
        
        
    def populate_reps(self):
        
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
            QMessageBox.information(self, "Error", query.lastError().text())
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
            self.rep_edit.setCurrentIndex(0)
    
    
    
    
    
    
    
    
    
    
    
    
    
    def save_purchase(self):
        self.show_price_review_dialog()

        # ------------------------------------------------------------
        # 1) Ask user whether they really want to save the purchase
        # ------------------------------------------------------------
        confirmation = QMessageBox.question(
            self,
            "Confirm Save",
            "Would you like to save the Purchase Order?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if confirmation != QMessageBox.Yes:
            return

        # ------------------------------------------------------------
        # 2) Get current database connection and start transaction
        # ------------------------------------------------------------
        db = QSqlDatabase.database()

        if not db.transaction():
            QMessageBox.critical(self, "Database Error", "Could not start database transaction.")
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
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while saving the purchase:\n{str(e)}"
            )
            return

        # ------------------------------------------------------------
        # 8) Commit transaction if all steps succeed
        # ------------------------------------------------------------
        if not db.commit():
            db.rollback()
            QMessageBox.critical(self, "Database Error", "Could not commit the purchase transaction.")
            return

        print("Transaction committed successfully")
        QMessageBox.information(self, "Success", "Purchase saved successfully.")
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
            raise Exception("Please enter seller invoice.")

        # rep can be optional if your system allows it
        # if rep is None:
        #     raise Exception("Please select a rep.")

        # ------------------------------------------------------------
        # 3) Convert numbers using your same style
        # ------------------------------------------------------------
        try:
            subtotal = float(subtotal) if subtotal else 0
            discount = float(discount) if discount else 0
            taxable = float(taxable) if taxable else 0
            tax_236g = float(tax_236g) if tax_236g else 0
            tax_236h = float(tax_236h) if tax_236h else 0
            sales_tax = float(sales_tax) if sales_tax else 0

            netamount = float(netamount) if netamount else 0
            cn_adjustment = float(cn_adjustment) if cn_adjustment else 0
            total = float(final_amount) if final_amount else 0
            paid = float(paid) if paid else 0
            remaining = float(remaining) if remaining else 0

        except ValueError:
            raise Exception("One or more numeric fields contain invalid values.")

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
        writeoff = 0.0
        payable = 0.0
        receivable = 0.0

        if remaining > 0.0:
            if self.writeoff_check.isChecked():
                writeoff = remaining
            else:
                payable = remaining

        elif remaining < 0.0:
            receivable = abs(remaining)

        # ------------------------------------------------------------
        # 8) Get session_id
        # ------------------------------------------------------------
        session_id = get_current_session(self)
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
            "writeoff": writeoff,
            "payable": payable,
            "receivable": receivable,
            "session_id": session_id,
            "header_net_amount": header_net_amount,
        }
        
        
    
    def _save_purchase_header(self, data):

        query = QSqlQuery()
        query.prepare("""
            INSERT INTO purchase (
                supplier,
                rep,
                sellerinvoice,
                subtotal,
                discount,
                tax_236g,
                tax_236h,
                salestax,
                netamount,
                cn_adjustment,
                total,
                paid,
                remaining,
                writeoff,
                payable,
                receivable,
                session_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        # ------------------------------------------------------------
        # 3) Bind values in the same sequence as query columns
        # ------------------------------------------------------------
        query.addBindValue(data["supplier"])
        query.addBindValue(data["rep"])
        query.addBindValue(data["sellerinvoice"])
        query.addBindValue(data["subtotal"])
        query.addBindValue(data["discount"])
        query.addBindValue(data["tax_236g"])
        query.addBindValue(data["tax_236h"])
        query.addBindValue(data["sales_tax"])
        query.addBindValue(data["netamount"])
        query.addBindValue(data["cn_adjustment"])
        query.addBindValue(data["total"])
        query.addBindValue(data["paid"])
        query.addBindValue(data["remaining"])
        query.addBindValue(data["writeoff"])
        query.addBindValue(data["payable"])
        query.addBindValue(data["receivable"])
        query.addBindValue(data["session_id"])

        # ------------------------------------------------------------
        # 4) Execute insert
        # ------------------------------------------------------------
        if not query.exec():
            raise Exception(f"Failed to save purchase header: {query.lastError().text()}")

        # ------------------------------------------------------------
        # 5) Read inserted purchase ID
        # ------------------------------------------------------------
        purchase_id = query.lastInsertId()

        if purchase_id is None:
            raise Exception("Purchase header saved, but could not retrieve purchase ID.")

        # Some drivers return QVariant-like values, so force int if needed
        try:
            purchase_id = int(purchase_id)
        except Exception:
            pass

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
                qty = float(qty) if qty else 0
                bonus = float(bonus) if bonus else 0
                rate = float(rate) if rate else 0
                item_discount = float(item_discount) if item_discount else 0
                item_tax = float(item_tax) if item_tax else 0
                item_total = float(item_total) if item_total else 0
            except ValueError:
                raise Exception(f"Invalid numeric value in row {row + 1}.")

            # --------------------------------------------------------
            # 9) Business validation
            # --------------------------------------------------------
            if qty <= 0:
                raise Exception(f"Quantity must be greater than zero in row {row + 1}.")

            if bonus < 0:
                raise Exception(f"Bonus cannot be negative in row {row + 1}.")

            if rate < 0:
                raise Exception(f"Rate cannot be negative in row {row + 1}.")

            if item_discount < 0:
                raise Exception(f"Discount cannot be negative in row {row + 1}.")

            if item_tax < 0:
                raise Exception(f"Tax cannot be negative in row {row + 1}.")


            # --------------------------------------------------------
            # 11) Insert into purchaseitem
            # --------------------------------------------------------
            item_query = QSqlQuery()
            item_query.prepare("""
                INSERT INTO purchaseitem (
                    purchase,
                    product,
                    qty,
                    bonus,
                    rate,
                    discount,
                    tax,
                    total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """)

            item_query.addBindValue(purchase_id)
            item_query.addBindValue(product)
            item_query.addBindValue(qty)
            item_query.addBindValue(bonus)
            item_query.addBindValue(rate)
            item_query.addBindValue(item_discount)
            item_query.addBindValue(item_tax)
            item_query.addBindValue(item_total)

            if not item_query.exec():
                raise Exception(
                    f"Failed to save purchase item in row {row + 1}: "
                    f"{item_query.lastError().text()}"
                )

            purchase_item_id = item_query.lastInsertId()

            if purchase_item_id is None:
                raise Exception(f"Purchase item saved in row {row + 1}, but no ID was returned.")

            try:
                purchase_item_id = int(purchase_item_id)
            except Exception:
                pass

            print("Purchase item saved with ID:", purchase_item_id)

            # --------------------------------------------------------
            # 12) Insert batch row
            # --------------------------------------------------------
            #
            received = qty + bonus
            batch_query = QSqlQuery()
            batch_query.prepare("""
                INSERT INTO batch (
                    batch_no,
                    expiry_date,
                    
                    product_id,
                    purchaseitem_id,
                    
                    total_received,
                    paid_qty,
                    quantity_remaining,
                    unit_cost,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)

            batch_query.addBindValue(batch if batch else None)
            batch_query.addBindValue(expiry if expiry else None)
            
            batch_query.addBindValue(product)
            batch_query.addBindValue(purchase_item_id if purchase_item_id else None)
            
            batch_query.addBindValue(received)
            batch_query.addBindValue(qty)
            batch_query.addBindValue(received)
            batch_query.addBindValue(rate)
            batch_query.addBindValue('PURCHASE')
            
            print("Batch query lastError before exec:", batch_query.lastError().text())
            print("Product:", product)
            print("Purchase Item ID:", purchase_item_id)
            print("Received:", received)
            print("Qty:", qty)
            print("Rate:", rate)
            
            if not batch_query.exec():
                raise Exception(
                    f"Failed to save batch in row {row + 1}: "
                    f"{batch_query.lastError().text()}"
                )

            print(f"Batch saved successfully for row {row + 1}")

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

        supplier = data["supplier"]
        rep = data["rep"]
        session_id = data["session_id"]

        paid = data["paid"]
        writeoff = data["writeoff"]
        payable = data["payable"]
        receivable = data["receivable"]
        total = data["total"]

        # ------------------------------------------------------------
        # 1) Get supplier balances BEFORE transaction
        # ------------------------------------------------------------
        query = QSqlQuery()
        query.prepare("SELECT payable, receiveable FROM supplier WHERE id = ?")
        query.addBindValue(supplier)

        if not query.exec() or not query.next():
            raise Exception("Failed to fetch supplier balances.")

        payable_before = float(query.value(0) or 0)
        receiveable_before = float(query.value(1) or 0)

        # ------------------------------------------------------------
        # 2) Calculate purchase transaction values
        # ------------------------------------------------------------
        transaction_type = "PURCHASE"
        ref = purchase_id
        return_ref = None

        due_amount = total
        remaining_due = payable
        payable_after = payable_before + payable

        receiveable_now = receivable
        received = paid
        remaining_now = receivable
        receiveable_after = receiveable_before + receivable


        # ------------------------------------------------------------
        # 4) Insert supplier transaction
        # ------------------------------------------------------------
        query = QSqlQuery()
        query.prepare("""
            INSERT INTO supplier_transaction 
            (
                supplier, transaction_type, ref, return_ref,
                payable_before, due_amount, paid, remaining_due, payable_after,
                receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                rep, session_id,
                payment_method, bank_name, account_no, transaction_mode,
                wallet_provider, wallet_no, payment_reference
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        query.addBindValue(supplier)
        query.addBindValue(transaction_type)
        query.addBindValue(ref)
        query.addBindValue(return_ref)

        query.addBindValue(payable_before)
        query.addBindValue(due_amount)
        query.addBindValue(paid)
        query.addBindValue(remaining_due)
        query.addBindValue(payable_after)

        query.addBindValue(receiveable_before)
        query.addBindValue(receiveable_now)
        query.addBindValue(received)
        query.addBindValue(remaining_now)
        query.addBindValue(receiveable_after)

        query.addBindValue(rep)
        query.addBindValue(session_id)
        
        payment = self.payment_handler.payment_data.copy()
        
        print(payment)
        

        query.addBindValue(payment["payment_method"])
        query.addBindValue(payment["bank_name"])
        query.addBindValue(payment["account_no"])
        query.addBindValue(payment["transaction_mode"])
        query.addBindValue(payment["wallet_provider"])
        query.addBindValue(payment["wallet_no"])
        query.addBindValue(payment["payment_reference"])

        

        if not query.exec():
            raise Exception(f"Failed to save supplier transaction: {query.lastError().text()}")

        # ------------------------------------------------------------
        # 5) Update supplier table balances
        # ------------------------------------------------------------
        update_query = QSqlQuery()
        update_query.prepare("""
            UPDATE supplier
            SET payable = ?, receiveable = ?
            WHERE id = ?
        """)

        update_query.addBindValue(payable_after)
        update_query.addBindValue(receiveable_after)
        update_query.addBindValue(supplier)

        if not update_query.exec():
            raise Exception(f"Failed to update supplier balances: {update_query.lastError().text()}")

        print("Supplier transaction saved successfully.")    
            
            
    
    
    
    
    def load_product_suggestions(self, item, completer):
        
        current_text = item.lineEdit().text().strip()
        print("Current Text is:", current_text)

        if not current_text:
            item.blockSignals(True)
            item.clear()
            item.setCurrentIndex(-1)
            item.blockSignals(False)
            return

        query = QSqlQuery()
        query.prepare("""
            SELECT id, display_name
            FROM product
            WHERE display_name LIKE ?
            LIMIT 10
        """)
        query.addBindValue(f"%{current_text}%")

        products = []
        product_data = []

        if not query.exec():
            print("Something wrong happened...", query.lastError().text())
            return

        while query.next():
            product_id = query.value(0)
            name = str(query.value(1)).strip()

            products.append(name)
            product_data.append((name, product_id))

        item.blockSignals(True)
        item.clear()

        for name, product_id in product_data:
            item.addItem(name, product_id)

        item.setCurrentIndex(-1)
        item.lineEdit().setText(current_text)
        item.blockSignals(False)

        model = QStringListModel(products)
        completer.setModel(model)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        # force popup to appear
        completer.complete()
        
    
    
    
      
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
    
    
    def clear_fields(self):
        
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
        
        self.table.setRowCount(0)
        
        self.payment_method.blockSignals(True); 
        self.payment_method.setCurrentIndex(0) 
        self.payment_method.blockSignals(False)
        
        self.populate_suppliers()
        
       


    def add_new_product_dialog(self, combo, new_product=None):
        
        dialog = ImportDialog(self)
        
        dialog.name_input.setText(new_product)
        
        if dialog.exec() == QDialog.Accepted:
            
            print("New Product is: ", new_product)
            
            
            item_name = dialog.name_input.text()
            item_form = dialog.form_input.currentText()
            item_packing = dialog.packing_input.text()
            
            display_name = f"{item_name} {item_form} {item_packing}"
            print("The display name is: ", display_name)
            
            manufacturer = dialog.brand_input.currentData()
            packsize = dialog.packsize_input.text()
            saleprice = dialog.saleprice_input.text()
            
            # Insert Data into Database
            
            brand_name = item_name.strip() if item_name.strip() else None
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
                    pack_size,
                    manufacturer_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
            
            code = ''
            reg_no = ''
            generic_name = ''
            packing = ''
            
            packsize = int(packsize)
            product_query.addBindValue(display_name)
            product_query.addBindValue(code)
            product_query.addBindValue(reg_no)
            product_query.addBindValue(generic_name)
            product_query.addBindValue(brand_name)
            product_query.addBindValue(item_form)
            product_query.addBindValue(item_packing)
            product_query.addBindValue(packing)
            product_query.addBindValue(packsize)
            product_query.addBindValue(manufacturer)

            if not product_query.exec():
                raise Exception(product_query.lastError().text())

            else:
                
                QMessageBox.information(None, "Success", "Product added successfully")
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
        main_layout.setContentsMargins(20, 20, 20, 20)
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
            QMessageBox.information(
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
            QMessageBox.critical(self, "Database Error", "Could not start price update transaction.")
            return

        try:
            updated_rows = 0

            for row in range(table.rowCount()):
                product_id_item = table.item(row, 0)
                previous_price_item = table.item(row, 2)
                new_price_item = table.item(row, 3)

                if product_id_item is None or new_price_item is None:
                    continue

                new_price_text = new_price_item.text().strip()
                if not new_price_text:
                    continue

                product_id = int(product_id_item.text().strip())
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
                        new_price
                    )
                    VALUES (?, ?, ?)
                """)
                change_query.addBindValue(product_id)
                change_query.addBindValue(previous_price)
                change_query.addBindValue(new_price)

                if not change_query.exec():
                    raise Exception(f"Failed to log price change in row {row + 1}: {change_query.lastError().text()}")

                updated_rows += 1

            if updated_rows == 0:
                raise Exception("Enter at least one new price before saving changes.")

            if not db.commit():
                raise Exception("Could not commit price changes.")

            dialog.accept()

        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", str(e))
             


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
        self.resize(600, 400)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.indicators = {}
        self.insert_subheading("PRODUCT Does Not Exist... Add INFORMATION")
        
        self.populate_product_fields()
       

        self.setLayout(self.layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)   # Save → dialog.accept()
        button_box.rejected.connect(self.reject)   # Cancel → dialog.reject()
        self.layout.addWidget(button_box)
    
    

    def insert_subheading(self, title):
        
        # === Sub Header Row ===
        subheader_layout = QHBoxLayout()
        subheading = QLabel(title, objectName="SubHeading")
        
        subheader_layout.addWidget(subheading)
        self.layout.addLayout(subheader_layout)
        
        
        
    
    def populate_product_fields(self):
        
        item_layout = QHBoxLayout()
        
        # Item Label with stretch factor 2
        item_label = QLabel("Item")
        item_layout.addWidget(item_label, stretch=2)

        # Spacer with stretch factor 1
        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        item_layout.addItem(spacer)

        # Name input with stretch factor 3
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('name')
        item_layout.addWidget(self.name_input, stretch=3)

        # Form input with stretch factor 1
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
        self.form_input.addItems(forms)
        item_layout.addWidget(self.form_input, stretch=1)

        # Packing input with stretch factor 1
        self.packing_input = QLineEdit()
        self.packing_input.setPlaceholderText('dose')
        item_layout.addWidget(self.packing_input, stretch=1)
        
        
        self.layout.addLayout(item_layout)
        
        
        
        # brand line
        
        brand_layout = QHBoxLayout()
        
        brand_label = QLabel("Brand")
        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.brand_input = QComboBox()
        self.setup_manufacturer_combobox(self.brand_input)
        
        brand_layout.addWidget(brand_label, 2)
        brand_layout.addItem(spacer)
        brand_layout.addWidget(self.brand_input, 5)
        
        self.layout.addLayout(brand_layout)
        
        
        
        # pack size - line
        
        size_layout = QHBoxLayout()
        
        size_label = QLabel("Pack Size")
        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.packsize_input = QLineEdit()
        
        size_layout.addWidget(size_label, 2)
        size_layout.addItem(spacer)
        size_layout.addWidget(self.packsize_input, 5)
        
        self.layout.addLayout(size_layout)
        
        
        
        # pack size - line
        
        price_layout = QHBoxLayout()
        
        size_label = QLabel("Pack Sale Price")
        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.saleprice_input = QLineEdit()
        
        price_layout.addWidget(size_label, 2)
        price_layout.addItem(spacer)
        price_layout.addWidget(self.saleprice_input, 5)
        
        self.layout.addLayout(price_layout)
        
        
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
        except:
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
