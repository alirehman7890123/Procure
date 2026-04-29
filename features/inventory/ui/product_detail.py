from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QDialog, QApplication, QHBoxLayout, QButtonGroup, QCheckBox, QFrame,QMessageBox,QTableWidget, QHeaderView, QTableWidgetItem, QLabel, QLineEdit, QGridLayout, QTableWidgetItem, QSpacerItem, QSizePolicy, QComboBox, QFileDialog
from PySide6.QtCore import QFile, Qt, QDate, QDateTime, Signal
from PySide6.QtGui import QColor
from functools import partial
from datetime import datetime

from medic.utilities.file_preview import preview_file
from medic.utilities.stylus import load_stylesheets
from medic.utilities.activity_logger import log_activity
from medic.utilities.permissions import Permissions
from medic.utilities.app_messagebox import AppMessageBox
from medic.features.inventory.services.product_media_service import (
    clear_product_media_fields,
    ensure_product_media_schema,
    fetch_product_media,
    save_product_media,
    update_product_media_fields,
)
from medic.services.sales_transaction_service import ensure_prescription_schema
from medic.features.inventory.services.product_write_service import (
    fetch_discount_group_options,
    fetch_product_detail_context,
    fetch_tax_group_options,
    update_product_detail_record,
)


class ProductDetailWidget(QWidget):
    
    modal_signal = Signal(int)
    
    def __init__(self, parent=None):

        super().__init__(parent)
        ensure_prescription_schema()
        ensure_product_media_schema()
        
        self.edit_mode = False
        self.selected_product_media_path = ""
        self.product_media_info = None
        self.product_media_removed = False


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
                   "Formula", "Pack Size", "Units", "Pack Price", "Unit Price", "Discount Group", "Tax Group", "Prescription"]

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
        self.prescription_required = QLabel()
        self.prescription_required_edit = QCheckBox("Prescription Required")
        
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
            (self.tax_group, self.tax_group_edit),
            (self.prescription_required, self.prescription_required_edit)
            
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

        media_row = QHBoxLayout()
        media_label = QLabel("Product File")
        media_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        media_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        media_label.setMinimumWidth(200)
        media_label.setStyleSheet("font-weight: normal; color: #444;")
        media_row.addWidget(media_label, 2)

        self.product_media_label = QLabel("No file attached")
        self.product_media_label.setWordWrap(True)
        media_row.addWidget(self.product_media_label, 5)

        self.preview_media_btn = QPushButton("Preview", objectName="TopRightButton")
        self.preview_media_btn.clicked.connect(self.preview_product_media)
        media_row.addWidget(self.preview_media_btn, 0)

        self.select_media_btn = QPushButton("Select File", objectName="TopRightButton")
        self.select_media_btn.clicked.connect(self.browse_product_media)
        self.select_media_btn.hide()
        media_row.addWidget(self.select_media_btn, 0)

        self.clear_media_btn = QPushButton("Clear", objectName="TopRightButton")
        self.clear_media_btn.clicked.connect(self.clear_product_media)
        self.clear_media_btn.hide()
        media_row.addWidget(self.clear_media_btn, 0)

        self.layout.addLayout(media_row)
            
        
        
        
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

        self.table.setMinimumWidth(700)
        
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
        self.update_product_media_display()

    def populate_discount_groups(self):
        self.discount_group_edit.clear()
        self.discount_group_edit.addItem("None", None)
        for option in fetch_discount_group_options():
            self.discount_group_edit.addItem(option["label"], option["id"])

    def populate_tax_groups(self):
        self.tax_group_edit.clear()
        self.tax_group_edit.addItem("None", None)
        for option in fetch_tax_group_options():
            self.tax_group_edit.addItem(option["label"], option["id"])

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

    def browse_product_media(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Product File",
            "",
            "Images and PDF Files (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.pdf);;Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;PDF Files (*.pdf);;All Files (*)",
        )
        if not file_path:
            return
        self.selected_product_media_path = file_path
        self.product_media_removed = False
        self.update_product_media_display()

    def clear_product_media(self):
        self.selected_product_media_path = ""
        self.product_media_info = None
        self.product_media_removed = True
        self.update_product_media_display()

    def preview_product_media(self):
        media_path = str(self.selected_product_media_path or "").strip()
        mime_type = ""
        if not media_path and self.product_media_info:
            media_path = str(self.product_media_info.get("absolute_path") or "").strip()
            mime_type = str(self.product_media_info.get("mime_type") or "").strip()
        if not media_path:
            AppMessageBox.information(self, "Preview File", "No product file is attached yet.")
            return
        preview_file(self, media_path, mime_type=mime_type)

    def update_product_media_display(self):
        text = "No file attached"
        if str(self.selected_product_media_path or "").strip():
            text = f"Selected: {self.selected_product_media_path.split('/')[-1]}"
        elif self.product_media_info:
            text = f"Stored: {self.product_media_info.get('original_filename') or 'Attached file'}"
        elif self.product_media_removed:
            text = "Existing file will be cleared"

        self.product_media_label.setText(text)
        has_media = bool(str(self.selected_product_media_path or "").strip() or self.product_media_info)
        self.preview_media_btn.setEnabled(has_media)
        self.clear_media_btn.setEnabled(has_media or self.product_media_removed)



        
        
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
            self.select_media_btn.show()
            self.clear_media_btn.show()
        else:
            self.save_changes()
            self.edit_btn.setText("Edit")
            # Switch back to QLabel
            for lbl, edit in self.field_pairs:
                if edit:
                    lbl.setText(self.get_edit_widget_text(edit))
                    edit.hide()
                    lbl.show()
            self.select_media_btn.hide()
            self.clear_media_btn.hide()
    
            
            
            
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
            self.select_media_btn.hide()
            self.clear_media_btn.hide()

        super().hideEvent(event)
        
        


    def load_product_data(self, id):
        
        self.product_id = id
        print("Loading Detail ID:", self.product_id)
        try:
            context = fetch_product_detail_context(self.product_id)
        except Exception as exc:
            print("Failed to fetch product data:", str(exc))
            return

        if context:
            header = context["header"]
            pricing = context["pricing"]
            self.product.setText(header["display_name"])
            self.code.setText(header["code"])
            self.formula.setText(header["generic_name"])
            self.brand.setText(header["brand"])
            discount_group_id = header["discount_group_id"]
            tax_group_id = header["tax_group_id"]
            discount_index = self.discount_group_edit.findData(discount_group_id)
            self.discount_group_edit.setCurrentIndex(discount_index if discount_index >= 0 else 0)
            self.discount_group.setText(self.discount_group_edit.currentText() or "None")
            tax_index = self.tax_group_edit.findData(tax_group_id)
            self.tax_group_edit.setCurrentIndex(tax_index if tax_index >= 0 else 0)
            self.tax_group.setText(self.tax_group_edit.currentText() or "None")
            prescription_required = header["prescription_required"]
            self.prescription_required.setText("Required" if prescription_required else "Not Required")
            self.prescription_required_edit.setChecked(prescription_required)
            self.product_media_info = context["media_info"]
            self.selected_product_media_path = ""
            self.product_media_removed = False
            self.update_product_media_display()
            
            print("Total stock is: ", context["stock"])
            self.units.setText(str(context["stock"]))

            self.packsize.setText(pricing["pack_size"])
            self.sale_price.setText(pricing["pack_price"])
            self.unit_price.setText(pricing["unit_price"])

            self.table.setRowCount(0)
            row = 0
            total_batches = 0
            active_batches = 0
            near_expiry_batches = 0
            expired_batches = 0
            sold_out_batches = 0
            
            for batch_row in context["batches"]:
                print(
                    "Batch:",
                    batch_row["id"],
                    batch_row["batch_no"],
                    batch_row["expiry_date"],
                    batch_row["total_received"],
                    batch_row["quantity_remaining"],
                    batch_row["unit_cost"],
                    batch_row["source"],
                    batch_row["received_at"],
                )
                
                self.table.insertRow(row)

                remaining_qty = int(batch_row["quantity_remaining"] or 0)
                status = self.get_batch_status(str(batch_row["expiry_date"] or ""), remaining_qty)

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
                    column_values = [
                        batch_row["id"],
                        batch_row["batch_no"],
                        batch_row["expiry_date"],
                        batch_row["total_received"],
                        batch_row["quantity_remaining"],
                        batch_row["unit_cost"],
                        batch_row["source"],
                        batch_row["received_at"],
                    ]
                    item = QTableWidgetItem(str(column_values[col]))
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

        try:
            product = self.productedit.text().strip()
            code = self.codeedit.text().strip()
            brand = self.brandedit.text().strip()
            formula = self.formulaedit.text().strip()
            result = update_product_detail_record(
                product_id=self.product_id,
                product_name=product,
                code=code,
                brand=brand,
                formula=formula,
                packsize=self.packsizeedit.text(),
                sale_price=self.sale_price_edit.text(),
                discount_group_id=self.discount_group_edit.currentData(),
                tax_group_id=self.tax_group_edit.currentData(),
                prescription_required=self.prescription_required_edit.isChecked(),
                media_removed=self.product_media_removed,
                selected_media_path=self.selected_product_media_path,
                audit_source="product_detail",
                audit_user_id=(QApplication.instance().property("user_id") if QApplication.instance() else None),
                audit_username=((QApplication.instance().property("username") or "") if QApplication.instance() else ""),
            )
            self.discount_group.setText(self.discount_group_edit.currentText() or "None")
            self.tax_group.setText(self.tax_group_edit.currentText() or "None")
            self.prescription_required.setText("Required" if self.prescription_required_edit.isChecked() else "Not Required")
            if self.product_media_removed:
                self.product_media_info = None
            elif result["media_info"] is not None:
                self.product_media_info = result["media_info"]
                self.selected_product_media_path = ""
                self.product_media_removed = False
            self.update_product_media_display()

            if result["price_changed"]:
                log_activity(
                    category="price",
                    action="price_updated",
                    entity_type="product",
                    entity_id=self.product_id,
                    note=(
                        f"Selling price updated for {product} (Product ID {self.product_id}). "
                        f"Pack price changed from {result['old_pack_price']} to {result['new_pack_price']} from the Product Detail screen."
                    ),
                    previous_value=str(result["old_pack_price"]),
                    new_value=str(result["new_pack_price"])
                )

            AppMessageBox.information(None, "Success", "All updates were successful")

        except Exception as e:
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




        
        
       
        
