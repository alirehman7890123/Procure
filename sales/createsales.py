from PySide6.QtWidgets import QApplication, QWidget, QCompleter, QDateEdit, QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QStringListModel, QDate, Signal, QTimer, QObject, QRectF
import os
import sys
import platform

from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent, QPdfWriter, QKeySequence, QPainter, QPageSize, QFont, QTextOption, QPen, QColor
from functools import partial
import math
from utilities.stylus import load_stylesheets





class KeyUpLineEdit(QLineEdit):
    keyReleased = Signal(QKeyEvent)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.keyReleased.emit(event)




from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QLineEdit, QCheckBox, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt


class CreateSalesWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scan_timer = QTimer(self)
        self.scan_timer.setSingleShot(True)
        self._pending_scan = None
        self.scan_timer.timeout.connect(lambda: self._run_pending_scan())
        
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reloading_sale = False
        self.order_modified = False
        self.row_height = 40
        self.min_visible_rows = 5

        # === Main Vertical Layout ===
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 20, 30, 20)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Create Sales Receipt", objectName='SectionTitle')
        
        self.invoicelist = QPushButton('SO List', objectName='TopRightButton')
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.invoicelist)
        self.layout.addLayout(header_layout)

        self.layout.addSpacing(20)

        # === Customer + Salesman Row ===
        top_row = QHBoxLayout()
        customerlabel = QLabel("Customer")
        self.customer = QComboBox()
        self.customer.setMinimumWidth(200)
        salesmanlabel = QLabel("Salesman")
        self.salesman = QComboBox()
        self.salesman.setMinimumWidth(200)
        top_row.addWidget(customerlabel)
        top_row.addWidget(self.customer, 2)
        top_row.addSpacing(40)
        top_row.addWidget(salesmanlabel)
        top_row.addWidget(self.salesman, 2)
        self.layout.addLayout(top_row)
        
        

        # === Table ===
        self.row_height = 40
        self.min_visible_rows = 5
        
    
        self.table = MyTable(column_ratios=[0.05, 0.35, 0.08, 0.08, 0.08, 0.08, 0.08, 0.15, 0.05])
        headers = ["#", " Product Description", "Stock", " Qty", "Rate", "Disc %", "Flat disc.", "Total", "X"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setTabKeyNavigation(False)
        self.table.setFixedHeight(260)   # pixels

        
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
        


        # === Add Row Button ===
        add_button_row = QHBoxLayout()
        self.add_button = QPushButton("Add Row", objectName='TopRightButton')
        
        self.add_button.clicked.connect(self.add_row)
        add_button_row.addWidget(self.add_button, stretch=1)
        self.layout.addLayout(add_button_row)
        add_button_row.addStretch()

        # === Subtotal + Total Row ===
        subtotal_row = QHBoxLayout()
        subtotal = QLabel("Sub Total")
        subtotal.setMinimumWidth(200)
        self.subtotaldata = QLabel("0.00")
        right_total = QLabel("Total")
        right_total.setMinimumWidth(200)
        self.right_totaldata = QLabel("0.00")
        self.right_totaldata.setMinimumWidth(200)
        subtotal_row.addWidget(subtotal)
        subtotal_row.addWidget(self.subtotaldata)
        subtotal_row.addStretch()
        subtotal_row.addWidget(right_total)
        subtotal_row.addWidget(self.right_totaldata)
        self.layout.addLayout(subtotal_row)

        # === Discount + Roundoff Row ===
        discount_row = QHBoxLayout()
        discount = QLabel("Discount")
        discount.setMinimumWidth(200)
        self.percentage = KeyUpLineEdit()
        self.percentage.setPlaceholderText(" Disc % ")
        self.percentage.setMinimumWidth(150)
        self.flatdiscount = KeyUpLineEdit()
        self.flatdiscount.setPlaceholderText("Flat")
        self.flatdiscount.setMinimumWidth(150)
        roundofflabel = QLabel("Roundoff")
        roundofflabel.setMinimumWidth(200)
        self.roundoffdata = QLabel("0.00")
        self.roundoffdata.setMinimumWidth(200)
        discount_row.addWidget(discount)
        discount_row.addWidget(self.percentage)
        discount_row.addWidget(self.flatdiscount)
        discount_row.addStretch()
        discount_row.addWidget(roundofflabel)
        discount_row.addWidget(self.roundoffdata)
        self.layout.addLayout(discount_row)

        self.percentage.keyReleased.connect(self.calculate_percentage_discount)
        self.flatdiscount.keyReleased.connect(self.calculate_flat_discount)

        # === Net + Final Amount Row ===
        net_row = QHBoxLayout()
        net_amount = QLabel("Net Amount")
        net_amount.setMinimumWidth(200)
        self.net_amountdata = QLabel("0.00")
        final_amount = QLabel("Final Amount")
        final_amount.setMinimumWidth(200)
        final_amount.setStyleSheet("font-size: 20px; font-weight: 700")
        self.final_amountdata = QLabel("0.00")
        self.final_amountdata.setMinimumWidth(200)
        self.final_amountdata.setStyleSheet("font-size: 20px; font-weight: 700")
        net_row.addWidget(net_amount)
        net_row.addWidget(self.net_amountdata)
        net_row.addStretch()
        net_row.addWidget(final_amount)
        net_row.addWidget(self.final_amountdata)
        self.layout.addLayout(net_row)

        # === Tax Row ===
        tax_row = QHBoxLayout()
        taxlabel = QLabel("Tax")
        taxlabel.setMinimumWidth(200)
        self.taxedit = QLineEdit()
        self.taxedit.setMinimumWidth(150)
        self.taxedit.setPlaceholderText("Tax %")
        self.taxamount = QLabel("0.00")
        self.taxamount.setMinimumWidth(150)
        tax_row.addWidget(taxlabel)
        tax_row.addWidget(self.taxedit)
        tax_row.addWidget(self.taxamount)
        tax_row.addStretch()
        self.layout.addLayout(tax_row)

        self.taxedit.textChanged.connect(self.calculate_tax)

        # === Total + Received Row ===
        payment_row = QHBoxLayout()
        lefttotal = QLabel("Total")
        lefttotal.setMinimumWidth(200)
        self.lefttotaldata = QLabel("0.00")
        receivelabel = QLabel("Received")
        receivelabel.setMinimumWidth(200)
        self.receiveedit = QLineEdit()
        self.receiveedit.setMinimumWidth(200)
        self.receiveedit.setPlaceholderText("0.00")
        payment_row.addWidget(lefttotal)
        payment_row.addWidget(self.lefttotaldata)
        payment_row.addStretch()
        payment_row.addWidget(receivelabel)
        payment_row.addWidget(self.receiveedit)
        self.layout.addLayout(payment_row)

        self.receiveedit.textChanged.connect(self.calculate_payment)

        # === Remaining + Writeoff Row ===
        remaining_row = QHBoxLayout()
        remaininglabel = QLabel("Remaining")
        remaininglabel.setMinimumWidth(200)
        self.remainingdata = QLabel("0.00")
        self.checkbox = QCheckBox("Write off")
        self.checkbox.toggled.connect(self.writeoffcheck)
        remaining_row.addStretch()
        remaining_row.addWidget(remaininglabel)
        remaining_row.addWidget(self.remainingdata)
        remaining_row.addWidget(self.checkbox)
        self.layout.addLayout(remaining_row)

        # === Note Row ===
        note_row = QHBoxLayout()
        self.note = QLabel("Note")
        
        note_row.addStretch()
        note_row.addWidget(self.note)
        self.layout.addLayout(note_row)

        # === Save Button ===
        save_row = QHBoxLayout()
        addreceipt = QPushButton('Save Sales Receipt', objectName='SaveButton')
        addreceipt.setCursor(Qt.PointingHandCursor)
        addreceipt.clicked.connect(lambda: self.save_receipt())
        save_row.addWidget(addreceipt, 1)
        save_row.addStretch()
        self.layout.addLayout(save_row)

        
        self.setStyleSheet(load_stylesheets())
        self.layout.addStretch()




    
    
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
            
            if self.checkbox.isChecked():
                
                self.note.setText(f"Amount {remaining} will be wrote-off / Cleared")
            else:
                self.note.setText(f"Amount {remaining} will be added to receiveable")
        
        else:
            
            self.note.setText(f"Amount {remaining} is excessive and will be added to payable")    
    
    
    
    
    def calculate_percentage_discount(self):
        
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
        
        finalamount = self.final_amountdata.text()
        finalamount = float(finalamount) if finalamount else 0.00

        received = self.receiveedit.text()
        received = float(received) if received else 0.00

        remaining = finalamount - received
        self.remainingdata.setText(str(remaining))
        
        self.writeoffcheck()
         

    
        
    

    def calculate_tax(self):
        
        net_amount = self.net_amountdata.text()
        net_amount = float(net_amount) if net_amount else 0
        
        tax = self.taxedit.text()
        tax = float(tax) if tax else 0
        
        tax_amount = net_amount * tax / 100
        self.taxamount.setText(f"{tax_amount:.2f}")
        
        self.update_total_amount()
        
        



        
    def add_row(self):
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, self.row_height)
        
        counter = QLabel()
        counter.setText(str(row + 1))
        counter.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row, 0, counter)

        item = QComboBox()
        item.wheelEvent = lambda event: event.ignore()
        
        item.setPlaceholderText("select product")
        item.setEditable(True)
        self.table.setCellWidget(row, 1, item)
        
        completer = QCompleter()
        item.setCompleter(completer)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        
        item.lineEdit().completer().popup().setStyleSheet("""
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


        item.lineEdit().textEdited.connect(lambda: self.load_product_suggestions(item, completer))
        
        stock = QLineEdit()
        stock.setPlaceholderText("stock")
        stock.setReadOnly(True)
        stock = self.table.setCellWidget(row, 2, stock)
        
        
        qty_edit = QLineEdit()
        qty_edit.setPlaceholderText("qty")
        
        rate_edit = QLineEdit()
        rate_edit.setPlaceholderText("rate")
        
        discount = KeyUpLineEdit()
        discount.setPlaceholderText("% Disc")
        discount.setText("0.00")
        
        discount_amount = KeyUpLineEdit()
        discount_amount.setReadOnly(True)
        discount_amount.setPlaceholderText("flat")
        discount_amount.setText("0.00")
        
        amount_edit = QLineEdit()
        amount_edit.setReadOnly(True)
        amount_edit.setPlaceholderText("total")
        amount_edit.setText("0.00")
        
        remove_btn = QPushButton("X")
        remove_btn.clicked.connect(lambda _, r=row: self.remove_row(r))
        remove_btn.setStyleSheet("color: #333;")
       
        
        self.table.setCellWidget(row, 3, qty_edit)
        self.table.setCellWidget(row, 4, rate_edit)
        self.table.setCellWidget(row, 5, discount)
        self.table.setCellWidget(row, 6, discount_amount)
        self.table.setCellWidget(row, 7, amount_edit)
        self.table.setCellWidget(row, 8, remove_btn)
        
        
        
        qty_edit.textChanged.connect(lambda _: self.update_amount(qty_edit))
        rate_edit.textChanged.connect(lambda _: self.update_amount(rate_edit))
        
        discount.textChanged.connect(lambda _: self.update_amount(discount))
        discount.keyReleased.connect(lambda: self.line_percentage_discount(discount))
        discount_amount.keyReleased.connect(lambda: self.line_flat_discount(discount_amount))

        

        # self.update_table_height()
        
    
    
    
    
    
    def line_percentage_discount(self, edited_widget):
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            
            qty_text = self.table.cellWidget(row, 3).text()
            rate_text = self.table.cellWidget(row, 4).text()
            # get percentage amount
            percentage_discount = self.table.cellWidget(row,5).text()

            qty = float(qty_text) if qty_text else 0
            rate = float(rate_text) if rate_text else 0
            percentage_discount = float(percentage_discount) if percentage_discount else 0
            
            discount_amount =  rate * (percentage_discount / 100)
            self.table.cellWidget(row, 6).setText(f"{discount_amount:.2f}")
            price = rate - discount_amount
            
            total = qty * price
            self.table.cellWidget(row, 7).setText(f"{total:.2f}")
            
            self.update_total_amount()
            
        except ValueError:
        
            self.table.cellWidget(row, 7).setText("0")
            
            
    
    def line_flat_discount(self, edited_widget):
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            
            qty_text = self.table.cellWidget(row, 3).text()
            rate_text = self.table.cellWidget(row, 4).text()
            # get percentage amount
            flat_discount = self.table.cellWidget(row,6).text()

            qty = float(qty_text) if qty_text else 0
            rate = float(rate_text) if rate_text else 0
            flat_discount = float(flat_discount) if flat_discount else 0

            if flat_discount > 0:
                percentage = ( flat_discount / rate ) * 100
            else:
                percentage = 0.0
                
            self.table.cellWidget(row, 5).setText(f"{percentage:.2f}")
            
            price = rate - flat_discount
            
            total = price * qty
            
            self.table.cellWidget(row, 7).setText(f"{total:.2f}")

            self.update_total_amount()
            
        except ValueError:
        
            self.table.cellWidget(row, 7).setText("0")
        
        
        
        
    
    
    
    

    def remove_row(self, target_row):
        self.table.removeRow(target_row)

        # Reconnect all remove buttons with updated row numbers
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 4)
            if isinstance(widget, QPushButton):
                widget.clicked.disconnect()
                widget.clicked.connect(lambda _, r=row: self.remove_row(r))

        
        

        
    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        
        if not self.reloading_sale:
            
            self.populate_customer()
            self.populate_salesman()




    
    def populate_customer(self):
        
        self.customer.clear()
        
        query = QSqlQuery()

        self.customer.addItem("Walk-in Customer")
        
        if query.exec("SELECT id, name, contact FROM customer WHERE status = 'active';"):
            while query.next():
                customer_id = query.value(0)
                customer = query.value(1)
                contact = query.value(2)
                
                customer = f'{customer}  [ {contact} ]'

                self.customer.addItem(customer, customer_id)  # Text shown, ID stored as data

        else:
            QMessageBox.information(None, 'Error', query.lastError().text())




    def populate_salesman(self):
        
        self.salesman.clear()
        
        username = QApplication.instance().property("username")
        
        query = QSqlQuery()
        query.prepare("SELECT id, firstname, lastname FROM auth WHERE username = ?;")
        query.addBindValue(username)
        
        if query.exec():
            
            while query.next():
                employee_id = query.value(0)
                firstname = query.value(1)
                lastname = query.value(2)
                
                salesman = f'{firstname} {lastname}'

                print(employee_id, salesman)

                self.salesman.addItem(salesman, employee_id)  # Text shown, ID stored as data

        else:
            QMessageBox.information(None, 'Error', query.lastError().text() )
        
        
    def confirm_and_save_sale(self):
        
        reply = QMessageBox.question(
            self,
            "Confirm Sale",
            "Do you want to proceed and save this sale?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 👉 Place your DB insert logic here
            print("Sale stored in database.")
            return True
        else:
            print("Sale ignored.")
            return False
        
        
    
    def insert_salesreceipt(self):
        
        confirmation = self.confirm_and_save_sale()
        
        if confirmation:
        
            print("Inserting sales receipts")
            
            try:

                customer = self.customer.currentData()
                salesman = self.salesman.currentData()
                
                subtotal = self.subtotaldata.text()
                discount = self.percentage.text()
                discountamount = self.flatdiscount.text()
                netamount = self.net_amountdata.text()
                tax = self.taxedit.text()
                taxamount = self.taxamount.text()
                totalaftertax = self.right_totaldata.text()
                roundoff = self.roundoffdata.text()
                total = self.final_amountdata.text()
                received = self.receiveedit.text()
                remaining = self.remainingdata.text()
                print("About to find customer out...")
                print("customer is: ", customer)
                
                if customer == '':
                    customer = None
                
                
                if customer is not None:
                    customer = int(customer)
                    

                salesman = int(salesman) if salesman else 0
                
                subtotal = float(subtotal) if subtotal else 0
                discount = float(discount) if discount else 0
                discountamount = float(discountamount) if discountamount else 0
                netamount = float(netamount) if netamount else 0
                tax = float(tax) if tax else 0
                taxamount = float(taxamount) if taxamount else 0
                totalaftertax = float(totalaftertax) if totalaftertax else 0
                roundoff = float(roundoff) if roundoff else 0
                total = float(total) if total else 0
                received = float(received) if received else 0
                remaining = float(remaining) if remaining else 0
                
                print("Customer: ", customer)
                print("Salesman: ", salesman)
                print("Subtotal: ", subtotal)
                print("Discount: ", discount)
                print("Discount Amount: ", discountamount)
                print("Net Amount: ", netamount)
                print("Tax: ", tax)
                print("Tax Amount: ", taxamount)
                print("Total After Tax: ", totalaftertax)
                print("Roundoff: ", roundoff)
                print("Total: ", total)
                print("Received: ", received)
                print("Remaining: ", remaining)
                
                
                if remaining == 0.0:
                    
                    writeoff = 0.0
                    payable = 0.0
                    receiveable = 0.0
                    
                elif remaining > 0.0 and self.checkbox.isChecked():
                    
                    writeoff = remaining
                    payable = 0.0
                    receiveable = 0.0
                    
                elif remaining > 0.0 and not self.checkbox.isChecked():
                    
                    if customer is None:
                        
                        QMessageBox.information(self, 'Error', "Walk-In Customer Can't Have Remaining Amount \n Receive Full amount or Write off")
                        return None
                        
                        
                    writeoff = 0.0
                    payable = 0.0
                    receiveable = remaining
                    
                else:
                    
                    writeoff = 0.0
                    payable = abs(remaining)
                    receiveable = 0.0
                
                if customer is None:
                    
                    payable = 0.0
                    receiveable = 0.0

                print("Writeoff: ", writeoff)
                print("Payable", payable)
                print("Receiveables", receiveable)
                
                sales_query = QSqlQuery()
                sales_query.prepare("""
                            INSERT INTO sales (customer, salesman, subtotal, discount, discamount, netamount,
                            tax, taxamount, totalaftertax, roundoff, total, received, remaining, writeoff, payable, receiveable)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """)
                        
                sales_query.addBindValue(customer)
                sales_query.addBindValue(salesman)
                
                sales_query.addBindValue(subtotal)
                sales_query.addBindValue(discount)
                sales_query.addBindValue(discountamount)
                sales_query.addBindValue(netamount)
                sales_query.addBindValue(tax)
                sales_query.addBindValue(taxamount)
                sales_query.addBindValue(totalaftertax)
                sales_query.addBindValue(roundoff)
                sales_query.addBindValue(total)
                sales_query.addBindValue(received)
                sales_query.addBindValue(abs(remaining))
                sales_query.addBindValue(writeoff)
                sales_query.addBindValue(payable)
                sales_query.addBindValue(receiveable)
                
                
                if not sales_query.exec():
                
                    print("Insert failed:", sales_query.lastError().text())
                    raise Exception()
                
                else:
                    sales_id = sales_query.lastInsertId()
                    print("Sales ID is: ", sales_id)
                    
                    
                    
                #####################################
                ####      SALES TRANSACTIONS     ####
                #####################################
                
                if customer is not None:
                    
                    customer_query = QSqlQuery()
                    customer_query.prepare("SELECT payable, receiveable FROM customer where id = ?")
                    customer_query.addBindValue(customer)
                    
                    if customer_query.exec() and customer_query.next():
                        
                        payable_before = customer_query.value(0)
                        receiveable_before = customer_query.value(1)
                        payable = float(payable)
                        receiveable = float(receiveable)
                        
                    else:
                        
                        print("Error ", customer_query.lastError().text())
                        QMessageBox.critical(self, "Error", "Customer not found or database error.")
                        raise Exception 
                    

                    transaction_type = 'Sales Order'
                    ref_no = sales_id
                    return_ref = None
                    payable_before = payable_before
                    due_amount = 0.00
                    paid = 0.00
                    remaining_due = 0.00
                    payable_after = payable_before
                    
                    receiveable_before = receiveable
                    receiveable_now = total
                    received = received
                    remaining_now = total - received
                    receiveable_after = receiveable + total - received 
                    
                else: 
                    
                    transaction_type = 'Sales Order'
                    ref_no = sales_id
                    return_ref = None
                    payable_before = 0.00
                    due_amount = 0.00
                    paid = 0.00
                    remaining_due = 0.00
                    payable_after = 0.00
                    
                    receiveable_before = 0.00
                    receiveable_now = total
                    received = received
                    remaining_now = total-received
                    receiveable_after = 0.00
                
                
                # insert transaction
                query = QSqlQuery()
                query.prepare("""
                            INSERT INTO customer_transaction 
                            (customer, transaction_type, ref, return_ref,
                            payable_before, due_amount, paid, remaining_due, payable_after,
                            receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                            salesman) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            
                            """)
                
                query.addBindValue(customer)
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
                query.addBindValue(salesman)
                
                
                if query.exec():
                    
                    insert_id = query.lastInsertId()
                    print("Transaction is saved ...")
                    QMessageBox.information(None, "Success", "Customer Transaction Stored Successfully with ID: " + str(insert_id) )
                    
                    
                else:
                    
                    QMessageBox.critical(None, "Error", query.lastError().text())
                    print("Query error:", query.lastError().text())
                    raise Exception 
                
                
                
                if customer is not None:
                    
                    customer_query = QSqlQuery()
                    customer_query.prepare("SELECT payable, receiveable FROM customer where id = ?")
                    customer_query.addBindValue(customer)
                    
                    if customer_query.exec() and customer_query.next():
                        
                        customer_payable = customer_query.value(0)
                        customer_receiveable = customer_query.value(1)

                        customer_payable = float(customer_payable)
                        customer_receiveable = float(customer_receiveable)
                                    
                    else:
                        
                        print("Error ", customer_query.lastError().text())
                        QMessageBox.critical(self, "Error", "customer not found or database error.")
                        raise Exception
                    
                    print("Payable and Receiveable are : ", customer_payable, customer_receiveable)
                    
                    customer_payable = customer_payable + payable
                    customer_receiveable = customer_receiveable + receiveable
                    
                    update_customer = QSqlQuery()
                    update_customer.prepare("UPDATE customer SET payable = ? , receiveable = ? WHERE id = ?")
                    
                    update_customer.addBindValue(customer_payable)
                    update_customer.addBindValue(customer_receiveable)
                    update_customer.addBindValue(customer)
                    
                    print("New Payable and Receiveable are : ", customer_payable, customer_receiveable)
                    
                    if update_customer.exec(): 
                        
                        print("customer Balance updated successfully")
                    
                    else:
                        QMessageBox.critical(self, "Error", update_customer.lastError().text())
                        raise Exception
                

                
                ### PRINT RECEIPT ###
                
                pdf_file = self.export_pdf('salesinvoice.pdf', sales_id)
                self.print_pdf(pdf_file)
                
                # self.thermal_receipt_printer(sales_id)
            
                    
                return sales_id
            
                    
                    
            except Exception as e:
                
                e = str(e)
                print("Error Occurred While Saving Sales Recipt ", e)

        
        
        
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
        """ Insert sales items into the database. """
        
        try:
            
            # Process each row in the sales items table
            for row in range(self.table.rowCount()):
                
                print("Row number is:", row)
                
                product_widget = self.table.cellWidget(row, 1)
                if not product_widget or not product_widget.currentData():
                    print("Row is empty ... ignoring it...")
                    continue

                product_id = product_widget.currentData()
                product_id = int(product_id)
                
                sales_id = int(sales_id)
                
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
                    INSERT INTO salesitem (sales, product, qty, unitrate, discount, discountamount, total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """)

                item_query.addBindValue(sales_id)
                item_query.addBindValue(product_id)
                item_query.addBindValue(qty)
                item_query.addBindValue(rate)
                item_query.addBindValue(discount)
                item_query.addBindValue(discountamount)
                item_query.addBindValue(total)
                
                if not item_query.exec():
                    
                    print("Error inserting Sales Item:", item_query.lastError().text())
                    raise Exception(f"Failed to insert sales item for product_id {product_id}: {item_query.lastError().text()}")

                    
                else:
                    
                    print("Item saved ")
                    print("Sales Item ID is: ", item_query.lastInsertId())
                    
                    
                    stock_query = QSqlQuery()
                    stock_query.prepare("SELECT units FROM stock WHERE product = ?")
                    stock_query.addBindValue(product_id)

                    if stock_query.exec() and stock_query.next():

                        units = stock_query.value(0)
                        units = int(units)
                        
                        sold_units = qty 
                        rem_units = units - sold_units
                        
                        update_query = QSqlQuery()
                        update_query.prepare("UPDATE stock SET units = ? WHERE product = ?")
                        update_query.addBindValue(rem_units)
                        update_query.addBindValue(product_id)

                        if update_query.exec():
                            
                            print("Stock updated successfully")
                                
                        else:
                            
                            print("Failed to update stock:", update_query.lastError().text())
                            raise Exception 

            

        except Exception :
            print("Error Occurred While Saving Sales Items ")
    
    
    
    def put_sale_on_hold(self):
        
        db = QSqlDatabase().database()
        db.transaction()
        
        try:
        
            print("Putting Sale on Hold")

            # get salesorder data
            customer = self.customer.currentData()
            salesman = self.salesman.currentData()
            status = 'On Hold'
            
            print("Customer is: ", customer)
            print("Salesman is: ", salesman)        
            
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
        
        print("Loading Product Suggestions")
        item = item
        completer = completer
        current_text = item.currentText().strip()
        print("Current Text is: ", current_text)
        
        if current_text == '':
            return 


            
        if current_text and current_text.isdigit():
            
            self._pending_scan = (current_text, item)
            self.scan_timer.start(150) # wait 150 ms before running the scan
            
            return
            
            
        
        query = QSqlQuery()
        query.prepare("SELECT id, name, form, strength FROM product WHERE name LIKE ? LIMIT 10")
        print("Current Text is: ", current_text)
        query.addBindValue(f"%{current_text}%")
        
        products = []
        
        
        if not query.exec():
            
            print("Something wrong happened...", query.lastError().text())
        
        else:
        
            while query.next():
                
                product_id = query.value(0)
                name = query.value(1)
                form = query.value(2)
                strength = query.value(3)
                
                label = f"{name} {strength} {form}".strip()
                print("Label is: ", label)
                products.append(label)
                item.addItem(label, product_id)
                
                
                
        
        print("Pringint Brought up products")        
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
            
        row = self.table.indexAt(item.pos()).row()
        product_id = self.table.cellWidget(row, 1).currentData()
        
        print("Med id is: ", product_id)

        stock_query = QSqlQuery()
        stock_query.prepare("SELECT packsize, units, saleprice FROM stock WHERE product = ?")
        stock_query.addBindValue(product_id)
        

        try:
            
            if stock_query.exec() and stock_query.next(): 
                 
                packsize = int(stock_query.value(0))
                units = int(stock_query.value(1))
                saleprice = float(stock_query.value(2))

                # get unit sale price
                unit_sale_price = saleprice / packsize if packsize > 0 else 0.0

                print(f"Stock info is: {units} {saleprice}")

                self.table.cellWidget(row, 2).setText(f'{units}')
                self.table.cellWidget(row, 4).setText(f'{unit_sale_price:.2f}')
                
            else:
                print("Stock Error... Maybe not found")
                QMessageBox.information(self, 'Stock Error', stock_query.lastError().text())

        except Exception as e:
                
            print(str(e))
            QMessageBox.critical(None, "Error", "An error occurred while loading stock data: " + str(e))




    def on_item_selected(self, item):
        
        text = item.currentText()
        data = item.currentData()

        
        print("Selected text is: ",text, data)
        data = int(data)
        
        query = QSqlQuery()
        query.prepare("""
            SELECT * FROM product
            WHERE id = ? """)
        
        query.addBindValue(data)
        
        if not query.exec():
            
            print("Cannot Get the product")
            
        else:
            
            print("Got the product")
                
      





    def split_packs_and_units(self, pack_size: int, units: int) -> tuple[int, int]:
   
        if pack_size <= 0:
            raise ValueError("Pack size must be greater than zero")
        if units < 0:
            raise ValueError("Units cannot be negative")

        packs = units // pack_size
        leftover_units = units % pack_size
        return packs, leftover_units
    
    
    

    def update_amount(self, edited_widget):
        
        self.order_modified = True
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            stock = self.table.cellWidget(row, 2).text()
            
            stock = int(stock)
            
            
            qty_text = self.table.cellWidget(row, 3).text()
            
            if int(qty_text) > stock:
                
                QMessageBox.information(None, "Error", "Quantity cannot be greater than available stock")
                self.table.cellWidget(row, 3).setText("0")
                qty_text = 0
            
            
            rate_text = self.table.cellWidget(row, 4).text()
            discount_edit = self.table.cellWidget(row, 5).text()
            discount_amount_edit = self.table.cellWidget(row, 6).text()
            
            print("Discount is: ", discount_edit)

            qty = float(qty_text) if qty_text else 0
            rate = float(rate_text) if rate_text else 0
            discount = float(discount_edit) if discount_edit else 0
            discount_amount = float(discount_amount_edit) if discount_amount_edit else 0
            
            print("Rate is: ", rate, " Discount is: ", discount)
            
            price = rate - discount_amount
            
            print("Final price is: ", price)
            
            total = qty * price
            
            print("Amount is: ", total)
            
             
            total = float(f"{total:.2f}")

            self.table.cellWidget(row, 7).setText(str(total))
            
            self.update_total_amount()
            
        except ValueError:
        
            self.table.cellWidget(row, 7).setText("0")

    
    
    

    def update_total_amount(self):
        
        subtotal = 0.0

        for row in range(self.table.rowCount()):
            
            linetotal = self.table.cellWidget(row, 7).text()
            
            if linetotal:
                try:
                    value = float(linetotal)
                    subtotal = subtotal + value
                    
                except ValueError:
                    pass
                
            
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
        



    def update_final_amount(self):
        
        print("Updating final amount")
        
        subtotal = float(self.subtotal.text())
        
        discount = self.discount.text()
        tax = self.tax.text()
        
        discount = float(discount) if discount else 0
        tax = float(tax) if tax else 0
        
        discountamount = subtotal * discount / 100
        self.percentage.setText(f"{discountamount:.2f}")
        self.flatdiscount.setText(f"{discountamount:.2f}")
        
        rem_amount = subtotal - discountamount
        self.net_amountdata.setText(f"{rem_amount:.2f}")
        
        tax = rem_amount * tax / 100
        self.taxamount.setText(f"{tax:.2f}")
        
        finalamount = rem_amount + tax
        
        rounded_total = math.floor(finalamount)
        roundoff = round(finalamount - rounded_total, 2)
        
        totalamount = finalamount - roundoff
        
        self.roundoffdata.setText(f"{roundoff:.2f}")
        self.final_amountdata.setText(f"{totalamount:.2f}")
        
        
    
    
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
        
        
    
    
    def pay_method_change(self):
        """
        This method is called when the payment method is changed.
        It checks if payment method is available for that customer.
        """
        # Get the selected payment method
        payment_method = self.payment_method_combo.currentText()
        
        # get the supplier_id
        customer_id = self.supplier_edit.currentData()
        customer_id = int(customer_id)
        
        
        # Check if payment method is available for that customer
        if payment_method == 'Bank Transfer':
            self.check_bank_transfer(customer_id)
            
        if payment_method == 'JazzCash':
            self.check_jazzcash(customer_id)

        if payment_method == "EasyPaisa":
            self.check_easypaisa(customer_id)
            
    
    def check_bank_transfer(self, customer_id):
        """
        This method is called when the payment method is changed to bank transfer.
        It checks if bank transfer is available for that customer.
        """
        # Check if bank transfer is available for that customer
        query = QSqlQuery()
        query.prepare("select count(*) from bank where customer = ?")
        query.addBindValue(customer_id)
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


    def check_jazzcash(self, customer_id):
        """
        This method is called when the payment method is changed to jazzcash.
        It checks if jazzcash is available for that customer.
        """
        # Check if jazzcash is available for that customer
        query = QSqlQuery()
        query.prepare("select count(*) from jazzcash where customer = ?")
        query.addBindValue(customer_id)
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


    def check_easypaisa(self, customer_id):
        """
        This method is called when the payment method is changed to easypaisa.
        It checks if easypaisa is available for that supplier.
        """
        # Check if easypaisa is available for that supplier
        query = QSqlQuery()
        query.prepare("select count(*) from easypaisa where customer = ?")
        query.addBindValue(customer_id)
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



    
    
    
    
    def hideEvent(self, event):
        
        if self.order_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard this order?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

            else:
                self.clear_fields()
            
        super().hideEvent(event)
    
    


    
    
    def clear_fields(self):
        
        self.order_modified = False
        self.reloading_sale = False
        
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
        self.receiveedit.clear()
        self.remainingdata.clear()
        
        self.checkbox.setChecked(True)        
        
        self.table.setRowCount(0)
        
        self.populate_customer()
        
        self.table.setRowCount(0)
        
        
        for _ in range(5):
            
            self.add_row()



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
            
    
   