from PySide6.QtWidgets import QApplication, QWidget, QCompleter, QDateEdit, QVBoxLayout, QHBoxLayout, QInputDialog, QFrame, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QStringListModel, QDate, Signal, QTimer, QEvent, QRectF
import os
import sys
import platform

from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent, QPdfWriter, QKeySequence, QPainter, QPageSize, QFont, QTextOption, QPen, QColor
from functools import partial
import math
from utilities.stylus import load_stylesheets
from PySide6.QtGui import QKeySequence, QShortcut





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
        
        # self.setFixedWidth(1200)
        self.sales_locked = False
        
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
        
        
        clear_btn = QPushButton('Clear Sale', objectName='TopRightButton')
        clear_btn.setCursor(Qt.PointingHandCursor)
        # clear_btn.clicked.connect(lambda: self.clear_fields())
        
        
        self.invoicelist = QPushButton('SO List', objectName='TopRightButton')
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        header_layout.addWidget(self.invoicelist)
        self.layout.addLayout(header_layout)

        self.layout.addSpacing(20)
        
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
        
        

        # === Customer + Salesman Row ===
        
        top_row = QHBoxLayout()
        customerlabel = QLabel("Customer")
        
        self.customer = QComboBox()
        self.customer.setMinimumWidth(200) 
               
        self.customer.setEditable(True)
        self.customer.completer().setCaseSensitivity(Qt.CaseInsensitive)
        self.customer.completer().setFilterMode(Qt.MatchContains)
        
        self.customer.lineEdit().selectionChanged.connect(lambda: None)  # prevents some focus quirks
        self.customer.lineEdit().installEventFilter(self)
        
        self.customer.setInsertPolicy(QComboBox.NoInsert)
        



        
        # salesmanlabel = QLabel("Salesman")
        self.salesman = QComboBox()
        self.salesman.setMinimumWidth(200)
        top_row.addWidget(customerlabel)
        top_row.addWidget(self.customer, 2)
        top_row.addSpacing(40)
        # top_row.addWidget(salesmanlabel)
        # top_row.addWidget(self.salesman, 2)
        self.layout.addLayout(top_row)
        
        
        
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
        
        product_label = QLabel("Product")
        # product_label.setFixedWidth(400)
        product_label.setStyleSheet(label_style)
        label_line.addWidget(product_label, 4)

        qty_label = QLabel("Qty")
        # qty_label.setFixedWidth(100)
        qty_label.setStyleSheet(label_style)
        label_line.addWidget(qty_label, 1)

        rate_label = QLabel("Unit Rate")
        # rate_label.setFixedWidth(100)
        rate_label.setStyleSheet(label_style)
        label_line.addWidget(rate_label, 1)
        
        discount_label = QLabel("Discount %")
        # rate_label.setFixedWidth(200)
        discount_label.setStyleSheet(label_style)
        label_line.addWidget(discount_label, 1)
        
        tax_label = QLabel("Tax %")
        # rate_label.setFixedWidth(100)
        tax_label.setStyleSheet(label_style)
        label_line.addWidget(tax_label, 1)
        
        total_label = QLabel("Amount")
        # total_label.setFixedWidth(100)
        total_label.setStyleSheet(label_style)
        label_line.addWidget(total_label, 1)
        
        empty_label = QLabel("")
        # empty_label.setFixedWidth(100)
        empty_label.setStyleSheet(label_style)
        label_line.addWidget(empty_label, 1)
        



        self.layout.addLayout(label_line)



       
        
        
        self.item = QComboBox()
        self.item.wheelEvent = lambda event: event.ignore()
        self.item.setPlaceholderText("select product")
        self.item.setEditable(True)
        
        line_edit = self.item.lineEdit()
        line_edit.textEdited.connect(self.force_uppercase)

        line_edit = SelectAllLineEdit()
        self.item.setLineEdit(line_edit)

        # self.item.lineEdit().editingFinished.connect(lambda c=self.item: self.handle_editing_finished(c))

        completer = QCompleter()
        self.item.setCompleter(completer)
        completer.setCompletionMode(QCompleter.PopupCompletion)

        completer.activated[str].connect(lambda text, c=self.item: self.on_completer_selected(text, c))

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

        self.item.lineEdit().textEdited.connect(
            lambda text: self.load_product_suggestions(self.item, completer)
        )
        
        
        
        entry_line = QHBoxLayout()
        
        # self.item.setFixedWidth(400)
        
        self.item.setStyleSheet(label_style)
        entry_line.addWidget(self.item, 4)
        
        self.qty_edit = QLineEdit()
        self.qty_edit.setPlaceholderText("qty")
        # self.qty_edit.setFixedWidth(100)
        self.qty_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.qty_edit, 1)
        
        self.rate_edit = QLineEdit()
        self.rate_edit.setPlaceholderText("rate")
        # self.rate_edit.setFixedWidth(100)
        self.rate_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.rate_edit, 1)
        
        self.discount = KeyUpLineEdit()
        self.discount.setPlaceholderText("Disc %")
        # self.discount.setFixedWidth(100)
        self.discount.setStyleSheet(label_style)
        entry_line.addWidget(self.discount, 1)
        
        self.tax = KeyUpLineEdit()
        self.tax.setPlaceholderText("Tax %")
        self.tax.setStyleSheet(label_style)
        entry_line.addWidget(self.tax, 1)

        self.amount_edit = QLineEdit()
        self.amount_edit.setReadOnly(True)
        # self.amount_edit.setFixedWidth(100)
        self.amount_edit.setText("0.00")
        self.amount_edit.setStyleSheet("font-weight: bold;")
        self.amount_edit.setStyleSheet(label_style)
        entry_line.addWidget(self.amount_edit, 1)
        
        
        self.qty_edit.returnPressed.connect(lambda: self.focus_next_field(self.rate_edit))
        self.rate_edit.returnPressed.connect(lambda: self.focus_next_field(self.discount))
        self.discount.returnPressed.connect(lambda: self.focus_next_field(self.tax))
        self.tax.returnPressed.connect(lambda: self.focus_next_field(add_button))
        

        self.qty_edit.textChanged.connect(self.update_line_total)
        self.rate_edit.textChanged.connect(self.update_line_total)

        self.discount.textChanged.connect(self.update_line_total)
        self.tax.textChanged.connect(self.update_line_total)
        
        
        add_button = QPushButton("Add", objectName="SaveButton")
        entry_line.addWidget(add_button, 1)
        
        
        add_button.clicked.connect(self.add_row)        
        
        self.layout.addLayout(entry_line)

        # === Table ===
        self.row_height = 40
        self.min_visible_rows = 5


        self.table = MyTable(column_ratios=[0.05, 0.35, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.05])
        headers = ["#", " Product Description", " Qty", "Unit Rate", "Disc %", "Tax %", "Total", "X"]
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
        
      

        ### --- calculate label 
        
        
        calculate_labels_layout = QHBoxLayout()
        
        gross_label = QLabel("Gross Amount")
        calculate_labels_layout.addWidget(gross_label, 1)
        
        discount_label = QLabel("Discount")
        calculate_labels_layout.addWidget(discount_label, 1)
        
        taxable_label = QLabel("Taxable")
        calculate_labels_layout.addWidget(taxable_label, 1)
        
        tax_label = QLabel("Tax")
        calculate_labels_layout.addWidget(tax_label, 1)
        
        net_amount_label = QLabel("Net Amount")
        calculate_labels_layout.addWidget(net_amount_label, 1)
        
        additional_label = QLabel("Additional Charges")
        calculate_labels_layout.addWidget(additional_label, 1)
        
        final_label = QLabel("Final Amount")
        calculate_labels_layout.addWidget(final_label, 1)
        
        self.final_amount = QLabel("0.0")
        calculate_labels_layout.addWidget(self.final_amount, 1)
        
        
        self.layout.addLayout(calculate_labels_layout)
        
        
        
        calculate_entry_layout = QHBoxLayout()
        
        self.gross_entry = QLabel("0.00")
        calculate_entry_layout.addWidget(self.gross_entry, 1)
        
        self.discount_entry = QLineEdit()
        calculate_entry_layout.addWidget(self.discount_entry, 1)
        
        self.taxable_entry = QLabel("0.00")
        calculate_entry_layout.addWidget(self.taxable_entry, 1)
        
        self.tax_entry = QLineEdit()
        calculate_entry_layout.addWidget(self.tax_entry, 1)
        
        self.net_amount_entry = QLabel("0.00")
        calculate_entry_layout.addWidget(self.net_amount_entry, 1)
        
        self.additional_entry = QLineEdit()
        calculate_entry_layout.addWidget(self.additional_entry, 1)
        
        self.received_label = QLabel("Received Amount")
        calculate_entry_layout.addWidget(self.received_label, 1)
        
        self.received_amount = QLineEdit()
        calculate_entry_layout.addWidget(self.received_amount, 1)
        

        self.layout.addLayout(calculate_entry_layout)
        
        
        self.discount_entry.textChanged.connect(self.update_total_amount)
        self.tax_entry.textChanged.connect(self.update_total_amount)
        self.additional_entry.textChanged.connect(self.update_total_amount)
        
        self.received_amount.textChanged.connect(self.calculate_payment)
        
        
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
        addreceipt = QPushButton('Save Sales Receipt', objectName='SaveButton')
        addreceipt.setCursor(Qt.PointingHandCursor)
        addreceipt.clicked.connect(lambda: self.save_receipt())
        save_row.addWidget(addreceipt, 1)
        save_row.addStretch()
        
        
        
        


        QShortcut(QKeySequence("Ctrl+Return"), self, activated=lambda: self.save_receipt())
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=lambda: self.save_receipt())  

        
        self.setStyleSheet(load_stylesheets())
        self.layout.addStretch()
        
        
        
        
        
    def focus_next_field(self, widget):
        widget.setFocus()

        if hasattr(widget, "selectAll"):
            widget.selectAll()
        

    
    
    def eventFilter(self, obj, event):
        
        if obj == self.customer.lineEdit():
            if event.type() == QEvent.FocusIn:
                obj.selectAll()
        return super().eventFilter(obj, event)
    
    
    
   

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
        
        finalamount = self.final_amount.text()
        finalamount = float(finalamount) if finalamount else 0.00

        received = self.received_amount.text()
        received = float(received) if received else 0.00

        remaining = finalamount - received
        self.remainingdata.setText(str(remaining))
        
    
        
    

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
        
        self.table.setRowHeight(row, self.row_height)
        
        self.table.insertRow(row)
        
        counter = QLabel()
        counter.setText(str(row + 1))
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
        
        rate_edit = QLineEdit()
        rate_edit.setReadOnly(True)
        rate_edit.setText(rate_data)
        
        discount = QLineEdit()
        discount.setReadOnly(True)
        discount.setText(discount_data)
        
        tax = QLineEdit()
        tax.setReadOnly(True)
        tax.setText(tax_data)
        
        amount_edit = QLineEdit()
        amount_edit.setReadOnly(True)
        amount_edit.setText(total_data)
        
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
        
        self.qty_edit.clear()
        self.rate_edit.clear()
        self.discount.clear()
        self.tax.clear()
        
        # clear combo field
        self.item.setCurrentIndex(-1)
        

    
    
    
    
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
            self.flat_discount.setText(f"{discount_amount:.2f}")
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
            flat_discount = self.flat_discount.text()

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

        
        

        
    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        
        if not self.reloading_sale:
            
            self.populate_customer()
            self.populate_salesman()




    def populate_customer(self):
    
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
    
    
    
    
    def find_customer_by_name(self, name):
    
        name = name.strip().lower()

        for i in range(self.customer.count()):
            text = self.customer.itemText(i).strip().lower()
            if text == name:
                return self.customer.itemData(i)

        return None
    
    
    
    def resolve_customer_for_sale(self):
    
        typed_name = self.customer.currentText().strip()

        if not typed_name or typed_name.lower() == "walk-in customer":
            return None

        existing_customer_id = self.find_customer_by_name(typed_name)

        if existing_customer_id is not None:
            return existing_customer_id

        reply = QMessageBox.question(
            self,
            "Add Customer",
            f'"{typed_name}" not found.\nWould you like to add it as a new customer?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            new_customer_id = self.insert_customer_quick(typed_name)
            if new_customer_id:
                self.customer.addItem(typed_name, new_customer_id)
                self.customer.setCurrentText(typed_name)
                return new_customer_id

        return None
    
    
    
    
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
    
    
    
    # def populate_customer(self):
        
    #     self.customer.clear()
        
    #     query = QSqlQuery()

    #     self.customer.addItem("Walk-in Customer")
        
    #     if query.exec("SELECT id, name, contact FROM customer WHERE status = 'active';"):
    #         while query.next():
    #             customer_id = query.value(0)
    #             customer = query.value(1)
    #             contact = query.value(2)
                
    #             customer = f'{customer}  [ {contact} ]'

    #             self.customer.addItem(customer, customer_id)  # Text shown, ID stored as data

    #     else:
    #         QMessageBox.information(None, 'Error', query.lastError().text())




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
        
        # reply = QMessageBox.question(
        #     self,
        #     "Confirm Sale",
        #     "Do you want to proceed and save this sale?",
        #     QMessageBox.Yes | QMessageBox.No,
        #     QMessageBox.No
        # )

        # if reply == QMessageBox.Yes:
        #     # 👉 Place your DB insert logic here
        #     print("Sale stored in database.")
        #     return True
        # else:
        #     print("Sale ignored.")
        #     return False
        
        return True
        
        
        
    # def insert_salesreceipt(self):
        
    #     try:
    #         # --- Collect Data ---
    #         customer_id = self.resolve_customer_for_sale()
    #         customer = self.customer.currentData()
    #         salesman = self.salesman.currentData()

    #         # Convert numeric fields safely
    #         def to_float(value):
    #             value = str(value).strip()
    #             return float(value) if value else 0.0

    #         subtotal = to_float(self.gross_entry.text())
    #         discount = to_float(self.discount_entry.text())
    #         taxable = to_float(self.taxable_entry.text())
    #         tax = to_float(self.tax_entry.text())
    #         net_amount = to_float(self.net_amount_entry.text())
    #         additional_charges = to_float(self.additional_entry.text())
    #         total = to_float(self.final_amount.text())
    #         received = to_float(self.received_amount.text())
    #         remaining = to_float(self.remainingdata.text())

    #         # --- Basic Validation ---
    #         if salesman is None:
    #             QMessageBox.warning(self, "Validation Error", "Salesman is required.")
    #             return None

    #         if total < 0:
    #             QMessageBox.warning(self, "Validation Error", "Total cannot be negative.")
    #             return None

    #         if received < 0:
    #             QMessageBox.warning(self, "Validation Error", "Received amount cannot be negative.")
    #             return None

    #         # Normalize customer (NULL if empty)
    #         customer_id = customer if customer else None

    #         writeoff = payable = receiveable = 0.0

    #         if remaining > 0:
    #             if self.writeoff_check.isChecked():
    #                 writeoff = remaining
    #             else:
    #                 if customer_id is None:
    #                     QMessageBox.information(
    #                         self,
    #                         'Error',
    #                         "Walk-In Customer Can't Have Remaining Amount\nReceive Full amount or Write off"
    #                     )
    #                     return None
    #                 receiveable = remaining

    #         elif remaining < 0:
    #             payable = abs(remaining)

    #         # Walk-in customer cannot carry balance
    #         if customer_id is None:
    #             payable = receiveable = 0.0

            
    #         print("Writeoff: ", writeoff)
    #         print("Payable", payable)
    #         print("Receiveables", receiveable)
            

    #         # --- Insert Query ---
    #         query = QSqlQuery()
    #         query.prepare("""
    #             INSERT INTO sales
    #             (customer, salesman, subtotal, discount, taxable, tax,
    #             net_amount, additional_charges, total, received,
    #             remaining, writeoff, payable, receiveable)
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         """)

    #         query.addBindValue(customer_id)
    #         query.addBindValue(salesman)
    #         query.addBindValue(subtotal)
    #         query.addBindValue(discount)
    #         query.addBindValue(taxable)
    #         query.addBindValue(tax)
    #         query.addBindValue(net_amount)
    #         query.addBindValue(additional_charges)
    #         query.addBindValue(total)
    #         query.addBindValue(received)
    #         query.addBindValue(remaining)
    #         query.addBindValue(writeoff)
    #         query.addBindValue(payable)
    #         query.addBindValue(receiveable)

    #         if not query.exec():
    #             QMessageBox.critical(self, "Database Error", query.lastError().text())
    #             return None

    #         sales_id = query.lastInsertId()
    #         print("Sales record inserted. ID:", sales_id)
            
            
    #         self.insert_customer_transaction(sales_id, customer_id, total, received,remaining, salesman)
            
            

    #         return sales_id

    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", str(e))
    #         return None

    
    
    
    def insert_salesreceipt(self):
    
        try:
            # --- Collect Data ---
            customer_id = self.resolve_customer_for_sale()
            salesman = self.salesman.currentData()

            def to_float(value):
                value = str(value).strip()
                return float(value) if value else 0.0

            subtotal = to_float(self.gross_entry.text())
            discount = to_float(self.discount_entry.text())
            taxable = to_float(self.taxable_entry.text())
            tax = to_float(self.tax_entry.text())
            net_amount = to_float(self.net_amount_entry.text())
            additional_charges = to_float(self.additional_entry.text())
            total = to_float(self.final_amount.text())
            received = to_float(self.received_amount.text())
            remaining = to_float(self.remainingdata.text())

            # --- Basic Validation ---
            if salesman is None:
                QMessageBox.warning(self, "Validation Error", "Salesman is required.")
                return None

            if total < 0:
                QMessageBox.warning(self, "Validation Error", "Total cannot be negative.")
                return None

            if received < 0:
                QMessageBox.warning(self, "Validation Error", "Received amount cannot be negative.")
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
                remaining, writeoff, payable, receiveable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

            if not query.exec():
                QMessageBox.critical(self, "Database Error", query.lastError().text())
                return None

            sales_id = query.lastInsertId()
            print("Sales record inserted. ID:", sales_id)

            self.insert_customer_transaction(
                sales_id, customer_id, total, received, remaining, salesman
            )

            return sales_id

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return None
        
    
    

    # def insert_customer_transaction(self, sales_id, customer_id,
    #                             total_amount, received,
    #                             remaining, salesman_id):

    #     try:
    #         payable_before = 0.0
    #         receiveable_before = 0.0

    #         db = QSqlDatabase.database()

    #         # --- Fetch Existing Balance ---
    #         if customer_id is not None:
    #             balance_query = QSqlQuery()
    #             balance_query.prepare("""
    #                 SELECT payable, receiveable
    #                 FROM customer
    #                 WHERE id = ?
    #             """)
    #             balance_query.addBindValue(customer_id)

    #             if not balance_query.exec() or not balance_query.next():
    #                 raise Exception("Failed to fetch customer balance.")

    #             payable_before = float(balance_query.value(0) or 0.0)
    #             receiveable_before = float(balance_query.value(1) or 0.0)

    #         # --- Determine Current Impact ---
    #         payable_now = 0.0
    #         receiveable_now = 0.0

    #         if remaining > 0:
    #             receiveable_now = remaining
    #         elif remaining < 0:
    #             payable_now = abs(remaining)

    #         payable_after = payable_before + payable_now
    #         receiveable_after = receiveable_before + receiveable_now

    #         # --- Insert Transaction Record ---
    #         insert_txn = QSqlQuery()
    #         insert_txn.prepare("""
    #             INSERT INTO customer_transaction
    #             (customer, transaction_type, ref,
    #             payable_before, due_amount, paid, remaining_due, payable_after,
    #             receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
    #             salesman, note)
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         """)

    #         insert_txn.addBindValue(customer_id)
    #         insert_txn.addBindValue("SALE")
    #         insert_txn.addBindValue(sales_id)

    #         insert_txn.addBindValue(payable_before)
    #         insert_txn.addBindValue(total_amount)
    #         insert_txn.addBindValue(received)
    #         insert_txn.addBindValue(max(remaining, 0))
    #         insert_txn.addBindValue(payable_after)

    #         insert_txn.addBindValue(receiveable_before)
    #         insert_txn.addBindValue(receiveable_now)
    #         insert_txn.addBindValue(received)
    #         insert_txn.addBindValue(max(remaining, 0))
    #         insert_txn.addBindValue(receiveable_after)

    #         insert_txn.addBindValue(salesman_id)
    #         insert_txn.addBindValue(f"Sale ID {sales_id} recorded with total {total_amount}, received {received}, remaining {remaining}")
    #         if not insert_txn.exec():
    #             raise Exception(insert_txn.lastError().text())

    #         # --- Update Customer Master ---
    #         if customer_id is not None:
    #             update_customer = QSqlQuery()
    #             update_customer.prepare("""
    #                 UPDATE customer
    #                 SET payable = ?, receiveable = ?
    #                 WHERE id = ?
    #             """)
    #             update_customer.addBindValue(payable_after)
    #             update_customer.addBindValue(receiveable_after)
    #             update_customer.addBindValue(customer_id)

    #             if not update_customer.exec():
    #                 raise Exception(update_customer.lastError().text())

    #         return True

    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", str(e))
    #         return False


        
    def insert_customer_transaction(self, sales_id, customer_id,
                                total_amount, received,
                                remaining, salesman_id):

        if customer_id is None:
            return True

        payable_before = 0.0
        receiveable_before = 0.0

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

        payable_now = 0.0
        receiveable_now = 0.0

        if remaining > 0:
            receiveable_now = remaining
        elif remaining < 0:
            payable_now = abs(remaining)

        payable_after = payable_before + payable_now
        receiveable_after = receiveable_before + receiveable_now

        insert_txn = QSqlQuery()
        insert_txn.prepare("""
            INSERT INTO customer_transaction
            (customer, transaction_type, ref,
             payable_before, due_amount, paid, remaining_due, payable_after,
             receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
             salesman, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        insert_txn.addBindValue(customer_id)
        insert_txn.addBindValue("SALE")
        insert_txn.addBindValue(sales_id)

        insert_txn.addBindValue(payable_before)
        insert_txn.addBindValue(total_amount)
        insert_txn.addBindValue(received)
        insert_txn.addBindValue(max(remaining, 0))
        insert_txn.addBindValue(payable_after)

        insert_txn.addBindValue(receiveable_before)
        insert_txn.addBindValue(receiveable_now)
        insert_txn.addBindValue(received)
        insert_txn.addBindValue(max(remaining, 0))
        insert_txn.addBindValue(receiveable_after)

        insert_txn.addBindValue(salesman_id)
        insert_txn.addBindValue(
            f"Sale ID {sales_id} recorded with total {total_amount}, received {received}, remaining {remaining}"
        )

        if not insert_txn.exec():
            raise Exception(insert_txn.lastError().text())

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
        
        
      
        
        
    # def insert_salesitems(self, sales_id):
        
        
    #     print("About to INSERT sales items with FIFO allocation for sales ID:", sales_id)
        
    #     try:
            
    #         def to_float(value):
    #             value = str(value).strip()
    #             return float(value) if value else 0.0

    #         subtotal = to_float(self.gross_entry.text())
    #         header_discount = to_float(self.discount_entry.text())
    #         header_tax = to_float(self.tax_entry.text())
    #         additional_charges = to_float(self.additional_entry.text())
            

    #         for row in range(self.table.rowCount()):

    #             product_widget = self.table.cellWidget(row, 1)
    #             if not product_widget:
    #                 continue

    #             product_id = product_widget.currentData()
    #             product_id = product_id.get("product_id")
    #             if not product_id:
    #                 continue
                
    #             print("Processing row ", row, " with Product ID: ", product_id)
    #             product_id = int(product_id)

    #             qty = int(self.table.cellWidget(row, 2).text())
    #             rate = float(self.table.cellWidget(row, 3).text())
    #             discount = float(self.table.cellWidget(row, 4).text())
    #             tax = float(self.table.cellWidget(row, 5).text())
    #             line_total = float(self.table.cellWidget(row, 6).text()) 
                
                
    #             # line weight
    #             line_weight = 0.0
    #             if subtotal > 0:
    #                 line_weight = line_total / subtotal
                    
                
                
    #             line_header_discount = header_discount * line_weight
    #             line_header_tax = header_tax * line_weight
    #             line_additional_charges = additional_charges * line_weight
                
    #             print("Line Weight: ", line_weight, " Line Header Discount: ", line_header_discount, " Line Header Tax: ", line_header_tax, " Line Additional Charges: ", line_additional_charges)
                
    #             effective_line_total = line_total - line_header_discount + line_header_tax + line_additional_charges
    #             effective_line_total = round(effective_line_total, 2)
                
    #             print("RECEIVED all the data now checking validation")
    #             print("Data is: Product ID:", product_id, " Qty: ", qty, " Rate: ", rate, " Discount: ", discount, " Tax: ", tax, " Line Total: ", line_total)

    #             if qty <= 0:
    #                 raise Exception("Invalid quantity.")

    #             # --- Check Stock Availability ---
    #             stock_query = QSqlQuery()
    #             stock_query.prepare("""
    #                 SELECT SUM(quantity_remaining)
    #                 FROM batch
    #                 WHERE product_id = ?
    #             """)
    #             stock_query.addBindValue(product_id)

    #             if not stock_query.exec() or not stock_query.next():
    #                 raise Exception("Stock check failed.")

    #             total_available = stock_query.value(0) or 0
                
    #             print("Available Stock is: ", total_available)

    #             if qty > total_available:
    #                 raise Exception(f"Insufficient stock for product {product_id}")

    #             # --- Insert Sales Item (temporary COGS = 0) ---
    #             insert_item = QSqlQuery()
    #             insert_item.prepare("""
    #                 INSERT INTO salesitem
    #                 (sales_id, product_id, qty_sold, unit_price,
    #                 discount, tax, line_total, line_weight, effective_line_total)
    #                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    #             """)
                
    #             print("Inserting Data into salesitem table...")
    #             print("Data is: Sales ID:", sales_id, " Product ID:", product_id, " Qty: ", qty, " Rate: ", rate, " Discount: ", discount, " Tax: ", tax, " Line Total: ", line_total, " Effective Line Total: ", effective_line_total)


    #             insert_item.addBindValue(sales_id)
    #             insert_item.addBindValue(product_id)
    #             insert_item.addBindValue(qty)
    #             insert_item.addBindValue(rate)
    #             insert_item.addBindValue(discount)
    #             insert_item.addBindValue(tax)
    #             insert_item.addBindValue(line_total)
    #             insert_item.addBindValue(line_weight)
    #             insert_item.addBindValue(effective_line_total)

    #             if not insert_item.exec():
    #                 raise Exception(insert_item.lastError().text())

    #             sale_item_id = insert_item.lastInsertId()
    #             print("Sales Item Id is: ", sale_item_id)

    #             # --- FIFO Allocation ---
    #             remaining_qty = qty

    #             batch_query = QSqlQuery()
    #             batch_query.prepare("""
    #                 SELECT id, quantity_remaining, unit_cost
    #                 FROM batch
    #                 WHERE product_id = ?
    #                 AND quantity_remaining > 0
    #                 ORDER BY received_at ASC, id ASC
    #             """)
    #             batch_query.addBindValue(product_id)
                
                

    #             if not batch_query.exec():
    #                 raise Exception(batch_query.lastError().text())

    #             while batch_query.next() and remaining_qty > 0:

    #                 batch_id = batch_query.value(0)
    #                 available = batch_query.value(1)
    #                 unit_cost = batch_query.value(2) or None

    #                 take_qty = min(available, remaining_qty)
    #                 if unit_cost is not None:
    #                     line_cost = take_qty * unit_cost
    #                 else:
    #                     line_cost = None
                        
                    
    #                 print("Batch Data is: ", batch_id, available, unit_cost, " Taking Qty: ", take_qty, " Line Cost: ", line_cost)

    #                 # Deduct batch quantity
    #                 update_batch = QSqlQuery()
    #                 update_batch.prepare("""
    #                     UPDATE batch
    #                     SET quantity_remaining = quantity_remaining - ?
    #                     WHERE id = ?
    #                 """)
    #                 update_batch.addBindValue(take_qty)
    #                 update_batch.addBindValue(batch_id)

    #                 if not update_batch.exec():
    #                     raise Exception(update_batch.lastError().text())



    #                 print("Inserting into Sold Batch Items")
    #                 # Insert sold_batch record
    #                 insert_sold = QSqlQuery()
    #                 insert_sold.prepare("""
    #                     INSERT INTO sold_batch
    #                     (sale_item_id, batch_id, qty_taken, unit_cost, line_cost)
    #                     VALUES (?, ?, ?, ?, ?)
    #                 """)
    #                 insert_sold.addBindValue(sale_item_id)
    #                 insert_sold.addBindValue(batch_id)
    #                 insert_sold.addBindValue(take_qty)
    #                 insert_sold.addBindValue(unit_cost)
    #                 insert_sold.addBindValue(line_cost)
                    
    #                 print("Data for SOLD BATCH is: Sale Item ID: ", sale_item_id, " Batch ID: ", batch_id, " Qty Taken: ", take_qty, " Unit Cost: ", unit_cost, " Line Cost: ", line_cost)

    #                 if not insert_sold.exec():
    #                     raise Exception(insert_sold.lastError().text())
                    
    #                 # if line_cost is not None:
    #                 #     total_cogs += line_cost
    #                 # else:
    #                 #     total_cogs = None
                        
    #                 remaining_qty -= take_qty

    #             if remaining_qty > 0:
    #                 raise Exception("FIFO allocation failed.")

                

                

    #     except Exception as e:
    #         raise Exception("Failed to insert sales items.")
    
               
    
    
    
    # def insert_salesitems(self, sales_id):

    #     print("About to INSERT sales items with FIFO allocation for sales ID:", sales_id)

    #     def to_float(value):
    #         value = str(value).strip()
    #         return float(value) if value else 0.0

    #     subtotal = to_float(self.gross_entry.text())
    #     header_discount = to_float(self.discount_entry.text())
    #     header_tax = to_float(self.tax_entry.text())
    #     additional_charges = to_float(self.additional_entry.text())

    #     for row in range(self.table.rowCount()):

    #         product_widget = self.table.cellWidget(row, 1)
    #         if not product_widget:
    #             continue

    #         product_data = product_widget.currentData()
    #         if not product_data:
    #             continue

    #         product_id = product_data.get("product_id")
    #         if not product_id:
    #             continue

    #         print("Processing row", row, "with Product ID:", product_id)
    #         product_id = int(product_id)

    #         qty = int(self.table.cellWidget(row, 2).text())
    #         rate = float(self.table.cellWidget(row, 3).text())
    #         discount = float(self.table.cellWidget(row, 4).text())
    #         tax = float(self.table.cellWidget(row, 5).text())
    #         line_total = float(self.table.cellWidget(row, 6).text())

    #         line_weight = 0.0
    #         if subtotal > 0:
    #             line_weight = line_total / subtotal

    #         line_header_discount = header_discount * line_weight
    #         line_header_tax = header_tax * line_weight
    #         line_additional_charges = additional_charges * line_weight

    #         effective_line_total = line_total - line_header_discount + line_header_tax + line_additional_charges
    #         effective_line_total = round(effective_line_total, 2)

    #         if qty <= 0:
    #             raise Exception("Invalid quantity.")

    #         stock_query = QSqlQuery()
    #         stock_query.prepare("""
    #             SELECT SUM(quantity_remaining)
    #             FROM batch
    #             WHERE product_id = ?
    #         """)
    #         stock_query.addBindValue(product_id)

    #         if not stock_query.exec() or not stock_query.next():
    #             raise Exception("Stock check failed.")

    #         total_available = stock_query.value(0) or 0

    #         if qty > total_available:
    #             raise Exception(f"Insufficient stock for product {product_id}")

    #         insert_item = QSqlQuery()
    #         insert_item.prepare("""
    #             INSERT INTO salesitem
    #             (sales_id, product_id, qty_sold, unit_price,
    #             discount, tax, line_total, line_weight, effective_line_total)
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         """)

    #         insert_item.addBindValue(sales_id)
    #         insert_item.addBindValue(product_id)
    #         insert_item.addBindValue(qty)
    #         insert_item.addBindValue(rate)
    #         insert_item.addBindValue(discount)
    #         insert_item.addBindValue(tax)
    #         insert_item.addBindValue(line_total)
    #         insert_item.addBindValue(line_weight)
    #         insert_item.addBindValue(effective_line_total)

    #         if not insert_item.exec():
    #             raise Exception(insert_item.lastError().text())

    #         sale_item_id = insert_item.lastInsertId()
    #         remaining_qty = qty

    #         batch_query = QSqlQuery()
    #         batch_query.prepare("""
    #             SELECT id, quantity_remaining, unit_cost
    #             FROM batch
    #             WHERE product_id = ?
    #             AND quantity_remaining > 0
    #             ORDER BY received_at ASC, id ASC
    #         """)
    #         batch_query.addBindValue(product_id)

    #         if not batch_query.exec():
    #             raise Exception(batch_query.lastError().text())

    #         while batch_query.next() and remaining_qty > 0:
    #             batch_id = batch_query.value(0)
    #             # available = batch_query.value(1)
    #             # unit_cost = batch_query.value(2) if batch_query.value(2) is not None else None
                
    #             available = int(batch_query.value(1) or 0)
    #             raw_cost = batch_query.value(2)
    #             unit_cost = float(raw_cost) if raw_cost is not None else None

    #             take_qty = min(available, remaining_qty)
    #             line_cost = take_qty * unit_cost if unit_cost is not None else None

    #             update_batch = QSqlQuery()
    #             update_batch.prepare("""
    #                 UPDATE batch
    #                 SET quantity_remaining = quantity_remaining - ?
    #                 WHERE id = ?
    #             """)
    #             update_batch.addBindValue(take_qty)
    #             update_batch.addBindValue(batch_id)

    #             if not update_batch.exec():
    #                 raise Exception(update_batch.lastError().text())

    #             insert_sold = QSqlQuery()
    #             insert_sold.prepare("""
    #                 INSERT INTO sold_batch
    #                 (sale_item_id, batch_id, qty_taken, unit_cost, line_cost)
    #                 VALUES (?, ?, ?, ?, ?)
    #             """)
    #             insert_sold.addBindValue(sale_item_id)
    #             insert_sold.addBindValue(batch_id)
    #             insert_sold.addBindValue(take_qty)
    #             insert_sold.addBindValue(unit_cost)
    #             insert_sold.addBindValue(line_cost)

    #             if not insert_sold.exec():
    #                 raise Exception(insert_sold.lastError().text())

    #             remaining_qty -= take_qty

    #         if remaining_qty > 0:
    #             raise Exception("FIFO allocation failed.")

    #     return True
    
    
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
        
    
    
        
    # def load_product_suggestions(self, item, completer):

    #     print("Loading Product Suggestions")

    #     current_text = item.currentText().strip()

    #     if not current_text:
    #         return

    #     # Clear old suggestions
    #     item.blockSignals(True)
    #     item.clear()
    #     item.blockSignals(False)

    #     query = QSqlQuery()
    #     query.prepare("""
    #         SELECT p.id, p.display_name, pp.unit_price
    #         FROM product p
    #         LEFT JOIN price_pack pp ON pp.product_id = p.id
    #         WHERE p.display_name LIKE ?
    #         LIMIT 10
    #     """)
    #     query.addBindValue(f"%{current_text}%")

    #     products = []

    #     if query.exec():
    #         while query.next():
    #             product_id = query.value(0)
    #             name = query.value(1)
    #             unit_price = query.value(2) or 0.0

    #             label = name.strip()

    #             products.append(label)

    #             item.addItem(label, {
    #                 "product_id": product_id,
    #                 "unit_price": unit_price
    #             })

    #     model = QStringListModel(products)
    #     completer.setModel(model)
        
    #     completer.activated[str].connect(partial(self.on_completer_selected, item=item))

    #     # DO NOT connect signals here
    #     item.lineEdit().setText(current_text)
        
    
    
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
            product_data.append((
                name,
                {
                    "product_id": product_id,
                    "unit_price": unit_price
                }
            ))

        item.blockSignals(True)
        item.clear()

        for name, data in product_data:
            item.addItem(name, data)

        item.setCurrentIndex(-1)
        item.lineEdit().setText(current_text)
        item.blockSignals(False)

        model = QStringListModel(products)
        completer.setModel(model)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        completer.complete()
       
        
        
    def on_completer_selected(self, text, item):

        index = item.findText(text, Qt.MatchFixedString)
        if index < 0:
            return
        
        item.setCurrentIndex(index) 
        data = item.itemData(index)

        if not data:
            return

        unit_price = data.get("unit_price")

        if unit_price is not None:
            self.rate_edit.setText(f"{float(unit_price):.2f}")
            
            
        # move to next field
        self.qty_edit.setFocus()
        self.qty_edit.selectAll()
    
    
        
            


    # def on_item_selected(self, item):
        
    #     text = item.currentText()
    #     data = item.currentData()

        
    #     print("Selected text is: ",text, data)
    #     data = int(data)
        
    #     query = QSqlQuery()
    #     query.prepare("""
    #         SELECT * FROM product
    #         WHERE id = ? """)
        
    #     query.addBindValue(data)
        
    #     if not query.exec():
            
    #         print("Cannot Get the product")
            
    #     else:
            
    #         print("Got the product")
                
      



    def update_total_amount(self):
        
        
        subtotal = 0.00
        for row in range(self.table.rowCount()):
            
            linetotal = self.table.cellWidget(row, 6).text()
            
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
        
        tax = self.tax_entry.text()
        tax = float(tax) if tax else 0.00
        
        net_amount = taxable + tax
        
        self.net_amount_entry.setText(f"{net_amount:.2f}")
        
        cn_adjust = self.additional_entry.text()
        cn_adjust = float(cn_adjust) if cn_adjust else 0.00
        
        final_amount = net_amount + cn_adjust
        self.final_amount.setText(f"{final_amount:.2f}")
        
        self.final_amount.setStyleSheet("font-weight: bold;")
        
    

    
    
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
        line_edit = self.name_input.lineEdit()
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
        self.final_amount.clear()
        self.received_amount.clear()
        self.remainingdata.clear()
        self.additional_entry.clear()
        
        
        self.writeoff_check.setChecked(True)        
        
        self.table.setRowCount(0)
        
        self.populate_customer()
        
        self.table.setRowCount(0)
        
        


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
            
    
   
