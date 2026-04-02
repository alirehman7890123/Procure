from PySide6.QtWidgets import QApplication, QWidget, QCompleter, QDateEdit, QVBoxLayout, QHBoxLayout, QDialog, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QStringListModel, QDate, Signal, QTimer, QEvent, QRectF
import os
import sys
import platform

from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent, QPdfWriter, QKeySequence, QPainter, QPageSize, QFont, QTextOption, QPen, QColor
from functools import partial
import math
from utilities.stylus import load_stylesheets
from utilities.get_session import get_current_session
from PySide6.QtGui import QKeySequence, QShortcut

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




from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QLineEdit, QCheckBox, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt


class CreateSalesWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        
        
        # === Main Vertical Layout ===
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        self.scan_timer = QTimer(self)
        self.scan_timer.setSingleShot(True)
        self._pending_scan = None
        self.scan_timer.timeout.connect(lambda: self._run_pending_scan())
        
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reloading_sale = False
        self.order_modified = False
        self.row_height = 40

        

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Sales Receipt", objectName='SectionTitle')
        
        
        clear_btn = QPushButton('Clear Sale', objectName='TopRightButton')
        clear_btn.setFixedWidth(150)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_fields)
        
        
        self.invoicelist = QPushButton('SO List', objectName='TopRightButton')
        self.invoicelist.setFixedWidth(150)
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(heading)
        header_layout.addWidget(clear_btn)
        header_layout.addWidget(self.invoicelist)
        
        self.layout.addLayout(header_layout)

        

        # === Customer + Salesman Row ===
        
        self.add_customer_section()
        

        self.add_product_section()
        
        

        self.add_totals_section()
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

        if self.item.completer():
            self.item.completer().popup().hide()

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
        customer_layout.setContentsMargins(15, 10, 15, 10)
        customer_layout.setSpacing(8)

        # Top Row Layout
        top_row = QHBoxLayout()
        top_row.setSpacing(15)

        top_row = QHBoxLayout()
        customerlabel = QLabel("CUSTOMER")
        
        self.customer = QComboBox()
        self.customer.setMinimumWidth(200) 
               
        self.customer.setEditable(True)
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
        main_final_label.setStyleSheet("font-weight: 500; font-size: 14px;")   
        
             
        self.main_final_amount = QLabel("0.00")
        self.main_final_amount.setStyleSheet("font-weight: 700; font-size: 20px;")
        top_row.addWidget(main_final_label)
        top_row.addWidget(self.main_final_amount)
        
        self.new_customer_btn.clicked.connect(self.open_customer_dialog)
        
        
        customer_layout.addLayout(top_row)

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
                QMessageBox.warning(dialog, "Validation Error", "Customer name is required.")
                return

            query = QSqlQuery()
            query.prepare("""
                INSERT INTO customer (
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
                    f"Failed to save customer:\n{query.lastError().text()}"
                )
                return

            QMessageBox.information(dialog, "Success", "Customer added successfully.")
            dialog.accept()

            if hasattr(self, "populate_customers"):
                self.populate_customers()


        save_btn.clicked.connect(save_customer)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()


    
    def add_table(self):
        
        self.row_height = 30

        self.table = MyTable(column_ratios=[0.05, 0.35, 0.08, 0.08, 0.08, 0.08, 0.08, 0.03])
        headers = ["#", " Product ", " Qty", "Rate", "Disc %", "Tax %", "Total", "X"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        self.table.setTabKeyNavigation(False)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumWidth(900)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        visible_rows = 8
        header_height = self.table.horizontalHeader().height()

        table_height = header_height + (self.row_height * visible_rows) + 2
        self.table.setFixedHeight(table_height)

        return self.table 
        
    
    def add_product_section(self):
        
        product_frame = QFrame()
        product_frame.setObjectName("sectionCard")
        self.product_frame = product_frame
        
        product_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        
        product_entry_layout = QVBoxLayout(product_frame)
        product_entry_layout.setContentsMargins(15, 10, 15, 20)
        product_entry_layout.setSpacing(0)
        self.product_entry_layout = product_entry_layout
        
        product_entry_layout.setAlignment(Qt.AlignTop)
        
        field_style = """
            QLabel {
                margin: 0;
                font-size: 11px;
                letter-spacing: 0.2px;
                margin-right: 5px;
            }

            QLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 12px;
                letter-spacing: 0.2px;
                background-color: #f9f9f9;
            }

            QComboBox {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 12px;
                letter-spacing: 0.2px;
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
                letter-spacing: 0.2px;
                background-color: #f9f9f9;
            }
        """

        
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        self.entry_grid = grid

        # -----------------------------
        # Labels
        # -----------------------------
        
        info_box_layout = QHBoxLayout()
        
        info_btn = QPushButton("i")
        info_btn.setFixedWidth(40)
        
        info_box_layout.addWidget(info_btn)
        
        grid.addLayout(info_box_layout, 0 , 0)

        
        product_box_layout = QHBoxLayout()
        
        product_label = QLabel("PRODUCT")
        product_label.setStyleSheet(field_style)
        
        
        self.item = QComboBox()
        self.item.wheelEvent = lambda event: event.ignore()
        self.item.setEditable(True)
        
        

        line_edit = SelectAllLineEdit()
        self.item.setLineEdit(line_edit)

        self.item.lineEdit().textEdited.connect(self.force_uppercase)

        completer = QCompleter()
        self.item.setCompleter(completer)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        completer.activated[str].connect(
            lambda text, c=self.item: self.on_completer_selected(text, c)
        )

        self.item.completer().popup().setStyleSheet("""
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
        
        
        QShortcut(
            QKeySequence(Qt.Key_Escape),
            self.item,
            activated=self.clear_product_field
        )
        
        
        self.item.setStyleSheet(field_style)
        
        product_box_layout.addWidget(product_label, 0)
        product_box_layout.addWidget(self.item, 1)
        
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

        self.discount = KeyUpLineEdit()
        self.discount.setPlaceholderText("Disc %")
        self.discount.setStyleSheet(field_style)

        discount_box_layout.addWidget(discount_label)
        discount_box_layout.addWidget(self.discount)

        grid.addLayout(discount_box_layout, 0, 4)



        # ---- TAX % ----
        tax_box_layout = QHBoxLayout()
        tax_box_layout.setSpacing(6)

        tax_label = QLabel("TAX %")
        tax_label.setStyleSheet(field_style)

        self.tax = KeyUpLineEdit()
        self.tax.setPlaceholderText("Tax %")
        self.tax.setStyleSheet(field_style)

        tax_box_layout.addWidget(tax_label)
        tax_box_layout.addWidget(self.tax)

        grid.addLayout(tax_box_layout, 0, 5)


        # ---- TOTAL ----
        total_box_layout = QHBoxLayout()
        total_box_layout.setSpacing(6)

        total_label = QLabel("TOTAL")
        total_label.setStyleSheet(field_style)

        self.amount_edit = QLineEdit()
        self.amount_edit.setReadOnly(True)
        self.amount_edit.setText("0.00")
        self.amount_edit.setStyleSheet(field_style)

        total_box_layout.addWidget(total_label)
        total_box_layout.addWidget(self.amount_edit)

        grid.addLayout(total_box_layout, 0, 6)


        # ---- ACTION ----
        add_button = QPushButton("+", objectName="EntryButton")
        add_button.clicked.connect(self.add_row)

        action_box_layout = QHBoxLayout()
        action_box_layout.setContentsMargins(0, 0, 0, 0)
        action_box_layout.setSpacing(6)
        action_box_layout.addWidget(add_button)

        grid.addLayout(action_box_layout, 0, 7)
        
        
        
        
        
        
        
        qty_filter = QtyValidationFilter(self, self.qty_edit, self.item)
        self.qty_edit.installEventFilter(qty_filter)

        # important: keep reference
        if not hasattr(self, "qty_filters"):
            self.qty_filters = []
        self.qty_filters.append(qty_filter)
        
        
        
        
        self.qty_edit.returnPressed.connect(lambda: self.focus_next_field(self.rate_edit))
        self.rate_edit.returnPressed.connect(lambda: self.focus_next_field(self.discount))
        self.discount.returnPressed.connect(lambda: self.focus_next_field(self.tax))
        self.tax.returnPressed.connect(lambda: self.focus_next_field(add_button))
        

        self.qty_edit.textChanged.connect(self.update_line_total)
        self.rate_edit.textChanged.connect(self.update_line_total)

        self.discount.textChanged.connect(self.update_line_total)
        self.tax.textChanged.connect(self.update_line_total)
        
        
        
        
        
        # -----------------------------
        # Stretch factors
        # -----------------------------
        ratios = [5, 35, 8, 8, 8, 8, 8, 3]

        for col, r in enumerate(ratios):
            grid.setColumnStretch(col, r)

        

        product_entry_layout.addLayout(grid)
        product_entry_layout.addSpacing(10)

        table = self.add_table()
        product_entry_layout.addWidget(table)

        self.layout.addWidget(product_frame)
    
    
    
    
    def clear_product_field(self):
        
        self.item.blockSignals(True)

        self.item.setCurrentIndex(-1)
        self.item.lineEdit().clear()

        if self.item.completer():
            self.item.completer().popup().hide()

        self.item.blockSignals(False)
        self.item.setFocus()
    
    
    
    
    def add_totals_section(self):
    
        totals_frame = QFrame()
        totals_frame.setObjectName("sectionCard")
        self.totals_frame = totals_frame

        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setContentsMargins(10, 10, 10, 10)
        totals_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(5)

        label_style = """
        QLabel {
            font-size: 12px;
            color: #555;
            font-weight: 600;
        }
        """

        # -----------------------------
        # Create labels
        # -----------------------------
        gross_label = QLabel("Sub Total")
        discount_label = QLabel("Discount")
        tax_label = QLabel("Sales Tax")
        additional_label = QLabel("Additional Charges")
        taxable_label = QLabel("Taxable")
        net_amount_label = QLabel("Net Amount")

        final_amount_label = QLabel("Final Amount")
        final_amount_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        final_amount_label.setStyleSheet("font-size: 16px; font-weight:600; color: #666;")

        received_label = QLabel("Received")
        received_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        received_label.setStyleSheet("font-size: 16px; font-weight: 600;")

        payment_method_label = QLabel("Payment Method")
        remaining_label = QLabel("Remaining Amount")
        change_label = QLabel("Change")

        gross_label.setStyleSheet(label_style)
        discount_label.setStyleSheet(label_style)
        taxable_label.setStyleSheet(label_style)
        tax_label.setStyleSheet(label_style)
        net_amount_label.setStyleSheet(label_style)
        additional_label.setStyleSheet(label_style)
        payment_method_label.setStyleSheet(label_style)
        remaining_label.setStyleSheet(label_style)
        change_label.setStyleSheet(label_style)

        # -----------------------------
        # Create fields
        # -----------------------------
        self.gross_entry = QLineEdit("0.00")
        self.gross_entry.setReadOnly(True)

        self.discount_entry = QLineEdit()

        self.tax_entry = QLineEdit()

        self.additional_entry = QLineEdit()

        self.taxable_entry = QLineEdit("0.00")
        self.taxable_entry.setReadOnly(True)

        self.net_amount_entry = QLineEdit("0.00")
        self.net_amount_entry.setReadOnly(True)

        self.final_amount_entry = QLabel("0.00")
        self.final_amount_entry.setObjectName("FinalAmount")

        self.received_entry = QLineEdit("0.00")
        self.received_entry.setObjectName("ReceivedAmount")
        
        self.change_entry = QLineEdit("0.00")
        self.change_entry.setReadOnly(True)

        self.remainingdata = QLineEdit("0.00")
        self.remainingdata.setReadOnly(True)

        self.writeoff_check = QCheckBox("Write-off Remaining")
        self.writeoff_check.setStyleSheet("QCheckBox { color: #333; }")

        self.payment_handler = PaymentMethodHandler(self)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        
        
        
        self.gross_entry.setAlignment(Qt.AlignRight)
        self.discount_entry.setAlignment(Qt.AlignRight)
        self.tax_entry.setAlignment(Qt.AlignRight)
        self.received_entry.setAlignment(Qt.AlignRight)
        self.remainingdata.setAlignment(Qt.AlignRight)

        # -----------------------------
        # Signals
        # -----------------------------
        self.discount_entry.textChanged.connect(self.update_total_amount)
        self.tax_entry.textChanged.connect(self.update_total_amount)
        self.additional_entry.textChanged.connect(self.update_total_amount)
        self.received_entry.textChanged.connect(self.calculate_payment)

        # -----------------------------
        # Row 1
        # subtotal-value, discount-value, tax-value,
        # final_amount-value, then a space, then received-value
        # -----------------------------
        subtotal_layout = QHBoxLayout()
        subtotal_layout.addWidget(gross_label)
        subtotal_layout.addWidget(self.gross_entry)
        grid.addLayout(subtotal_layout, 0, 0)

        discount_layout = QHBoxLayout()
        discount_layout.addWidget(discount_label)
        discount_layout.addWidget(self.discount_entry)
        grid.addLayout(discount_layout, 0, 1)

        tax_layout = QHBoxLayout()
        tax_layout.addWidget(tax_label)
        tax_layout.addWidget(self.tax_entry)
        grid.addLayout(tax_layout, 0, 2)
        
        additional_layout = QHBoxLayout()
        
        additional_layout.addWidget(additional_label)
        additional_layout.addWidget(self.additional_entry)
        grid.addLayout(additional_layout, 0, 3)
        
        space_label = QLabel()
        grid.addWidget(space_label, 0, 4)

        final_amount_layout = QHBoxLayout()
        final_amount_layout.setContentsMargins(10, 0, 0, 0)
        final_amount_layout.addWidget(final_amount_label)
        final_amount_layout.addWidget(self.final_amount_entry)
        grid.addLayout(final_amount_layout, 0, 5)

        # give layout left margin
        

        received_layout = QHBoxLayout()
        received_layout.addWidget(received_label)
        received_layout.addWidget(self.received_entry)
        grid.addLayout(received_layout, 0, 6)

        # -----------------------------
        # Row 2
        # under final_amount-value column make payment method-value,
        # then space, then remaining-value
        # -----------------------------
        method_layout = QHBoxLayout()
        method_layout.addWidget(payment_method_label)
        method_layout.addWidget(self.payment_method)
        grid.addLayout(method_layout, 1, 3)

        space_label_2 = QLabel()
        grid.addWidget(space_label_2, 1, 4)

        remaining_layout = QHBoxLayout()
        remaining_layout.addWidget(remaining_label)
        remaining_layout.addWidget(self.remainingdata)
        grid.addLayout(remaining_layout, 1, 6)

        # -----------------------------
        # Row 3
        # checkbox at the end column
        # -----------------------------
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.writeoff_check)
        grid.addLayout(checkbox_layout, 2, 6)

        # -----------------------------
        # Stretch
        # -----------------------------
        for col in range(7):
            grid.setColumnStretch(col, 1)

        totals_layout.addLayout(grid)

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
        addreceipt.clicked.connect(lambda: self.save_receipt())
        save_row.addWidget(addreceipt, 1)

        self.layout.addLayout(save_row, 0)
        
    
    # def add_totals_section(self):
    
    #     totals_frame = QFrame()
    #     totals_frame.setObjectName("sectionCard")
    #     self.totals_frame = totals_frame

    #     totals_layout = QVBoxLayout(totals_frame)
    #     totals_layout.setContentsMargins(10, 10, 10, 10)
    #     totals_layout.setSpacing(12)

    #     grid = QGridLayout()
    #     grid.setHorizontalSpacing(14)
    #     grid.setVerticalSpacing(5)
        
    #     label_style= """
        
    #     QLabel {
    #         font-size: 12px;
    #         color: #555; 
    #         font-weight: 600;    
    #     }
        
    #     """

    #     # -----------------------------
    #     # Create labels
    #     # -----------------------------
        
        
    #     subtotal_layout = QHBoxLayout()
    #     gross_label = QLabel("Sub Total")
    #     self.gross_entry = QLineEdit("0.00")
    #     self.gross_entry.setReadOnly(True)
        
    #     subtotal_layout.addWidget(gross_label)
    #     subtotal_layout.addWidget(self.gross_entry)
    #     grid.addLayout(subtotal_layout, 0, 0)
        
        
        
        
    #     discount_layout = QHBoxLayout()
    #     discount_label = QLabel("Discount")
    #     self.discount_entry = QLineEdit()
        
    #     discount_layout.addWidget(discount_label)
    #     discount_layout.addWidget(self.discount_entry)
        
    #     grid.addLayout(discount_layout, 0, 1)
        
        
        
    #     tax_layout = QHBoxLayout()
        
    #     tax_label = QLabel("Sales Tax")
    #     self.tax_entry = QLineEdit()
        
    #     tax_layout.addWidget(tax_label)
    #     tax_layout.addWidget(self.tax_entry)
        
    #     grid.addLayout(tax_layout, 0, 2)
        
        
        
        
        
    #     additional_layout = QHBoxLayout()
        
    #     additional_label = QLabel("Additional Charges")
    #     self.additional_entry = QLineEdit()
        
    #     additional_layout.addWidget(additional_label)
    #     additional_layout.addWidget(self.additional_entry)
        
    #     grid.addLayout(additional_layout, 0, 3)

        
    #     taxable_label = QLabel("Taxable")
        
    #     net_amount_label = QLabel("Net Amount")
    #     final_amount_label = QLabel("Final Amount")
    #     final_amount_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    #     final_amount_label.setStyleSheet("font-size: 16px; font-weight:600;")
        
        
    #     gross_label.setStyleSheet(label_style)
    #     discount_label.setStyleSheet(label_style)
    #     taxable_label.setStyleSheet(label_style)
    #     tax_label.setStyleSheet(label_style)
    #     net_amount_label.setStyleSheet(label_style)
    #     additional_label.setStyleSheet(label_style)

        
    #     change_label = QLabel("Change")
    #     remaining_label = QLabel("Remaining Amount")
        
    #     remaining_label.setStyleSheet(label_style)
    #     change_label.setStyleSheet(label_style)

    #     # -----------------------------
    #     # Create fields
    #     # -----------------------------
        
        
        
    #     space_label = QLabel()
    #     grid.addWidget(space_label, 0, 4)
        
        
        
    #     method_layout = QHBoxLayout()
        
    #     payment_method_label = QLabel("Payment Method")
    #     payment_method_label.setStyleSheet(label_style)
        
    #     self.payment_handler = PaymentMethodHandler(self)

    #     self.payment_method = QComboBox()
    #     self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
    #     self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        
        
    #     method_layout.addWidget(payment_method_label)
    #     method_layout.addWidget(self.payment_method)
        
    #     grid.addLayout(method_layout, 1, 0)
        
        
        
    #     received_layout = QHBoxLayout()   
        
    #     received_label = QLabel("Received")
    #     received_label.setStyleSheet(label_style)
    #     received_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    #     received_label.setStyleSheet('font-size: 16px; font-weight: 600;')
        
    #     self.received_entry = QLineEdit("0.00")
    #     self.received_entry.setStyleSheet('font-size: 16px; font-weight: 600; padding: 5px;')
        
        
    #     received_layout.addWidget(received_label)
    #     received_layout.addWidget(self.received_entry)
        
    #     grid.addLayout(received_layout, 0, 7)
        
        



        
    #     self.taxable_entry = QLineEdit("0.00")
    #     self.taxable_entry.setReadOnly(True)
        

    #     self.net_amount_entry = QLineEdit("0.00")
    #     self.net_amount_entry.setReadOnly(True)



        
    #     self.final_amount_entry = QLabel("0.00")
    #     self.final_amount_entry.setStyleSheet("font-size: 20px; font-weight: 700;")
        
        
        
        
        
        
        
        
    #     self.change_entry = QLineEdit("0.00")
    #     self.change_entry.setReadOnly(True)
        
    #     self.remainingdata = QLineEdit("0.00")
    #     self.remainingdata.setReadOnly(True)

        
        
        
        

    #     self.writeoff_check = QCheckBox("Write-off Remaining")
    #     self.writeoff_check.setStyleSheet("QCheckBox { color: #333; }")

    #     # -----------------------------
    #     # Signals
    #     # -----------------------------
    #     self.discount_entry.textChanged.connect(self.update_total_amount)
    #     self.tax_entry.textChanged.connect(self.update_total_amount)
    #     self.additional_entry.textChanged.connect(self.update_total_amount)
    #     self.received_entry.textChanged.connect(self.calculate_payment)


        
    #     final_amount_layout = QHBoxLayout()
        
        
    #     final_amount_layout.addWidget(final_amount_label)
    #     final_amount_layout.addWidget(self.final_amount_entry)
    #     grid.addLayout(final_amount_layout, 0, 5)
        
        
    #     grid.addWidget(payment_method_label, 2, 0)
    #     grid.addWidget(self.payment_method,  2, 1)
        
        
        
        

    #     grid.addWidget(remaining_label, 2, 5)
    #     grid.addWidget(self.remainingdata,   2, 6)
        
        
    #     grid.addWidget(self.writeoff_check,  3, 6)
        

        

    #     # -----------------------------
    #     # Stretch
    #     # -----------------------------
    #     for col in range(7):
    #         grid.setColumnStretch(col, 1)

        
        
        
        
    #     totals_layout.addLayout(grid)

    #     # -----------------------------
    #     # Add totals frame
    #     # -----------------------------
    #     self.layout.addWidget(totals_frame, 0)

    #     # -----------------------------
    #     # Save Button
    #     # -----------------------------
    #     save_row = QHBoxLayout()
    #     addreceipt = QPushButton("Save Sales Receipt", objectName="SaveButton")
    #     addreceipt.setCursor(Qt.PointingHandCursor)
    #     addreceipt.clicked.connect(lambda: self.save_receipt())
    #     save_row.addWidget(addreceipt, 1)

    #     self.layout.addLayout(save_row, 0)
        
    
    
    
            
        
    def focus_next_field(self, widget):
        widget.setFocus()

        if hasattr(widget, "selectAll"):
            widget.selectAll()
        

    
    
    def eventFilter(self, obj, event):
        
        if obj == self.customer.lineEdit():
            if event.type() == QEvent.FocusIn:
                obj.selectAll()
        return super().eventFilter(obj, event)
    
    
    
    
    
    def on_payment_method_changed(self, method):
        
        success = self.payment_handler.handle_method_change(method)

        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)
   




    def update_line_total(self):
        
        qty = self.qty_edit.text()
        rate = self.rate_edit.text()
        
        
        if qty == '':
            qty = 0
            
        if rate == '':
            rate = 0.00
        
        
        discount = self.discount.text()
        
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
        tax = self.tax.text()
        
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
        
      


    
    
    def keyPressEvent(self, event):
        # Check if Ctrl is pressed AND key is K
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_H:
            self.put_sale_on_hold()
        
        elif event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_L:
            self.load_hold_orders()
        
            
        else:
            super().keyPressEvent(event)  # Propagate if not handled
    
    
    
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
            QMessageBox.information(self, 'Error', "Please Select a product first")
            QTimer.singleShot(0, lambda: self.item.lineEdit().setFocus())
            return
        
        elif product_id is None:
            print("Entered product is not available... Please Add this product first")
            QMessageBox.information(self, 'Error', "Entered product is not available... Please Add this product first")
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
        discount_data = self.discount.text()
        tax_data = self.tax.text()
        total_data = self.amount_edit.text()
        
        if discount_data == '':
            discount_data = '0'
        
        if tax_data == '':
            tax_data = '0'    
        
        
        qty_edit = QLineEdit()
        qty_edit.setReadOnly(True)
        qty_edit.setText(qty_data)
        
        qty_edit.setStyleSheet("font-weight: 600;")
        
        
        
        
        
        
        
        rate_edit = QLineEdit()
        rate_edit.setReadOnly(True)
        rate_edit.setText(rate_data)
        rate_edit.setStyleSheet("font-weight: 600;")
        discount = QLineEdit()
        discount.setReadOnly(True)
        discount.setText(discount_data)
        
        tax = QLineEdit()
        tax.setReadOnly(True)
        tax.setText(tax_data)
        
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
        
        
        
        self.item.setCurrentIndex(-1)
        self.qty_edit.clear()
        self.rate_edit.clear()
        self.discount.clear()
        self.tax.clear()
        self.amount_edit.setText("0.00")
        
        
        
        self.item.setFocus()
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
        print("Widget shown — refreshing data")
        
        if not self.reloading_sale:
            
            self.populate_customers()




    def populate_customers(self):
    
        self.customer.clear()
        self.customer.addItem("Walk-in Customer", None)

        query = QSqlQuery()
        if query.exec("SELECT id, name FROM customer WHERE status = 'active' ORDER BY name ASC"):
            while query.next():
                customer_id = query.value(0)
                name = str(query.value(1)).strip()
                self.customer.addItem(name, customer_id)
        else:
            QMessageBox.information(self, "Error", query.lastError().text())
    
    
    
    
    
    
    
    
    
    
    
    def insert_customer_quick(self, name):
    
        name = name.strip()
        
        if not name:
            return None

        query = QSqlQuery()
        query.prepare("""
            INSERT INTO customer (name, contact, email, payable, receiveable, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        """)
        query.addBindValue(name)
        query.addBindValue("")       # contact
        query.addBindValue("")       # email
        query.addBindValue(0.0)      # payable
        query.addBindValue(0.0)      # receiveable

        if not query.exec():
            print("Insert customer failed:", query.lastError().text())
            return None

        return query.lastInsertId()
    
    
    

    def get_customer_id(self):
        
        customer = self.customer.currentData()
        return customer
        
        
        
    
    
    def get_salesman_id(self):
        
        username = QApplication.instance().property("username")
        query = QSqlQuery()
        query.prepare("SELECT id FROM auth WHERE username = ?;")
        query.addBindValue(username)
        if query.exec() and query.next():
            return query.value(0)
        else:
            QMessageBox.information(None, 'Error', query.lastError().text() )
            self.close()                # Close main window
            QApplication.quit()
            return None    
    
    
    
    
    def insert_salesreceipt(self):
    
        try:
            # --- Collect Data ---
            customer_id = self.get_customer_id()
            salesman = self.get_salesman_id()
                

            def to_float(value):
                
                value = str(value).strip()
                return float(value) if value else 0.0
            

            subtotal = to_float(self.gross_entry.text())
            discount = to_float(self.discount_entry.text())
            taxable = to_float(self.taxable_entry.text())
            tax = to_float(self.tax_entry.text())
            net_amount = to_float(self.net_amount_entry.text())
            additional_charges = to_float(self.additional_entry.text())
            total = to_float(self.net_amount_entry.text())
            received = to_float(self.received_entry.text())
            remaining = to_float(self.remainingdata.text())

            # --- Basic Validation ---
            if total < 0:
                QMessageBox.warning(self, "Validation Error", "Total cannot be negative.")
                return None

            if received < 0:
                QMessageBox.warning(self, "Validation Error", "Received amount cannot be negative.")
                return None

            session_id = get_current_session(self)
            
            if session_id is None:
                QMessageBox.warning(self, "Validation Error", "No active session found.")
                return None

            writeoff = payable = receiveable = 0.0

            if remaining > 0:
                if self.writeoff_check.isChecked():
                    writeoff = remaining
                else:
                    if customer_id is None:
                        QMessageBox.information(
                            self,
                            "Error",
                            "Walk-In Customer Can't Have Remaining Amount\nReceive Full amount or Write off"
                        )
                        return None
                    receiveable = remaining

            elif remaining < 0:
                payable = abs(remaining)

            if customer_id is None:
                payable = receiveable = 0.0

            print("Writeoff:", writeoff)
            print("Payable:", payable)
            print("Receiveables:", receiveable)

            query = QSqlQuery()
            query.prepare("""
                INSERT INTO sales
                (customer, salesman, subtotal, discount, taxable, tax,
                net_amount, additional_charges, total, received,
                remaining, writeoff, payable, receiveable, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)

    

            query.addBindValue(customer_id)
            query.addBindValue(salesman)
            query.addBindValue(subtotal)
            query.addBindValue(discount)
            query.addBindValue(taxable)
            query.addBindValue(tax)
            query.addBindValue(net_amount)
            query.addBindValue(additional_charges)
            query.addBindValue(total)
            query.addBindValue(received)
            query.addBindValue(remaining)
            query.addBindValue(writeoff)
            query.addBindValue(payable)
            query.addBindValue(receiveable)
            query.addBindValue(session_id)

            if not query.exec():
                QMessageBox.critical(self, "Database Error", query.lastError().text())
                return None

            sales_id = query.lastInsertId()
            print("Sales record inserted. ID:", sales_id)

            txn_inserted = self.insert_customer_transaction(
                sales_id, customer_id, total, received, remaining, salesman
            )
            if txn_inserted:
                print("Customer transaction inserted for Sales ID:", sales_id)
                

            return sales_id

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return None
        
    
    
    def insert_customer_transaction(self, sales_id, customer_id,
                                total_amount, received,
                                remaining, salesman_id):

        print("ABOUT TO INSERT CUSTOMER TRANSACTION NOW...")

        # default values for walk-in / no customer
        payable_before = 0.0
        receiveable_before = 0.0
        payable_now = 0.0
        receiveable_now = 0.0
        paid = 0.0
        remaining_due = 0.0
        remaining_now = 0.0
        payable_after = 0.0
        receiveable_after = 0.0

        # only fetch/update balances if customer exists
        if customer_id is not None:
            balance_query = QSqlQuery()
            balance_query.prepare("""
                SELECT payable, receiveable
                FROM customer
                WHERE id = ?
            """)
            balance_query.addBindValue(customer_id)

            if not balance_query.exec() or not balance_query.next():
                raise Exception("Failed to fetch customer balance.")

            payable_before = float(balance_query.value(0) or 0.0)
            receiveable_before = float(balance_query.value(1) or 0.0)

            if remaining > 0:
                receiveable_now = float(remaining)
                remaining_now = float(remaining)
            elif remaining < 0:
                payable_now = abs(float(remaining))
                remaining_due = abs(float(remaining))

            payable_after = payable_before + payable_now
            receiveable_after = receiveable_before + receiveable_now

        session_id = get_current_session(self)
        if session_id is None:
            QMessageBox.warning(self, "Validation Error", "No active session found.")
            return None

        payment = self.payment_handler.payment_data.copy()
        print(payment)
        print("Payment data is as above")

        note = (
            f"Sale ID {sales_id} recorded with total {total_amount}, "
            f"received {received}, remaining {remaining}"
        )

        insert_txn = QSqlQuery()
        insert_txn.prepare("""
            INSERT INTO customer_transaction
            (
                customer, transaction_type, ref, return_ref,
                payable_before, due_amount, paid, remaining_due, payable_after,
                receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                payment_method, bank_name, account_no, transaction_mode,
                wallet_provider, wallet_no, payment_reference,
                salesman, note, session_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        insert_txn.addBindValue(customer_id)   # None becomes NULL
        insert_txn.addBindValue("SALE")
        insert_txn.addBindValue(sales_id)
        insert_txn.addBindValue(None)

        insert_txn.addBindValue(payable_before)
        insert_txn.addBindValue(float(total_amount or 0.0))
        insert_txn.addBindValue(paid)
        insert_txn.addBindValue(remaining_due)
        insert_txn.addBindValue(payable_after)

        insert_txn.addBindValue(receiveable_before)
        insert_txn.addBindValue(receiveable_now)
        insert_txn.addBindValue(float(received or 0.0))
        insert_txn.addBindValue(remaining_now)
        insert_txn.addBindValue(receiveable_after)

        insert_txn.addBindValue(payment.get("payment_method") or None)
        insert_txn.addBindValue(payment.get("bank_name") or None)
        insert_txn.addBindValue(payment.get("account_no") or None)
        insert_txn.addBindValue(payment.get("transaction_mode") or None)
        insert_txn.addBindValue(payment.get("wallet_provider") or None)
        insert_txn.addBindValue(payment.get("wallet_no") or None)
        insert_txn.addBindValue(payment.get("payment_reference") or None)

        insert_txn.addBindValue(salesman_id)
        insert_txn.addBindValue(note)
        insert_txn.addBindValue(session_id)

        if not insert_txn.exec():
            raise Exception(insert_txn.lastError().text())

        print("Transaction Stored with ID:", insert_txn.lastInsertId())

        # only update customer running balance if linked customer exists
        if customer_id is not None:
            update_customer = QSqlQuery()
            update_customer.prepare("""
                UPDATE customer
                SET payable = ?, receiveable = ?
                WHERE id = ?
            """)
            update_customer.addBindValue(payable_after)
            update_customer.addBindValue(receiveable_after)
            update_customer.addBindValue(customer_id)

            if not update_customer.exec():
                raise Exception(update_customer.lastError().text())

        return True
    
        
    
        
        
    def thermal_receipt_printer(self, sales_id):
        
        # get business
        business_query = QSqlQuery()
        business_query.prepare("""
                                SELECT businessname, address, contact from business where id = ? ;
                               """)
        business_query.addBindValue(1)
        
        
        if business_query.exec() and business_query.next():

            businessname = business_query.value(0)
            address = business_query.value(1)
            contact = business_query.value(2)
            
            business = {
                "name": businessname,
                "address": address,
                "contact": contact
            }
            
            
        
        else:
            
            print("Error Fetching Business ", business_query.lastError().text())
        
        
      
        
    
    
    def insert_salesitems(self, sales_id):
    
        print("About to INSERT sales items with FIFO allocation for sales ID:", sales_id)

        def text_from_widget(widget, field_name, row):
            if widget is None:
                raise Exception(f"Row {row + 1}: {field_name} widget is missing.")
            text = widget.text().strip()
            return text

        def to_int(text, field_name, row):
            try:
                return int(text)
            except (TypeError, ValueError):
                raise Exception(f"Row {row + 1}: Invalid {field_name}.")

        def to_float(text, field_name, row, default=0.0):
            if text == "":
                return default
            try:
                return float(text)
            except (TypeError, ValueError):
                raise Exception(f"Row {row + 1}: Invalid {field_name}.")

        def get_total_available_stock(product_id):
            query = QSqlQuery()
            query.prepare("""
                SELECT COALESCE(SUM(quantity_remaining), 0)
                FROM batch
                WHERE product_id = ?
            """)
            query.addBindValue(product_id)

            if not query.exec() or not query.next():
                raise Exception(f"Stock check failed for product ID {product_id}.")

            return int(query.value(0) or 0)


        def insert_sales_item_record(
            sales_id, product_id, qty, rate, discount, tax,
            line_total, line_weight, effective_line_total
        ):
            query = QSqlQuery()
            query.prepare("""
                INSERT INTO salesitem
                (sales_id, product_id, qty_sold, unit_price,
                discount, tax, line_total, line_weight, effective_line_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
            query.addBindValue(sales_id)
            query.addBindValue(product_id)
            query.addBindValue(qty)
            query.addBindValue(rate)
            query.addBindValue(discount)
            query.addBindValue(tax)
            query.addBindValue(line_total)
            query.addBindValue(line_weight)
            query.addBindValue(effective_line_total)

            if not query.exec():
                raise Exception(f"Failed to insert sales item: {query.lastError().text()}")

            return query.lastInsertId()

        def allocate_fifo_batches(product_id, sale_item_id, qty_needed):
            remaining_qty = qty_needed

            batch_query = QSqlQuery()
            batch_query.prepare("""
                SELECT id, quantity_remaining, unit_cost
                FROM batch
                WHERE product_id = ?
                AND quantity_remaining > 0
                ORDER BY received_at ASC, id ASC
            """)
            batch_query.addBindValue(product_id)

            if not batch_query.exec():
                raise Exception(f"Failed to fetch FIFO batches: {batch_query.lastError().text()}")

            while batch_query.next() and remaining_qty > 0:
                batch_id = int(batch_query.value(0))
                available = int(batch_query.value(1) or 0)

                raw_cost = batch_query.value(2)
                unit_cost = float(raw_cost) if raw_cost is not None else None

                if available <= 0:
                    continue

                take_qty = min(available, remaining_qty)
                line_cost = round(take_qty * unit_cost, 2) if unit_cost is not None else None

                print(
                    "Batch Data:",
                    "Batch ID:", batch_id,
                    "Available:", available,
                    "Unit Cost:", unit_cost,
                    "Taking Qty:", take_qty,
                    "Line Cost:", line_cost
                )

                update_batch = QSqlQuery()
                update_batch.prepare("""
                    UPDATE batch
                    SET quantity_remaining = quantity_remaining - ?
                    WHERE id = ?
                """)
                update_batch.addBindValue(take_qty)
                update_batch.addBindValue(batch_id)

                if not update_batch.exec():
                    raise Exception(f"Failed to update batch {batch_id}: {update_batch.lastError().text()}")

                insert_sold = QSqlQuery()
                insert_sold.prepare("""
                    INSERT INTO sold_batch
                    (sale_item_id, batch_id, qty_taken, unit_cost, line_cost)
                    VALUES (?, ?, ?, ?, ?)
                """)
                insert_sold.addBindValue(sale_item_id)
                insert_sold.addBindValue(batch_id)
                insert_sold.addBindValue(take_qty)
                insert_sold.addBindValue(unit_cost)
                insert_sold.addBindValue(line_cost)

                if not insert_sold.exec():
                    raise Exception(f"Failed to insert sold batch: {insert_sold.lastError().text()}")

                remaining_qty -= take_qty

            if remaining_qty > 0:
                raise Exception(f"FIFO allocation failed for product ID {product_id}. Unallocated qty: {remaining_qty}")

        def get_header_values():
            def safe_text(line_edit):
                return line_edit.text().strip() if line_edit else ""

            subtotal = to_float(safe_text(self.gross_entry), "subtotal", 0, default=0.0)
            header_discount = to_float(safe_text(self.discount_entry), "header discount", 0, default=0.0)
            header_tax = to_float(safe_text(self.tax_entry), "header tax", 0, default=0.0)
            additional_charges = to_float(safe_text(self.additional_entry), "additional charges", 0, default=0.0)

            return subtotal, header_discount, header_tax, additional_charges

        subtotal, header_discount, header_tax, additional_charges = get_header_values()
        
        
        # check for empty table
        row_count = self.table.rowCount()
        if row_count <= 0:
            QMessageBox
            raise Exception(f"No Items in Table")
            
        

        for row in range(self.table.rowCount()):

            product_widget = self.table.cellWidget(row, 1)
            if product_widget is None:
                continue

            product_data = product_widget.currentData()
            if not isinstance(product_data, dict):
                continue

            product_id = product_data.get("product_id")
            if not product_id:
                continue

            product_id = int(product_id)
            print(f"Processing row {row} with Product ID: {product_id}")

            qty_widget = self.table.cellWidget(row, 2)
            rate_widget = self.table.cellWidget(row, 3)
            discount_widget = self.table.cellWidget(row, 4)
            tax_widget = self.table.cellWidget(row, 5)
            total_widget = self.table.cellWidget(row, 6)

            qty = to_int(text_from_widget(qty_widget, "quantity", row), "quantity", row)
            rate = to_float(text_from_widget(rate_widget, "rate", row), "rate", row)
            discount = to_float(text_from_widget(discount_widget, "discount", row), "discount", row)
            tax = to_float(text_from_widget(tax_widget, "tax", row), "tax", row)
            line_total = to_float(text_from_widget(total_widget, "line total", row), "line total", row)

            if qty <= 0:
                raise Exception(f"Row {row + 1}: Quantity must be greater than zero.")

            if rate < 0:
                raise Exception(f"Row {row + 1}: Rate cannot be negative.")

            if discount < 0:
                raise Exception(f"Row {row + 1}: Discount cannot be negative.")

            if tax < 0:
                raise Exception(f"Row {row + 1}: Tax cannot be negative.")

            if line_total < 0:
                raise Exception(f"Row {row + 1}: Line total cannot be negative.")

            line_weight = (line_total / subtotal) if subtotal > 0 else 0.0
            line_header_discount = header_discount * line_weight
            line_header_tax = header_tax * line_weight
            line_additional_charges = additional_charges * line_weight

            effective_line_total = line_total - line_header_discount + line_header_tax + line_additional_charges
            effective_line_total = round(effective_line_total, 2)

            print(
                "Line Weight:", line_weight,
                "Line Header Discount:", line_header_discount,
                "Line Header Tax:", line_header_tax,
                "Line Additional Charges:", line_additional_charges
            )

            print(
                "Validated Row Data:",
                "Product ID:", product_id,
                "Qty:", qty,
                "Rate:", rate,
                "Discount:", discount,
                "Tax:", tax,
                "Line Total:", line_total,
                "Effective Line Total:", effective_line_total
            )

            total_available = get_total_available_stock(product_id)
            print("Available Stock is:", total_available)

            if qty > total_available:
                raise Exception(f"Row {row + 1}: Insufficient stock for product ID {product_id}.")

            sale_item_id = insert_sales_item_record(
                sales_id=sales_id,
                product_id=product_id,
                qty=qty,
                rate=rate,
                discount=discount,
                tax=tax,
                line_total=line_total,
                line_weight=line_weight,
                effective_line_total=effective_line_total
            )

            print("Sales Item ID is:", sale_item_id)

            allocate_fifo_batches(
                product_id=product_id,
                sale_item_id=sale_item_id,
                qty_needed=qty
            )

        return True
    
    
    
    def put_sale_on_hold(self):
        
        db = QSqlDatabase().database()
        db.transaction()
        
        try:
        
            print("Putting Sale on Hold")

            # get salesorder data
            customer = self.customer.currentData()
            status = 'On Hold'
            
            print("Customer is: ", customer)
            
            if customer == 0:
                customer = None

            # inserting sales into holdsales table
            
            hold_query = QSqlQuery()
            hold_query.prepare("""
                INSERT INTO holdsale (customer, salesman, status)
                VALUES (?, ?, ?)
            """)

            hold_query.addBindValue(customer)
            hold_query.addBindValue(salesman)
            hold_query.addBindValue(status)
            
            if hold_query.exec():

                print("Sales on Hold Running...")
                hold_id = hold_query.lastInsertId()
                print("Sales ID is: ", hold_id)
                
                
                # save hold items
                self.hold_sales_items(hold_id)
                
                
            else:
                print("Error inserting sales on hold:", hold_query.lastError().text())
                QMessageBox.critical(self, "Error", hold_query.lastError().text())
                raise Exception

        
        
        except Exception:
            
            print("rolling back transactions")
            db.rollback()
            QMessageBox.information(self, "Error", "Database error - rolling back Transactions")
            
        else:
            
            db.commit()
            print("Transaction committed successfully")
            self.clear_fields()
            QMessageBox.information(None, "Success", "Sales Hold saved successfully")
        
        
        
        
        
    def hold_sales_items(self, hold_id):
        
        print("Putting Sales Items on Hold")
        
          
            
        items_exits = False
        # Process each row in the sales items table
        for row in range(self.table.rowCount()):
            
            print("Row number is:", row)
            
            product_widget = self.table.cellWidget(row, 1)
            if not product_widget or not product_widget.currentData():
                print("Row is empty ... ignoring it...")
                continue

            product_id = product_widget.currentData()
            product_id = int(product_id)
            items_exits = True
            
            hold_id = int(hold_id)
            
            print("Current Data is: ", product_id)
            
            qty = int(self.table.cellWidget(row, 3).text())
            rate = float(self.table.cellWidget(row, 4).text())
            discount = float(self.table.cellWidget(row, 5).text())
            discountamount = float(self.table.cellWidget(row, 6).text())
            total = float(self.table.cellWidget(row, 7).text())
            
            
            print("we have reached here...")
        
            # Insert sales item
            item_query = QSqlQuery()
            item_query.prepare("""
                INSERT INTO holditems (holdsale, product, qty, unitrate, discount, discountamount, total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """)

            item_query.addBindValue(hold_id)
            item_query.addBindValue(product_id)
            item_query.addBindValue(qty)
            item_query.addBindValue(rate)
            item_query.addBindValue(discount)
            item_query.addBindValue(discountamount)
            item_query.addBindValue(total)
            
            if not item_query.exec():
                
                print("Error inserting Hold Item:", item_query.lastError().text())
                raise Exception(f"Failed to insert Hold item for product_id {product_id}: {item_query.lastError().text()}")

                
            else:
                
                print("Item saved ")
                print("Hold Item ID is: ", item_query.lastInsertId())
                
        if not items_exits:
            print("No Records in the Order")
            raise Exception
    
    
    
    
    
    def load_hold_items(self):
        
        pass
        
        
        
        
        
        
    
    #  Saving Sales Receipt
    def save_receipt(self):
        
        db = QSqlDatabase.database()
        db.transaction()
        
        try: 
        
            # Insert Sales Receipt
            sales_id = self.insert_salesreceipt()
            
            if sales_id is None:
                
                raise Exception
            # Insert Sales Items
            self.insert_salesitems(sales_id)
            
        
        except Exception:
            
            print("rolling back transactions")
            db.rollback()
            QMessageBox.information(self, "Error", "Database error - rolling back Transactions")
            
        else:
            
            db.commit()
            print("Transaction committed successfully")
            self.clear_fields()
            QMessageBox.information(None, "Success", "Sales Record saved successfully")
        
        
        
        
    def get_product_via_code(self, code):
        
        # --- Step 1: Validate input ---
        if not str(code).isdigit():
            print("Invalid or empty code.")
            return None

        code = int(code)
        print(f"Getting product via code: {code}")

        # --- Step 2: Query product info ---
        query = QSqlQuery()
        query.prepare("""
            SELECT id, name, form, strength 
            FROM product 
            WHERE code = ? 
            LIMIT 1
        """)
        query.addBindValue(code)

        if not query.exec():
            print("Product query failed:", query.lastError().text())
            return None


        if not query.next():
            print("No product found with code:", code)
            row = self.table.currentRow()
            combo = self.table.cellWidget(row, 1)
            print("Clearing the combo box...")
            combo.clear()
            
            combo.lineEdit().setText('')
            combo
            return None

        # --- Step 3: Extract product details ---
        product_id = int(query.value(0))
        name = query.value(1)
        form = query.value(2) or ""
        strength = query.value(3) or ""
        label = f"{name} {strength} {form}".strip()

        print(f"Product found: {label} (ID: {product_id})")

        row = self.table.currentRow()
        combo = self.table.cellWidget(row, 1)
        if not combo:
            print("Combo not found at row:", row)
            return None

        # --- Step 4: Query stock info ---
        stock_query = QSqlQuery()
        stock_query.prepare("""
            SELECT packsize, units, saleprice 
            FROM stock 
            WHERE product = ? 
            LIMIT 1
        """)
        stock_query.addBindValue(product_id)

        if not stock_query.exec():
            print("Stock query failed:", stock_query.lastError().text())
            return None

        if not stock_query.next():
            print("Stock record missing for product:", product_id)
            QMessageBox.warning(self, "Stock Error", f"No stock found for {label}")
            return None

        # --- Step 5: Extract and fill stock data ---
        packsize = int(stock_query.value(0))
        units = int(stock_query.value(1))
        saleprice = float(stock_query.value(2))
        unit_sale_price = saleprice / packsize if packsize > 0 else 0.0

        print(f"Stock info: packsize={packsize}, units={units}, saleprice={saleprice}")

        self.table.cellWidget(row, 2).setText(str(units))
        self.table.cellWidget(row, 4).setText(f"{unit_sale_price:.2f}")
        
        

        return product_id, label

    
    
    
    def _run_pending_scan(self):
        
        if not self._pending_scan:
            return
        
        code, combo = self._pending_scan
        self._pending_scan = None

        # call your lookup (make sure it returns (product_id, label) on success)
        res = self.get_product_via_code(code)
        
        if not res:
            
            return

        product_id, label = res
        
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(label, product_id)
        combo.setCurrentIndex(0)
        
        if combo.isEditable():
            combo.lineEdit().setText(label)
            
        combo.blockSignals(False)


    
        
    
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
            SELECT p.id, p.display_name, pp.unit_price
            FROM product p
            LEFT JOIN price_pack pp ON pp.product_id = p.id
            WHERE p.display_name LIKE ?
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
            unit_price = query.value(2) or 0.0

            products.append(name)
            product_data.append((name, {
                "product_id": product_id,
                "unit_price": unit_price
            }))

        item.blockSignals(True)
        item.clear()

        for name, data in product_data:
            item.addItem(name, data)

        item.setCurrentIndex(-1)
        item.lineEdit().setText(current_text)
        item.blockSignals(False)

        completer.setModel(QStringListModel(products))
        completer.complete()
     
    
    
        
    def on_completer_selected(self, text, combo):
        
        index = combo.findText(text.strip(), Qt.MatchExactly)

        if index == -1:
            combo.setCurrentIndex(-1)
            return None

        combo.setCurrentIndex(index)
        data = combo.currentData()

        if not isinstance(data, dict):
            return None

        product_id = data.get("product_id")
        unit_price = data.get("unit_price", 0)

        try:
            self.rate_edit.setText(f"{float(unit_price):.2f}")
        except (TypeError, ValueError):
            self.rate_edit.clear()

        self.qty_edit.setFocus()
        self.qty_edit.selectAll()
        
        
        # empty completer
        combo.completer().setModel(QStringListModel([]))

        return product_id
            
            




    def update_total_amount(self):
        
        
        subtotal = 0.00
        for row in range(self.table.rowCount()):
            
            linetotal = self.table.cellWidget(row, 6).text()
            
            if linetotal:
                try:
                   
                    value = float(linetotal)
                    subtotal = subtotal + value
                    
                except ValueError:
                    pass  
                
            else:
                continue
                
        self.gross_entry.setText(f"{subtotal:.2f}")
        discount = self.discount_entry.text()
        discount = float(discount) if discount else 0.00
        
        taxable = subtotal - discount
        self.taxable_entry.setText(f"{taxable:.2f}")
        
        tax = self.tax_entry.text()
        tax = float(tax) if tax else 0.00
        
        net_amount = taxable + tax
        
        self.net_amount_entry.setText(f"{net_amount:.2f}")
        
        additional_charges = self.additional_entry.text()
        additional_charges = float(additional_charges) if additional_charges else 0.00
        
        final_amount = net_amount + additional_charges
        self.final_amount_entry.setText(f"{final_amount:.2f}")
        
        self.final_amount_entry.setStyleSheet("font-weight: bold;")
        
        self.main_final_amount.setText(f"{final_amount:.2f}")
        
    

    
    
    def reload_hold_order(self, id):
        
        print("Reloading Hold Data")
        
        self.reloading_sale = True

        hold_id = int(id)
        
        self.customer.clear()
        self.salesman.clear()
        
        # get customer and salesman from hold order
        query = QSqlQuery()
        query.prepare("""
            SELECT customer, salesman FROM holdsale WHERE id = ? """)
        query.addBindValue(hold_id)
        
        print("About to run query")
        if query.exec() and query.next():

            customer_id = query.value(0)
            salesman_id = query.value(1)

            print("Customer_id is:", customer_id, ' Salesman_id is: ', salesman_id)

            # get customer name 
            if customer_id != 0:
    
                customer_id = int(customer_id)
                # get the customer data
                customer_query = QSqlQuery()
                customer_query.prepare("""
                    SELECT name FROM customer WHERE id = ? """)
                
                customer_query.addBindValue(customer_id)
                
                if customer_query.exec() and customer_query.next():

                    customer = customer_query.value(0)
                    self.customer.addItem(customer, customer_id)
                    
                    customer_query = QSqlQuery()
                    customer_query.prepare(""" SELECT id, name FROM customer """)
                    existing_id = customer_id
                    if customer_query.exec():
                        
                        while customer_query.next():

                            
                            customer_id = customer_query.value(0)
                            customer_name = customer_query.value(1)
                            
                            if customer_id == existing_id:
                                continue
                            
                            self.customer.addItem(customer_name, customer_id)
                
                else:
                    print("Error getting customer")
                    print(customer_query.lastError().text())
                
            else:
                
                customer = 'Walk-In Customer'
                customer_query = None
                
                self.customer.addItem(customer, customer_id)
                
                customer_query = QSqlQuery()
                customer_query.prepare(""" SELECT id, name FROM customer """)
                existing_id = customer_id
                if customer_query.exec():
                    
                    while customer_query.next():

                        
                        customer_id = customer_query.value(0)
                        customer_name = customer_query.value(1)
                        
                        self.customer.addItem(customer_name, customer_id)
                
                
                else:
                    print("Error getting customer")
                    print(customer_query.lastError().text())
                
            
            # get salesman name
            if salesman_id is not None:

                salesman_id = int(salesman_id)
                # get the salesman data
                salesman_query = QSqlQuery()
                salesman_query.prepare("""
                    SELECT name FROM employee WHERE id = ? """)

                salesman_query.addBindValue(salesman_id)

                if salesman_query.exec() and salesman_query.next():

                    salesman = salesman_query.value(0)
                    self.salesman.addItem(salesman, salesman_id)
                    
                    salesman_query = QSqlQuery()
                    salesman_query.prepare(""" SELECT id, name FROM employee """)
                    
                    existing_id = salesman_id
                    
                    if salesman_query.exec():

                        while salesman_query.next():

                            salesman_id = salesman_query.value(0)
                            salesman_name = salesman_query.value(1)

                            if salesman_id == existing_id:
                                continue

                            self.salesman.addItem(salesman_name, salesman_id)
                    
                    

                else:
                    print("Error getting salesman")
                    print(salesman_query.lastError().text())



            print("Customer is: ", customer, ' Salesman is: ', salesman)
            
            
        else:
            print("Error getting customer and supplier")
            print(query.lastError().text())


        
        # insert holditems data
        print("Inserting holditems data")
        items_query = QSqlQuery()
        items_query.prepare(""" SELECT product, qty, unitrate, discount, discountamount, total FROM holditems WHERE holdsale = ?""")
        items_query.addBindValue(hold_id)
        
        if items_query.exec():
            
            print("got the data now geting records to insert items")
            self.table.setRowCount(0)
           
            while items_query.next():
                
                print("Adding new Row for record")
                self.add_row()
                new_row = self.table.rowCount() - 1

                print("Getting Data after adding rows")
                product = int(items_query.value(0))
                quantity = str(items_query.value(1))
                rate = str(items_query.value(2))
                discount = str(items_query.value(3))
                discountamount = str(items_query.value(4))
                total = str(items_query.value(5))
                
                print("Got the data now getting MEDICINE INFO")

                query2 = QSqlQuery()
                query2.prepare("SELECT id, name, form, strength FROM product WHERE id = ?")
                query2.addBindValue(product)
                
                if query2.exec() and query2.next():
                    
                    product_id = query2.value(0)
                    name = query2.value(1)
                    form = query2.value(2)
                    strength = query2.value(3)
                    
                    label = f"{name} {strength} {form}".strip()
                    print("insertint lable and id into combobox")
                    
                    combo = self.table.cellWidget(new_row, 1)
                    combo.addItem(label, product_id)
                    combo.setCurrentIndex(combo.findData(product_id))  # ✅ Select it!




                stock_query = QSqlQuery()
                stock_query.prepare("SELECT packsize, units FROM stock WHERE product = ?")
                stock_query.addBindValue(product_id)
                    
                if stock_query.exec() and stock_query.next():  
                        
                    packsize = stock_query.value(0)
                    units = stock_query.value(1)
                    
                    rate = str(rate)
                    
                    self.table.cellWidget(new_row, 2).setText(str(units))
                    self.table.cellWidget(new_row, 3).setText(str(quantity))
                    self.table.cellWidget(new_row, 4).setText(rate)
                    self.table.cellWidget(new_row, 5).setText(discount)
                    self.table.cellWidget(new_row, 6).setText(discountamount)
                    self.table.cellWidget(new_row, 7).setText(total)

        

            # Deleting Hold Items after reloading
            item_delete = QSqlQuery()
            item_delete.prepare("DELETE FROM holditems WHERE holdsale = ?") 
            item_delete.addBindValue(hold_id)
            
            
            if item_delete.exec():
                
                print("Hold Items Deleted")
                
                # Deleting Hold Order Ref
                query = QSqlQuery()
                query.prepare("DELETE FROM holdsale WHERE id = ?")
                query.addBindValue(hold_id)
                
                if query.exec():
                    print("Hold Order Deleted")
                    
                    
                else:
                    print("Error deleting hold order")
                    print(query.lastError().text())
                
                
            else:
                
                print("Error deleting hold items")
                print(item_delete.lastError().text())
                
                
            
        
            
        else:
            print("Error getting hold items")
            print(items_query.lastError().text())
        
        
    



    def force_uppercase(self, text):
        line_edit = self.item.lineEdit()
        line_edit.blockSignals(True)
        line_edit.setText(text.upper())
        line_edit.blockSignals(False)
    
    

    
    
    def clear_fields(self):
        
        self.order_modified = False
        self.reloading_sale = False
        
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
        
        self.payment_method.blockSignals(True); 
        self.payment_method.setCurrentText("Cash"); 
        self.payment_method.blockSignals(False)
        
        
        self.writeoff_check.setChecked(True)        
        
        self.table.setRowCount(0)
        
        self.populate_customers()
        
        # set focus back to combobox
        self.item.setCurrentIndex(-1)
        self.item.setFocus()
        
        


    def export_pdf(self, filename="salesinvoice.pdf", sales_id=None):
        
        print("Exporting PDF")
        
        print("Sales id is: ", sales_id)
        
        
        query = QSqlQuery()
        query.prepare("""
            SELECT product, qty, unitrate, discount, discountamount, total
            FROM salesitem 
            WHERE sales = ?
        """)
        query.addBindValue(sales_id)
        
        items = []
        
        if query.exec():
            
            print("Query has been executed successfully")
            
            while query.next():
                
                product_id = int(query.value(0))
                qty = str(query.value(1))
                rate = str(query.value(2))
                discount = str(query.value(3))
                discount_amount = str(query.value(4))
                price = float(rate) - float(discount_amount)
                total = str(query.value(5))

                # Get product name
                product_name = ""
                query2 = QSqlQuery()
                query2.prepare("SELECT name FROM product WHERE id = ?")
                query2.addBindValue(product_id)

                if query2.exec() and query2.next():
                    product_name = query2.value(0)
                    
                items.append((product_name, qty, rate, discount, price, total))
                print(items)



        else:
            print("Query failed:", query.lastError().text())

        
    
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

        business_name = "Muzammil Medical & General Store"
        painter.drawText(x, y, business_name)

        y += 80
        
        address_font = QFont("Arial", 12)
        painter.setFont(address_font)
        
        address = "123 Health St, Wellness City"
        painter.drawText(x, y, address)
        
        y += 70
        contact = "Phone: (123) 456-7890"
        painter.drawText(x, y, contact)
        
        
        invoice_font = QFont("Arial", 36, QFont.Bold)
        painter.setFont(invoice_font)

        invoice_title = "Invoice"
        painter.drawText(1700, 230, invoice_title)
        
        invoice_no_font = QFont("Arial", 12)
        painter.setFont(invoice_no_font)
        
        rect = QRectF(1700, 250, 500, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        invoice_no = "# 12345"
        painter.drawText(rect, invoice_no, option)
        
        
        invoice_date_font = QFont("Arial", 12)
        painter.setFont(invoice_date_font)

        rect = QRectF(1700, 320, 500, 100)
        
        option = QTextOption()
        option.setAlignment(Qt.AlignRight)

        invoice_no = "21 October, 2025"
        painter.drawText(rect, invoice_no, option)

        y += 150
        
        customer_font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(customer_font)
        info = " Asad Clinic & Pharmacy"
        customer = f"To : {info}"
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
        total = 0
        
        print("Drawing Items into Table")
        
        for item, qty, price, discount, net_price, item_total in items:

            painter.drawText(x + 20, y, item)
            painter.drawText(x + 900, y, str(qty))
            painter.drawText(x + 1100, y, f"{price:.2f}")
            painter.drawText(x + 1400, y, f"{discount:.2f} %")
            painter.drawText(x + 1650, y, f"{net_price:.2f}")
            painter.drawText(x + 1900, y, f"{item_total:.2f}")
            
            total += item_total
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

        painter.drawText(rect, f"{total}", option)
        
        
        
        y += 100
        painter.drawText(x + 1600, y, f"Discount: ")
        painter.drawText(x + 1900, y, f"0.00")
        
        y += 80

        painter.drawText(x + 1600, y, f"Sales Tax: ")
        painter.drawText(x + 1900, y, f"0.00")
        
        y += 80
        pen = QPen(QColor("black"))
        pen.setWidth(5)  # line thickness
        painter.setPen(pen)
        painter.drawLine(x + 1500, y, pdf.width() - 200, y) 
        
        y += 80
        total_font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(total_font)
        painter.drawText(x + 1500, y, f"Total Amount: ")
        painter.drawText(x + 1950, y, f"{total:.2f}")

        painter.end()
        return filename
    


    def print_pdf(self, filename):
        
        system = platform.system()
        if system in ("Linux", "Darwin"):
            os.system(f"lp '{filename}'")
        elif system == "Windows":
            os.startfile(filename, "print")
            
    
    
    def clear_product_field(self):
        
        self.item.blockSignals(True)

        self.item.setCurrentIndex(-1)
        self.item.lineEdit().clear()

        if self.item.completer():
            self.item.completer().popup().hide()

        self.item.blockSignals(False)

    
    
    
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
            
    
   
   
   
from PySide6.QtCore import QObject, QEvent, QTimer
from PySide6.QtWidgets import QMessageBox
from PySide6.QtSql import QSqlQuery


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
            QMessageBox.warning(
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
        
        print(f"product Id isL {product_id}")
        available_qty = self.get_available_qty(product_id)
        
        print(f"Available Qty is: {available_qty}")

        if entered_qty > available_qty:
            QMessageBox.warning(
                self.parent_page,
                "Insufficient Stock",
                f"Entered quantity ( {entered_qty} ) is greater than available stock ( {available_qty} )."
            )
            self.qty_edit.clear()
            QTimer.singleShot(0, self.qty_edit.setFocus)

    def get_available_qty(self, product_id):
        query = QSqlQuery()
        query.prepare("""
            SELECT COALESCE(SUM(quantity_remaining), 0)
            FROM batch
            WHERE product_id = ?
        """)
        query.addBindValue(product_id)

        if query.exec() and query.next():
            return int(query.value(0) or 0)

        return 0
    
    
    
    
   
   