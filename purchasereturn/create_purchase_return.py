
from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame , QVBoxLayout, QCheckBox, QPushButton,QMessageBox, QTableWidgetItem, QGridLayout, QHeaderView, QLabel, QSpacerItem, QSizePolicy, QLineEdit, QComboBox, QTableWidget
from PySide6.QtCore import QFile, Qt, QTimer, Signal
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtGui import  QKeyEvent
from utilities.product_search_widget import ProductSearchBox
from functools import partial

import math
from utilities.stylus import load_stylesheets
from utilities.activity_logger import log_activity
from utilities.permissions import Permissions
from utilities.session_gate import require_open_session
from utilities.session_service import get_active_session_id
from utilities.payment_handler import PaymentMethodHandler
from utilities.app_messagebox import AppMessageBox





class KeyUpLineEdit(QLineEdit):
    keyReleased = Signal(QKeyEvent)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.keyReleased.emit(event)





class AddPurchaseReturnWidget(QWidget):


    def __init__(self, parent=None):

        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Purchase Return Invoice", objectName="SectionTitle")
        self.invoicelist = QPushButton("Purchase Returns List", objectName="TopRightButton")
        self.invoicelist.setCursor(Qt.PointingHandCursor)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
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
        
        
        payment_method_layout = QHBoxLayout()
        
        payment_method_label = QLabel("Payment Method")
        
        self.payment_handler = PaymentMethodHandler(self)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "EasyPaisa", "JazzCash"])
        self.payment_method.currentTextChanged.connect(self.on_payment_method_changed)
        
        
        payment_method_layout.addWidget(payment_method_label, 1)
        payment_method_layout.addWidget(self.payment_method, 1)
        
        
        self.layout.addLayout(payment_method_layout)

        
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

        
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(10)

        savereturn = QPushButton('Save Purchase Return', objectName='SaveButton')
        savereturn.setCursor(Qt.PointingHandCursor)
        savereturn.clicked.connect(lambda: self.save_purchase_return())

        clear_button = QPushButton("Clear Return", objectName="TopRightButton")
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(self.confirm_clear_return)

        action_row.addWidget(savereturn, 1)
        action_row.addWidget(clear_button)
        
        self.layout.addLayout(action_row)
        
        self.layout.addStretch()
        
        self.setStyleSheet(load_stylesheets())
        


        
    def on_payment_method_changed(self, method):
        
        success = self.payment_handler.handle_method_change(method)

        if not success:
            self.payment_method.blockSignals(True)
            self.payment_method.setCurrentText("Cash")
            self.payment_method.blockSignals(False)    
        
        
    

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

        product = ProductSearchBox(self, placeholder="select product", defer_numeric_to_enter=True)
        product.wheelEvent = lambda event: event.ignore()
        product.product_selected.connect(
            lambda pid, name, p=product: self.on_completer_highlighted(name, p)
        )
        product.lineEdit().returnPressed.connect(
            lambda p=product: self.handle_product_return_pressed(p)
        )

        
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
            AppMessageBox.information(None, 'Error', query.lastError().text() )
        
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
            AppMessageBox.information(None, 'Error', query.lastError().text())
        
    
     
        
    @Permissions.require_permission('purchasereturn.create')
    def save_purchase_return(self):
        if not require_open_session(self):
            return

        db = QSqlDatabase.database()

        if not db.transaction():
            AppMessageBox.critical(None, "Database Error", "Could not start transaction.")
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
            supplier_name = self.supplier_edit.currentText().strip()

            return_item_count = 0
            for row in range(self.table.rowCount()):
                qty_widget = self.table.cellWidget(row, 4)
                if qty_widget is None:
                    continue
                try:
                    if int(qty_widget.text() or 0) > 0:
                        return_item_count += 1
                except ValueError:
                    continue

            if return_item_count <= 0:
                raise ValueError("Enter at least one returned item before saving the purchase return.")

            payment = self.payment_handler.payment_data.copy()

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

            session_id = get_active_session_id(strict=True)
            if session_id is None:
                raise ValueError("No active session found.")

            # --- Insert Header ---
            query = QSqlQuery()
            query.prepare("""
                INSERT INTO purchase_return
                (
                    supplier, rep, subtotal, roundoff, total, received, remaining,
                    writeoff, payable, receiveable, session_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )
            """)

            values = (
                supplier, rep,
                subtotal, roundoff, total,
                received, remaining,
                writeoff, payable, receiveable,
                session_id
            )

            for v in values:
                query.addBindValue(v)

            if not query.exec():
                raise Exception(query.lastError().text())

            return_id = query.lastInsertId()

            if not return_id:
                raise Exception("Failed to retrieve inserted return ID.")

            print("About to add purchase transaction")

            supplier = int(supplier)

            # Fetch current supplier balances
            supplier_query = QSqlQuery()
            supplier_query.prepare("""
                SELECT payable, receiveable
                FROM supplier
                WHERE id = ?
            """)
            supplier_query.addBindValue(supplier)

            if supplier_query.exec() and supplier_query.next():
                supplier_payable = float(supplier_query.value(0) or 0.0)
                supplier_receiveable = float(supplier_query.value(1) or 0.0)
            else:
                print("Error fetching supplier:", supplier_query.lastError().text())
                AppMessageBox.critical(self, "Error", "Supplier not found or database error.")
                raise Exception("Supplier not found or database error.")

            transaction_type = "PURCHASE RETURN"
            ref_no = None
            return_ref = return_id

            current_payable = 0.0
            current_receivable = 0.0

            remaining = round(total - received, 2)

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
            paid_now = 0.0
            received_now = received

            if current_receivable > 0.0:
                due_amount = 0.0
                remaining_due = payable_before
                receiveable_now = current_receivable
                remaining_now = receivable_after
            else:
                due_amount = current_payable
                remaining_due = payable_after
                receiveable_now = 0.0
                remaining_now = receivable_before

            note = (
                "Purchase Return recorded with total amount " + str(total) +
                ". Received: " + str(received_now) +
                ". Remaining: " + str(remaining_now) +
                ". Write-off: " + str(writeoff)
            )

            # Insert transaction record
            query = QSqlQuery()
            query.prepare("""
                INSERT INTO supplier_transaction
                (
                    supplier, transaction_type, ref, return_ref,
                    payable_before, due_amount, paid, remaining_due, payable_after,
                    receiveable_before, receiveable_now, received, remaining_now, receiveable_after,
                    payment_method, bank_name, account_no, transaction_mode,
                    wallet_provider, wallet_no, payment_reference,
                    rep, note, session_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            query.addBindValue(received_now)
            query.addBindValue(remaining_now)
            query.addBindValue(receivable_after)

            query.addBindValue(payment.get("payment_method") or None)
            query.addBindValue(payment.get("bank_name") or None)
            query.addBindValue(payment.get("account_no") or None)
            query.addBindValue(payment.get("transaction_mode") or None)
            query.addBindValue(payment.get("wallet_provider") or None)
            query.addBindValue(payment.get("wallet_no") or None)
            query.addBindValue(payment.get("payment_reference") or None)

            query.addBindValue(rep)
            query.addBindValue(note)
            query.addBindValue(session_id)

            if query.exec():
                insert_id = query.lastInsertId()
                print("Supplier transaction saved with ID:", insert_id)
            else:
                print("Error inserting supplier transaction:", query.lastError().text())
                AppMessageBox.critical(None, "Error", query.lastError().text())
                raise Exception(query.lastError().text())

            # Update supplier balances
            new_payable = payable_after
            new_receiveable = receivable_after

            update_supplier = QSqlQuery()
            update_supplier.prepare("""
                UPDATE supplier
                SET payable = ?, receiveable = ?
                WHERE id = ?
            """)
            update_supplier.addBindValue(new_payable)
            update_supplier.addBindValue(new_receiveable)
            update_supplier.addBindValue(supplier)

            if update_supplier.exec():
                print("Supplier balances updated successfully")
            else:
                print("Error updating supplier balances:", update_supplier.lastError().text())
                AppMessageBox.critical(self, "Error", update_supplier.lastError().text())
                raise Exception(update_supplier.lastError().text())

            self.return_items(return_id)

        except Exception as e:
            print("An error occurred:", str(e))
            AppMessageBox.critical(None, "Error", f"An error occurred while saving the purchase return: {str(e)}")
            db.rollback()

        else:
            db.commit()
            log_activity(
                category="purchase",
                action="purchase_return_created",
                entity_type="purchase_return",
                entity_id=int(return_id),
                note=(
                    f"Purchase return #{return_id} was recorded for supplier {supplier_name or supplier}. "
                    f"It includes {return_item_count} item(s) with a total value of {total}."
                ),
                previous_value=None,
                new_value=str(total)
            )
            print("Transaction committed successfully")
            AppMessageBox.information(None, "Success", "Purchase return saved successfully")
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

        processed_rows = 0

        for row in range(row_count):
            
            product_widget = self.table.cellWidget(row, 1)
            product_id = product_widget.currentData()
            
            
            product_widget = self.table.cellWidget(row, 1)
            if not product_widget:
                continue

            product_id = product_widget.currentData()
            if product_id is None:
                continue
            
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

            if update_query.numRowsAffected() == 0:
                raise Exception(f"Batch quantity update failed for row {row + 1}.")
            
            print("update query executed successfully for batch update")
            processed_rows += 1

        if processed_rows <= 0:
            raise ValueError("No purchase return items were posted.")

        return True

        
        
        
        
        
        
        
    def on_batch_highlighted(self, text, item):
        

        row = self.table.indexAt(item.pos()).row()
        batch = self.table.cellWidget(row, 2).currentText()
        
        self.table.cellWidget(row, 3).clear()
        self.table.cellWidget(row, 5).setText("0.00")
        self.table.cellWidget(row, 6).setText("0.00")
        
        batch = batch.strip()
        print("Batch is: ", batch)

        if not batch:
            self.table.cellWidget(row, 2).setFocus()
            return

        product_id = self.table.cellWidget(row, 1).currentData()

        batch_query = QSqlQuery()
        batch_query.prepare("""
            SELECT quantity_remaining, unit_cost
            FROM batch
            WHERE batch_no = ? AND product_id = ?
            LIMIT 1
        """)
        batch_query.addBindValue(batch)
        batch_query.addBindValue(product_id)
        

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
                self.table.cellWidget(row, 2).setCurrentIndex(-1)
                if self.table.cellWidget(row, 2).isEditable():
                    self.table.cellWidget(row, 2).lineEdit().clear()
                AppMessageBox.information(
                    self,
                    "Not Found",
                    f"Batch '{batch}' was not found for the selected product."
                )
                self.table.cellWidget(row, 2).setFocus()

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
        supplier_id = self.supplier_edit.currentData()
        
        self.table.cellWidget(row, 2).clear()
        
        
        print("Product id is: ", product_id)

        stock_query = QSqlQuery()
        stock_query.prepare("""
            SELECT DISTINCT b.batch_no
            FROM batch b
            JOIN purchaseitem pi ON pi.id = b.purchaseitem_id
            JOIN purchase p ON p.id = pi.purchase
            WHERE b.product_id = ?
              AND p.supplier = ?
              AND b.quantity_remaining > 0
              AND COALESCE(b.source, '') = 'PURCHASE'
              AND b.batch_no IS NOT NULL
              AND TRIM(b.batch_no) <> ''
        """)
        stock_query.addBindValue(product_id)
        stock_query.addBindValue(supplier_id)
        

        try:
            
            if stock_query.exec():
                found_batches = False
                
                while stock_query.next():  
                      
                    batch = stock_query.value(0)
                    
                    print(f"Batch info is: {batch}")
                    
                    self.table.cellWidget(row, 2).addItem(batch)
                    found_batches = True
                    
                
                if found_batches:
                    widget = self.table.cellWidget(row, 2)
                    self.table.cellWidget(row, 2).setCurrentIndex(0)
                    self.table.cellWidget(row, 3).setText('')
                    self.on_batch_highlighted(widget.currentText(), widget)

                    try:
                        widget.activated.disconnect()
                    except Exception:
                        pass
                    widget.activated.connect(lambda _=None, w=widget: self.update_amount(w))
                else:
                    self.table.cellWidget(row, 3).clear()
                    self.table.cellWidget(row, 5).setText("0.00")
                    self.table.cellWidget(row, 6).setText("0.00")
                    AppMessageBox.information(
                        self,
                        "No Eligible Batch",
                        "No remaining purchase batches for this product were found for the selected supplier."
                    )
                    item.clear_selection()
                    item.setFocus()
                
                
            else:
            
                AppMessageBox.information(None, 'Error', stock_query.lastError().text())

        except Exception as e:
                
            print(str(e))

    def handle_product_return_pressed(self, product_box):
        text = product_box.currentText().strip()
        if not text:
            return

        if text.isdigit():
            match = product_box.lookup_product_by_code(text)
            if match:
                product_id, display_name = match
                product_box.select_result(display_name, product_id)
                self.on_completer_highlighted(display_name, product_box)
            else:
                AppMessageBox.information(self, "Not Found", f"No product found for code/barcode '{text}'.")
                product_box.clear_selection()
                product_box.setFocus()
            return

        index = product_box.findText(text, Qt.MatchFixedString)
        if index >= 0:
            product_box.setCurrentIndex(index)
            self.on_completer_highlighted(text, product_box)
        
    
                



    def update_amount(self, edited_widget):
        
        row = self.table.indexAt(edited_widget.pos()).row()
        
        try:
            
            remaining = self.table.cellWidget(row, 3).text()
            qty_text = self.table.cellWidget(row, 4).text()
            
            if int(qty_text) > int(remaining):
                
                AppMessageBox.information(None, "Error", "Quantity cannot be greater than purchased stock")
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
        
        self.payment_method.blockSignals(True); 
        self.payment_method.setCurrentIndex(0) 
        self.payment_method.blockSignals(False)
        
        self.populate_suppliers()
        
        # clear the table 
        
        
            
        self.add_row()
        self.supplier_edit.setFocus()

    def confirm_clear_return(self):
        _, accepted = AppMessageBox.confirm(
            self,
            "Clear Purchase Return",
            "Clear the current purchase return and reset all fields?",
            confirm_label="Clear Return",
            cancel_label="Keep Editing",
        )
        if accepted:
            self.clear_fields()





    
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



        
        
        

    
