from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QDialog, QApplication, QHBoxLayout, QButtonGroup, QCheckBox, QFrame,QMessageBox,QTableWidget, QHeaderView, QTableWidgetItem, QLabel, QLineEdit, QGridLayout, QTableWidgetItem, QSpacerItem, QSizePolicy, QComboBox
from PySide6.QtCore import QFile, Qt, QDate, QDateTime, Signal
from PySide6.QtSql import  QSqlQuery, QSqlDatabase
from PySide6.QtGui import QColor
from functools import partial
from datetime import datetime

from utilities.stylus import load_stylesheets
from utilities.activity_logger import log_activity
from utilities.permissions import Permissions
from utilities.app_messagebox import AppMessageBox


class ProductDetailWidget(QWidget):
    
    modal_signal = Signal(int)
    
    def __init__(self, parent=None):

        super().__init__(parent)
        
        self.edit_mode = False


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Product Detail", objectName="SectionTitle")
        self.productlist = QPushButton("Products List", objectName="TopRightButton")
        self.productlist.setCursor(Qt.PointingHandCursor)
        
        self.edit_btn = QPushButton("Edit", objectName="TopRightButton")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
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
                   "Formula", "Pack Size", "Units", "Pack Price", "Unit Price", "Discount Group", "Tax Group"]

        self.product = QLabel() ; self.productedit = QLineEdit()
        self.code = QLabel() ; self.codeedit = QLineEdit()
        self.brand = QLabel() ; self.brandedit = QLineEdit()
        
        self.formula = QLabel() ; self.formulaedit = QLineEdit()

        self.packsize = QLabel(); self.packsizeedit = QLineEdit()
        self.units = QLabel(); 
        self.sale_price = QLabel() ; self.sale_price_edit = QLineEdit()
        self.unit_price = QLabel()
        self.discount_group = QLabel() ; self.discount_group_edit = QComboBox()
        self.populate_discount_groups()
        self.tax_group = QLabel() ; self.tax_group_edit = QComboBox()
        self.populate_tax_groups()
        
        self.field_pairs = [
            (self.product, self.productedit),
            (self.code, self.codeedit),
            (self.brand, self.brandedit),
            (self.formula, self.formulaedit),
            (self.packsize, self.packsizeedit),
            (self.units, None),
            (self.sale_price, self.sale_price_edit),
            (self.unit_price, None),
            (self.discount_group, self.discount_group_edit),
            (self.tax_group, self.tax_group_edit)
            
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

        self.table = MyTable(column_ratios=[1, 2, 2, 2, 2, 2, 2, 2, 2], parent=self)
        headers = ["Id", "Batch No", "Expiry", "Received Qty", "Remaining", "Unit Cost", "Source", "Date/Time", "Status"]
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

        summary_layout = QHBoxLayout()
        self.total_batches_label = QLabel("Batches: 0")
        self.active_batches_label = QLabel("Active: 0")
        self.near_expiry_label = QLabel("Near Expiry: 0")
        self.expired_batches_label = QLabel("Expired: 0")
        self.sold_out_batches_label = QLabel("Sold Out: 0")

        summary_layout.addWidget(self.total_batches_label)
        summary_layout.addWidget(self.active_batches_label)
        summary_layout.addWidget(self.near_expiry_label)
        summary_layout.addWidget(self.expired_batches_label)
        summary_layout.addWidget(self.sold_out_batches_label)
        summary_layout.addStretch()

        self.layout.addLayout(summary_layout)
        
        self.layout.addStretch()
        
        
        

        
        self.setStyleSheet(load_stylesheets())

    def populate_discount_groups(self):
        self.discount_group_edit.clear()
        self.discount_group_edit.addItem("None", None)
        query = QSqlQuery("""
            SELECT id, name, discount_percent, COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1)
            FROM discount_group
            WHERE status = 'active'
            ORDER BY name
        """)
        while query.next():
            group_id = query.value(0)
            name = str(query.value(1) or "").strip()
            percent = float(query.value(2) or 0.0)
            fixed_amount = float(query.value(3) or 0.0)
            apply_on_sale = bool(int(query.value(4) or 0))
            self.discount_group_edit.addItem(
                f"{name} ({percent:.2f}% + {fixed_amount:.2f}, {'Sale On' if apply_on_sale else 'Sale Off'})",
                group_id,
            )

    def populate_tax_groups(self):
        self.tax_group_edit.clear()
        self.tax_group_edit.addItem("None", None)
        query = QSqlQuery("""
            SELECT id, name, tax_percent, COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1)
            FROM tax_group
            WHERE status = 'active'
            ORDER BY name
        """)
        while query.next():
            group_id = query.value(0)
            name = str(query.value(1) or "").strip()
            percent = float(query.value(2) or 0.0)
            fixed_amount = float(query.value(3) or 0.0)
            apply_on_sale = bool(int(query.value(4) or 0))
            self.tax_group_edit.addItem(
                f"{name} ({percent:.2f}% + {fixed_amount:.2f}, {'Sale On' if apply_on_sale else 'Sale Off'})",
                group_id,
            )

    def get_edit_widget_text(self, widget):
        if isinstance(widget, QComboBox):
            return widget.currentText()
        return widget.text() if hasattr(widget, "text") else ""

    def set_edit_widget_text(self, widget, text):
        if isinstance(widget, QComboBox):
            index = widget.findText(str(text), Qt.MatchExactly)
            widget.setCurrentIndex(index if index >= 0 else 0)
            return
        if hasattr(widget, "setText"):
            widget.setText(str(text))



        
        
    # === Toggle Edit Mode ===
    @Permissions.require_permission('product.update')
    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.edit_btn.setText("Save")
            # Switch to QLineEdit
            for lbl, edit in self.field_pairs:
                if edit:
                    self.set_edit_widget_text(edit, lbl.text())
                    lbl.hide()
                    edit.show()
        else:
            self.save_changes()
            self.edit_btn.setText("Edit")
            # Switch back to QLabel
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(self.get_edit_widget_text(edit))
                    edit.hide()
                    lbl.show()
    
            
            
            
    def hideEvent(self, event):
        
        if self.edit_mode:
            
            self.edit_mode = not self.edit_mode
            # reset state, discard edits
            self.edit_btn.setText("Edit")
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(self.get_edit_widget_text(edit))
                    edit.hide()
                    lbl.show()

        super().hideEvent(event)
        
        


    def load_product_data(self, id):
        
        self.product_id = id
        print("Loading Detail ID:", self.product_id)
        query = QSqlQuery()
        query.prepare("SELECT display_name, code, generic_name, brand, discount_group_id, tax_group_id FROM product WHERE id = ?")
        query.addBindValue(self.product_id)
        
        if query.exec() and query.next():
            
            self.product.setText(query.value(0))
            self.code.setText(query.value(1))
            self.formula.setText(query.value(2))
            self.brand.setText(query.value(3))
            discount_group_id = query.value(4)
            tax_group_id = query.value(5)
            discount_index = self.discount_group_edit.findData(discount_group_id)
            self.discount_group_edit.setCurrentIndex(discount_index if discount_index >= 0 else 0)
            self.discount_group.setText(self.discount_group_edit.currentText() or "None")
            tax_index = self.tax_group_edit.findData(tax_group_id)
            self.tax_group_edit.setCurrentIndex(tax_index if tax_index >= 0 else 0)
            self.tax_group.setText(self.tax_group_edit.currentText() or "None")
            
        
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
        price_query.prepare("""
            SELECT pack_size, pack_price, unit_price
            FROM price_pack
            WHERE product_id = ?
            ORDER BY is_default DESC, id DESC
            LIMIT 1
        """)
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
                            SELECT id, batch_no, expiry_date, total_received, quantity_remaining, unit_cost, source, received_at
                            FROM batch
                            WHERE product_id = ?
                            ORDER BY expiry_date ASC
                            """)
        batch_query.addBindValue(self.product_id)
        if batch_query.exec():
            
            self.table.setRowCount(0)
            row = 0
            total_batches = 0
            active_batches = 0
            near_expiry_batches = 0
            expired_batches = 0
            sold_out_batches = 0
            
            while batch_query.next():
                
                print("Batch:", batch_query.value(0), batch_query.value(1), batch_query.value(2),
                      batch_query.value(3), batch_query.value(4), batch_query.value(5), batch_query.value(6), batch_query.value(7))
                
                self.table.insertRow(row)

                remaining_qty = int(batch_query.value(4) or 0)
                status = self.get_batch_status(str(batch_query.value(2) or ""), remaining_qty)

                if status == "Expired":
                    expired_batches += 1
                elif status == "Near Expiry":
                    near_expiry_batches += 1
                elif status == "Sold Out":
                    sold_out_batches += 1
                else:
                    active_batches += 1

                total_batches += 1
                
                for col in range(8):
                    item = QTableWidgetItem(str(batch_query.value(col)))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # make item non-editable
                    self.table.setItem(row, col, item)

                status_item = QTableWidgetItem(status)
                status_item.setFlags(status_item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row, 8, status_item)
                
                row += 1
            
            print(f"[OK] Loaded {row} batches for product ID {self.product_id}")

            self.total_batches_label.setText(f"Batches: {total_batches}")
            self.active_batches_label.setText(f"Active: {active_batches}")
            self.near_expiry_label.setText(f"Near Expiry: {near_expiry_batches}")
            self.expired_batches_label.setText(f"Expired: {expired_batches}")
            self.sold_out_batches_label.setText(f"Sold Out: {sold_out_batches}")
            
            # Colour rows by status
            self.color_rows_by_status(self.table, status_column=8)
            
        



    def get_batch_status(self, expiry_text: str, remaining_qty: int) -> str:
        if remaining_qty <= 0:
            return "Sold Out"

        parsed_expiry = self.parse_expiry_date(expiry_text)
        if parsed_expiry is None:
            return "No Expiry"

        today = QDate.currentDate()
        if parsed_expiry < today:
            return "Expired"

        days_to_expiry = today.daysTo(parsed_expiry)
        if days_to_expiry <= 180:
            return "Near Expiry"

        return "Healthy"


    def parse_expiry_date(self, expiry_text: str):
        if not expiry_text:
            return None

        expiry_text = expiry_text.strip()
        if not expiry_text:
            return None

        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                parsed = datetime.strptime(expiry_text, fmt)
                return QDate(parsed.year, parsed.month, parsed.day)
            except ValueError:
                continue

        return None


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
                color = QColor(255, 224, 178)  # orange
            elif status == "sold out":
                color = QColor(224, 224, 224)  # gray
            elif status == "healthy":
                color = QColor(220, 245, 220)  # green
            else:
                color = None

            if color:
                for col in range(table.columnCount()):
                    cell = table.item(row, col)
                    if cell:
                        cell.setBackground(color)

    
    
    
    
            
    @Permissions.require_permission('product.update')
    def save_changes(self):
        
        if not self.product_id:
            print("[ERROR] No Product loaded.")
            AppMessageBox.warning(None, "Error", "No product loaded.")
            return

        # Read old values for audit BEFORE starting the transaction
        old_price_query = QSqlQuery()
        old_price_query.prepare("SELECT pack_price FROM price_pack WHERE product_id = ? LIMIT 1")
        old_price_query.addBindValue(self.product_id)
        old_pack_price = None
        if old_price_query.exec() and old_price_query.next():
            old_pack_price = float(old_price_query.value(0) or 0)

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
                SET display_name = ?, code = ?, brand = ?, generic_name = ?, discount_group_id = ?, tax_group_id = ?
                WHERE id = ?
            """)

            if code == '':
                code = None
            
            product_query.addBindValue(product)
            product_query.addBindValue(code)
            product_query.addBindValue(brand)
            product_query.addBindValue(formula)
            product_query.addBindValue(self.discount_group_edit.currentData())
            product_query.addBindValue(self.tax_group_edit.currentData())
            product_query.addBindValue(self.product_id)

            if not product_query.exec():
                raise Exception(f"Product update failed: {product_query.lastError().text()}")

            print(f"[OK] Product updated. Rows affected: {product_query.numRowsAffected()}")
            self.discount_group.setText(self.discount_group_edit.currentText() or "None")
            self.tax_group.setText(self.tax_group_edit.currentText() or "None")
            
            
            
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

            if old_pack_price is not None and old_pack_price != sale:
                price_change_query = QSqlQuery()
                price_change_query.prepare("""
                    INSERT INTO price_changes (
                        product_id,
                        previous_price,
                        new_price,
                        source,
                        user_id,
                        username
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """)
                app = QApplication.instance()
                change_user_id = app.property("user_id") if app else None
                change_username = (app.property("username") or "") if app else ""
                price_change_query.addBindValue(self.product_id)
                price_change_query.addBindValue(old_pack_price)
                price_change_query.addBindValue(sale)
                price_change_query.addBindValue("product_detail")
                price_change_query.addBindValue(change_user_id)
                price_change_query.addBindValue(change_username)

                if not price_change_query.exec():
                    raise Exception(f"Price change audit insert failed: {price_change_query.lastError().text()}")

                # Audit log — price change (non-blocking)
                log_activity(
                    category="price",
                    action="price_updated",
                    entity_type="product",
                    entity_id=self.product_id,
                    note=(
                        f"Selling price updated for {product} (Product ID {self.product_id}). "
                        f"Pack price changed from {old_pack_price} to {sale} from the Product Detail screen."
                    ),
                    previous_value=str(old_pack_price),
                    new_value=str(sale)
                )

            AppMessageBox.information(None, "Success", "All updates were successful")

        except Exception as e:
            db.rollback()
            error_msg = f"[ROLLBACK] {type(e).__name__}: {e}"
            print(error_msg)
            AppMessageBox.critical(None, "Error", error_msg)
        
    



    
     
            
    

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




        
        
       
        
