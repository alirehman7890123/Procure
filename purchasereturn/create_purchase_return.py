
from PySide6.QtWidgets import QWidget, QCompleter, QHBoxLayout, QFrame , QVBoxLayout, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QStringListModel, QTimer, Signal
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import  QKeyEvent
from functools import partial

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
        
    
        self.table = MyTable(column_ratios=[0.03, 0.25, 0.07, 0.07, 0.05, 0.07, 0.10, 0.05])
        headers = ["#", "Product", "Batch", "Qty", "Return Qty", "Rate", "Total", "X"]
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

        
        temporary_row = QHBoxLayout()
        
        
        
        
        
        
        
        receivelabel = QLabel("Received")
        self.receive_edit = QLineEdit()
        self.receive_edit.setPlaceholderText("0.00")
        
        self.receive_edit.textChanged.connect(self.calculate_payment)
        
        
        # 7th Line
        remaininglabel = QLabel("Remaining")
        self.remainingdata = QLabel("0.00")
        
        self.checkbox = QCheckBox("Write off")
        
        # 8th Line
        self.note = QLabel("Note")
        self.note_entry = QLineEdit()
        
        temporary_row.addWidget(receivelabel)
        temporary_row.addWidget(self.receive_edit)
        temporary_row.addWidget(remaininglabel)
        temporary_row.addWidget(self.remainingdata)
        temporary_row.addWidget(self.checkbox)
        temporary_row.addWidget(self.note)
        temporary_row.addWidget(self.note_entry)
        
        self.layout.addLayout(temporary_row)

        
        savereturn = QPushButton('Save Purchase Return', objectName='SaveButton')
        savereturn.setCursor(Qt.PointingHandCursor)
        
        savereturn.clicked.connect(lambda: self.save_purchase_return())
        
        
        self.layout.addWidget(savereturn)
        
        self.layout.addStretch()
        
        self.setStyleSheet(load_stylesheets())
        


        
        
        
        
    

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
        
        remaining_qty = QLabel()
        
        return_qty = QLineEdit()
        
        rate = QLabel()
        rate.setText("0.00")
        
        total_edit = QLineEdit()
        total_edit.setReadOnly(True)
        total_edit.setText("0.00")
        

        remove_btn = QPushButton("x")
        remove_btn.setCursor(Qt.PointingHandCursor)
        
        
        self.table.setCellWidget(row, 0, counter)
        self.table.setCellWidget(row, 1, product)
        self.table.setCellWidget(row, 2, batch)
        self.table.setCellWidget(row, 3, remaining_qty)
        self.table.setCellWidget(row, 4, return_qty)
        self.table.setCellWidget(row, 5, rate)
        self.table.setCellWidget(row, 6, total_edit)
        self.table.setCellWidget(row, 7, remove_btn)
        
        
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
        
        if not db.transaction():
            QMessageBox.critical(None, "Database Error", "Could not start transaction.")
            return

        try:
            
            supplier = self.supplier_edit.currentData()
            rep = self.rep_edit.currentData()

            if not supplier or not rep:
                raise ValueError("Supplier and representative must be selected.")

            def safe_float(value):
                try:
                    return float(value) if value else 0.0
                except ValueError:
                    return 0.0

            subtotal = round(safe_float(self.subtotal.text()), 2)
            roundoff = round(safe_float(self.roundoff.text()), 2)
            total = round(safe_float(self.final_amountdata.text()), 2)
            received = round(safe_float(self.receive_edit.text()), 2)
            remaining = round(safe_float(self.remainingdata.text()), 2)

            # # --- Financial Consistency Check ---
            # if round(subtotal + roundoff, 2) != total:
            #     raise ValueError("Total does not match Subtotal + Roundoff.")

            # if round(total - received, 2) != remaining:
            #     raise ValueError("Remaining amount calculation mismatch.")

            # --- Remaining Logic ---
            writeoff = 0.0
            payable = 0.0
            receiveable = 0.0

            if remaining == 0.0:
                pass

            elif remaining > 0.0:
                if self.checkbox.isChecked():
                    writeoff = remaining
                else:
                    receiveable = remaining

            else:  # remaining < 0
                payable = abs(remaining)

            # --- Insert Header ---
            query = QSqlQuery()
            query.prepare("""
                INSERT INTO purchase_return
                (supplier, rep, subtotal, roundoff, total, received, remaining, writeoff, payable, receiveable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)

            values = (
                supplier, rep,
                subtotal, roundoff, total,
                received, remaining,
                writeoff, payable, receiveable
            )

            for v in values:
                query.addBindValue(v)

            if not query.exec():
                raise Exception(query.lastError().text())

            return_id = query.lastInsertId()

            if not return_id:
                raise Exception("Failed to retrieve inserted return ID.")

            db.commit()
            QMessageBox.information(None, "Success", "Purchase Return Saved Successfully")



            print("About to add purchase transaction")
            
            
            
            supplier = int(supplier)

            # Fetch current supplier balances
            supplier_query = QSqlQuery()
            supplier_query.prepare("SELECT payable, receiveable FROM supplier WHERE id = ?")
            supplier_query.addBindValue(supplier)

            if supplier_query.exec() and supplier_query.next():
                supplier_payable = float(supplier_query.value(0))
                supplier_receiveable = float(supplier_query.value(1))
            else:
                print("Error fetching supplier:", supplier_query.lastError().text())
                QMessageBox.critical(self, "Error", "Supplier not found or database error.")
                raise Exception

            transaction_type = "PURCHASE RETURN"
            ref_no = None
            return_ref = return_id

            current_payable = 0.0
            current_receivable = 0.0

            remaining = total - received   # IMPORTANT

            if remaining > 0.0:
                # Supplier owes you
                current_receivable = remaining

            elif remaining < 0.0:
                # You owe supplier (over refund case)
                current_payable = abs(remaining)

            # Previous balances
            payable_before = supplier_payable
            receivable_before = supplier_receiveable

            # Apply movement WITHOUT offset
            payable_after = payable_before + current_payable
            receivable_after = receivable_before + current_receivable

            # Transaction meta fields
            due_amount = 0.0              # not applicable for return
            paid_now = 0.0                # not applicable for return
            remaining_due = 0.0           # not applicable

            receiveable_now = total       # value of goods returned
            received = received      # refund received now
            remaining_now = remaining

            note = "Purchase Return recorded with total amount " + str(total) + ". Received: " + str(received) + ". Remaining: " + str(remaining_now) + ". Write-off: " + str(writeoff)

            # Insert transaction record
            query = QSqlQuery()
            query.prepare("""
                INSERT INTO supplier_transaction 
                (supplier, transaction_type, ref, return_ref,
                payable_before, due_amount, paid, remaining_due, payable_after,
                receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                rep, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            query.addBindValue(receiveable_now)
            query.addBindValue(received)
            query.addBindValue(remaining_now)
            query.addBindValue(receivable_after)
            query.addBindValue(rep)
            query.addBindValue(note if 'note' in locals() else "")

            if query.exec():
                insert_id = query.lastInsertId()
                print("Supplier transaction saved with ID:", insert_id)
                QMessageBox.information(None, "Success", f"Supplier Transaction Stored Successfully (ID: {insert_id})")
            else:
                print("Error inserting supplier transaction:", query.lastError().text())
                QMessageBox.critical(None, "Error", query.lastError().text())
                raise Exception

            # Update supplier balances
            new_payable = payable_after
            new_receiveable = receivable_after

            update_supplier = QSqlQuery()
            update_supplier.prepare("UPDATE supplier SET payable = ?, receiveable = ? WHERE id = ?")
            update_supplier.addBindValue(new_payable)
            update_supplier.addBindValue(new_receiveable)
            update_supplier.addBindValue(supplier)

            if update_supplier.exec():
                print("Supplier balances updated successfully")
            else:
                print("Error updating supplier balances:", update_supplier.lastError().text())
                QMessageBox.critical(self, "Error", update_supplier.lastError().text())
                raise Exception

            
            
            
            
            self.return_items(return_id)
        
        
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
        
        
    
    
    
    def return_items(self, return_id):

        db = QSqlDatabase.database()
        
        def safe_int(widget):
            if widget is None:
                return 0
            value = widget.text()
            return int(value) if value and value.strip() else 0

        def safe_float(widget):
            if widget is None:
                return 0.0
            value = widget.text()
            return float(value) if value and value.strip() else 0.0


        row_count = self.table.rowCount()

        if row_count == 0:
            raise ValueError("No items to return.")


        print("About to save returned items...")

        for row in range(row_count):
            
            product_widget = self.table.cellWidget(row, 1)
            product_id = product_widget.currentData()
            
            
            product_widget = self.table.cellWidget(row, 1)
            if not product_widget:
                raise ValueError(f"Product missing at row {row+1}")

            product_id = product_widget.currentData()
            if product_id is None:
                raise ValueError(f"Product not selected at row {row+1}")
            
            batch_no = self.table.cellWidget(row, 2).currentText()
            purchased_qty = safe_int(self.table.cellWidget(row, 3))
            return_qty = safe_int(self.table.cellWidget(row, 4))
            rate = safe_float(self.table.cellWidget(row, 5))
            total = safe_float(self.table.cellWidget(row, 6))

            # --- Basic Validation ---
            if return_qty <= 0:
                continue  # skip empty rows safely

            if return_qty > purchased_qty:
                raise ValueError(
                    f"Return qty exceeds purchased qty (Row {row + 1})."
                )

            # --- Fetch Current Batch Quantity ---
            check_query = QSqlQuery()
            check_query.prepare("""
                SELECT quantity_remaining
                FROM batch
                WHERE batch_no = ? AND product_id = ?
            """)
            check_query.addBindValue(batch_no)
            check_query.addBindValue(product_id)

            if not check_query.exec() or not check_query.next():
                raise ValueError(
                    f"Batch not found (Row {row + 1})."
                )

            current_qty = check_query.value(0)
            

            if return_qty > current_qty:
                raise ValueError(
                    f"Insufficient stock in batch (Row {row + 1})."
                )

            print("Data to be inserted is: ", return_id, product_id, batch_no, purchased_qty, return_qty, rate, total)
            
            # --- Insert Return Item ---
            query = QSqlQuery()
            query.prepare("""
                INSERT INTO purchase_return_item
                (purchase_return, product, batch, purchased, returned, rate, total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """)

            values = (
                return_id,
                product_id,
                batch_no,
                purchased_qty,
                return_qty,
                round(rate, 4),
                round(total, 2)
            )

            for v in values:
                query.addBindValue(v)

            if not query.exec():
                raise Exception(query.lastError().text())

            
            
            
            print("Updating Batch Quantity")
            print("DATA TO BE updated is: ", type(batch_no), batch_no, type(product_id), product_id)
            # --- Update Batch ---
            update_query = QSqlQuery()
            update_query.prepare("""
                UPDATE batch
                SET quantity_remaining = quantity_remaining - ?
                WHERE batch_no = ? AND product_id = ?
            """)
            
            if return_qty is None:
                print("Return quantity is None, defaulting to 0")
            
            if batch_no is None:
                print("Batch number is None, defaulting to empty string")

            if product_id is None:
                print("Product ID is None, defaulting to 0")
            
            update_query.addBindValue(return_qty)
            update_query.addBindValue(batch_no)
            update_query.addBindValue(product_id)

            if not update_query.exec():
                print("some problem occurred...while updating batch qty")
                print("Error:", update_query.lastError().text())
                raise Exception(update_query.lastError().text())
            
            print("update query executed successfully for batch update")

        return True

        
        
        
        
        
        
        
    def load_product_suggestions(self, item, completer):
        
        print("Loading Medicine Suggestions")
        item = item
        completer = completer
        current_text = item.currentText() 
        print("Current Text is: ", current_text)
        
        if current_text == '':
            return 
        
        query = QSqlQuery()
        query.prepare("SELECT id, display_name FROM product WHERE display_name LIKE ? LIMIT 10")
        
        value = f"%{current_text}%"
        query.addBindValue(value)
        
        products = []
        
        if not query.exec():
            
            print("Something wrong happened...")
        
        else:
        
            while query.next():
                
                product_id = int(query.value(0))
                label = query.value(1)
                
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
        

        row = self.table.indexAt(item.pos()).row()
        batch = self.table.cellWidget(row, 2).currentText()
        
        self.table.cellWidget(row, 3).clear()
        
        batch = batch.strip()
        print("Batch is: ", batch)

        batch_query = QSqlQuery()
        batch_query.prepare("SELECT quantity_remaining, unit_cost FROM batch WHERE batch_no = ?")
        batch_query.addBindValue(batch)
        

        try:
            
            if batch_query.exec() and batch_query.next():
                
                quantity_remaining = batch_query.value(0)
                unit_cost = batch_query.value(1)
                
                
                
                print(f"Batch info is: {quantity_remaining}, {unit_cost}")
                
                qty = str(quantity_remaining)
                rate = str(unit_cost)
                
                self.table.cellWidget(row, 3).setText(qty)
                self.table.cellWidget(row, 5).setText(rate)
                    
            else:
                QMessageBox.information(None, 'Error', batch_query.lastError().text())

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
        stock_query.prepare("SELECT batch_no FROM batch WHERE product_id = ? and source = 'PURCHASE' ")
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
        
    
                



    def update_amount(self, edited_widget):
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            
            remaining = self.table.cellWidget(row, 3).text()
            qty_text = self.table.cellWidget(row, 4).text()
            
            if int(qty_text) > int(remaining):
                
                QMessageBox.information(None, "Error", "Quantity cannot be greater than purchased stock")
                self.table.cellWidget(row, 4).setText("0")
                qty_text = 0
            
            rate_text = self.table.cellWidget(row, 5).text()
            

            qty = int(qty_text) if qty_text else 0
            rate = float(rate_text) if rate_text else 0
            
            amount = qty * rate
            
            amount = float(f"{amount:.2f}")
            
            self.table.cellWidget(row, 6).setText(str(amount))
            print("Updating Final Amount")
            self.update_total_amount()
            
            
        except ValueError:
        
            self.table.cellWidget(row, 6).setText("0.00")



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
        
        # clear the table 
        
        
            
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



        
        
        

    



