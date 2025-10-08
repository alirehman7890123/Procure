
from PySide6.QtWidgets import QWidget, QCompleter, QHBoxLayout, QFrame , QDateEdit,  QVBoxLayout, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QStringListModel, QDate, QDateTime, QTimer, Signal
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import QPalette, QColor, QKeyEvent
from functools import partial
import csv    
import os
import math
from utilities.stylus import load_stylesheets






class KeyUpLineEdit(QLineEdit):
    keyReleased = Signal(QKeyEvent)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.keyReleased.emit(event)





class AddPurchaseReturnWidget(QWidget):


    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Return Invoice", objectName="SectionTitle")
        self.invoicelist = QPushButton("Purchase Returns List", objectName="TopRightButton")
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

        self.supplier_edit = QComboBox()
        self.rep_edit = QComboBox()
        self.invoice_edit = QLineEdit()
        
        
        top_row.addWidget(supplier, 1)
        top_row.addWidget(self.supplier_edit, 2)
        
        top_row.addWidget(rep, 1)
        top_row.addWidget(self.rep_edit, 2)
        
        self.layout.addLayout(top_row)
        
        top_row.addSpacing(40)
        
        self.supplier_edit.currentIndexChanged.connect(self.populate_reps)

        
        
        self.row_height = 40
        self.min_visible_rows = 5
        
    
        self.table = MyTable(column_ratios=[0.03, 0.25, 0.07, 0.10, 0.05, 0.05, 0.07, 0.05, 0.07, 0.05, 0.07, 0.10, 0.05])
        headers = ["#", "Product", "Batch", "PO_Ref", "Purchased", "Return", "Rate", "Disc (%)", "Tax (%)", "PO % Disc", "PO % Tax", "Total", "X"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        
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
        self.layout.addWidget(self.table)
        
        
        self.layout.addStretch()
        
         # === Add Row Button ===
        add_button_row = QHBoxLayout()
        self.add_button = QPushButton("Add Row", objectName='TopRightButton')
        
        self.add_button.clicked.connect(self.add_row)
        add_button_row.addWidget(self.add_button, stretch=1)
        self.layout.addLayout(add_button_row)
        
        
        
        # === Subtotal Row ===
        subtotal_row = QHBoxLayout()
        
        subtotal_label = QLabel("Sub Total")
        subtotal_label.setMinimumWidth(200)
        self.subtotal = QLabel("0.00")

        subtotal_row.addWidget(subtotal_label)
        subtotal_row.addWidget(self.subtotal)
        
        self.layout.addLayout(subtotal_row)
        
        # === roundoff Row ===
        roundoff_row = QHBoxLayout()
        
        roundoff_label = QLabel("Round Off")
        self.roundoff = QLabel("0.00")
        
        roundoff_row.addWidget(roundoff_label)
        roundoff_row.addWidget(self.roundoff)
        
        self.layout.addLayout(roundoff_row)
        
        # === Final Amount Row ===
        final_amount_row = QHBoxLayout()
        
        final_amount = QLabel("Final Amount")
        self.final_amountdata = QLabel("0.00")
        
        final_amount_row.addWidget(final_amount)
        final_amount_row.addWidget(self.final_amountdata)
        
        self.layout.addLayout(final_amount_row)

        
        
        
        
        
        receivelabel = QLabel("Received")
        self.receive_edit = QLineEdit()
        self.receive_edit.setPlaceholderText("0.00")
        
        self.receive_edit.textChanged.connect(self.calculate_payment)
        
        
        # 7th Line
        remaininglabel = QLabel("Remaining")
        self.remainingdata = QLabel("0.00")
        
        self.checkbox = QCheckBox("Write off")
        self.checkbox.toggled.connect(self.writeoffcheck)
        
        
        # 8th Line
        self.note = QLabel("Note")
        
        savereturn = QPushButton('Save Purchase Return', objectName='supplierlist')
        savereturn.setCursor(Qt.PointingHandCursor)
        
        savereturn.clicked.connect(lambda: self.save_purchase_return())
        
        self.layout.addStretch()
        
        self.setStyleSheet(load_stylesheets())
        


        
        
        
        
        
        

    
    def writeoffcheck(self):
        
        remaining = self.remainingdata.text()
        remaining = float(remaining) if remaining else 0
        
        if remaining > 0:
            
            if self.checkbox.isChecked():
                
                self.note.setText(f"Amount {remaining} will be wrote-off / Cleared")
            else:
                self.note.setText(f"Amount {remaining} will be added to receiveables")
        
        else:
            
            self.note.setText(f"Amount {remaining} is excessive and will be added to payables to supplier")    
    
    

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
                
        self.subtotal.setText(f"{subtotal:.2f}")
        
        
        rounded_total = math.floor(subtotal)
        roundoff = round(subtotal - rounded_total, 2)
        print("round off is: ", roundoff)
        # set Round off
        
        finaltotal = rounded_total
        
        self.roundoff.setText(f"{roundoff:.2f}")
        self.final_amountdata.setText(f"{finaltotal:.2f}")
        
        

    def calculate_payment(self):
        
        finalamount = self.final_amountdata.text()
        finalamount = float(finalamount) if finalamount else 0.00
        
        received = self.receive_edit.text()
        received = float(received) if received else 0.00
        
        remaining = finalamount - received
        self.remainingdata.setText(str(remaining))
        
        self.writeoffcheck()
         

       
        
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

        
        batch = QComboBox()
        batch.activated.connect(partial(self.on_batch_highlighted, item=batch))
        
        po_ref = QLabel()
        
        purchased_qty = QLabel()
        
        return_qty = QLineEdit()
        
        rate = QLabel()
        rate.setText("0.00")
        
        discount = QLabel()
        discount.setText("0.00")
        
        tax = QLabel()
        tax.setText("0.00")
        
        po_discount = QLabel()
        po_discount.setText("0.00")
        
        po_tax = QLabel()
        po_tax.setText("0.00")
        
        total_edit = QLineEdit()
        total_edit.setReadOnly(True)
        total_edit.setText("0.00")
        

        remove_btn = QPushButton("x")
        remove_btn.setCursor(Qt.PointingHandCursor)
        
        
        self.table.setCellWidget(row, 0, counter)
        self.table.setCellWidget(row, 1, product)
        self.table.setCellWidget(row, 2, batch)
        self.table.setCellWidget(row, 3, po_ref)
        self.table.setCellWidget(row, 4, purchased_qty)
        self.table.setCellWidget(row, 5, return_qty)
        self.table.setCellWidget(row, 6, rate)
        self.table.setCellWidget(row, 7, discount)
        self.table.setCellWidget(row, 8, tax)
        self.table.setCellWidget(row, 9, po_discount)
        self.table.setCellWidget(row, 10, po_tax)
        self.table.setCellWidget(row, 11, total_edit)
        self.table.setCellWidget(row, 12, remove_btn)
        
        
        return_qty.textChanged.connect(lambda _: self.update_amount(return_qty))
        remove_btn.clicked.connect(lambda _, r=row: self.remove_row(r))

        self.update_table_height()
        
        

    def remove_row(self, target_row):
        self.table.removeRow(target_row)

        # Reconnect all remove buttons with updated row numbers
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 11)
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
        print("Widget shown — refreshing data")
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
        
    
    
    def save_purchase_return(self):
        
        
        db = QSqlDatabase.database()
        db.transaction()
        
        try: 
        
            supplier = self.supplier_edit.currentData()
            rep = self.rep_edit.currentData()
            
            if supplier is None or rep is None:
                
                QMessageBox.warning(None, "Error", "Please select a supplier and a seller representative.")
                return
            
            
            subtotal = self.subtotal.text()
            roundoff = self.roundoff.text()
            total = self.final_amountdata.text()
            received = self.receive_edit.text()
            remaining = self.remainingdata.text()
            
            
            subtotal = float(subtotal) if subtotal else 0
            roundoff = float(roundoff) if roundoff else 0
            total = float(total) if total else 0
            received = float(received) if received else 0
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
                payable = 0.0
                receiveable = remaining
                
            else:
                
                writeoff = 0.0
                payable = abs(remaining)
                receiveable = 0.0
                
            
        
            query = QSqlQuery()
            
            query.prepare("""
                INSERT INTO purchase_return (supplier, rep, subtotal, roundoff, total, received, remaining, writeoff, payable, receiveable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """)                   
                    
            query.addBindValue(supplier)
            query.addBindValue(rep)
            
            query.addBindValue(subtotal)
            query.addBindValue(roundoff)
            query.addBindValue(total)
            
            query.addBindValue(received)
            query.addBindValue(remaining)
            query.addBindValue(writeoff)
            
            query.addBindValue(payable)
            query.addBindValue(receiveable)
            
            print("Prepared Query: ", query.lastQuery())
                
            if not query.exec():
                print("Insert failed:", query.lastError().text())
            else:
                QMessageBox.information(None, "Success", 'Purchase Return Saved Successfully')
                return_id = query.lastInsertId()
                
            
            
            print("About to add purchase transaction")
            
            
            #####################################
            ####    PURCHASE TRANSACTIONS    ####
            #####################################
            
            supplier = int(supplier)
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
            
            
            transaction_type = 'purchase return'
            ref_no = None
            return_ref = return_id
            
            payable_before = supplier_payable
            due_amount = 0.00
            paid = 0.00
            remaining_due = 0.00
            payable_after = supplier_payable
            
            receiveable_before = supplier_receiveable
            receiveable_now = total
            received = received
            remaining_now = total - received
            receiveable_after = receiveable_before + total - received
            
            print("about to insert transaction")
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
                print("Transaction is saved ...")
                QMessageBox.information(None, "Success", "Supplier Transaction Stored Successfully with ID: " + str(insert_id) )
                
                
            else:
                print("COULD NOT ADD TRANSACTION...")
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
                
                print("Med Widget is: ", product_widget.currentData())
                
                if not product_widget or not product_widget.currentData():
                    print("Row is empty ... ignoring it...")
                    continue

                product_id = product_widget.currentData()
                item_exist = True
                
                try:
                    
                    batch = self.table.cellWidget(row, 2).currentText()
                    po_ref = self.table.cellWidget(row, 3).text()
                    purchased = self.table.cellWidget(row, 4).text()
                    returned = int(self.table.cellWidget(row, 5).text())
                    rate = float(self.table.cellWidget(row, 6).text())
                    discount = float(self.table.cellWidget(row, 7).text())
                    tax = float(self.table.cellWidget(row, 8).text())
                    po_discount = float(self.table.cellWidget(row, 9).text())
                    po_tax = float(self.table.cellWidget(row, 10).text())
                    total = float(self.table.cellWidget(row, 11).text())
                    
                    
                    # get the purchase order by
                    
                    
                    
                    
                except (ValueError, AttributeError):
                    
                    print("Invalid data in row", row, "- skipping this row")
                    continue


                item_query = QSqlQuery()
                item_query.prepare("""
                    INSERT INTO purchase_return_item (purchase_return, po_ref, product, batch, purchased, returned, rate, discount, tax, po_discount, po_tax, total)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """)
                
                item_query.addBindValue(return_id)
                item_query.addBindValue(po_ref)
                item_query.addBindValue(product_id)
                item_query.addBindValue(batch)
                item_query.addBindValue(purchased)
                item_query.addBindValue(returned)
                item_query.addBindValue(rate)
                item_query.addBindValue(discount)
                item_query.addBindValue(tax)
                item_query.addBindValue(po_discount)
                item_query.addBindValue(po_tax)
                item_query.addBindValue(total)

                if not item_query.exec():
                    print("Error inserting purchaseitem:", item_query.lastError().text())
                
                else:
                    print("Purchase item inserted successfully")
                    item = item_query.lastInsertId()
                    
                    

                # ✅ Check and update stock
                stock_query = QSqlQuery()
                stock_query.prepare("SELECT packsize, units FROM stock WHERE product = ?")
                stock_query.addBindValue(product_id)

                if stock_query.exec() and stock_query.next():
                    
                    packsize = stock_query.value(0)
                    units = stock_query.value(1)
                    
                    newpacks = int(units) - returned

                    update_query = QSqlQuery()
                    
                    update_query.prepare("UPDATE stock SET packs = ? WHERE product = ?")
                    
                    update_query.addBindValue(newpacks)
                    update_query.addBindValue(product_id)

                    if update_query.exec():
                        
                        print("Stock decreased successfully")
                        print(f"Row {row}: product_id={product_id}, qty={returned}, rate={rate}, total={total}")

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
        
        print("Loading Medicine Suggestions")
        item = item
        completer = completer
        current_text = item.currentText() 
        print("Current Text is: ", current_text)
        
        if current_text == '':
            return 
        
        query = QSqlQuery()
        query.prepare("""
            SELECT id, name, form, strength
            FROM product
            WHERE name ILIKE ? LIMIT 10 """)
        
        value = f"%{current_text}%"
        query.addBindValue(value)
        
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
        
        
        

    def on_batch_highlighted(self, text, item):
        
        
        # Prevent redundant triggers for the same value
        # if hasattr(self, "_last_highlighted") and self._last_highlighted == text:
        #     return
        
        # self._last_highlighted = text
        
        # index = item.findText(text, Qt.MatchFixedString)
        # if index >= 0:
        #     item.setCurrentIndex(index)
            
            
        row = self.table.indexAt(item.pos()).row()
        batch = self.table.cellWidget(row, 2).currentText()
        
        self.table.cellWidget(row, 3).clear()
        
        
        print("Batch is: ", batch)

        stock_query = QSqlQuery()
        stock_query.prepare("SELECT purchaseitem FROM batch WHERE batch = ?")
        stock_query.addBindValue(batch)
        

        try:
            
            if stock_query.exec() and stock_query.next():
                
                purchaseitem = stock_query.value(0)
                purchaseitem = int(purchaseitem)
                
                print(f"Purchase item info is: {purchaseitem}")
                
                item_query = QSqlQuery()
                item_query.prepare("SELECT qty, rate, discount, tax, purchase FROM purchaseitem WHERE id = ?")
                item_query.addBindValue(purchaseitem)
                
                if item_query.exec() and item_query.next():
                    
                    self.table.cellWidget(row, 3).setText('')
                    
                    qty = item_query.value(0)
                    qty = str(qty)
                    rate = item_query.value(1)
                    rate = str(rate)
                    discount = item_query.value(2)
                    tax = item_query.value(3)
                    discount = str(discount)
                    tax = str(tax)
                    
                    purchase = item_query.value(4)
                    purchase = int(purchase)
                    
                    self.table.cellWidget(row, 3).setText(str(purchase))
                    self.table.cellWidget(row, 4).setText(qty)
                    self.table.cellWidget(row, 6).setText(rate)
                    self.table.cellWidget(row, 7).setText(discount)
                    self.table.cellWidget(row, 8).setText(tax)
                    
                    purchase_query = QSqlQuery()
                    purchase_query.prepare("SELECT id, discount, tax FROM purchase WHERE id = ?")
                    purchase_query.addBindValue(purchase)
                    
                    if purchase_query.exec() and purchase_query.next():
                        
                        self.table.cellWidget(row, 8).setText('')
                        self.table.cellWidget(row, 9).setText('')
                        
                        po = str(purchase_query.value(0))
                        po_discount = str(purchase_query.value(1))
                        po_tax = str(purchase_query.value(2))
                        
                        self.table.cellWidget(row, 8).setText(po_discount)
                        self.table.cellWidget(row, 9).setText(po_tax)
                        
                        
                    else:
                        QMessageBox.information(None, 'Error', purchase_query.lastError().text())
                
                else:
                    QMessageBox.information(None, 'Error', item_query.lastError().text())        
                    
            else:
                QMessageBox.information(None, 'Error', stock_query.lastError().text())

        except Exception as e:
                
            print(str(e))
        
        

    def on_completer_highlighted(self, text, item):
        
        
        # Prevent redundant triggers for the same value
        if hasattr(self, "_last_highlighted") and self._last_highlighted == text:
            return
        self._last_highlighted = text
        
        index = item.findText(text, Qt.MatchFixedString)
        if index >= 0:
            item.setCurrentIndex(index)
            
            
        row = self.table.indexAt(item.pos()).row()
        product_id = self.table.cellWidget(row, 1).currentData()
        
        self.table.cellWidget(row, 2).clear()
        
        
        print("Product id is: ", product_id)

        stock_query = QSqlQuery()
        stock_query.prepare("SELECT batch FROM batch WHERE product = ?")
        stock_query.addBindValue(product_id)
        

        try:
            
            if stock_query.exec():
                
                while stock_query.next():  
                      
                    batch = stock_query.value(0)
                    
                    print(f"Batch info is: {batch}")
                    
                    self.table.cellWidget(row, 2).addItem(batch)
                    
                
                widget = self.table.cellWidget(row, 2)
                self.table.cellWidget(row, 2).setCurrentIndex(0)
                self.table.cellWidget(row, 3).setText('')
                
                widget.activated.connect(partial(self.update_amount(widget)))
                
                
            else:
            
                QMessageBox.information(None, 'Error', stock_query.lastError().text())

        except Exception as e:
                
            print(str(e))
        
        


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
                
                



    def update_amount(self, edited_widget):
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            
            purchased = self.table.cellWidget(row, 4).text()
            
            qty_text = self.table.cellWidget(row, 5).text()
            
            if int(qty_text) > int(purchased):
                
                QMessageBox.information(None, "Error", "Quantity cannot be greater than purchased stock")
                self.table.cellWidget(row, 5).setText("0")
                qty_text = 0
            
            rate_text = self.table.cellWidget(row, 6).text()
            
            discount_edit = self.table.cellWidget(row,7).text()
            tax_edit = self.table.cellWidget(row,8).text()
            
            po_discount = self.table.cellWidget(row, 9).text()
            po_tax = self.table.cellWidget(row, 10).text()

            qty = int(qty_text) if qty_text else 0
            rate = float(rate_text) if rate_text else 0
            
            discount = float(discount_edit) if discount_edit else 0
            tax = float(tax_edit) if tax_edit else 0
            
            po_discount = float(po_discount) if po_discount else 0
            po_tax = float(po_tax) if po_tax else 0
            
            amount = qty * rate
            
            discount = amount * discount / 100
            amount = amount - discount
            
            tax_amount = amount * tax / 100
            amount = amount + tax_amount
            
            amount = float(f"{amount:.2f}")
            
            po_discount = amount * po_discount / 100
            amount = amount - po_discount
            
            po_tax = amount * po_tax / 100
            amount = amount + po_tax
            
            amount = float(f"{amount:.2f}")
                        
            self.table.cellWidget(row, 11).setText(str(amount))
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
        self.rep_edit.clear()
        self.subtotal.clear()
        self.roundoff.clear()
        self.final_amountdata.clear()
        self.receive_edit.clear()
        self.remainingdata.clear()
        self.checkbox.setChecked(False)        
        self.note.clear()
        self.table.setRowCount(0)
        
        self.populate_suppliers()
        
        for _ in range(5):
            
            self.add_row()





    
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



        
        
        

    



