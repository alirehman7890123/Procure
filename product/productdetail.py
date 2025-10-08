from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QDialog, QApplication, QHBoxLayout, QButtonGroup, QCheckBox, QFrame,QMessageBox,QTableWidget, QHeaderView, QTableWidgetItem, QLabel, QLineEdit, QGridLayout, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import QFile, Qt, QDate, QDateTime, Signal
from PySide6.QtSql import  QSqlQuery, QSqlDatabase
from PySide6.QtGui import QColor
from functools import partial

from utilities.stylus import load_stylesheets


class ProductDetailWidget(QWidget):
    
    modal_signal = Signal(int)
    
    def __init__(self, parent=None):

        super().__init__(parent)
        
        self.edit_mode = False


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Product Detail", objectName="SectionTitle")
        self.productlist = QPushButton("Products List", objectName="TopRightButton")
        self.productlist.setCursor(Qt.PointingHandCursor)
        self.productlist.setFixedWidth(200)
        
        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setFixedWidth(100)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.productlist)
        header_layout.addWidget(self.edit_btn)

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
        
        labels = ["Product Name", "Code/Barcode", "Category", "Brand", 
                   "Formula", "Form", "Strength",
                   "Pack Size", "Packs", "Units", "Reorder Level", "Sale Price per Pack"]

        self.product = QLabel() ; self.productedit = QLineEdit()
        self.code = QLabel() ; self.codeedit = QLineEdit()
        self.category = QLabel() ; self.categoryedit = QLineEdit()
        self.brand = QLabel() ; self.brandedit = QLineEdit()
        
        self.formula = QLabel() ; self.formulaedit = QLineEdit()
        self.form = QLabel() ; self.formedit = QLineEdit()
        self.strength = QLabel() ; self.strengthedit = QLineEdit()

        self.packsize = QLabel()
        self.packs = QLabel()
        self.units = QLabel()
        self.reorder_level = QLabel() ; self.reorder_level_edit = QLineEdit()
        self.sale_price = QLabel() ; self.sale_price_edit = QLineEdit()
        
        self.field_pairs = [
            (self.product, self.productedit),
            (self.code, self.codeedit),
            (self.category, self.categoryedit),
            (self.brand, self.brandedit),
            (self.formula, self.formulaedit),
            (self.form, self.formedit),
            (self.strength, self.strengthedit),
            (self.packsize, None),
            (self.packs, None),
            (self.units, None),
            (self.reorder_level, self.reorder_level_edit),
            (self.sale_price, self.sale_price_edit),
            
        ]
        
       
        
        for (label, (lbl_field, edit_field)) in zip(labels, self.field_pairs):

            row = QHBoxLayout()
            
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setStyleSheet("font-weight: normal; color: #444;")
            
            lbl_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(200)

            row.addWidget(lbl, 2)
            row.addWidget(lbl_field, 8)
            
            if edit_field:  # hidden initially
                edit_field.hide()
                row.addWidget(edit_field, 8)

            self.layout.addLayout(row)
            
        
        
        
        # Create Product Batch Table
        self.row_height = 40

        self.table = MyTable(column_ratios=[1, 2, 2, 2, 2, 2])
        headers = ["##", "Batch No", "Expiry Date","Status", "RESOLVED", "Detail"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

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
        
        self.layout.addStretch()
        
        
        

        
        self.setStyleSheet(load_stylesheets())



        
        
    # === Toggle Edit Mode ===
    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.edit_btn.setText("Save")
            # Switch to QLineEdit
            for lbl, edit in self.field_pairs:
                if edit:
                    edit.setText(lbl.text())
                    lbl.hide()
                    edit.show()
        else:
            self.save_changes()
            self.edit_btn.setText("Edit")
            # Switch back to QLabel
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(edit.text())
                    edit.hide()
                    lbl.show()
    
            
            
            
    def hideEvent(self, event):
        
        if self.edit_mode:
            
            self.edit_mode = not self.edit_mode
            # reset state, discard edits
            self.edit_btn.setText("Edit")
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(edit.text())
                    edit.hide()
                    lbl.show()

        super().hideEvent(event)
        
        


    def load_product_data(self, id):
        
        self.product_id = id
        print("Loading Detail ID:", self.product_id)
        query = QSqlQuery()
        query.prepare("SELECT name, code, category, brand, formula, form, strength FROM product WHERE id = ?")
        query.addBindValue(self.product_id)
        
        if query.exec() and query.next():
            
            self.product.setText(query.value(0))
            self.code.setText(query.value(1))
            self.category.setText(query.value(2))
            self.brand.setText(query.value(3))
            self.formula.setText(query.value(4))
            self.form.setText(query.value(5))
            self.strength.setText(query.value(6))
            
            
            
            
            stock_query = QSqlQuery()
            stock_query.prepare("SELECT packsize, units, reorder, saleprice FROM stock WHERE product = ?")
            stock_query.addBindValue(self.product_id)

            if stock_query.exec() and stock_query.next():
                
                size = stock_query.value(0)
                units = stock_query.value(1)
                packs = int(size) if size is not None else 0
                totalunits = int(units) if units is not None else 0

                packs, leftover_units = self.split_packs_and_units(packs, totalunits)

                self.packsize.setText(str(size))
                self.packs.setText(str(packs))
                self.units.setText(str(leftover_units))
                self.reorder_level.setText(str(stock_query.value(2)))
                self.sale_price.setText(str(stock_query.value(3)))

            else:
                print("Failed to fetch stock data:", stock_query.lastError().text())
    
    
        # Load Data into Batch Table
        
        batch_query = QSqlQuery()
        batch_query.prepare("""
                SELECT batch, expiry, status, id, resolved
                FROM batch
                WHERE product = ?
                ORDER BY expiry ASC
                      
                      """)
        batch_query.addBindValue(self.product_id)
        
        if not batch_query.exec():

            QMessageBox.critical(self, "Error", "Failed to load product batch: " + batch_query.lastError().text())
            print("Error executing query:", batch_query.lastError().text())
            return
        
        else:
            self.table.setRowCount(0)  # Clear existing rows
            row = 0
            
            while batch_query.next():
                
                self.table.insertRow(row)
                
                counter = str(row + 1)
                batch = batch_query.value(0)
                expiry = batch_query.value(1)
                status = batch_query.value(2)
                batch_id = batch_query.value(3)
                resolved = batch_query.value(4)
                
                if isinstance(expiry, QDateTime):
                    expiry = expiry.date().toString("dd-MM-yyyy")
                elif isinstance(expiry, QDate):
                    expiry = expiry.toString("dd-MM-yyyy")
                else:
                    expiry = str(expiry)
                

                counter = QTableWidgetItem(counter)
                batch = QTableWidgetItem(batch)
                expiry = QTableWidgetItem(expiry)
                status = QTableWidgetItem(status)
                resolved = QTableWidgetItem(str(resolved))
                
                # Apply colouring based on status
                if status == "expired":
                    color = QColor(255, 150, 150)  # light red
                    for item in [counter, batch, expiry, status]:
                        item.setBackground(color)

                elif status == "near expiry":
                    color = QColor(255, 255, 150)  # yellow
                    for item in [counter, batch, expiry, status]:
                        item.setBackground(color)
                
                
                
                
                # Add items to table
                self.table.setItem(row, 0, counter)
                self.table.setItem(row, 1, batch)
                self.table.setItem(row, 2, expiry)
                self.table.setItem(row, 3, status)
                self.table.setItem(row, 4, resolved)
                
                detail = QPushButton('Details')
                detail.setCursor(Qt.PointingHandCursor)
                detail.setStyleSheet("""
                        QPushButton {
                            background-color: transparent;
                            color: #333;
                            padding: 4px 12px;
                            border-radius: 2px;
                            font-weight: 600;
                        }
                        QPushButton:hover {
                            background-color: #340238;
                            color: #fff;
                        }
                        QPushButton:pressed {
                            background-color: #47034E;
                            color: #fff;
                        }
                    
                """)
                
                batch_id = int(batch_id)
                self.table.setCellWidget(row, 5, detail)
                detail.clicked.connect(partial(self.modal_signal.emit, batch_id))
                # detail.clicked.connect(lambda checked, b_id=batch_id: self.modal_signal.emit(b_id))
                
                row += 1
                
                
                
        self.color_rows_by_status(self.table, status_column=3)

    



    def color_rows_by_status(self, table, status_column: int = 3):
        """
        Check each row in the table, read the status column,
        and colour the entire row accordingly.
        
        :param table: QTableWidget instance
        :param status_column: which column contains the status text
        """
        for row in range(table.rowCount()):
            item = table.item(row, status_column)
            if not item:
                continue

            status = item.text().lower().strip()

            if status == "expired":
                color = QColor(255, 120, 120)  # red
            elif status == "near expiry":
                color = QColor(255, 255, 150)  # yellow
            else:
                color = None

            if color:
                for col in range(table.columnCount()):
                    cell = table.item(row, col)
                    if cell:
                        cell.setBackground(color)

    
    
    
    
    def split_packs_and_units(self, pack_size: int, units: int) -> tuple[int, int]:
   
        # if pack_size <= 0:
        #     raise ValueError("Pack size must be greater than zero")
        # if units < 0:
        #     raise ValueError("Units cannot be negative")
        
        if pack_size <= 0: 
            packs = 0
            leftover_units = 0
        else:
            packs = units // pack_size
            leftover_units = units % pack_size
            
        return packs, leftover_units
       
            
            
    def save_changes(self):
        if not self.product_id:
            print("[ERROR] No Product loaded.")
            QMessageBox.warning(None, "Error", "No product loaded.")
            return

        try:
            db = QSqlDatabase.database()
            if not db.transaction():
                raise Exception("Failed to start database transaction")

            # --- Get form values ---
            product = self.productedit.text().strip()
            code = self.codeedit.text().strip()
            category = self.categoryedit.text().strip()
            brand = self.brandedit.text().strip()
            formula = self.formulaedit.text().strip()
            form = self.formedit.text().strip()
            strength = self.strengthedit.text().strip()

            # Safe type casting
            try:
                reorder = int(self.reorder_level_edit.text()) if self.reorder_level_edit.text().strip() else 0
                sale = float(self.sale_price_edit.text()) if self.sale_price_edit.text().strip() else 0.0
            except ValueError:
                raise ValueError("Reorder level must be an integer and Sale Price must be a number.")

            # --- Update product table ---
            product_query = QSqlQuery()
            product_query.prepare("""
                UPDATE product
                SET name = ?, code = ?, category = ?, brand = ?, formula = ?, form = ?, strength = ?
                WHERE id = ?
            """)

            product_query.addBindValue(product)
            product_query.addBindValue(code)
            product_query.addBindValue(category)
            product_query.addBindValue(brand)
            product_query.addBindValue(formula)
            product_query.addBindValue(form)
            product_query.addBindValue(strength)
            product_query.addBindValue(self.product_id)

            if not product_query.exec():
                raise Exception(f"Product update failed: {product_query.lastError().text()}")

            if product_query.numRowsAffected() == 0:
                raise Exception("No product rows were updated. Invalid product_id?")

            print(f"[OK] Product updated. Rows affected: {product_query.numRowsAffected()}")

            # --- Update stock table ---
            stock_query = QSqlQuery()
            stock_query.prepare("""
                UPDATE stock
                SET reorder = ?, saleprice = ?
                WHERE product = ?
            """)
            stock_query.addBindValue(reorder)
            stock_query.addBindValue(sale)
            stock_query.addBindValue(self.product_id)

            if not stock_query.exec():
                raise Exception(f"Stock update failed: {stock_query.lastError().text()}")

            if stock_query.numRowsAffected() == 0:
                raise Exception("No stock rows were updated. Invalid product_id link?")

            print(f"[OK] Stock updated. Rows affected: {stock_query.numRowsAffected()}")
            
            
            # # --- Update Batch Status ---
            # self.update_batch_status()

            # --- Commit transaction ---
            if not db.commit():
                raise Exception(f"Commit failed: {db.lastError().text()}")

            print("[SUCCESS] Transaction committed.")
            QMessageBox.information(None, "Success", "All updates were successful")

        except Exception as e:
            db.rollback()
            error_msg = f"[ROLLBACK] {type(e).__name__}: {e}"
            print(error_msg)
            QMessageBox.critical(None, "Error", error_msg)
        
    


    def update_batch_status(self):
        
        today = QDate.currentDate()

        query = QSqlQuery()

        # Select all batches with expiry dates
        if not query.exec("SELECT id, expiry FROM batch"):
            print("Error selecting batches:", query.lastError().text())
            return

        while query.next():
            batch_id = query.value(0)
            expiry_date = query.value(1)  # should be date type in DB

            if expiry_date is None:
                continue

            days_diff = today.daysTo(expiry_date)

            if days_diff < 0:
                status = "expired"
            elif days_diff <= 60:  # within 2 months
                status = "near expiry"
            else:
                status = "valid"
                
            # Update status
            update_query = QSqlQuery()
            
            update_query.prepare("UPDATE batch SET status = :status WHERE id = :id")
            update_query.bindValue(":status", status)
            update_query.bindValue(":id", batch_id)
            
            if not update_query.exec():
                print("Error updating batch:", update_query.lastError().text())



    
    def open_modal_window(self, batch_id):
        
        print("Opening Batch Details Window")
        
        print("THE BATCH ID is : ", batch_id)
        # get batch query
        batch_query = QSqlQuery()
        batch_query.prepare("SELECT batch, resolved FROM batch WHERE id = :batch_id")
        batch_query.bindValue(":batch_id", batch_id)
        
        if batch_query.exec() and batch_query.next():
            
            batch = batch_query.value(0)
            resolved = batch_query.value(1)
            resolved = bool(resolved)
            
            print("Batch is: ", batch, " and resolved is: ", resolved)
            
            if resolved:
                print("Batch is resolved")
                QMessageBox.information(self, "Already Resolved", "Batch is Already Resolved")
                return
                
        else:
            
            print("Could not get Batch", batch_query.lastError().text())
            return
        
            
        print("Batch not resolved...")
        modal = BatchDetailsDialog()
        
        batch_info = self.get_batch(batch_id)
        
        print(batch_info)
        
        product_name, batch, expiry, status = batch_info
        
        if isinstance(expiry, QDateTime):
            expiry = expiry.date().toString("dd-MM-yyyy")
        elif isinstance(expiry, QDate):
            expiry = expiry.toString("dd-MM-yyyy")
        else:
            expiry = str(expiry)
        
        modal.batch_id_value.setText(str(batch_id))
        modal.product_value.setText(str(product_name)) 
        modal.batch_value.setText(str(batch))
        modal.expiry_value.setText(str(expiry))
        modal.status_value.setText(str(status))

        
        modal.exec()  # <-- blocks until closed
        
        
        
        
    def get_batch(self, batch_id):
        
        print("Trying to get the batch")
        
        # get batch values from db
        batch_query = QSqlQuery()
        batch_query.prepare("SELECT product, batch, expiry, status FROM batch WHERE id = :batch_id")
        batch_query.bindValue(":batch_id", batch_id)
        
        if batch_query.exec() and batch_query.next():
            print("Query successful")
            product = batch_query.value(0)
            batch = batch_query.value(1)
            expiry = batch_query.value(2)
            status = batch_query.value(3)
            
            # get product name
            product_query = QSqlQuery()
            product_query.prepare("SELECT name FROM product WHERE id = :product_id")
            product_query.bindValue(":product_id", product)
            
            if product_query.exec() and product_query.next():
                
                product_name = product_query.value(0)    

            else:
                print("Error Getting Product name, ", product_query.lastError().text())
            
            return (product_name, batch, expiry, status)
            
        else:
            print(batch_query.lastError().text())
        
        

            
    

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




class BatchDetailsDialog(QDialog):
    
    def __init__(self, parent=None):
        
        super().__init__(parent)
        
        self.setWindowTitle("Batch Details")
        self.setModal(True)  # block main window until closed
        self.resize(800, 300)
        
        # Center the dialog on the screen
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        center_x = (screen_geometry.width() - self.width()) // 2
        center_y = (screen_geometry.height() - self.height()) // 2
        self.move(center_x, center_y)


        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        self.setStyleSheet("background-color: #fff; color:#333;")

        # Header
        header = QLabel("Batch Details")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        
        
        batch_id_row = QHBoxLayout()
        
        batch_id_label = QLabel("Batch Id")
        self.batch_id_value = QLabel()
        
        batch_id_row.addWidget(batch_id_label)
        batch_id_row.addWidget(self.batch_id_value)
        
        layout.addLayout(batch_id_row)
        
        
        product_row = QHBoxLayout()
        product_label = QLabel("Product")
        self.product_value = QLabel()
        product_row.addWidget(product_label)
        product_row.addWidget(self.product_value)
        layout.addLayout(product_row)
        
        
        batch_row = QHBoxLayout()
        batch_label = QLabel("Batch")
        self.batch_value = QLabel()
        batch_row.addWidget(batch_label)
        batch_row.addWidget(self.batch_value)
        layout.addLayout(batch_row)

        
        expiry_row = QHBoxLayout()
        expiry_label = QLabel("Expiry Date")
        self.expiry_value = QLabel()
        expiry_row.addWidget(expiry_label)
        expiry_row.addWidget(self.expiry_value)
        layout.addLayout(expiry_row)
        
        
        status_row = QHBoxLayout()
        status_label = QLabel("Batch Status")
        self.status_value = QLabel()
        status_row.addWidget(status_label)
        status_row.addWidget(self.status_value)
        layout.addLayout(status_row)
        
        
        # Handle the Batch
        handle_heading = QHBoxLayout()
        handle_label = QLabel("Handle Batch")
        handle_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        
        handle_heading.addWidget(handle_label)
        layout.addLayout(handle_heading)
        
        checkbox_layout = QVBoxLayout()
        # create checkbox group
        
        self.sold_check = QCheckBox("Sold")
        self.returned_check = QCheckBox("Returned")
        self.disposed_check = QCheckBox("Disposed")

        # Add them to a group
        group = QButtonGroup(self)
        
        group.setExclusive(True)  # if True -> only one can be checked at a time
        
        group.addButton(self.sold_check)
        group.addButton(self.returned_check)
        group.addButton(self.disposed_check)
        
        
        checkbox_layout.addWidget(self.sold_check)
        checkbox_layout.addWidget(self.returned_check)
        checkbox_layout.addWidget(self.disposed_check)
        
        
        layout.addLayout(checkbox_layout)
        
        # Connect signals
        self.sold_check.stateChanged.connect(lambda state: print("Sold:", bool(state)))
        self.returned_check.stateChanged.connect(lambda state: print("Returned:", bool(state)))
        self.disposed_check.stateChanged.connect(lambda state: print("Disposed:", bool(state)))
        
        
        
        # note 
        note_row = QHBoxLayout()
        note_label = QLabel("Note")
        self.note_value = QLineEdit()
        note_row.addWidget(note_label)
        note_row.addWidget(self.note_value)
        layout.addLayout(note_row)
        
        
        # batch resolve button
        
        resolve_button_row = QHBoxLayout()
        
        resolve_button = QPushButton("Resolve Batch Issue", objectName="SaveButton")
        resolve_button.clicked.connect(lambda: self.batch_resolved())
        
        resolve_button_row.addWidget(resolve_button, 1)
        layout.addLayout(resolve_button_row)
        

        
        layout.addStretch()
        
        
        
        
        
    def batch_resolved(self):
        
        batch_id = self.batch_id_value.text()
        batch_id = int(batch_id)
        
        expiry = self.expiry_value.text()
        expiry = QDate.fromString(expiry, "dd-MM-yyyy")
        print(expiry)
        
        batch_status = self.status_value.text()
        
        sold = self.sold_check.isChecked()
        returned = self.returned_check.isChecked()
        disposed = self.disposed_check.isChecked()
        
        note = self.note_value.text()
        
        
        # insert batch_resolve record
        resolve_query = QSqlQuery()
        resolve_query.prepare("""
                    INSERT INTO batch_resolve (batch, expiry, batch_status, sold, returned, disposed, note) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """)

        resolve_query.addBindValue(batch_id)
        resolve_query.addBindValue(expiry)
        resolve_query.addBindValue(batch_status)
        resolve_query.addBindValue(sold)
        resolve_query.addBindValue(returned)
        resolve_query.addBindValue(disposed)
        resolve_query.addBindValue(note)
        
        if resolve_query.exec():
            
            resolve_id = resolve_query.lastInsertId()
            print("Resolve Query Successful with id: ", resolve_id)
            
            # setting batch resolve value
            
            batch_query = QSqlQuery()
            batch_query.prepare("UPDATE batch SET resolved = :resolved WHERE id = :batch_id")

            batch_query.bindValue(":resolved", True)
            batch_query.bindValue(":batch_id", batch_id)

            if batch_query.exec():
                
                print("Batch updated successfully")
                self.accept()
                
            else:
                print("Error updating batch:", batch_query.lastError().text())

            
            
        else:
            print("Resolve Query Unsuccessful")
            print(resolve_query.lastError().text())
            
            
            
            
        
        
       
        

