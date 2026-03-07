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
        
        labels = ["Product Name", "Code/Barcode", "Brand", 
                   "Formula", "Pack Size", "Units", "Pack Price", "Unit Price"]

        self.product = QLabel() ; self.productedit = QLineEdit()
        self.code = QLabel() ; self.codeedit = QLineEdit()
        self.brand = QLabel() ; self.brandedit = QLineEdit()
        
        self.formula = QLabel() ; self.formulaedit = QLineEdit()

        self.packsize = QLabel(); self.packsizeedit = QLineEdit()
        self.units = QLabel(); 
        self.sale_price = QLabel() ; self.sale_price_edit = QLineEdit()
        self.unit_price = QLabel()
        
        self.field_pairs = [
            (self.product, self.productedit),
            (self.code, self.codeedit),
            (self.brand, self.brandedit),
            (self.formula, self.formulaedit),
            (self.packsize, self.packsizeedit),
            (self.units, None),
            (self.sale_price, self.sale_price_edit),
            (self.unit_price, None)
            
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

        self.table = MyTable(column_ratios=[1, 2, 2, 2, 2, 2, 2], parent=self)
        headers = ["Id", "Batch No", "Expiry","Received Qty", "Remaining", "Source", "Date/Time"]
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
        query.prepare("SELECT display_name, code, generic_name, brand FROM product WHERE id = ?")
        query.addBindValue(self.product_id)
        
        if query.exec() and query.next():
            
            self.product.setText(query.value(0))
            self.code.setText(query.value(1))
            self.formula.setText(query.value(2))
            self.brand.setText(query.value(3))
            
        
        else:
            print("Failed to fetch product data:", query.lastError().text())
            
            
            
        # get batch and stock
            
        stock_query = QSqlQuery()
        stock_query.prepare("""SELECT COALESCE(SUM(quantity_remaining), 0) AS total_stock
                                FROM batch
                                WHERE product_id = ?;
                            """)
        
        stock_query.addBindValue(self.product_id)
        
        if stock_query.exec() and stock_query.next():
            
            total_stock = stock_query.value(0)
            print("Total stock is: ", total_stock)
            
            self.units.setText(str(total_stock))
            
        else:
            self.units.setText("0")
            
        
        
        
        # Load Price Data
        
        price_query = QSqlQuery()
        price_query.prepare("SELECT pack_size, pack_price, unit_price FROM price_pack WHERE product_id = ?")
        price_query.addBindValue(self.product_id)
        
        if price_query.exec() and price_query.next():
            
            print("Price data found", price_query.value(0), price_query.value(1), price_query.value(2))
            
            self.packsize.setText(str(price_query.value(0)))
            self.sale_price.setText(str(price_query.value(1)))
            self.unit_price.setText(str(price_query.value(2)))
        else:
            self.packsize.setText("0")
            self.sale_price.setText("0")
            self.unit_price.setText("0")
            
            
            
            
        # Load Batch Data
        
        batch_query = QSqlQuery()
        batch_query.prepare("""
                            SELECT id, batch_no, expiry_date, total_received, quantity_remaining, source, received_at
                            FROM batch
                            WHERE product_id = ?
                            ORDER BY expiry_date ASC
                            """)
        batch_query.addBindValue(self.product_id)
        if batch_query.exec():
            
            self.table.setRowCount(0)
            row = 0
            
            while batch_query.next():
                
                print("Batch:", batch_query.value(0), batch_query.value(1), batch_query.value(2),
                      batch_query.value(3), batch_query.value(4), batch_query.value(5), batch_query.value(6))
                
                self.table.insertRow(row)
                
                for col in range(7):
                    item = QTableWidgetItem(str(batch_query.value(col)))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # make item non-editable
                    self.table.setItem(row, col, item)
                
                row += 1
            
            print(f"[OK] Loaded {row} batches for product ID {self.product_id}")
            
            # Colour rows by status
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
            brand = self.brandedit.text().strip()
            formula = self.formulaedit.text().strip()

            # Safe type casting
            packsize = int(self.packsizeedit.text()) if self.packsizeedit.text().strip() else 0
            sale = float(self.sale_price_edit.text()) if self.sale_price_edit.text().strip() else 0.0
            
            
            
            

            # --- Update product table ---
            product_query = QSqlQuery()
            product_query.prepare("""
                UPDATE product
                SET display_name = ?, code = ?, brand = ?, generic_name = ?
                WHERE id = ?
            """)

            if code == '':
                code = None
            
            product_query.addBindValue(product)
            product_query.addBindValue(code)
            product_query.addBindValue(brand)
            product_query.addBindValue(formula)
            product_query.addBindValue(self.product_id)

            if not product_query.exec():
                raise Exception(f"Product update failed: {product_query.lastError().text()}")


            print(f"[OK] Product updated. Rows affected: {product_query.numRowsAffected()}")
            
            # --- Update stock table ---
            pricing_query = QSqlQuery()
            pricing_query.prepare("""
                UPDATE price_pack
                SET pack_size = ?, pack_price = ?
                WHERE product_id = ?
            """)
            
            pricing_query.addBindValue(packsize)
            pricing_query.addBindValue(sale)
            pricing_query.addBindValue(self.product_id)

            if not pricing_query.exec():
                raise Exception(f"Stock update failed: {pricing_query.lastError().text()}")

            if pricing_query.numRowsAffected() == 0:
                raise Exception("No stock rows were updated. Invalid product_id link ?")

            print(f"[OK] Stock updated. Rows affected: {pricing_query.numRowsAffected()}")
            
            

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
            
            
            
            
        
        
       
        

