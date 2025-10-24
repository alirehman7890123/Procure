from PySide6.QtWidgets import QWidget, QCompleter, QVBoxLayout, QHBoxLayout, QFrame,  QStyledItemDelegate, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
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
        self.layout.addSpacing(20)
        
        
        
        
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


        # Purchse Table
        self.row_height = 40
        self.min_visible_rows = 5
        
    
        self.table = MyTable(column_ratios=[0.03, 0.25, 0.07, 0.10, 0.05, 0.05, 0.07, 0.05, 0.07, 0.05, 0.07, 0.10, 0.05])
        headers = ["#", "Product Description", "Batch", "Expiry", "Qty", "Bonus", "Rate", "Disc% ", "Amt", "Tax %", "Amt", "Total", "X"]
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
        
        
      
        # Fill initial rows
        for _ in range(5):
            
            self.add_row()
        
        self.table.currentCellChanged.connect(self.on_cell_focus)
        
        
        # === Add Row Button ===
        add_button_row = QHBoxLayout()
        self.add_button = QPushButton("Add Row", objectName='TopRightButton')
        
        self.add_button.clicked.connect(self.add_row)
        add_button_row.addWidget(self.add_button, stretch=1)
        self.layout.addLayout(add_button_row)
        
        
        
        
        
        
        # Cacluation Layout
        
        calculation_layout = QHBoxLayout()
        
        left_wrapper_widget = QWidget()
        left_layout = QVBoxLayout()
        left_wrapper_widget.setLayout(left_layout)
        
        subtotal_row = QHBoxLayout()
        subtotal = QLabel("Sub Total")
        self.subtotaldata = QLabel("0.00")

        subtotal_row.addWidget(subtotal, 1)
        subtotal_row.addWidget(self.subtotaldata, 2)

        left_layout.addLayout(subtotal_row)
        left_layout.addSpacing(5)
        
        discount_row = QHBoxLayout()
        discount = QLabel("Discount")
        self.percentage = KeyUpLineEdit()
        self.percentage.setPlaceholderText(" Disc % ")
        self.flatdiscount = KeyUpLineEdit()
        self.flatdiscount.setPlaceholderText("Flat")
        discount_row.addWidget(discount, 1)
        discount_row.addWidget(self.percentage, 1)
        discount_row.addWidget(self.flatdiscount, 1)
        left_layout.addLayout(discount_row)
        
        self.percentage.keyReleased.connect(self.percentage_discount)
        self.flatdiscount.keyReleased.connect(self.flat_discount)
        
        
        netamount_row = QHBoxLayout()
        net_amount = QLabel("Net Amount")
        self.net_amountdata = QLabel("0.00")
        netamount_row.addWidget(net_amount, 1)
        netamount_row.addWidget(self.net_amountdata, 2)
        left_layout.addLayout(netamount_row)
        
        
        tax_row = QHBoxLayout()
        taxlabel = QLabel("Tax")
        self.taxedit = KeyUpLineEdit()
        self.taxedit.setPlaceholderText("Tax %")
        self.taxamount = QLabel("0.00")
        tax_row.addWidget(taxlabel, 1)
        tax_row.addWidget(self.taxedit, 1)
        tax_row.addWidget(self.taxamount, 1)
        left_layout.addLayout(tax_row)
        self.taxedit.keyReleased.connect(self.calculate_tax)
        
        left_layout.addSpacing(15)
        
        total_row = QHBoxLayout()
        lefttotal = QLabel("Total")
        self.lefttotaldata = QLabel("0.00")

        total_row.addWidget(lefttotal, 1)
        total_row.addWidget(self.lefttotaldata, 2)
        
        left_layout.addLayout(total_row)
        
        
        right_wrapper_widget = QWidget()
        right_layout = QVBoxLayout()
        right_wrapper_widget.setLayout(right_layout)
        
        
        right_total_row = QHBoxLayout()
        right_total = QLabel("Total")
        self.right_totaldata = QLabel("0.00")
        right_total_row.addWidget(right_total, 1)
        right_total_row.addWidget(self.right_totaldata, 2)
        right_layout.addLayout(right_total_row)
        right_layout.addSpacing(5)


        roundoff_row = QHBoxLayout()
        roundofflabel = QLabel("Roundoff")
        self.roundoffdata = QLabel("0.00")
        roundoff_row.addWidget(roundofflabel, 1)
        roundoff_row.addWidget(self.roundoffdata, 2)
        right_layout.addLayout(roundoff_row)


        final_amount_row = QHBoxLayout()
        final_amount = QLabel("Final Amount")
        self.final_amountdata = QLabel("0.00")
        final_amount_row.addWidget(final_amount, 1)
        final_amount_row.addWidget(self.final_amountdata, 2)
        right_layout.addLayout(final_amount_row)
        
        
        payment_method_row = QHBoxLayout()
        payment_method_label = QLabel("Payment Method")
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "On Credit", "Bank Transfer", "JazzCash", "EasyPaisa"])
        self.payment_method_combo.currentIndexChanged.connect(self.pay_method_change)
        
        payment_method_row.addWidget(payment_method_label, 1)
        payment_method_row.addWidget(self.payment_method_combo, 2)
        right_layout.addLayout(payment_method_row)


        
        payment_row = QHBoxLayout()
        paidlabel = QLabel("Paid Amount")
        self.paidedit = QLineEdit()
        payment_row.addWidget(paidlabel, 1)
        payment_row.addWidget(self.paidedit, 2)
        right_layout.addLayout(payment_row)

        self.paidedit.textChanged.connect(self.calculate_payment)
        
        
        remaining_row = QHBoxLayout()
        remaininglabel = QLabel("Remaining")
        self.remainingdata = QLabel("0.00")
        self.checkbox = QCheckBox("Write off")
        self.checkbox.setStyleSheet("color: #333;")
        self.checkbox.toggled.connect(self.writeoffcheck)
        remaining_row.addWidget(remaininglabel, 1)
        remaining_row.addWidget(self.remainingdata, 1)
        remaining_row.addWidget(self.checkbox, 1)
        right_layout.addLayout(remaining_row)
        
        

        calculation_layout.addWidget(left_wrapper_widget)
        calculation_layout.addWidget(right_wrapper_widget)
        self.layout.addLayout(calculation_layout)
        
        
        note_row = QHBoxLayout()
        
        self.note = QLabel("Note")
        self.note_edit = QLineEdit()
        note_row.addWidget(self.note, 1)
        note_row.addWidget(self.note_edit, 3)
        
        self.layout.addLayout(note_row)
        
        
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

        
        

        
    
    
    def writeoffcheck(self):
        
        remaining = self.remainingdata.text()
        remaining = float(remaining) if remaining else 0
        
        if remaining > 0:
            
            if self.checkbox.isChecked():
                
                self.note.setText(f"Amount {remaining} will be wrote-off / Cleared")
            else:
                self.note.setText(f"Amount {remaining} will be added to payable")
        
        else:
            
            self.note.setText(f"Amount {remaining} is excessive and will be added to receiveable")    
    
    
    
    
    def percentage_discount(self):
        
        print("Running Percentage Discount")
        
        subtotal = self.subtotaldata.text()
        subtotal = float(subtotal) if subtotal else 0
        
        discount = self.percentage.text()
        discount = float(discount) if discount else 0
        
        print("Subtotal is: ", subtotal, " percentage discount is; ", discount )
        amount = subtotal * discount / 100
        print("Flat Dsicout is: ", amount)
        self.flatdiscount.setText(f"{amount:.2f}")
        
        self.update_total_amount()
        
        
        
        
    def flat_discount(self):
        
        print("Running Flat Discount")
        
        subtotal = self.subtotaldata.text()
        subtotal = float(subtotal) if subtotal else 0
        
        
        discount = self.flatdiscount.text()
        discount = float(discount) if discount else 0
        
        percentage = ( discount / subtotal ) * 100
        self.percentage.setText(f"{percentage:.2f}")
        
        self.update_total_amount()
        
        
        
    
    
    def calculate_tax(self):
        
        net_amount = self.net_amountdata.text()
        net_amount = float(net_amount) if net_amount else 0
        
        tax = self.taxedit.text()
        tax = float(tax) if tax else 0
        
        tax_amount = net_amount * tax / 100
        self.taxamount.setText(f"{tax_amount:.2f}")
        
        self.update_total_amount()
        
        

    def update_total_amount(self):
        
        
        subtotal = 0.00
        for row in range(self.table.rowCount()):
            
            linetotal = self.table.cellWidget(row, 11).text()
            
            
            if linetotal:
                try:
                   
                    value = float(linetotal)
                    subtotal = subtotal + value
                    
                except ValueError:
                    pass  # skip empty or invalid cells
                
            else:
                continue
                
        self.subtotaldata.setText(f"{subtotal:.2f}")
        
        discount = self.flatdiscount.text()
        print("Discount is: ", discount)
        discount = float(discount) if discount else 0
        netamount = subtotal - discount
        
        # set Net Amount 
        self.net_amountdata.setText(f"{netamount:.2f}")
        
        
        
        tax = self.taxedit.text()
        tax = float(tax) if tax else 0
        
        taxamount = netamount * tax/100
        self.taxamount.setText(f"{taxamount:.2f}")
        
        total = netamount + taxamount
        self.lefttotaldata.setText(f"{total:.2f}")
        
        # set Right Side Total
        self.right_totaldata.setText(f"{total:.2f}")
        
        
        rounded_total = math.floor(total)
        roundoff = round(total - rounded_total, 2)
        print("round off is: ", roundoff)
        # set Round off
        
        finaltotal = rounded_total
        
        self.roundoffdata.setText(f"{roundoff:.2f}")
        self.final_amountdata.setText(f"{finaltotal:.2f}")
        


    def calculate_payment(self):
        
        finalamount = self.final_amountdata.text()
        finalamount = float(finalamount) if finalamount else 0.00
        
        paid = self.paidedit.text()
        paid = float(paid) if paid else 0.00
        
        remaining = finalamount - paid
        self.remainingdata.setText(str(remaining))
        
        self.writeoffcheck()
         
    
         
    def eventFilter(self, obj, event):
        if isinstance(obj, QComboBox) and event.type() == QEvent.FocusOut:
            
            index = self.table.indexAt(obj.pos())
            row = index.row()
            col = index.column()
            print(f"ComboBox at row {row}, col {col} lost focus: {obj.currentText()}")
            
            obj.addItem('Paracetamol', 23)            
            
        
        return super().eventFilter(obj, event)

       
    
    
    def add_row(self):
        
        row = self.table.rowCount()
        
        self.table.insertRow(row)
        
        self.table.setRowHeight(row, self.row_height)
        
        counter = QLabel(str(row + 1))
        counter.setAlignment(Qt.AlignCenter)

        
        dummy_item1 = QTableWidgetItem()
        dummy_item1.setFlags(Qt.NoItemFlags)
        self.table.setItem(row, 1, dummy_item1)

        product = QComboBox()
        product.setPlaceholderText("select product")
        
        product.setEditable(True)
        product.wheelEvent = lambda event: event.ignore()
        
        product.installEventFilter(self)
        
        
        
        completer = QCompleter()
        product.setCompleter(completer)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        
        product.lineEdit().completer().popup().setStyleSheet("""
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


        product.lineEdit().textEdited.connect(lambda: self.load_product_suggestions(product, completer))

        
        batch = QLineEdit()
        batch.setPlaceholderText("Batch")
        
        expiry = QLineEdit()
        expiry.setInputMask("00-00-0000")
        expiry.setPlaceholderText("dd-mm-yyyy")
    
        
        qty_edit = QLineEdit()
        qty_edit.setPlaceholderText("qty")
        qty_edit.setText("0")
        
        bonus_edit = QLineEdit()
        bonus_edit.setPlaceholderText("bonus")
        bonus_edit.setText("0")
        
        rate_edit = QLineEdit()
        rate_edit.setPlaceholderText("rate")
        rate_edit.setText("0.00")
        
        
        discount = KeyUpLineEdit()
        discount.setText("0")
        
        discount_amount = KeyUpLineEdit()
        discount_amount.setReadOnly(True)
        discount_amount.setStyleSheet("background-color: #ccc")
        discount_amount.setText("0.0")
        
        tax = QLineEdit()
        tax.setText("0")
        
        tax_amount = QLineEdit()
        tax_amount.setReadOnly(True)
        tax_amount.setStyleSheet("background-color: #ccc")
        
        total_edit = QLineEdit()
        total_edit.setReadOnly(True)
        total_edit.setText("0.0")
        
        
        remove_btn = QPushButton("X")
        remove_btn.setCursor(Qt.PointingHandCursor)#
        remove_btn.setStyleSheet("color: #333;")
        
        
        self.table.setCellWidget(row, 0, counter)
        self.table.setCellWidget(row, 1, product)
        self.table.setCellWidget(row, 2, batch)
        self.table.setCellWidget(row, 3, expiry)
        self.table.setCellWidget(row, 4, qty_edit)
        self.table.setCellWidget(row, 5, bonus_edit)
        self.table.setCellWidget(row, 6, rate_edit)
        self.table.setCellWidget(row, 7, discount)
        self.table.setCellWidget(row, 8, discount_amount)
        self.table.setCellWidget(row, 9, tax)
        self.table.setCellWidget(row, 10, tax_amount)
        self.table.setCellWidget(row, 11, total_edit)
        self.table.setCellWidget(row, 12, remove_btn)
        
        dummy_item2 = QTableWidgetItem()
        dummy_item2.setFlags(Qt.NoItemFlags)  # Makes the cell unselectable
        self.table.setItem(row, 12, dummy_item2)
        
        qty_edit.textChanged.connect(lambda _: self.update_amount(qty_edit))
        rate_edit.textChanged.connect(lambda _: self.update_amount(rate_edit))
        
        discount.keyReleased.connect(lambda _: self.update_amount(discount))
        discount_amount.keyReleased.connect(lambda _:self.update_amount(discount_amount))
        tax.textChanged.connect(lambda _: self.update_amount(tax))
        
        remove_btn.clicked.connect(lambda _, r=row: self.remove_row(r))

        self.update_table_height()
        
        

    def remove_row(self, target_row):
        
        self.table.removeRow(target_row)

        # Reconnect all remove buttons with updated row numbers
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 4)
            if isinstance(widget, QPushButton):
                widget.clicked.disconnect()
                widget.clicked.connect(lambda _, r=row: self.remove_row(r))

        self.update_table_height()
        
        

    def update_table_height(self):
        
        row_count = self.table.rowCount()
        visible_rows = max(row_count, self.min_visible_rows)
        header_height = self.table.horizontalHeader().height()
        total_height = visible_rows * self.row_height + header_height + self.table.frameWidth() * 2 + 6
        self.table.setFixedHeight(total_height)
        
    
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
                rep = self.rep_edit.currentData()
                
                if supplier is None or rep is None:
                    
                    QMessageBox.warning(None, "Error", "Please select a supplier and a seller representative.")
                    return
                
                sellerinvoice = self.invoice_edit.text()
                
                if not sellerinvoice:
                    
                    QMessageBox.warning(None, "Error", "Please enter a seller invoice number.")
                    return
                
                subtotal = self.subtotaldata.text()
                discount = self.percentage.text()
                discountamount = self.flatdiscount.text()
                netamount = self.net_amountdata.text()
                tax = self.taxedit.text()
                taxamount = self.taxamount.text()
                totalaftertax = self.right_totaldata.text()
                roundoff = self.roundoffdata.text()
                total = self.final_amountdata.text()
                paid = self.paidedit.text()
                remaining = self.remainingdata.text()
                
                
                subtotal = float(subtotal) if subtotal else 0
                discount = float(discount) if discount else 0
                discountamount = float(discountamount) if discountamount else 0
                netamount = float(netamount) if netamount else 0
                tax = float(tax) if tax else 0
                taxamount = float(taxamount) if taxamount else 0
                totalaftertax = float(totalaftertax) if totalaftertax else 0
                roundoff = float(roundoff) if roundoff else 0
                total = float(total) if total else 0
                paid = float(paid) if paid else 0
                remaining = float(remaining) if remaining else 0
                
                
                if remaining == 0.0:
                    
                    writeoff = 0.0
                    payable = 0.0
                    receiveable = 0.0
                    
                elif remaining > 0.0 and self.checkbox.isChecked():
                    
                    writeoff = remaining
                    payable = 0.0
                    receiveable = 0.0
                    
                elif remaining > 0.0 and not self.checkbox.isChecked():
                    
                    writeoff = 0.0
                    payable = remaining
                    receiveable = 0.0
                    
                else:
                    
                    writeoff = 0.0
                    payable = 0.0
                    receiveable = abs(remaining)
                    
                
            
                query = QSqlQuery()
                
                query.prepare("""
                            INSERT INTO purchase (supplier, rep, sellerinvoice, subtotal, discount, discamount, netamount,
                            tax, taxamount, totalaftertax, roundoff, total, paid, remaining, writeoff, payable, receiveable)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """)
                        
                query.addBindValue(supplier)
                query.addBindValue(rep)
                query.addBindValue(sellerinvoice)
                
                query.addBindValue(subtotal)
                query.addBindValue(discount)
                query.addBindValue(discountamount)
                query.addBindValue(netamount)
                query.addBindValue(tax)
                query.addBindValue(taxamount)
                query.addBindValue(totalaftertax)
                query.addBindValue(roundoff)
                query.addBindValue(total)
                query.addBindValue(paid)
                query.addBindValue(abs(remaining))
                query.addBindValue(writeoff)
                query.addBindValue(payable)
                query.addBindValue(receiveable)
                
                print("Prepared Query: ", query.lastQuery())
                    
                if not query.exec():
                    print("Insert failed:", query.lastError().text())
                else:
                    QMessageBox.information(None, "Success", 'Purchase Record Saved Successfully')
                    purchase_id = query.lastInsertId()
                    
                
                
            
                
                
                
                    
                
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
                
                
                transaction_type = 'purchase'
                ref_no = purchase_id
                return_ref = None
                
                payable_before = supplier_payable
                due_amount = total
                paid = paid
                remaining_due = total - paid
                payable_after = payable_before + total - paid
                
                receiveable_before = supplier_receiveable
                receiveable_now = 0.00
                received = 0.00
                remaining_now = 0.00
                receiveable_after = receiveable_before
                
                
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
                query.addBindValue(paid)
                query.addBindValue(remaining_due)
                query.addBindValue(payable_after)
                query.addBindValue(receiveable_before)
                query.addBindValue(receiveable_now)
                query.addBindValue(received)
                query.addBindValue(remaining_now)
                query.addBindValue(receiveable_after)
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
                
                supplier_payable = supplier_payable + payable
                supplier_receiveable = supplier_receiveable + receiveable
                
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
                    
                    product_widget = self.table.cellWidget(row, 1)
                    
                    
                    if not product_widget or not product_widget.currentData():
                        print("Row is empty ... ignoring it...")
                        continue

                    product_id = product_widget.currentData()
                    
                    
                    item_exist = True
                    
                    try:
                        
                        batch = self.table.cellWidget(row, 2).text()
                        expiry = self.table.cellWidget(row, 3).text()
                        
                        qty = int(self.table.cellWidget(row, 4).text())
                        bonus = int(self.table.cellWidget(row, 5).text())
                        rate = float(self.table.cellWidget(row, 6).text())
                        discount = float(self.table.cellWidget(row, 7).text())
                        discountamount = float(self.table.cellWidget(row, 8).text())
                        tax = float(self.table.cellWidget(row, 9).text())
                        taxamount = float(self.table.cellWidget(row, 10).text())
                        total = float(self.table.cellWidget(row, 11).text())

                    except Exception as e:
                        
                        QMessageBox.information(self, 'Error', str(e))
                        print("Invalid data in row", row, "- skipping this row")


                    # ✅ Insert purchase item
                    item_query = QSqlQuery()
                    item_query.prepare("""
                        INSERT INTO purchaseitem (purchase, product, qty, bonus, rate, discount, discountamount, tax, taxamount, total)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """)
                    
                    item_query.addBindValue(purchase_id)
                    item_query.addBindValue(product_id)
                    item_query.addBindValue(qty)
                    item_query.addBindValue(bonus)
                    item_query.addBindValue(rate)
                    item_query.addBindValue(discount)
                    item_query.addBindValue(discountamount)
                    item_query.addBindValue(tax)
                    item_query.addBindValue(taxamount)
                    item_query.addBindValue(total)

                    if not item_query.exec():
                        print("Error inserting purchaseitem:", item_query.lastError().text())
                    
                    else:
                        print("Purchase item inserted successfully")
                        item = item_query.lastInsertId()
                        
                        
                    if batch != '':
                        
                        print("EXPIRY IS....  is: ", expiry)
                        
                        # insert Batch info if available
                        batch_query = QSqlQuery()
                        batch_query.prepare("""
                            INSERT INTO batch (purchaseitem, product, batch, expiry)
                            VALUES (?, ?, ?, ?)
                        """)
                        batch_query.addBindValue(item)
                        batch_query.addBindValue(product_id)
                        batch_query.addBindValue(batch)
                        batch_query.addBindValue(expiry)
                        
                        if not batch_query.exec():
                            
                            print("Error inserting batch:", batch_query.lastError().text())
                            
                        else:
                            print("Batch record inserted successfully")
                        
                        

                    # ✅ Check and update stock
                    stock_query = QSqlQuery()
                    stock_query.prepare("SELECT packsize, units FROM stock WHERE product = ?")
                    
                    stock_query.addBindValue(product_id)


                    if stock_query.exec() and stock_query.next():
                        
                        packsize = stock_query.value(0)
                        units = stock_query.value(1)
                        
                        newunits = int(units) + int(qty) * int(packsize)
                        

                        update_query = QSqlQuery()
                        
                        update_query.prepare("UPDATE stock SET units = ? WHERE product = ?")
                        
                        update_query.addBindValue(newunits)
                        update_query.addBindValue(product_id)

                        if update_query.exec():
                            
                            print("Stock updated successfully")
                            print(f"Row {row}: product_id={product_id}, qty={qty}, rate={rate}, total={total}")

                            cost_query = QSqlQuery()
                            cost_query.prepare("""
                                INSERT INTO stockcost(product, qty, totalcost, stocktype)
                                VALUES (?, ?, ?, ?)
                            """)
                            cost_query.addBindValue(product_id)
                            cost_query.addBindValue(str(qty))
                            cost_query.addBindValue(str(total))
                            cost_query.addBindValue('purchased')

                            if not cost_query.exec():
                                print("Error inserting stockcost:", cost_query.lastError().text())
                            else:
                                print("Stock Cost saved successfully")
                                self.clear_fields()
                        else:
                            print("Failed to update stock:", update_query.lastError().text())
                    else:
                        print("Stock record not found for product_id:", product_id)            
                        self.clear_fields()
                        print("Table and fields are cleared")
                        
                        
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
            
            finally:
                print("Database connection closed")
        
        
        
    def load_product_suggestions(self, item, completer):
        
        item = item
        completer = completer
        current_text = item.currentText() 
        print("Current Text is: ", current_text)
        
        if current_text == '':
            return 
        
        query = QSqlQuery()
        query.prepare("SELECT id, name, form, strength FROM product WHERE name LIKE ? LIMIT 10")
        print("Current Text is: ", current_text)
        query.addBindValue(f"%{current_text}%")
        
        products = []
        
        if not query.exec():
            
            print("Something wrong happened...")
        
        else:
        
            while query.next():
                
                product_id = query.value(0)
                name = query.value(1)
                form = query.value(2)
                strength = query.value(3)
                
                label = f"{name} {form} {strength}".strip()
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
                
                



    def update_amount(self, edited_widget):
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            
            qty_text = self.table.cellWidget(row, 4).text()
            bonus = self.table.cellWidget(row, 5).text()
            rate_text = self.table.cellWidget(row, 6).text()
            
            discount_edit = self.table.cellWidget(row,7).text()
            
            tax_edit = self.table.cellWidget(row,9).text()

            qty = int(qty_text) if qty_text else 0
            bonus = int(bonus) if bonus else 0
            rate = float(rate_text) if rate_text else 0
            
            discount = float(discount_edit) if discount_edit else 0
            
            tax = float(tax_edit) if tax_edit else 0
            
            if discount :
                discount = rate * discount / 100
                self.table.cellWidget(row, 8).setText(str(discount))
                
                
            flat_discount = self.table.cellWidget(row,8).text()
            flat_discount = float(flat_discount) if flat_discount else 0
            
            price = rate - flat_discount
            
            tax_amount = price * tax / 100
            
            self.table.cellWidget(row, 10).setText(str(tax_amount))
            
            price = price + tax_amount
            
            price = float(f"{price:.2f}")
            
            total = qty * price

            self.table.cellWidget(row, 11).setText(str(total))
            print("Updating Final Amount")
            self.update_total_amount()
            
        except ValueError:
        
            self.table.cellWidget(row, 11).setText("0.00")



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
        self.subtotaldata.clear()
        self.percentage.clear()
        self.flatdiscount.clear()
        
        self.net_amountdata.clear()
        self.taxedit.clear()
        self.taxamount.clear()
        self.right_totaldata.clear()
        self.roundoffdata.clear()
        self.final_amountdata.clear()
        self.lefttotaldata.clear()
        self.paidedit.clear()
        self.remainingdata.clear()
        
        self.checkbox.setChecked(False)        
        
        self.table.setRowCount(0)
        
        self.populate_suppliers()
        
        for _ in range(5):
            
            self.add_row()


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
            
    
    def check_bank_transfer(self, supplier_id):
        """
        This method is called when the payment method is changed to bank transfer.
        It checks if bank transfer is available for that supplier.
        """
        # Check if bank transfer is available for that supplier
        query = QSqlQuery()
        query.prepare("select count(*) from bank where supplier = ?")
        query.addBindValue(supplier_id)
        if query.exec() and query.next():
            bank_transfer = query.value(0)
            
            if bank_transfer > 0 :
                print("Bank Transfer Method Available")
                return True
            else:
                QMessageBox.warning(None, "Bank Transfer Not Available", "Bank Transfer is not available for this supplier.")
                self.payment_method_combo.setCurrentText('Cash')
                return False
                
        else:
            QMessageBox.warning(None, "Error", query.lastError().text())
            self.payment_method_combo.setCurrentText('Cash')
            return False


    def check_jazzcash(self, supplier_id):
        """
        This method is called when the payment method is changed to jazzcash.
        It checks if jazzcash is available for that supplier.
        """
        # Check if jazzcash is available for that supplier
        query = QSqlQuery()
        query.prepare("select count(*) from jazzcash where supplier = ?")
        query.addBindValue(supplier_id)
        if query.exec() and query.next():
            jazzcash = query.value(0)

            if jazzcash > 0 :
                print("JazzCash Method Available")
                return True
            else:
                QMessageBox.warning(None, "JazzCash Not Available", "JazzCash is not available for this supplier.")
                self.payment_method_combo.setCurrentText('Cash')
                return False

        else:
            QMessageBox.warning(None, "Error", query.lastError().text())
            self.payment_method_combo.setCurrentText('Cash')
            return False


    def check_easypaisa(self, supplier_id):
        """
        This method is called when the payment method is changed to easypaisa.
        It checks if easypaisa is available for that supplier.
        """
        # Check if easypaisa is available for that supplier
        query = QSqlQuery()
        query.prepare("select count(*) from easypaisa where supplier = ?")
        query.addBindValue(supplier_id)
        if query.exec() and query.next():
            easypaisa = query.value(0)

            if easypaisa > 0 :
                print("EasyPaisa Method Available")
                return True
            else:
                QMessageBox.warning(None, "EasyPaisa Not Available", "EasyPaisa is not available for this supplier.")
                self.payment_method_combo.setCurrentText('Cash')
                return False

        else:
            QMessageBox.warning(None, "Error", query.lastError().text())
            self.payment_method_combo.setCurrentText('Cash')
            return False


    def add_new_product_dialog(self):
        
        dialog = ImportDialog(self)
        if dialog.exec() == QDialog.Accepted:
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
from PySide6.QtWidgets import QDialog, QDialogButtonBox

class ImportDialog(QDialog):
    
    # ... your __init__ / UI methods ...
    def __init__(self, parent=None):
        
        super().__init__(parent)
        self.setWindowTitle("Import Stock Data")
        self.resize(600, 400)

        layout = QVBoxLayout()
        
        self.insert_subheading("PRODUCT INFORMATION")
        
        self.populate_product_fields()
        self.populate_medicine_fields()
       

        self.setLayout(layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)   # Save → dialog.accept()
        button_box.rejected.connect(self.reject)   # Cancel → dialog.reject()
        layout.addWidget(button_box)
    
    

    def insert_subheading(self, title):
        
        # === Sub Header Row ===
        subheader_layout = QHBoxLayout()
        subheading = QLabel(title, objectName="SubHeading")
        
        subheader_layout.addWidget(subheading)
        self.layout.addLayout(subheader_layout)
        
        self.layout.addSpacing(10)
        
        
    
    def populate_product_fields(self):
        
        labels = ["Product Name", "Code/Barcode", "Category", "Brand"]
        
        self.name_input = QComboBox()
        self.name_input.setEditable(True)
        self.code_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.addItems(["Medicine", "General Item", "Other"])
        self.brand_input = QLineEdit()
        
        fields = [self.name_input, self.code_input, self.category_input, self.brand_input]
        
        self.insert_labels_and_fields(labels, fields)
        
        
    def populate_medicine_fields(self):
        
        # === Sub Header Row ===
        self.medicine_layout = QHBoxLayout()
        self.medicine_subheading = QLabel("MEDICINE & BATCH  INFORMATION", objectName="SubHeading")
        
        self.medicine_layout.addWidget(self.medicine_subheading)
        self.layout.addLayout(self.medicine_layout)
        
        self.layout.addSpacing(10)
        
        self.medicine_subheading.hide()
        
        self.formula_input = QLineEdit()
        self.form_input = QLineEdit()
        self.strength_input = QLineEdit()
        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.batch_input = QLineEdit()
        self.expiry_input.setDate(QDate.currentDate())

        self.medicine_fields = [
            ("Formula:", self.formula_input),
            ("Form (Tablet/Syrup):", self.form_input),
            ("Strength:", self.strength_input),
            ("Batch No:", self.batch_input),
            ("Expiry Date:", self.expiry_input)
            
        ]
        
        
        
        # Keep track of full row containers for show/hide
        self.medicine_rows = []

        for label, field in self.medicine_fields:
            # --- row container ---
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            # indicator
            indicator = QFrame()
            indicator.setFixedWidth(4)
            indicator.setStyleSheet("background-color: #ccc; border: none;")

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setFixedWidth(250)
            field.setStyleSheet("margin-left: 18px;")

            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            row_layout.addWidget(indicator)
            row_layout.addWidget(lbl, 1)
            row_layout.addWidget(field, 8)

            # Add whole row widget into main layout
            self.layout.addWidget(row_widget)
            self.layout.setSpacing(15)

            # Map indicator for highlighting
            self.indicators[field] = indicator
            field.installEventFilter(self)

            # Initially hide medicine rows
            self.medicine_rows.append(row_widget)
            
        
            self.layout.addSpacing(20)
            
    

    









