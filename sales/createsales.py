from PySide6.QtWidgets import QApplication, QWidget, QDateEdit, QVBoxLayout, QHBoxLayout, QDialog, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QDate, Signal, QTimer, QEvent, QRectF, QSizeF
from utilities.product_search_widget import ProductSearchBox
import os
import sys
import platform
import subprocess

from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent, QPdfWriter, QKeySequence, QPainter, QPageSize, QFont, QTextOption, QPen, QColor
from functools import partial
import math
from utilities.stylus import load_stylesheets
from utilities.session_gate import require_open_session
from utilities.session_service import get_active_session_id
from PySide6.QtGui import QKeySequence, QShortcut

from utilities.payment_handler import PaymentMethodHandler
from utilities.permissions import Permissions
from utilities.app_messagebox import AppMessageBox
from sales.pricing_logic import compute_header_totals, compute_line_pricing
from services.accounting_settings_service import load_sales_policy_settings
from services.sales_defaults_service import resolve_sales_header_pricing
from services.sales_posting_service import (
    build_customer_transaction_note,
    build_sales_header_payload,
    compute_customer_transaction_balances,
    compute_due_date_from_option,
    resolve_sales_settlement,
)
from services.sales_items_service import (
    compute_fifo_allocation_plan,
    normalize_sales_item_row,
)
from services.sales_transaction_service import (
    build_customer_transaction_payload,
    decrement_batch_quantity,
    fetch_customer_balances,
    fetch_fifo_batch_rows,
    fetch_total_available_stock,
    insert_customer_transaction_record,
    insert_sales_header,
    insert_sales_item_record as persist_sales_item_record,
    insert_sold_batch_record,
    update_customer_running_balance,
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
        customer_layout.setContentsMargins(12, 8, 12, 8)
        customer_layout.setSpacing(4)

        # Top Row Layout
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

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

        customer_meta_row = QHBoxLayout()
        customer_meta_row.setContentsMargins(0, 0, 0, 0)
        customer_meta_row.setSpacing(18)

        self.customer_credit_summary = QLabel()
        self.customer_credit_summary.setWordWrap(False)
        self.customer_credit_summary.setStyleSheet(
            "color: #546776; font-size: 10px; font-weight: 600; padding-left: 0; margin: 0;"
        )
        self.customer_credit_summary.setContentsMargins(0, 0, 0, 0)
        customer_meta_row.addWidget(self.customer_credit_summary)

        self.customer_pricing_summary = QLabel()
        self.customer_pricing_summary.setWordWrap(False)
        self.customer_pricing_summary.setStyleSheet(
            "color: #6B7F8F; font-size: 10px; font-weight: 600; padding-left: 0; margin: 0;"
        )
        self.customer_pricing_summary.setContentsMargins(0, 0, 0, 0)
        customer_meta_row.addWidget(self.customer_pricing_summary, 1)
        customer_meta_row.addStretch()
        customer_layout.addLayout(customer_meta_row)

        promo_status_row = QHBoxLayout()
        promo_status_row.setContentsMargins(0, 0, 0, 0)
        promo_status_row.setSpacing(10)

        self.global_pricing_status = QLabel()
        self.global_pricing_status.setWordWrap(False)
        self.global_pricing_status.setStyleSheet(
            "color: #3F5F75; font-size: 10px; font-weight: 700; padding-left: 0; margin: 0;"
        )
        self.global_pricing_status.setContentsMargins(0, 0, 0, 0)
        promo_status_row.addWidget(self.global_pricing_status)
        promo_status_row.addStretch()
        customer_layout.addLayout(promo_status_row)

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
                AppMessageBox.critical(
                    dialog,
                    "Database Error",
                    f"Failed to save customer:\n{query.lastError().text()}"
                )
                return

            AppMessageBox.information(dialog, "Success", "Customer added successfully.")
            dialog.accept()

            if hasattr(self, "populate_customers"):
                self.populate_customers()


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
        self.table.setMinimumWidth(900)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        visible_rows = 6
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
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 12px;
                letter-spacing: 0.2px;
                background-color: #fbfcfd;
            }

            QComboBox {
                margin: 0;
                padding: 5px 10px;
                padding-right: 30px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 12px;
                letter-spacing: 0.2px;
                background-color: #fbfcfd;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
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
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 12px;
                letter-spacing: 0.2px;
                background-color: #fbfcfd;
            }
        """

        
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(2)
        grid.setContentsMargins(6, 4, 6, 2)
        self.entry_grid = grid

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
        
        grid.addLayout(info_box_layout, 0 , 0)

        
        product_box_layout = QHBoxLayout()
        
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

        self.discount_mode_combo = QComboBox()
        self.discount_mode_combo.addItem("%", "percent")
        self.discount_mode_combo.addItem("Amt", "amount")
        self.discount_mode_combo.setStyleSheet(field_style)
        self.discount_mode_combo.setFixedWidth(62)

        discount_box_layout.addWidget(discount_label)
        discount_box_layout.addWidget(self.discount)
        discount_box_layout.addWidget(self.discount_mode_combo)

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
        self.add_line_button = add_button

        self.reset_line_defaults_btn = QPushButton("Reset", objectName="EntryButton")
        self.reset_line_defaults_btn.clicked.connect(self.reset_current_line_defaults)

        action_box_layout = QHBoxLayout()
        action_box_layout.setContentsMargins(6, 6, 6, 6)
        action_box_layout.setSpacing(6)
        action_box_layout.addWidget(add_button)
        action_box_layout.addWidget(self.reset_line_defaults_btn)

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
        self.refresh_pricing_details_dialog()
    
    
    
    
    def add_totals_section(self):
    
        totals_frame = QFrame()
        totals_frame.setObjectName("sectionCard")
        self.totals_frame = totals_frame

        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setContentsMargins(8, 8, 8, 8)
        totals_layout.setSpacing(6)

        main_grid = QGridLayout()
        main_grid.setHorizontalSpacing(18)
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
        gross_label = QLabel("Sub Total")
        discount_label = QLabel("Header Discount")
        tax_label = QLabel("Header Tax")
        additional_label = QLabel("Additional Charges")
        taxable_label = QLabel("Taxable")
        net_amount_label = QLabel("Net Amount")
        line_discount_label = QLabel("Line Discount Total")
        line_tax_label = QLabel("Line Tax Total")

        final_amount_label = QLabel("Final Amount")
        final_amount_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        final_amount_label.setStyleSheet("font-size: 14px; font-weight:600; color: #666;")

        received_label = QLabel("Received")
        received_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        received_label.setStyleSheet("font-size: 14px; font-weight: 600;")

        payment_method_label = QLabel("Payment Method")
        remaining_label = QLabel("Remaining Amount")
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

        self.line_discount_total_entry = QLineEdit("0.00")
        self.line_discount_total_entry.setReadOnly(True)

        self.line_tax_total_entry = QLineEdit("0.00")
        self.line_tax_total_entry.setReadOnly(True)

        self.header_discount_source_label = QLabel("Source: Manual / None")
        self.header_discount_source_label.setStyleSheet("color: #6B7F8F; font-size: 10px; font-weight: 600; padding-left: 0;")
        self.header_tax_source_label = QLabel("Source: Manual / None")
        self.header_tax_source_label.setStyleSheet("color: #6B7F8F; font-size: 10px; font-weight: 600; padding-left: 0;")

        self.final_amount_entry = QLabel("0.00")
        self.final_amount_entry.setObjectName("FinalAmount")

        self.received_entry = QLineEdit("0.00")
        self.received_entry.setObjectName("ReceivedAmount")
        
        self.change_entry = QLineEdit("0.00")
        self.change_entry.setReadOnly(True)

        self.remainingdata = QLineEdit("0.00")
        self.remainingdata.setReadOnly(True)

        self.writeoff_check = QCheckBox("Write-off Remaining")
        self.writeoff_check.setStyleSheet("QCheckBox { color: #333; font-size: 11px; }")
        self.writeoff_check.setChecked(False)
        self.auto_print_check = QCheckBox("Auto Print")
        self.auto_print_check.setStyleSheet("QCheckBox { color: #333; font-size: 11px; }")
        self.auto_print_check.setChecked(True)

        self.payment_handler = PaymentMethodHandler(self)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)

        self.due_date_combo = QComboBox()
        self.due_date_combo.addItems(["None", "+15 days", "+30 days", "+45 days", "+60 days", "+90 days"])
        self.due_date_combo.setCurrentText("None")
        self.due_date_combo.setEnabled(False)
        
        self.gross_entry.setAlignment(Qt.AlignRight)
        self.discount_entry.setAlignment(Qt.AlignRight)
        self.tax_entry.setAlignment(Qt.AlignRight)
        self.line_discount_total_entry.setAlignment(Qt.AlignRight)
        self.line_tax_total_entry.setAlignment(Qt.AlignRight)
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
        self.received_entry.textChanged.connect(self.calculate_payment)
        self.received_entry.textChanged.connect(self.update_due_date_availability)
        self.writeoff_check.toggled.connect(self.update_due_date_availability)

        left_grid = QGridLayout()
        left_grid.setHorizontalSpacing(10)
        left_grid.setVerticalSpacing(8)
        left_grid.addWidget(gross_label, 0, 0)
        left_grid.addWidget(self.gross_entry, 0, 1)
        left_grid.addWidget(discount_label, 0, 2)
        left_grid.addWidget(self.discount_entry, 0, 3)
        left_grid.addWidget(tax_label, 0, 4)
        left_grid.addWidget(self.tax_entry, 0, 5)
        left_grid.addWidget(additional_label, 0, 6)
        left_grid.addWidget(self.additional_entry, 0, 7)
        left_grid.addWidget(self.header_discount_source_label, 1, 2, 1, 2)
        left_grid.addWidget(self.header_tax_source_label, 1, 4, 1, 2)
        left_grid.addWidget(line_discount_label, 2, 0)
        left_grid.addWidget(self.line_discount_total_entry, 2, 1)
        left_grid.addWidget(line_tax_label, 2, 2)
        left_grid.addWidget(self.line_tax_total_entry, 2, 3)
        left_grid.addWidget(taxable_label, 2, 4)
        left_grid.addWidget(self.taxable_entry, 2, 5)
        left_grid.addWidget(net_amount_label, 2, 6)
        left_grid.addWidget(self.net_amount_entry, 2, 7)
        left_grid.addWidget(payment_method_label, 3, 6)
        left_grid.addWidget(self.payment_method, 3, 7)
        left_grid.setColumnMinimumWidth(0, 54)
        left_grid.setColumnMinimumWidth(2, 54)
        left_grid.setColumnMinimumWidth(4, 54)
        left_grid.setColumnMinimumWidth(6, 110)
        left_grid.setColumnStretch(1, 1)
        left_grid.setColumnStretch(3, 1)
        left_grid.setColumnStretch(5, 1)
        left_grid.setColumnStretch(7, 1)

        right_grid = QGridLayout()
        right_grid.setHorizontalSpacing(10)
        right_grid.setVerticalSpacing(8)
        right_grid.addWidget(final_amount_label, 0, 0)
        right_grid.addWidget(self.final_amount_entry, 0, 1)
        right_grid.addWidget(received_label, 0, 2)
        right_grid.addWidget(self.received_entry, 0, 3)

        due_date_label = QLabel("Due Date")
        due_date_label.setStyleSheet(label_style)
        right_grid.addWidget(due_date_label, 1, 0)
        right_grid.addWidget(self.due_date_combo, 1, 1)
        right_grid.addWidget(remaining_label, 1, 2)
        right_grid.addWidget(self.remainingdata, 1, 3)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(10)
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.auto_print_check)
        checkbox_layout.addWidget(self.writeoff_check)
        right_grid.addLayout(checkbox_layout, 2, 0, 1, 4)
        right_grid.setColumnMinimumWidth(0, 92)
        right_grid.setColumnMinimumWidth(2, 118)
        right_grid.setColumnStretch(1, 1)
        right_grid.setColumnStretch(3, 1)

        main_grid.addLayout(left_grid, 0, 0)
        section_gap = QSpacerItem(28, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        main_grid.addItem(section_gap, 0, 1)
        main_grid.addLayout(right_grid, 0, 2)
        main_grid.setColumnStretch(0, 3)
        main_grid.setColumnStretch(2, 2)

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
        rate_text = self.rate_edit.text().strip()

        if self.has_auto_price_for_current_row():
            self.focus_next_field(self.add_line_button)
            return

        if rate_text:
            try:
                if float(rate_text) > 0:
                    self.focus_next_field(self.add_line_button)
                    return
            except ValueError:
                pass

        self.focus_next_field(self.rate_edit)
        

    
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            if isinstance(obj, QLineEdit) and not obj.isReadOnly():
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
        self.sales_discount_policy = load_sales_policy_settings()["discount_policy"]
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
        discount_data = self.discount.text()
        tax_data = self.tax.text()
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
        discount.setProperty("discount_input_mode", discount_mode)
        discount.setProperty("discount_percent_applied", resolved["discount_percent"])
        discount.setProperty("discount_amount_applied", resolved["discount_amount"])
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
        tax.setReadOnly(True)
        tax.setText(tax_data)
        tax.setProperty("tax_percent_applied", resolved["tax_percent"])
        tax.setProperty("tax_fixed_amount_applied", resolved["tax_fixed_amount"])
        tax.setProperty("tax_amount_applied", resolved["tax_amount"])
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
            AppMessageBox.information(self, "Error", query.lastError().text())

        self.update_customer_credit_summary()
    
    
    
    
    
    
    
    
    
    
    
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

    def on_discount_entry_edited(self):
        self.discount_group_manual_override = True
        self.refresh_customer_pricing_summary()

    def on_tax_entry_edited(self):
        self.tax_group_manual_override = True
        self.refresh_customer_pricing_summary()

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

        query = QSqlQuery()
        query.prepare("""
            SELECT
                COALESCE(name, 'Walk-in Customer'),
                COALESCE(receiveable, 0),
                COALESCE(credit_limit, 0)
            FROM customer
            WHERE id = ?
        """)
        query.addBindValue(customer_id)

        if not query.exec() or not query.next():
            self.customer_credit_summary.setText("Credit Summary: Unable to load customer credit position")
            return

        customer_name = str(query.value(0) or "")
        receivable = float(query.value(1) or 0.0)
        credit_limit = float(query.value(2) or 0.0)

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

        print(
            "[SALES][PRICING] Re-evaluating pricing defaults:",
            {
                "customer_id": customer_id,
                "sales_discount_policy": self.sales_discount_policy,
                "sales_tax_policy": self.sales_tax_policy,
            }
        )

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

        if global_discount_meta["state"] == "ok":
            print("[SALES][GLOBAL] Loaded global promo discount:", global_discount_meta["data"])
        elif global_discount_meta["state"] == "disabled":
            print(
                "[SALES][GLOBAL] Global promo discount is disabled in accounting_settings.",
                {"selected_group_id": global_discount_meta.get("selected_group_id")}
            )
        elif global_discount_meta["state"] == "enabled_without_selection":
            print("[SALES][GLOBAL] Global promo discount is enabled, but no discount group is selected.")
        elif global_discount_meta["state"] == "group_unresolved":
            print(
                "[SALES][GLOBAL] Global promo discount is enabled, but the selected discount group could not be resolved.",
                {"selected_group_id": global_discount_meta.get("selected_group_id")}
            )
        else:
            print("[SALES][GLOBAL] No accounting_settings row found for discount settings.")

        if global_tax_meta["state"] == "ok":
            print("[SALES][GLOBAL] Loaded global sales tax:", global_tax_meta["data"])
        elif global_tax_meta["state"] == "disabled":
            print(
                "[SALES][GLOBAL] Global sales tax is disabled in accounting_settings.",
                {"selected_group_id": global_tax_meta.get("selected_group_id")}
            )
        elif global_tax_meta["state"] == "enabled_without_selection":
            print("[SALES][GLOBAL] Global sales tax is enabled, but no tax group is selected.")
        elif global_tax_meta["state"] == "group_unresolved":
            print(
                "[SALES][GLOBAL] Global sales tax is enabled, but the selected tax group could not be resolved.",
                {"selected_group_id": global_tax_meta.get("selected_group_id")}
            )
        else:
            print("[SALES][GLOBAL] No accounting_settings row found for tax settings.")

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

        if self.active_discount_source == "customer_default":
            print(
                "[SALES][PRICING] Using customer discount defaults:",
                {
                    "group_id": self.active_discount_group_id,
                    "name": self.active_discount_group_name,
                    "percent": self.active_discount_percent,
                    "fixed_amount": self.active_discount_fixed_amount,
                    "apply_on_sale": self.active_discount_apply_on_sale,
                }
            )

        if self.active_tax_source == "customer_default":
            print(
                "[SALES][PRICING] Using customer tax defaults:",
                {
                    "group_id": self.active_tax_group_id,
                    "name": self.active_tax_group_name,
                    "percent": self.active_tax_percent,
                    "fixed_amount": self.active_tax_fixed_amount,
                    "apply_on_sale": self.active_tax_apply_on_sale,
                }
            )

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
        print(
            "[SALES][PRICING] Active header defaults after evaluation:",
            {
                "discount_source": self.active_discount_source,
                "discount_group_id": self.active_discount_group_id,
                "discount_group_name": self.active_discount_group_name,
                "discount_percent": self.active_discount_percent,
                "discount_fixed_amount": self.active_discount_fixed_amount,
                "discount_apply_on_sale": self.active_discount_apply_on_sale,
                "tax_source": self.active_tax_source,
                "tax_group_id": self.active_tax_group_id,
                "tax_group_name": self.active_tax_group_name,
                "tax_percent": self.active_tax_percent,
                "tax_fixed_amount": self.active_tax_fixed_amount,
                "tax_apply_on_sale": self.active_tax_apply_on_sale,
            }
        )

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
        query = QSqlQuery()
        query.prepare("SELECT id FROM auth WHERE username = ?;")
        query.addBindValue(username)
        if query.exec() and query.next():
            return query.value(0)
        else:
            AppMessageBox.information(None, 'Error', query.lastError().text() )
            self.close()                # Close main window
            QApplication.quit()
            return None    
    
    
    
    
    def insert_salesreceipt(self):
    
        try:
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
                sales_id = insert_sales_header(header_payload)
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

        query = QSqlQuery()
        query.prepare("""
            SELECT
                COALESCE(name, 'Walk-in Customer'),
                COALESCE(receiveable, 0),
                COALESCE(credit_limit, 0)
            FROM customer
            WHERE id = ?
        """)
        query.addBindValue(customer_id)

        if not query.exec() or not query.next():
            AppMessageBox.warning(self, "Credit Limit", "Could not load customer credit information.")
            return False

        customer_name = str(query.value(0) or "")
        current_receivable = float(query.value(1) or 0.0)
        credit_limit = float(query.value(2) or 0.0)

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

        # default values for walk-in / no customer
        payable_before = 0.0
        receiveable_before = 0.0
        balance_state = compute_customer_transaction_balances(
            payable_before=0.0,
            receiveable_before=0.0,
            remaining=remaining,
        )

        # only fetch/update balances if customer exists
        if customer_id is not None:
            existing_balances = fetch_customer_balances(customer_id)
            payable_before = existing_balances["payable_before"]
            receiveable_before = existing_balances["receiveable_before"]
            print(
                "[SALES][TXN] Customer balances before:",
                {
                    "payable_before": payable_before,
                    "receiveable_before": receiveable_before,
                }
            )

            balance_state = compute_customer_transaction_balances(
                payable_before=payable_before,
                receiveable_before=receiveable_before,
                remaining=remaining,
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

        session_id = get_active_session_id(strict=True)
        if session_id is None:
            AppMessageBox.warning(self, "Validation Error", "No active session found.")
            return None

        payment = self._normalize_payment_data(self.payment_handler.payment_data.copy())
        print(payment)
        print("Payment data is as above")
        print("[SALES][TXN] Normalized payment data:", payment)

        note = build_customer_transaction_note(
            sales_id=sales_id,
            total_amount=total_amount,
            received=received,
            remaining=remaining,
        )
        txn_payload = build_customer_transaction_payload(
            sales_id=sales_id,
            customer_id=customer_id,
            total_amount=self._float_or_default(total_amount, 0.0),
            received=self._float_or_default(received, 0.0),
            salesman_id=salesman_id,
            session_id=session_id,
            payment=payment,
            note=note,
            balance_state=balance_state,
        )
        transaction_id = insert_customer_transaction_record(txn_payload)

        print("Transaction Stored with ID:", transaction_id)
        print(f"[SALES][TXN] Customer transaction persisted for sales_id={sales_id}")

        # only update customer running balance if linked customer exists
        if customer_id is not None:
            update_customer_running_balance(
                customer_id,
                payable_after=balance_state["payable_after"],
                receiveable_after=balance_state["receiveable_after"],
            )

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

    def _persist_sales_item_record(self, sales_id, row_payload):
        sale_item_id = persist_sales_item_record(sales_id, row_payload)
        print("[SALES][ITEMS] salesitem insert payload:", {"sales_id": sales_id, **row_payload})
        return sale_item_id

    def _allocate_sales_fifo_batches(self, product_id, sale_item_id, qty_needed, row_number):
        print(
            f"[SALES][FIFO] Starting FIFO allocation for row={row_number}, "
            f"product_id={product_id}, sale_item_id={sale_item_id}, qty_needed={qty_needed}"
        )

        batch_rows = fetch_fifo_batch_rows(product_id)
        allocation_result = compute_fifo_allocation_plan(batch_rows, qty_needed)

        for allocation in allocation_result["allocations"]:
            batch_id = allocation["batch_id"]
            available = allocation["available"]
            unit_cost = allocation["unit_cost"]
            take_qty = allocation["take_qty"]
            line_cost = allocation["line_cost"]

            if allocation["invalid_cost"]:
                print(
                    f"[SALES][FIFO][WARN] Invalid batch.unit_cost encountered for "
                    f"batch_id={batch_id}, row={row_number}, raw_cost={allocation['raw_cost']!r}"
                )
            print(
                "[SALES][FIFO] Batch candidate:",
                {
                    "row": row_number,
                    "batch_id": batch_id,
                    "available": available,
                    "raw_cost": allocation["raw_cost"],
                    "unit_cost": unit_cost,
                    "remaining_qty_before": take_qty + allocation["remaining_after"],
                }
            )
            print(
                "Batch Data:",
                "Batch ID:", batch_id,
                "Available:", available,
                "Unit Cost:", unit_cost,
                "Taking Qty:", take_qty,
                "Line Cost:", line_cost
            )

            decrement_batch_quantity(batch_id, take_qty)
            print(
                f"[SALES][FIFO] Batch updated: batch_id={batch_id}, "
                f"deducted={take_qty}, remaining_after_update_should_be={available - take_qty}"
            )
            insert_sold_batch_record(sale_item_id, allocation)
            print(
                "[SALES][FIFO] sold_batch inserted:",
                {
                    "sale_item_id": sale_item_id,
                    "batch_id": batch_id,
                    "qty_taken": take_qty,
                    "unit_cost": unit_cost,
                    "line_cost": line_cost,
                }
            )
            print(f"[SALES][FIFO] Remaining qty after batch {batch_id}: {allocation['remaining_after']}")

        if allocation_result["remaining_qty"] > 0:
            raise Exception(
                f"FIFO allocation failed for product ID {product_id}. "
                f"Unallocated qty: {allocation_result['remaining_qty']}"
            )
        print(
            f"[SALES][FIFO] FIFO allocation completed for row={row_number}, "
            f"product_id={product_id}, sale_item_id={sale_item_id}"
        )

    def thermal_receipt_printer(self, sales_id):
        filename = "salesinvoice_thermal.pdf"
        return self.export_thermal_pdf(filename=filename, sales_id=sales_id)

    def get_saved_sale_tax_breakdown(self, sales_id):
        header_tax = 0.0
        line_tax = 0.0
        policy = "both"

        header_query = QSqlQuery()
        header_query.prepare("SELECT COALESCE(tax, 0) FROM sales WHERE id = ? LIMIT 1")
        header_query.addBindValue(sales_id)
        if header_query.exec() and header_query.next():
            header_tax = float(header_query.value(0) or 0.0)

        line_query = QSqlQuery()
        line_query.prepare("SELECT COALESCE(SUM(COALESCE(taxamount, 0)), 0) FROM salesitem WHERE sales_id = ?")
        line_query.addBindValue(sales_id)
        if line_query.exec() and line_query.next():
            line_tax = float(line_query.value(0) or 0.0)

        policy = load_sales_policy_settings()["tax_policy"]

        return {
            "line_tax": line_tax,
            "header_tax": header_tax,
            "policy": policy,
        }
    
    
    def export_thermal_pdf(self, filename=None, sales_id=None, paper_width_mm=80.0):
        
        print("Exporting thermal PDF")
        print("Sales id is:", sales_id)

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

        # ---------------------------
        # Fetch business information
        # ---------------------------
        business_name = "Business"
        address = "-"
        contact = "-"

        business_query = QSqlQuery()
        business_query.prepare("""
            SELECT businessname, address, contact
            FROM business
            WHERE id = 1
            LIMIT 1
        """)
        if business_query.exec() and business_query.next():
            business_name = str(business_query.value(0) or business_name)
            address = str(business_query.value(1) or address)
            contact = str(business_query.value(2) or contact)

        # ---------------------------
        # Fetch sales header details
        # ---------------------------
        header_query = QSqlQuery()
        header_query.prepare("""
            SELECT
                s.id,
                s.creation_date,
                s.subtotal,
                s.discount,
                s.tax,
                s.total,
                COALESCE(c.name, 'Walk-In Customer')
            FROM sales s
            LEFT JOIN customer c ON c.id = s.customer
            WHERE s.id = ?
            LIMIT 1
        """)
        header_query.addBindValue(sales_id)
        if not header_query.exec() or not header_query.next():
            print("Failed to fetch sales header:", header_query.lastError().text())
            return None

        invoice_no = str(header_query.value(0) or sales_id)
        invoice_date = str(header_query.value(1) or "")
        sales_subtotal = float(header_query.value(2) or 0.0)
        sales_discount = float(header_query.value(3) or 0.0)
        sales_tax = float(header_query.value(4) or 0.0)
        sales_total = float(header_query.value(5) or 0.0)
        customer_name = str(header_query.value(6) or "Walk-In Customer")
        tax_breakdown = self.get_saved_sale_tax_breakdown(sales_id)

        # ---------------------------
        # Fetch sale items
        # ---------------------------
        items = []
        item_query = QSqlQuery()
        item_query.prepare("""
            SELECT
                p.display_name,
                si.qty_sold,
                si.unit_price,
                si.discount,
                si.line_total
            FROM salesitem si
            JOIN product p ON p.id = si.product_id
            WHERE si.sales_id = ?
            ORDER BY si.id
        """)
        item_query.addBindValue(sales_id)

        if not item_query.exec():
            print("Failed to fetch sale items:", item_query.lastError().text())
            return None

        while item_query.next():
            items.append({
                "name": str(item_query.value(0) or ""),
                "qty": int(item_query.value(1) or 0),
                "unit_price": float(item_query.value(2) or 0.0),
                "discount": float(item_query.value(3) or 0.0),
                "line_total": float(item_query.value(4) or 0.0),
            })

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
            name = row["name"][:32]
            qty = row["qty"]
            total = row["line_total"]
            unit_price = row["unit_price"]

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

            total_available = fetch_total_available_stock(product_id)
            print(f"[SALES][STOCK] Product {product_id} total available stock: {total_available}")
            print("Available Stock is:", total_available)

            if normalized_row["qty"] > total_available:
                raise Exception(f"Row {row + 1}: Insufficient stock for product ID {product_id}.")

            sale_item_id = self._persist_sales_item_record(
                sales_id,
                {
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
                },
            )

            print("Sales Item ID is:", sale_item_id)

            self._allocate_sales_fifo_batches(
                product_id=product_id,
                sale_item_id=sale_item_id,
                qty_needed=normalized_row["qty"],
                row_number=row + 1,
            )

        print(f"[SALES][ITEMS] Completed item processing for sales_id={sales_id}")
        return True
    
    
    
    def put_sale_on_hold(self):
        
        db = QSqlDatabase().database()
        db.transaction()
        
        try:
        
            print("Putting Sale on Hold")

            # get salesorder data
            customer = self.customer.currentData()
            salesman = self.get_salesman_id()
            status = 'On Hold'
            subtotal = self._parse_float_field(self.gross_entry.text(), "Sub Total", 0.0)
            discount_amount = self._parse_float_field(self.discount_entry.text(), "Discount", 0.0)
            taxable_amount = self._parse_float_field(self.taxable_entry.text(), "Taxable", 0.0)
            tax_amount = self._parse_float_field(self.tax_entry.text(), "Sales Tax", 0.0)
            additional_charges = self._parse_float_field(self.additional_entry.text(), "Additional Charges", 0.0)
            final_amount = self._parse_float_field(self.final_amount_entry.text(), "Final Amount", 0.0)
            received_amount = self._parse_float_field(self.received_entry.text(), "Received", 0.0)
            remaining_amount = self._parse_float_field(self.remainingdata.text(), "Remaining Amount", 0.0)
            payment_method = self._text_or_none(self.payment_method.currentText()) if hasattr(self, "payment_method") else "Cash"
            due_date = self.compute_due_date()
            
            print("Customer is: ", customer)
            
            if customer == 0:
                customer = None

            # inserting or updating hold sale
            hold_id = self.current_hold_sale_id
            hold_query = QSqlQuery()

            if hold_id is not None:
                hold_query.prepare("""
                    UPDATE holdsale
                    SET customer = ?, salesman = ?, status = ?,
                        subtotal = ?, discount_amount = ?, taxable_amount = ?, tax_amount = ?,
                        additional_charges = ?, final_amount = ?, received_amount = ?,
                        remaining_amount = ?, payment_method = ?, due_date = ?
                    WHERE id = ?
                """)
            else:
                hold_query.prepare("""
                    INSERT INTO holdsale (
                        customer, salesman, status,
                        subtotal, discount_amount, taxable_amount, tax_amount,
                        additional_charges, final_amount, received_amount,
                        remaining_amount, payment_method, due_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """)

            hold_query.addBindValue(customer)
            hold_query.addBindValue(salesman)
            hold_query.addBindValue(status)
            hold_query.addBindValue(subtotal)
            hold_query.addBindValue(discount_amount)
            hold_query.addBindValue(taxable_amount)
            hold_query.addBindValue(tax_amount)
            hold_query.addBindValue(additional_charges)
            hold_query.addBindValue(final_amount)
            hold_query.addBindValue(received_amount)
            hold_query.addBindValue(remaining_amount)
            hold_query.addBindValue(payment_method)
            hold_query.addBindValue(due_date)
            if hold_id is not None:
                hold_query.addBindValue(int(hold_id))
            
            if hold_query.exec():

                print("Sales on Hold Running...")
                if hold_id is None:
                    hold_id = int(hold_query.lastInsertId())
                else:
                    clear_items_query = QSqlQuery()
                    clear_items_query.prepare("DELETE FROM holditems WHERE holdsale = ?")
                    clear_items_query.addBindValue(int(hold_id))
                    if not clear_items_query.exec():
                        raise Exception(clear_items_query.lastError().text())

                self.current_hold_sale_id = int(hold_id)
                print("Sales ID is: ", hold_id)

                # save hold items
                self.hold_sales_items(hold_id)

            else:
                print("Error inserting sales on hold:", hold_query.lastError().text())
                AppMessageBox.error(self, "Error", hold_query.lastError().text())
                raise Exception

        
        
        except Exception as exc:
            
            print("rolling back transactions")
            db.rollback()
            AppMessageBox.error(self, "Error", f"Database error - rolling back transactions.\n\n{exc}")
            
        else:
            
            db.commit()
            print("Transaction committed successfully")
            self.clear_fields()
            AppMessageBox.success(self, "Success", "Sales Hold saved successfully")
        
        
        
        
        
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

            product_id = self.extract_product_id(product_widget.currentData())
            if product_id is None:
                continue
            items_exits = True
            
            hold_id = int(hold_id)
            
            print("Current Data is: ", product_id)
            
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
            
            
            print("we have reached here...")
        
            # Insert sales item
            item_query = QSqlQuery()
            item_query.prepare("""
                INSERT INTO holditems (
                    holdsale, product, qty, unitrate, discount,
                    discountamount, tax, taxamount, discount_input_mode, total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)

            item_query.addBindValue(hold_id)
            item_query.addBindValue(product_id)
            item_query.addBindValue(qty)
            item_query.addBindValue(rate)
            item_query.addBindValue(discount)
            item_query.addBindValue(discountamount)
            item_query.addBindValue(tax)
            item_query.addBindValue(taxamount)
            item_query.addBindValue(discount_input_mode)
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
        self.load_hold_orders()
        
        
        
        
        
        
    
    #  Saving Sales Receipt
    @Permissions.require_permission('sales.create')
    def save_receipt(self):
        if not require_open_session(self):
            return

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.error(self, "Database Error", "Could not start sales transaction.")
            return
        
        try: 
        
            # Insert Sales Receipt
            sales_id = self.insert_salesreceipt()
            
            if sales_id is None:
                raise Exception("Sales receipt header was not saved.")
            # Insert Sales Items
            self.insert_salesitems(sales_id)
            
        
        except Exception as exc:
            
            print("rolling back transactions")
            db.rollback()
            AppMessageBox.error(self, "Error", f"Database error - rolling back transactions.\n\n{exc}")
            
        else:
            
            if not db.commit():
                db.rollback()
                AppMessageBox.error(self, "Error", "Failed to commit sales transaction.")
                return

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
        code_text = str(code or "").strip()
        if not code_text:
            return None

        query = QSqlQuery()
        query.prepare("""
            SELECT
                p.id,
                p.display_name,
                COALESCE(pp.unit_price, 0),
                COALESCE(dg.id, 0),
                COALESCE(dg.discount_percent, 0),
                COALESCE(dg.name, ''),
                COALESCE(dg.fixed_amount, 0),
                COALESCE(dg.apply_on_sale, 1),
                COALESCE(tg.id, 0),
                CASE WHEN COALESCE(tg.apply_on_sale, 1) = 1 THEN COALESCE(tg.tax_percent, 0) ELSE 0 END,
                COALESCE(tg.fixed_amount, 0),
                COALESCE(tg.apply_on_sale, 1),
                COALESCE(tg.name, ''),
                COALESCE((
                    SELECT SUM(quantity_remaining)
                    FROM batch
                    WHERE product_id = p.id
                      AND quantity_remaining > 0
                      AND (
                          expiry_date IS NULL
                          OR (
                              CASE
                                  WHEN expiry_date LIKE '____-__-__' THEN date(expiry_date)
                                  WHEN expiry_date LIKE '__-__-____'
                                      THEN date(substr(expiry_date, 7, 4) || '-' || substr(expiry_date, 4, 2) || '-' || substr(expiry_date, 1, 2))
                                  ELSE NULL
                              END
                          ) >= date('now', 'localtime')
                      )
                ), 0) as available_stock
            FROM product p
            LEFT JOIN discount_group dg ON dg.id = p.discount_group_id
            LEFT JOIN tax_group tg ON tg.id = p.tax_group_id
            LEFT JOIN price_pack pp ON pp.id = (
                SELECT id
                FROM price_pack
                WHERE product_id = p.id
                ORDER BY is_default DESC, id ASC
                LIMIT 1
            )
            WHERE TRIM(CAST(p.code AS TEXT)) = ?
              AND COALESCE(p.status, 'active') IN ('active', 'used')
            LIMIT 1
        """)
        query.addBindValue(code_text)

        if not query.exec():
            print("Barcode product query failed:", query.lastError().text())
            return None

        if not query.next():
            return None

        product_id = int(query.value(0))
        display_name = str(query.value(1) or "").strip()
        unit_price = float(query.value(2) or 0.0)
        discount_group_id = int(query.value(3) or 0) or None
        discount_percent = float(query.value(4) or 0.0)
        discount_group_name = str(query.value(5) or "").strip()
        discount_fixed_amount = float(query.value(6) or 0.0)
        discount_apply_on_sale = bool(int(query.value(7) or 0))
        tax_group_id = int(query.value(8) or 0) or None
        tax_percent = float(query.value(9) or 0.0)
        tax_fixed_amount = float(query.value(10) or 0.0)
        tax_apply_on_sale = bool(int(query.value(11) or 0))
        tax_group_name = str(query.value(12) or "").strip()
        available_stock = int(query.value(13) or 0)

        return {
            "product_id": product_id,
            "display_name": display_name,
            "unit_price": unit_price,
            "discount_group_id": discount_group_id,
            "discount_percent": discount_percent,
            "discount_group_name": discount_group_name,
            "discount_fixed_amount": discount_fixed_amount,
            "discount_apply_on_sale": discount_apply_on_sale,
            "tax_group_id": tax_group_id,
            "tax_percent": tax_percent,
            "tax_fixed_amount": tax_fixed_amount,
            "tax_apply_on_sale": tax_apply_on_sale,
            "tax_group_name": tax_group_name,
            "available_stock": available_stock,
            "code": code_text,
        }


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

    
    
    
    def _run_pending_scan(self):
        
        if not self._pending_scan:
            return
        
        code, combo = self._pending_scan
        self._pending_scan = None
        self.process_barcode_code(str(code or ""))


    
        
    
    def _sales_product_query_fn(self, search_text):
        query = QSqlQuery()
        query.prepare("""
            SELECT p.id, p.display_name, pp.unit_price
                 , COALESCE(dg.id, 0)
                 , COALESCE(dg.discount_percent, 0)
                 , COALESCE(dg.name, '')
                 , COALESCE(dg.fixed_amount, 0)
                 , COALESCE(dg.apply_on_sale, 1)
                 , COALESCE(tg.id, 0)
                 , CASE WHEN COALESCE(tg.apply_on_sale, 1) = 1 THEN COALESCE(tg.tax_percent, 0) ELSE 0 END
                 , COALESCE(tg.fixed_amount, 0)
                 , COALESCE(tg.apply_on_sale, 1)
                 , COALESCE(tg.name, '')
            FROM product p
            LEFT JOIN discount_group dg ON dg.id = p.discount_group_id
            LEFT JOIN tax_group tg ON tg.id = p.tax_group_id
            LEFT JOIN price_pack pp ON pp.id = (
                SELECT id
                FROM price_pack
                WHERE product_id = p.id
                ORDER BY is_default DESC, id DESC
                LIMIT 1
            )
            WHERE p.display_name LIKE ?
            LIMIT 10
        """)
        query.addBindValue(f"%{search_text}%")

        results = []
        if not query.exec():
            return results

        while query.next():
            product_id = query.value(0)
            name = str(query.value(1)).strip()
            unit_price = query.value(2) or 0.0
            discount_group_id = int(query.value(3) or 0) or None
            discount_percent = query.value(4) or 0.0
            discount_group_name = str(query.value(5) or "").strip()
            discount_fixed_amount = query.value(6) or 0.0
            discount_apply_on_sale = bool(int(query.value(7) or 0))
            tax_group_id = int(query.value(8) or 0) or None
            tax_percent = query.value(9) or 0.0
            tax_fixed_amount = query.value(10) or 0.0
            tax_apply_on_sale = bool(int(query.value(11) or 0))
            tax_group_name = str(query.value(12) or "").strip()
            results.append((name, {
                "product_id": product_id,
                "unit_price": unit_price,
                "discount_group_id": discount_group_id,
                "discount_percent": discount_percent,
                "discount_group_name": discount_group_name,
                "discount_fixed_amount": discount_fixed_amount,
                "discount_apply_on_sale": discount_apply_on_sale,
                "tax_group_id": tax_group_id,
                "tax_percent": tax_percent,
                "tax_fixed_amount": tax_fixed_amount,
                "tax_apply_on_sale": tax_apply_on_sale,
                "tax_group_name": tax_group_name,
            }))
        return results
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
        discount_percent = float(product_data.get("discount_percent") or 0.0)
        discount_fixed_amount = float(product_data.get("discount_fixed_amount") or 0.0)
        discount_apply_on_sale = bool(product_data.get("discount_apply_on_sale", True))
        tax_percent = float(product_data.get("tax_percent") or 0.0)
        tax_fixed_amount = float(product_data.get("tax_fixed_amount") or 0.0)
        tax_apply_on_sale = bool(product_data.get("tax_apply_on_sale", True))
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

        badge = "Manual Override Active" if has_manual_override else "Defaults Active"
        badge_color = "#B45309" if has_manual_override else "#2F5D7C"
        self.current_line_pricing_summary_text = (
            f"Line Pricing [{badge}]: Discount {discount_text} [{discount_source}, Mode: {'Amt' if discount_mode == 'amount' else '%'}, Policy {self._sales_discount_policy_label()}] | "
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

        if self.discount_entry.text().strip() != f"{discount:.2f}":
            self.discount_entry.blockSignals(True)
            self.discount_entry.setText(f"{discount:.2f}")
            self.discount_entry.blockSignals(False)

        self.taxable_entry.setText(f"{taxable:.2f}")

        if self.tax_entry.text().strip() != f"{tax:.2f}":
            self.tax_entry.blockSignals(True)
            self.tax_entry.setText(f"{tax:.2f}")
            self.tax_entry.blockSignals(False)

        self.net_amount_entry.setText(f"{net_amount:.2f}")

        if self.additional_entry.text().strip() != f"{additional_charges:.2f}":
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
        self.refresh_customer_pricing_summary()
        
    def build_hold_row_product_data(self, product_id):
        query = QSqlQuery()
        query.prepare("""
            SELECT
                p.display_name,
                COALESCE(pp.unit_price, 0),
                COALESCE(dg.id, 0),
                COALESCE(dg.discount_percent, 0),
                COALESCE(dg.name, ''),
                COALESCE(dg.fixed_amount, 0),
                COALESCE(dg.apply_on_sale, 1),
                COALESCE(tg.id, 0),
                CASE WHEN COALESCE(tg.apply_on_sale, 1) = 1 THEN COALESCE(tg.tax_percent, 0) ELSE 0 END,
                COALESCE(tg.fixed_amount, 0),
                COALESCE(tg.apply_on_sale, 1),
                COALESCE(tg.name, '')
            FROM product p
            LEFT JOIN discount_group dg ON dg.id = p.discount_group_id
            LEFT JOIN tax_group tg ON tg.id = p.tax_group_id
            LEFT JOIN price_pack pp ON pp.id = (
                SELECT id
                FROM price_pack
                WHERE product_id = p.id
                ORDER BY is_default DESC, id ASC
                LIMIT 1
            )
            WHERE p.id = ?
            LIMIT 1
        """)
        query.addBindValue(int(product_id))

        if not query.exec() or not query.next():
            return None

        return {
            "product_id": int(product_id),
            "display_name": str(query.value(0) or "").strip(),
            "unit_price": float(query.value(1) or 0.0),
            "discount_group_id": int(query.value(2) or 0) or None,
            "discount_percent": float(query.value(3) or 0.0),
            "discount_group_name": str(query.value(4) or "").strip(),
            "discount_fixed_amount": float(query.value(5) or 0.0),
            "discount_apply_on_sale": bool(int(query.value(6) or 0)),
            "tax_group_id": int(query.value(7) or 0) or None,
            "tax_percent": float(query.value(8) or 0.0),
            "tax_fixed_amount": float(query.value(9) or 0.0),
            "tax_apply_on_sale": bool(int(query.value(10) or 0)),
            "tax_group_name": str(query.value(11) or "").strip(),
        }

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
        qty_edit.setReadOnly(True)
        qty_edit.setText(str(qty_data))
        qty_edit.setStyleSheet("font-weight: 600;")

        rate_edit = QLineEdit()
        rate_edit.setReadOnly(True)
        rate_edit.setText(str(rate_data))
        rate_edit.setStyleSheet("font-weight: 600;")

        discount = QLineEdit()
        discount.setReadOnly(True)
        discount.setText(str(discount_data))
        discount.setProperty("discount_input_mode", discount_mode)
        discount.setProperty("discount_percent_applied", resolved["discount_percent"])
        discount.setProperty("discount_fixed_amount_applied", resolved["discount_fixed_amount"])
        discount.setProperty("discount_amount_applied", resolved["discount_amount"])
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
        tax.setReadOnly(True)
        tax.setText(str(tax_data))
        tax.setProperty("tax_percent_applied", resolved["tax_percent"])
        tax.setProperty("tax_fixed_amount_applied", resolved["tax_fixed_amount"])
        tax.setProperty("tax_amount_applied", resolved["tax_amount"])
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
        
    

    
    
    def reload_hold_order(self, id):
        
        print("Reloading Hold Data")

        self.clear_fields(reset_hold_reference=False)
        self.reloading_sale = True
        hold_id = int(id)
        self.current_hold_sale_id = hold_id

        query = QSqlQuery()
        query.prepare("""
            SELECT
                customer, salesman, subtotal, discount_amount, taxable_amount,
                tax_amount, additional_charges, final_amount, received_amount,
                remaining_amount, payment_method, due_date
            FROM holdsale
            WHERE id = ?
        """)
        query.addBindValue(hold_id)

        if not (query.exec() and query.next()):
            self.reloading_sale = False
            AppMessageBox.error(self, "Error", "Unable to load held sale.")
            return

        customer_id = query.value(0)
        salesman_id = query.value(1)
        stored_discount = float(query.value(3) or 0.0)
        stored_tax = float(query.value(5) or 0.0)
        additional_charges = float(query.value(6) or 0.0)
        received_amount = float(query.value(8) or 0.0)
        payment_method = str(query.value(10) or "Cash").strip() or "Cash"

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

        items_query = QSqlQuery()
        items_query.prepare("""
            SELECT
                product, qty, unitrate, discount, discountamount,
                COALESCE(tax, 0), COALESCE(discount_input_mode, 'percent'), total
            FROM holditems
            WHERE holdsale = ?
        """)
        items_query.addBindValue(hold_id)

        if not items_query.exec():
            self.reloading_sale = False
            AppMessageBox.error(self, "Error", items_query.lastError().text())
            return

        self.table.setRowCount(0)

        while items_query.next():
            product_id = int(items_query.value(0))
            quantity = int(items_query.value(1) or 0)
            rate = float(items_query.value(2) or 0.0)
            discount_percent = float(items_query.value(3) or 0.0)
            discount_amount = float(items_query.value(4) or 0.0)
            tax_percent = float(items_query.value(5) or 0.0)
            discount_mode = str(items_query.value(6) or "percent")
            total = float(items_query.value(7) or 0.0)

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
        query = QSqlQuery()
        if not query.exec("""
            SELECT
                h.id,
                COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                COALESCE(a.username, e.name, '-') AS user_name,
                COALESCE(h.final_amount, 0),
                COALESCE((SELECT COUNT(*) FROM holditems hi WHERE hi.holdsale = h.id), 0),
                h.creation_date
            FROM holdsale h
            LEFT JOIN customer c ON c.id = h.customer
            LEFT JOIN auth a ON a.id = h.salesman
            LEFT JOIN employee e ON e.id = h.salesman
            ORDER BY h.id DESC
        """):
            AppMessageBox.error(self, "Hold Sales", query.lastError().text())
            return

        rows = []
        while query.next():
            rows.append({
                "id": int(query.value(0) or 0),
                "customer": str(query.value(1) or "Walk-in Customer"),
                "user": str(query.value(2) or "-"),
                "final_amount": float(query.value(3) or 0.0),
                "items": int(query.value(4) or 0),
                "created_at": str(query.value(5) or "-"),
            })

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

        item_delete = QSqlQuery()
        item_delete.prepare("DELETE FROM holditems WHERE holdsale = ?")
        item_delete.addBindValue(int(hold_id))
        if not item_delete.exec():
            print("Error deleting hold items")
            print(item_delete.lastError().text())
            return

        hold_delete = QSqlQuery()
        hold_delete.prepare("DELETE FROM holdsale WHERE id = ?")
        hold_delete.addBindValue(int(hold_id))
        if not hold_delete.exec():
            print("Error deleting hold order")
            print(hold_delete.lastError().text())
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
        
        self.payment_method.blockSignals(True); 
        self.payment_method.setCurrentText("Cash"); 
        self.payment_method.blockSignals(False)
        
        
        self.writeoff_check.setChecked(False)
        
        self.table.setRowCount(0)
        
        self.populate_customers()
        self.refresh_customer_pricing_summary()
        
        # set focus back to combobox
        self.item.setCurrentIndex(-1)
        self.item.setFocus()
        
        


    def export_pdf(self, filename="salesinvoice.pdf", sales_id=None):
        
        print("Exporting PDF")
        
        print("Sales id is: ", sales_id)
        if sales_id is None:
            print("Cannot export PDF without sales_id.")
            return None

        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                print("Could not remove old invoice pdf:", e)

        # ---------------------------
        # Fetch business information
        # ---------------------------
        business_name = "Business"
        address = "-"
        contact = "-"

        business_query = QSqlQuery()
        business_query.prepare("""
            SELECT businessname, address, contact
            FROM business
            WHERE id = 1
            LIMIT 1
        """)
        if business_query.exec() and business_query.next():
            business_name = str(business_query.value(0) or business_name)
            address = str(business_query.value(1) or address)
            contact = str(business_query.value(2) or contact)

        # ---------------------------
        # Fetch sales header details
        # ---------------------------
        header_query = QSqlQuery()
        header_query.prepare("""
            SELECT
                s.id,
                s.creation_date,
                s.subtotal,
                s.discount,
                s.tax,
                s.total,
                COALESCE(c.name, 'Walk-In Customer')
            FROM sales s
            LEFT JOIN customer c ON c.id = s.customer
            WHERE s.id = ?
            LIMIT 1
        """)
        header_query.addBindValue(sales_id)

        if not header_query.exec() or not header_query.next():
            print("Failed to fetch sales header:", header_query.lastError().text())
            return None

        invoice_no = f"# {int(header_query.value(0))}"
        invoice_date = str(header_query.value(1) or "")
        sales_subtotal = float(header_query.value(2) or 0.0)
        sales_discount = float(header_query.value(3) or 0.0)
        sales_tax = float(header_query.value(4) or 0.0)
        sales_total = float(header_query.value(5) or 0.0)
        tax_breakdown = self.get_saved_sale_tax_breakdown(sales_id)
        customer_name = str(header_query.value(6) or "Walk-In Customer")
        
        
        query = QSqlQuery()
        query.prepare("""
            SELECT
                p.display_name,
                si.qty_sold,
                si.unit_price,
                si.discount,
                si.line_total
            FROM salesitem si
            JOIN product p ON p.id = si.product_id
            WHERE si.sales_id = ?
            ORDER BY si.id
        """)
        query.addBindValue(sales_id)
        
        items = []
        
        if query.exec():
            
            print("Query has been executed successfully")
            
            while query.next():
                
                product_name = str(query.value(0) or "")
                qty = int(query.value(1) or 0)
                rate = float(query.value(2) or 0.0)
                discount = float(query.value(3) or 0.0)
                total = float(query.value(4) or 0.0)

                # discount is stored per line item; net price shown per unit.
                price = rate - discount

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
        
        print(f"product Id isL {product_id}")
        available_qty = self.get_available_qty(product_id)
        
        print(f"Available Qty is: {available_qty}")

        if entered_qty > available_qty:
            AppMessageBox.warning(
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
            AND quantity_remaining > 0
            AND (
                expiry_date IS NULL
                OR (
                    CASE
                        WHEN expiry_date LIKE '____-__-__' THEN date(expiry_date)
                        WHEN expiry_date LIKE '__-__-____'
                            THEN date(substr(expiry_date, 7, 4) || '-' || substr(expiry_date, 4, 2) || '-' || substr(expiry_date, 1, 2))
                        ELSE NULL
                    END
                ) >= date('now', 'localtime')
            )
        """)
        query.addBindValue(product_id)

        if query.exec() and query.next():
            return int(query.value(0) or 0)

        return 0
    
    
    
    
   
   

    
