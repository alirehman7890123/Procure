from datetime import datetime
from PySide6.QtWidgets import QWidget, QCompleter, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QStringListModel, QDate, QTimer, Signal, QEvent
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent
from functools import partial
from PySide6.QtGui import QKeySequence, QShortcut

import csv    
import os
import math

from utilities.stylus import load_stylesheets






class KeyUpLineEdit(QLineEdit):
    keyReleased = Signal(QKeyEvent)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.keyReleased.emit(event)





class AddPurchaseWidget(QWidget):


    def __init__(self, parent=None):

        super().__init__(parent)
        
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Invoice", objectName="SectionTitle")
        self.invoicelist = QPushButton("Invoice List", objectName="TopRightButton")
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        self.invoicelist.setFixedWidth(200)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.invoicelist)

        self.layout.addLayout(header_layout)
        

        line = QFrame()
        line.setObjectName("lineSeparator")

        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
                QFrame#lineSeparator {
                    border: none;
                    border-top: 2px solid #333;
                }
            """)


        self.layout.addWidget(line)
        self.layout.addSpacing(5)
        
        
        
        
        # Top Row 
        top_row = QHBoxLayout()
        
        supplier = QLabel("Supplier")
        rep = QLabel("Seller Rep")
        seller_invoice = QLabel("Seller Invoice")

        self.supplier_edit = QComboBox()
        # self.add_supplier = QPushButton("+")
        self.rep_edit = QComboBox()
        
        # self.add_rep = QPushButton("+")
        self.invoice_edit = QLineEdit()
        
        
        top_row.addWidget(supplier, 1)
        top_row.addWidget(self.supplier_edit, 2)
        # top_row.addWidget(self.add_supplier)
        
        top_row.addWidget(rep, 1)
        top_row.addWidget(self.rep_edit, 2)
        # top_row.addWidget(self.add_rep)
        
        
        top_row.addWidget(seller_invoice, 1)
        top_row.addWidget(self.invoice_edit, 2)
        
        self.layout.addLayout(top_row)
        
        top_row.addSpacing(40)

        
        self.supplier_edit.currentIndexChanged.connect(self.populate_reps)
        
        
        
        line = QFrame()
        line.setObjectName("lineSeparator")

        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
                QFrame#lineSeparator {
                    border: none;
                    border-top: 2px solid #333;
                }
            """)


        self.layout.addWidget(line)
        self.layout.addSpacing(10)
        
        
        ### Populate Labels & Entry Line
        self.populate_label_line()
        
        
        
        # Purchse Table
        self.row_height = 40
        self.min_visible_rows = 5
    
        self.table = MyTable(column_ratios=[0.03, 0.25, 0.07, 0.10, 0.05, 0.05, 0.07, 0.07, 0.05, 0.10, 0.05])
        headers = ["#", "Product", "Batch", "Expiry", "Qty", "Bonus", "Rate", "Disc % ", "Tax %", "Total", "X"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setTabKeyNavigation(False)
        
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.table.verticalHeader().setFixedWidth(0)
        remove_col = headers.index("X")
        self.table.horizontalHeaderItem(remove_col).setTextAlignment(Qt.AlignCenter)
        
        self.table.setStyleSheet("QTableWidget::item { color: #333; }")

        self.table.verticalHeader().setFixedWidth(0)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)   
        
        self.table.setMinimumWidth(1000)
        
        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)
        

        # Alternating row colors
        self.table.setAlternatingRowColors(True)

        # Selection behaviour
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.table)
        


        entry_layout = QVBoxLayout()
        entry_layout.setSpacing(10)

        
        ### --- calculate label 
        
        calculate_labels_layout = QHBoxLayout()
        
        gross_label = QLabel("Gross Amount")
        calculate_labels_layout.addWidget(gross_label, 1)
        
        discount_label = QLabel("Discount")
        calculate_labels_layout.addWidget(discount_label, 1)
        
        taxable_label = QLabel("Taxable")
        calculate_labels_layout.addWidget(taxable_label, 1)
        
        tax_236g_label = QLabel("Tax 236(G)")
        calculate_labels_layout.addWidget(tax_236g_label, 1)
        
        tax_236h_label = QLabel("Tax 236(H)")
        calculate_labels_layout.addWidget(tax_236h_label, 1)
        
        sales_tax_label = QLabel("Sales Tax")
        calculate_labels_layout.addWidget(sales_tax_label, 1)
        
        net_amount_label = QLabel("Net Amount")
        calculate_labels_layout.addWidget(net_amount_label, 1)
        
        cn_adjust_label = QLabel("CN Adjustment")
        calculate_labels_layout.addWidget(cn_adjust_label, 1)
        
        final_label = QLabel("Final Amount")
        calculate_labels_layout.addWidget(final_label, 1)
        
        self.final_amount = QLabel("0.0")
        calculate_labels_layout.addWidget(self.final_amount, 1)
        
        
        entry_layout.addLayout(calculate_labels_layout)
        # self.layout.addLayout(calculate_labels_layout)
        
        
        
        calculate_entry_layout = QHBoxLayout()
        
        self.gross_entry = QLabel("0.00")
        calculate_entry_layout.addWidget(self.gross_entry, 1)
        
        self.discount_entry = QLineEdit()
        calculate_entry_layout.addWidget(self.discount_entry, 1)
        
        self.taxable_entry = QLabel("0.00")
        calculate_entry_layout.addWidget(self.taxable_entry, 1)
        
        self.tax_236g_entry = QLineEdit()
        calculate_entry_layout.addWidget(self.tax_236g_entry, 1)
        
        self.tax_236h_entry = QLineEdit()
        calculate_entry_layout.addWidget(self.tax_236h_entry, 1)
        
        self.sales_tax_entry = QLineEdit()
        calculate_entry_layout.addWidget(self.sales_tax_entry, 1)
        
        self.net_amount_entry = QLabel("0.00")
        calculate_entry_layout.addWidget(self.net_amount_entry, 1)
        
        self.cn_adjustment_entry = QLineEdit()
        calculate_entry_layout.addWidget(self.cn_adjustment_entry, 1)
        
        self.paid_label = QLabel("Paid Amount")
        calculate_entry_layout.addWidget(self.paid_label, 1)
        
        self.paid_amount = QLineEdit()
        calculate_entry_layout.addWidget(self.paid_amount, 1)
        

        entry_layout.addLayout(calculate_entry_layout)
        # self.layout.addLayout(calculate_entry_layout)
        
        self.layout.addLayout(entry_layout)
        
        
        self.discount_entry.textChanged.connect(self.update_total_amount)
        self.tax_236g_entry.textChanged.connect(self.update_total_amount)
        self.tax_236h_entry.textChanged.connect(self.update_total_amount)
        self.sales_tax_entry.textChanged.connect(self.update_total_amount)
        self.cn_adjustment_entry.textChanged.connect(self.update_total_amount)
        
        self.paid_amount.textChanged.connect(self.calculate_payment)
        
        
        
        
        
        
        
        remaining_layout = QHBoxLayout()
        
        spacer_label = QLabel()
        remaining_layout.addWidget(spacer_label, 7)
        
        self.remaining_label = QLabel("Remaining Amount")
        remaining_layout.addWidget(self.remaining_label, 1)
        
        self.remainingdata = QLabel("0.00")
        self.remainingdata.setStyleSheet("font-weight: bold;")
        self.remainingdata.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        remaining_layout.addWidget(self.remainingdata, 1)
        
        self.writeoff_check = QCheckBox("Write-off Remaining")
        remaining_layout.addWidget(self.writeoff_check, 1)
        self.writeoff_check.setStyleSheet("QCheckBox { color: #333; }")
        
        self.layout.addLayout(remaining_layout)
        
        
        # === Save Button ===
        save_row = QHBoxLayout()
        addpurchase = QPushButton('Save Purchase Invoice', objectName='SaveButton')
        addpurchase.setCursor(Qt.PointingHandCursor)
        
        save_row.addWidget(addpurchase)
        self.layout.addLayout(save_row)
        
        addpurchase.clicked.connect(self.save_purchase)
        
        self.layout.addStretch()
        
        
        
        self.setStyleSheet(load_stylesheets())
        
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.add_row)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, activated=self.remove_row)
        
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.save_purchase)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.save_purchase)

        
        
        
        
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
        
        
        
        
        
        
    def populate_label_line(self):
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        
        label_style = """

            QLabel {
                margin: 0;
                padding: 0;
            }
            
            QLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                background-color: #f9f9f9;
            }
            QComboBox {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                background-color: #f9f9f9;
            }
            KeyUpLineEdit {
                margin: 0;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                background-color: #f9f9f9;
            }   
            
            
        """
        
        
        label_line = QHBoxLayout()

        
        product_label = QLabel("Enter Product")
        product_label.setStyleSheet(label_style)
        label_line.addWidget(product_label, 3)
        
        qty_label = QLabel("Qty (Pack)")
        qty_label.setStyleSheet(label_style)
        label_line.addWidget(qty_label, 1)

        bonus_label = QLabel("Bonus (Pack)")
        bonus_label.setStyleSheet(label_style)
        label_line.addWidget(bonus_label, 1)

        rate_label = QLabel("Pack Cost")
        rate_label.setStyleSheet(label_style)
        label_line.addWidget(rate_label, 1)
        
        batch_label = QLabel("Batch")
        # rate_label.setFixedWidth(100)
        batch_label.setStyleSheet(label_style)
        label_line.addWidget(batch_label, 1)
        
        expiry_label = QLabel("Expiry")
        # rate_label.setFixedWidth(100)
        expiry_label.setStyleSheet(label_style)
        label_line.addWidget(expiry_label, 1)
        
        discount_label = QLabel("Discount %")
        # rate_label.setFixedWidth(200)
        discount_label.setStyleSheet(label_style)
        label_line.addWidget(discount_label, 1)
        
        tax_label = QLabel("Tax %")
        # rate_label.setFixedWidth(200)
        tax_label.setStyleSheet(label_style)
        label_line.addWidget(tax_label, 1)
        
        
        
        total_label = QLabel("Total")
        # total_label.setFixedWidth(100)
        total_label.setStyleSheet(label_style)
        label_line.addWidget(total_label, 1)
        
        add_button_label = QLabel()
        add_button_label.setStyleSheet(label_style)
        label_line.addWidget(add_button_label, 1)
        
        



        entry_line = QHBoxLayout()
        
        
        self.item = QComboBox()
        self.item.wheelEvent = lambda event: event.ignore()
        self.item.setPlaceholderText("select product")
        self.item.setEditable(True)
        
        self.item.lineEdit().editingFinished.connect(lambda c=self.item: self.handle_editing_finished(c))
        
        completer = QCompleter()
        self.item.setCompleter(completer)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        
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
                background-color: #0078d7;
                color: white;
            }
        """)


        self.item.lineEdit().textEdited.connect(lambda: self.load_product_suggestions(self.item, completer))
        
        
        
        
        self.item.setStyleSheet(label_style)
        entry_line.addWidget(self.item, 3)
        
        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText("qty")
        self.qty_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.qty_edit, 1)
        
        self.qty_edit.textChanged.connect(self.update_total_amount)
        
        self.bonus_edit = QLineEdit()
        self.bonus_edit.setPlaceholderText("bonus")
        self.bonus_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.bonus_edit, 1)
        
        self.rate_edit = QLineEdit()
        self.rate_edit.setPlaceholderText("rate")
        self.rate_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.rate_edit, 1)
        
        self.batch_edit = QLineEdit()
        self.batch_edit.setPlaceholderText("batch")
        self.batch_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.batch_edit, 1)
        
        
        self.expiry_edit = QDateEdit()
        self.expiry_edit.setCalendarPopup(True)
        self.expiry_edit.setDisplayFormat("dd MMM yyyy")
        self.expiry_edit.setMinimumDate(QDate.currentDate())
        self.expiry_edit.setDate(self.expiry_edit.minimumDate()) 

        self.expiry_edit.setStyleSheet("""
            QDateEdit {
                padding: 4px;
            }

            QCalendarWidget QWidget {
                background-color: white;
                color: black;
            }

            QCalendarWidget QAbstractItemView {
                selection-background-color: #0078d7;
                selection-color: white;
                color: black;
            }

            QCalendarWidget QToolButton {
                background: none;
                color: black;
            }
        """)
        
        entry_line.addWidget(self.expiry_edit, 1)
        
        
        self.discount_edit = KeyUpLineEdit()
        self.discount_edit.setPlaceholderText("% Disc")
        self.discount_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.discount_edit, 1)
        
        self.tax_edit = KeyUpLineEdit()
        self.tax_edit.setPlaceholderText("% Tax")
        self.tax_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.tax_edit, 1)
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setReadOnly(True)
        self.amount_edit.setText("0.00")
        self.amount_edit.setStyleSheet("font-weight: bold;")
        self.amount_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.amount_edit, 1)
        
        
        
        self.rate_edit.textChanged.connect(self.update_line_total)
        self.qty_edit.textChanged.connect(self.update_line_total)
        self.discount_edit.textChanged.connect(self.update_line_total)
        self.tax_edit.textChanged.connect(self.update_line_total)

        
        
        add_button = QPushButton("Add", objectName="SaveButton")
        entry_line.addWidget(add_button, 1)
        
        add_button.clicked.connect(self.add_row)
        
        
        info_layout.addLayout(label_line)
        info_layout.addLayout(entry_line)
        
        
        
        self.layout.addLayout(info_layout)

        
    
    
        
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
        
        product = combo
        index = self.table.indexAt(product.pos())
        row = index.row()
        col = index.column()
        data = product.currentData()
        text = product.currentText()
        
        print(f"Current data is {data} and text is {text} at row {row}, col {col}")
        
        if data is None:
            self.new_product = product.currentText()
            
            if self.new_product.strip() != "":
                self.add_new_product_dialog(combo, new_product=self.new_product)

        
    
    
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
        remove_btn.setCursor(Qt.PointingHandCursor)#
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
        
        

    
    
        

    def remove_row(self, target_row):
        
        self.table.removeRow(target_row)

        # Reconnect all remove buttons with updated row numbers
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 10)
            if isinstance(widget, QPushButton):
                widget.clicked.disconnect()
                widget.clicked.connect(lambda _, r=row: self.remove_row(r))

        
        self.update_total_amount()
        
        

    def showEvent(self, event):
        super().showEvent(event)
        self.populate_suppliers()
        


    def populate_suppliers(self):
        
        self.supplier_edit.blockSignals(True)
        
        self.supplier_edit.clear()
        
        query = QSqlQuery()
        
        if query.exec("SELECT id, name FROM supplier WHERE status = 'active';"):
            
            while query.next():
                supplier_id = query.value(0)
                supplier_name = query.value(1)
                self.supplier_edit.addItem(supplier_name, supplier_id)  # Text shown, ID stored as data
            

        else:
            QMessageBox.information(None, 'Error', query.lastError().text() )
        
        self.supplier_edit.blockSignals(False)
        self.populate_reps()
        
        
        
        
    def populate_reps(self):
        
        supplier = self.supplier_edit.currentData()
        if supplier is None:
            return
        
        self.rep_edit.clear()
        
        query = QSqlQuery()
        query.prepare("SELECT id, name FROM rep WHERE supplier_id = ?;")
        query.addBindValue(supplier)
        
        if query.exec():
            while query.next():
                rep_id = query.value(0)
                rep_name = query.value(1)
                
                self.rep_edit.addItem(rep_name, rep_id)  # Text shown, ID stored as data
            
        else:
            QMessageBox.information(None, 'Error', query.lastError().text())
        
    
    
    
    def save_purchase(self):
        
        
        confirmation = QMessageBox.question(
                            self,
                            "Confirm Save",
                            "Would you like to save the Purchase Order?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
        
        
        if confirmation:
            
            db = QSqlDatabase.database()
            db.transaction()
            
            try: 
            
                supplier = self.supplier_edit.currentData()
                supplier = int(supplier)
                rep = self.rep_edit.currentData()
                if rep is not None:
                    rep = int(rep)
                
                if supplier is None or rep is None:
                    
                    QMessageBox.warning(None, "Error", "Please select a supplier and a seller representative.")
                    return
                
                sellerinvoice = self.invoice_edit.text()
                
                if not sellerinvoice:
                    
                    QMessageBox.warning(None, "Error", "Please enter a seller invoice number.")
                    return
                
                subtotal = self.gross_entry.text()
                discount = self.discount_entry.text()
                
                taxable = self.taxable_entry.text()
                
                tax_236g = self.tax_236g_entry.text()
                tax_236h = self.tax_236h_entry.text()
                sales_tax = self.sales_tax_entry.text()
                
                netamount = self.net_amount_entry.text()
                cn_adjustment = self.cn_adjustment_entry.text()
                final_amount = self.final_amount.text()
                
                paid = self.paid_amount.text()
                remaining = self.remainingdata.text()
                
                
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
                
                
                
                # calculating header net amount
                header_net_amount = ( - discount - tax_236g + tax_236h + sales_tax - cn_adjustment )
                
                print("Header Net Amount: ", header_net_amount)
                
                
                # visualize data
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

                    
                
            
                query = QSqlQuery()
                
                query.prepare("""
                            INSERT INTO purchase (supplier, rep, sellerinvoice, subtotal, discount, tax_236g, tax_236h, salestax,
                            netamount, cn_adjustment, total, paid, remaining, writeoff, payable, receiveable)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """)
                        
                query.addBindValue(supplier)
                query.addBindValue(rep)
                query.addBindValue(sellerinvoice)
                
                query.addBindValue(subtotal)
                query.addBindValue(discount)
                query.addBindValue(tax_236g)
                query.addBindValue(tax_236h)
                query.addBindValue(sales_tax)
                query.addBindValue(netamount)
                query.addBindValue(cn_adjustment)
                query.addBindValue(final_amount)
                query.addBindValue(paid)
                query.addBindValue(remaining)
                query.addBindValue(writeoff)
                query.addBindValue(payable)
                query.addBindValue(receivable)
                
                print("Prepared Query: ", query.lastQuery())
                    
                if not query.exec():
                    print("Insert failed:", query.lastError().text())
                    db.rollback()
                    raise Exception("Purchase insert failed")
                else:
                    QMessageBox.information(None, "Success", 'Purchase Record Saved Successfully')
                    purchase_id = query.lastInsertId()
                    print("Successfully inserted purchase record with ID:", purchase_id)
                
                
            
                #####################################
                ####    PURCHASE TRANSACTIONS    ####
                #####################################
                
                
                supplier_query = QSqlQuery()
                supplier_query.prepare("SELECT payable, receiveable FROM supplier where id = ?")
                supplier_query.addBindValue(supplier)
                
                if supplier_query.exec() and supplier_query.next():
                    
                    supplier_payable = supplier_query.value(0)
                    supplier_receiveable = supplier_query.value(1)

                    supplier_payable = float(supplier_payable)
                    supplier_receiveable = float(supplier_receiveable)
                                
                else:
                    
                    print("Error ", supplier_query.lastError().text())
                    QMessageBox.critical(self, "Error", "Supplier not found or database error.")
                    raise Exception
                
                
                # transaction_type = 'purchase'
                # ref_no = purchase_id
                # return_ref = None
                
                # if remaining > 0.0 :
                #     current_payable = remaining
                #     current_receivable = 0.00
                # elif remaining < 0.0:
                #     current_payable = 0.00
                #     current_receivable = abs(remaining)
                # else:
                #     current_payable = 0.00
                #     current_receivable = 0.00
                    
                # print("Current Payable: ", current_payable)
                # print("Current Receivable: ", current_receivable)
                    
                
                # payable_before = supplier_payable
                # due_now = total
                # paid_now = paid
                # remaining_now = remaining
                # payable_after = payable_before + current_payable
                
                # receiveable_before = supplier_receiveable
                # receiveable_now = current_receivable
                # received_now = 0.00
                # remaining_now = 0.00
                # receiveable_after = receiveable_before + current_receivable
                
                
                
                transaction_type = 'PURCHASE'
                ref_no = purchase_id
                return_ref = None

                current_payable = 0.0
                current_receivable = 0.0

                if remaining > 0.0:
                    current_payable = remaining
                elif remaining < 0.0:
                    current_receivable = abs(remaining)

                payable_before = supplier_payable
                payable_after = payable_before + current_payable

                receivable_before = supplier_receiveable
                receivable_after = receivable_before + current_receivable

                due_amount = total
                paid_now = paid          # paid at purchase time
                remaining_due = remaining

                received = 0.0          # for PURCHASE transaction
                remaining_now = 0.0       # for PURCHASE transaction
                
                
                # insert transaction
                query = QSqlQuery()
                query.prepare("""
                            INSERT INTO supplier_transaction 
                            (supplier, transaction_type, ref, return_ref,
                            payable_before, due_amount, paid, remaining_due, payable_after,
                            receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                            rep) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            
                            """)
                
                query.addBindValue(supplier)
                query.addBindValue(transaction_type)
                query.addBindValue(ref_no)
                query.addBindValue(return_ref)
                
                query.addBindValue(payable_before)
                query.addBindValue(due_amount)
                query.addBindValue(paid_now)
                query.addBindValue(remaining_due)
                query.addBindValue(payable_after)
                
                query.addBindValue(receivable_before)
                query.addBindValue(current_receivable)
                query.addBindValue(received)
                query.addBindValue(remaining_now)
                query.addBindValue(receivable_after)
                query.addBindValue(rep)
                
                
                if query.exec():
                    
                    insert_id = query.lastInsertId()
                    print("Purchase Transaction is saved ...")
                    QMessageBox.information(None, "Success", "Supplier Transaction Stored Successfully with ID: " + str(insert_id) )
                    
                    
                else:
                    
                    QMessageBox.critical(None, "Error", query.lastError().text())
                    print("Query error:", query.lastError().text())
                    raise Exception 
                
                
                
                
                
                
                supplier_query = QSqlQuery()
                supplier_query.prepare("SELECT payable, receiveable FROM supplier where id = ?")
                supplier_query.addBindValue(supplier)
                
                if supplier_query.exec() and supplier_query.next():
                    
                    supplier_payable = supplier_query.value(0)
                    supplier_receiveable = supplier_query.value(1)

                    supplier_payable = float(supplier_payable)
                    supplier_receiveable = float(supplier_receiveable)
                                
                else:
                    
                    print("Error ", supplier_query.lastError().text())
                    QMessageBox.critical(self, "Error", "Supplier not found or database error.")
                    raise Exception
                
                print("Payable and Receiveable are : ", supplier_payable, supplier_receiveable)
                
                supplier_payable = supplier_payable + current_payable
                supplier_receiveable = supplier_receiveable + current_receivable
                
                update_supplier = QSqlQuery()
                update_supplier.prepare("UPDATE supplier SET payable = ? , receiveable = ? WHERE id = ?")
                
                update_supplier.addBindValue(supplier_payable)
                update_supplier.addBindValue(supplier_receiveable)
                update_supplier.addBindValue(supplier)
                
                print("New Payable and Receiveable are : ", supplier_payable, supplier_receiveable)
                
                if update_supplier.exec(): 
                    
                    print("Supplier Balance updated successfully")
                
                else:
                    QMessageBox.critical(self, "Error", update_supplier.lastError().text())
                    raise Exception
                
                
                
                
                item_exist = False
                

                for row in range(self.table.rowCount()):
                    
                    print("Row number is:", row)
                    print("Rows text and data is ", self.table.cellWidget(row, 1).currentText(), self.table.cellWidget(row, 1).currentData())
                    
                    product_widget = self.table.cellWidget(row, 1)
                    
                    if not product_widget or not product_widget.currentData():
                        print("Row is empty ... ignoring it...")
                        continue

                    product_id = product_widget.currentData()
                    item_exist = True
                    
                    try:
                        
                        batch = self.table.cellWidget(row, 2).text()
                        expiry = self.table.cellWidget(row, 3).text()
                        print("Expiry is ", expiry)
                        
                        # convert string to date
                        expiry = expiry.strip()
                        
                        if expiry == '': 
                            expiry = None
                        
                        if expiry is not None:
                            
                            expiry = datetime.strptime(expiry, "%d-%m-%Y").date()
                            current_date = datetime.now().date()
                            
                            print("Current Date is: ", current_date)
                            
                            if expiry <= current_date:
                                expiry = None
                            else:
                                # convert date to string in yyyy-mm-dd format for database
                                expiry = expiry.strftime("%Y-%m-%d")

                        
                        print("Processed expiry date is: ", expiry)
                        
                        
                        qty = int(self.table.cellWidget(row, 4).text())
                        bonus = int(self.table.cellWidget(row, 5).text())
                        rate = float(self.table.cellWidget(row, 6).text())
                        discount = float(self.table.cellWidget(row, 7).text())
                        tax = float(self.table.cellWidget(row, 8).text())
                        line_total = float(self.table.cellWidget(row, 9).text())
                        
                        # convert discount and tax into flat values
                        discount_amount = (qty * rate) * (discount / 100)
                        tax_amount = ((qty * rate) - discount_amount) * (tax / 100)
                        
                        print(f"Calculated discount amount: {discount_amount} and tax amount: {tax_amount} for row {row}")
                        
                        
                        if bonus == '': 
                            bonus = 0

                    except Exception as e:
                        
                        QMessageBox.information(self, 'Error', str(e))
                        print("Invalid data in row", row, "- skipping this row")


                    # ✅ Insert purchase item
                    item_query = QSqlQuery()
                    item_query.prepare("""
                        INSERT INTO purchaseitem (purchase, product, qty, bonus, rate, discount, tax, total)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """)
                    
                    item_query.addBindValue(purchase_id)
                    item_query.addBindValue(product_id)
                    item_query.addBindValue(qty)
                    item_query.addBindValue(bonus)
                    item_query.addBindValue(rate)
                    item_query.addBindValue(discount_amount)
                    item_query.addBindValue(tax_amount)
                    item_query.addBindValue(line_total)

                    if not item_query.exec():
                        print("Error inserting purchaseitem:", item_query.lastError().text())
                    
                    else:
                        print("Purchase item inserted successfully")
                        item = item_query.lastInsertId()
                        
                        
                    
                    # get product packsize from price_pack
                    product_query = QSqlQuery()
                    product_query.prepare("SELECT pack_size FROM price_pack WHERE product_id = ?")
                    product_query.addBindValue(product_id)
                    
                    if not product_query.exec():
                        print("Error fetching pack size:", product_query.lastError().text())
                        db.rollback()
                        raise Exception("Failed to fetch pack size for product ID: " + str(product_id))
                    
                    pack_size = 1
                    if product_query.next():
                        pack_size = int(product_query.value(0))
                        
                        
                    print("line total is: ", line_total)
                    print("subtotal is: ", subtotal)

                    if subtotal > 0:
                        proportion = line_total / subtotal
                        allocated_header = proportion * header_net_amount
                    else:
                        allocated_header = 0.0
                    
                    
                    final_line_total = line_total + allocated_header
                    
                    # convert packs into units
                    qty = qty * pack_size
                    bonus = bonus * pack_size
                    
                    paid_qty = qty
                    total_qty = qty + bonus
                    
                    
                    print("Final Line Total is: ", final_line_total)
                    print("Total Quantity (including bonus) is: ", total_qty)
                    
                    if total_qty > 0:
                        unit_cost = final_line_total / total_qty 
                    else:
                        unit_cost = 0.0
                    
                    unit_cost = round(unit_cost, 4)

                    print("Effective Unit Cost is: ", unit_cost)
                    
                    # insert Batch info if available
                    batch_query = QSqlQuery()
                    batch_query.prepare("""
                        INSERT INTO batch (batch_no, expiry_date, product_id, total_received, paid_qty, quantity_remaining, unit_cost, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """)
                    batch_query.addBindValue(batch)
                    batch_query.addBindValue(expiry)
                    batch_query.addBindValue(product_id)
                    batch_query.addBindValue(total_qty)
                    batch_query.addBindValue(paid_qty)
                    batch_query.addBindValue(total_qty)
                    batch_query.addBindValue(unit_cost)
                    batch_query.addBindValue('PURCHASE')

                    if not batch_query.exec():
                        db.rollback()
                        raise Exception("Batch insert failed: " + batch_query.lastError().text())
                        
                    else:
                        print("Batch record inserted successfully")
                        


                if not item_exist:
                    QMessageBox.warning(None, "Error", "No valid items found in the purchase order. Please add items before saving.")
                    db.rollback()
                    return
                
                print("All items processed successfully")
            
            
            except Exception as e:
                print("An error occurred:", str(e))
                QMessageBox.critical(None, "Error", f"An error occurred while saving the purchase: {str(e)}")
                db.rollback()
            
            else:
                db.commit()
                print("Transaction committed successfully")
                QMessageBox.information(None, "Success", "Purchase saved successfully")
                self.clear_fields()
            
            finally:
                print("Database connection closed")
        
      
        
        
    def load_product_suggestions(self, item, completer):
        
        item = item
        completer = completer
        current_text = item.currentText() 
        print("Current Text is: ", current_text)
        
        if current_text == '':
            item.setCurrentIndex(-1)
            return 
        
        query = QSqlQuery()
        query.prepare("SELECT id, display_name FROM product WHERE display_name LIKE ? LIMIT 10")
        print("Current Text is: ", current_text)
        query.addBindValue(f"%{current_text}%")
        
        products = []
        
        if not query.exec():
            
            print("Something wrong happened...")
        
        else:
        
            while query.next():
                
                product_id = query.value(0)
                name = query.value(1)
                
                label = f"{name}".strip()
                products.append(label)
                item.addItem(label, product_id)
                
        print(products)

        
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        data = products
        model = QStringListModel()
        model.setStringList(data)
        
        
        completer.setModel(model)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        item.setCompleter(completer)
        
        completer.highlighted[str].connect(partial(self.on_completer_highlighted, item=item))

        print("Setting Current Text")
        item.lineEdit().setText(current_text)        
        

    def on_completer_highlighted(self, text, item):
        
        index = item.findText(text, Qt.MatchFixedString)
        if index >= 0:
            item.setCurrentIndex(index) 
        
        

    def on_item_selected(self, item):
        
        text = item.currentText()
        data = item.currentData()

        
        print("Selected text is: ",text, data)
        data = int(data)
        
        
        print("Data is: ", data)
        
        query = QSqlQuery()
        query.prepare("""
            SELECT * FROM product
            WHERE id = ? """)
        
        query.addBindValue(data)
        
        if not query.exec():
            
            print("Cannot Get the product")
            
        else:
            
            print("Got the product")
                
                



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
        
        self.populate_suppliers()
        
       


    def pay_method_change(self):
        """
        This method is called when the payment method is changed.
        It checks if payment method is available for that supplier.
        """
        # Get the selected payment method
        payment_method = self.payment_method_combo.currentText()
        
        # get the supplier_id
        supplier_id = self.supplier_edit.currentData()
        supplier_id = int(supplier_id)
        
        
        # Check if payment method is available for that supplier
        if payment_method == 'Bank Transfer':
            self.check_bank_transfer(supplier_id)
            
        if payment_method == 'JazzCash':
            self.check_jazzcash(supplier_id)

        if payment_method == "EasyPaisa":
            self.check_easypaisa(supplier_id)
            


    def add_new_product_dialog(self, combo, new_product=None):
        
        dialog = ImportDialog(self)
        
        dialog.name_input.setText(new_product)
        
        if dialog.exec() == QDialog.Accepted:
            
            print("New Product is: ", new_product)
            
            
            item_name = dialog.name_input.text()
            item_form = dialog.form_input.currentText()
            item_packing = dialog.packing_input.text()
            
            display_name = f"{item_name} {item_form} {item_packing}"
            
            brand = dialog.brand_input.text()
            packsize = dialog.packsize_input.text()
            saleprice = dialog.saleprice_input.text()
            
            # Insert Data into Database
            
            query = QSqlQuery()
            query.prepare("""
                INSERT INTO product (display_name, brand )
                VALUES (?, ?)
            """)
            
            query.addBindValue(display_name)
            query.addBindValue(brand)
            
            if not query.exec():
                
                QMessageBox.critical(None, "Error", query.lastError().text())
                print("Error inserting product:", query.lastError().text())
                
            else:
                
                QMessageBox.information(None, "Success", "Product added successfully")
                product_id = query.lastInsertId()
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
        self.form_input = QComboBox()
        self.form_input.addItems(['Tabs', 'Caps', 'Syrup', 'Inj'])
        item_layout.addWidget(self.form_input, stretch=1)

        # Packing input with stretch factor 1
        self.packing_input = QLineEdit()
        self.packing_input.setPlaceholderText('packing')
        item_layout.addWidget(self.packing_input, stretch=1)
        
        
        self.layout.addLayout(item_layout)
        
        
        
        # brand line
        
        brand_layout = QHBoxLayout()
        
        brand_label = QLabel("Brand")
        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.brand_input = QLineEdit()
        
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
        
        
        
        
         
    










