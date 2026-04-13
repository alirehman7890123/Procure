from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHeaderView,QDialog, QLineEdit,QComboBox, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem, QMessageBox, QSpinBox, QAbstractItemView, QApplication, QCheckBox, QCompleter
from PySide6.QtCore import QFile, Qt, Signal, QTimer, QStringListModel
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from functools import partial
from PySide6.QtGui import QColor
from utilities.product_search_widget import ProductSearchBox
import csv
import os
import sys
from pathlib import Path


from utilities.stylus import load_stylesheets
from utilities.activity_logger import log_activity
from utilities.permissions import Permissions
from utilities.app_messagebox import AppMessageBox


def resource_path(relative_path: str) -> str:
    relative = Path(relative_path)
    candidates = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / relative)

    module_root = Path(__file__).resolve().parent.parent
    candidates.append(module_root / relative)
    candidates.append(Path.cwd() / relative)

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(candidates[0])



class ProductListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)
        
        self.current_page = 1
        self.page_size = 50
        self.current_search_text = ""

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(6)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Product Information", objectName="SectionTitle")
        self.master_catalog_btn = QPushButton("Master Catalog", objectName="TopRightButton")
        self.master_catalog_btn.setCursor(Qt.PointingHandCursor)
        self.master_catalog_btn.clicked.connect(self.open_master_catalog_dialog)
        self.addproduct = QPushButton("Add Product", objectName="TopRightButton")
        self.addproduct.setCursor(Qt.PointingHandCursor)
        
        
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.master_catalog_btn)
        header_layout.addWidget(self.addproduct)

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
        self.layout.addSpacing(10)
        
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)
        
        total_products_label = QLabel("Resulted Records: ")
        total_products_label.setFixedWidth(200)
        self.total_products_value = QLabel("0")
        
        # push to the left
        self.total_products_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.total_products_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) 

        
        info_layout.addWidget(total_products_label)
        info_layout.addWidget(self.total_products_value, 1)
        
        
        low_stock = QPushButton("Low Stock", objectName="TopRightButton")
        low_stock.clicked.connect(lambda: self.view_low_stock())
        
        info_layout.addWidget(low_stock)
        low_stock.setCursor(Qt.PointingHandCursor)

        self.adjust_inventory_btn = QPushButton("Adjust Inventory", objectName="TopRightButton")
        self.adjust_inventory_btn.setCursor(Qt.PointingHandCursor)
        self.adjust_inventory_btn.clicked.connect(self.open_inventory_adjustment_dialog)
        info_layout.addWidget(self.adjust_inventory_btn)

        self.change_prices_btn = QPushButton("Change Prices", objectName="TopRightButton")
        self.change_prices_btn.setCursor(Qt.PointingHandCursor)
        self.change_prices_btn.clicked.connect(self.open_price_change_dialog)
        info_layout.addWidget(self.change_prices_btn)

        

        self.layout.addLayout(info_layout)
        self.layout.addSpacing(8)
        

        # Search Field
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search product or scan barcode...")
        # convert input to uppercase
        self.search_edit.textChanged.connect(lambda text: self.search_edit.setText(text.upper()))

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.search_rows(self.search_edit.text()))
        
        self.search_edit.textChanged.connect(self.on_unified_search_text_changed)
        self.search_edit.returnPressed.connect(self.handle_unified_search_enter)


        search_layout.addWidget(self.search_edit, 6)

        self.layout.addLayout(search_layout)
        
        self.search_category = QComboBox()
        self.search_category.addItems(["Product", "Brand", "All"])
        self.search_category.setFixedWidth(150)
        search_layout.addWidget(self.search_category, 1)

        self.stock_status = QComboBox()
        self.stock_status.addItems(["All", "Available", "In Stock", "Out of Stock"])
        self.stock_status.setFixedWidth(150)
        self.stock_status.currentTextChanged.connect(self.apply_filters_on_current_input)
        search_layout.addWidget(self.stock_status)


        self.layout.addSpacing(4)
        
        


        self.row_height = 35

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.12, 0.05])
        headers = ['No.', 'Product', 'Manufacturer', 'Stock', 'Detail']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        detail_col = headers.index("Detail")
        self.table.horizontalHeaderItem(detail_col).setTextAlignment(Qt.AlignCenter)
        
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

        self.layout.addWidget(self.table, 1)
        
        # Pagination Layout
        pagination_layout = QHBoxLayout()
        
        self.page_size = 50
        self.current_page = 1

        self.prev_button = QPushButton("Previous", objectName="TopRightButton")
        self.prev_button.clicked.connect(self.show_previous_page)

        self.next_button = QPushButton("Next", objectName="TopRightButton")
        self.next_button.clicked.connect(self.show_next_page)

        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.next_button)

        self.layout.addLayout(pagination_layout)

        
        self.show_products_info()
        
        
        self.setStyleSheet(load_stylesheets())

    def _get_manufacturer_lookup(self):
        lookup = {}
        query = QSqlQuery()
        if query.exec("SELECT id, name FROM manufacturer"):
            while query.next():
                try:
                    key = str(int(query.value(0)))
                except Exception:
                    continue
                lookup[key] = str(query.value(1) or "")
        return lookup

    def open_master_catalog_dialog(self):
        csv_path = resource_path("master_products.csv")
        if not os.path.exists(csv_path):
            AppMessageBox.warning(self, "Master Catalog", f"Catalog file not found:\n{csv_path}")
            return

        manufacturer_lookup = self._get_manufacturer_lookup()

        dialog = QDialog(self)
        dialog.setWindowTitle("Master Catalog")
        dialog.resize(1120, 680)

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(12, 12, 12, 12)
        dialog_layout.setSpacing(8)

        top_row = QHBoxLayout()
        count_label = QLabel("Records:")
        count_value = QLabel("0")
        manufacturer_count_label = QLabel("Manufacturers:")
        manufacturer_count_value = QLabel(str(len(manufacturer_lookup)))
        top_row.addWidget(count_label)
        top_row.addWidget(count_value)
        top_row.addStretch()
        top_row.addWidget(manufacturer_count_label)
        top_row.addWidget(manufacturer_count_value)
        dialog_layout.addLayout(top_row)

        headers = [
            "Reg.#",
            "Name",
            "Generic",
            "Form",
            "Strength",
            "Packing",
            "Size",
            "Manufacturer ID",
            "Manufacturer Name",
        ]

        table = MyTable(column_ratios=[0.11, 0.17, 0.15, 0.09, 0.1, 0.1, 0.08, 0.1, 0.2])
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        dialog_layout.addWidget(table, 1)

        rows_loaded = 0
        try:
            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)

                for row in reader:
                    if not row or len(row) < 8:
                        continue

                    reg_no = row[0].strip()
                    name = row[1].strip()
                    generic = row[2].strip()
                    form = row[3].strip()
                    strength = row[4].strip()
                    packing = row[5].strip()
                    size = row[6].strip()
                    manufacturer_id = row[7].strip()
                    manufacturer_name = manufacturer_lookup.get(manufacturer_id, "")

                    table.insertRow(rows_loaded)
                    values = [
                        reg_no,
                        name,
                        generic,
                        form,
                        strength,
                        packing,
                        size,
                        manufacturer_id,
                        manufacturer_name,
                    ]
                    for col, value in enumerate(values):
                        table.setItem(rows_loaded, col, QTableWidgetItem(value))
                    rows_loaded += 1
        except Exception as exc:
            AppMessageBox.critical(self, "Master Catalog", f"Failed to load catalog:\n{exc}")
            return

        count_value.setText(str(rows_loaded))
        dialog.exec()


    def open_inventory_adjustment_dialog(self):
        dialog = InventoryAdjustmentDialog(self)
        dialog.adjustment_saved.connect(self.load_products_into_table)
        dialog.exec()

    @Permissions.require_permission('product.update')
    def open_price_change_dialog(self):
        try:
            dialog = PriceChangeDialog(self)
            dialog.prices_updated.connect(self.load_products_into_table)
            dialog.exec()
        except Exception as exc:
            AppMessageBox.critical(self, "Price Change Error", str(exc))
        
        
        
    def view_low_stock(self):
        
        print("view low stock clicked")

        # Implement the logic to view low stock products
        low_stock_query = QSqlQuery()
        low_stock_query.exec("""
                SELECT 
                    p.id,
                    p.display_name,
                    p.code, p.generic_name, p.brand,
                    COALESCE(SUM(b.quantity_remaining), 0) AS total_stock
                FROM product p
                LEFT JOIN batch b ON b.product_id = p.id
                LEFT JOIN (
                    SELECT product_id, MAX(COALESCE(reorder_level, 0)) AS reorder_level
                    FROM price_pack
                    GROUP BY product_id
                ) pp ON pp.product_id = p.id
                WHERE p.status = 'used'
                GROUP BY p.id, p.display_name, p.code, p.generic_name, p.brand
                HAVING COALESCE(SUM(b.quantity_remaining), 0) <= MAX(COALESCE(pp.reorder_level, 0));
            """)


        # Show the results in a new dialog or table
        self.show_query_results(low_stock_query)
        
        
        
    def view_expired_products(self):
        
        print("view expired products clicked")

        # Implement the logic to view expired products
        expired_query = QSqlQuery()
        expired_query.exec("""
            SELECT DISTINCT
                p.id,
                p.display_name,
                p.code,
                p.generic_name,
                p.brand
            FROM product p
            JOIN batch b ON b.product_id = p.id
            WHERE
                p.status = 'used'
                AND b.quantity_remaining > 0
                AND b.expiry_date IS NOT NULL
                AND (
                    CASE
                        WHEN b.expiry_date LIKE '____-__-__' THEN date(b.expiry_date)
                        WHEN b.expiry_date LIKE '__-__-____'
                            THEN date(substr(b.expiry_date, 7, 4) || '-' || substr(b.expiry_date, 4, 2) || '-' || substr(b.expiry_date, 1, 2))
                        ELSE NULL
                    END
                ) < date('now', 'localtime')
            ORDER BY p.display_name ASC
        """)

        # Show the results in a new dialog or table
        self.show_query_results(expired_query)

    
    
    def show_query_results(self, query):
        # Create a dialog to show the results
        dialog = QDialog(self)
        dialog.setWindowTitle("Query Results")
        dialog_layout = QVBoxLayout(dialog)
        
        
        query_layout = QHBoxLayout()

        item_count = QLabel("Items Found: ")
        count_value = QLabel("0")
        
        query_layout.addWidget(item_count)
        query_layout.addWidget(count_value)

        dialog_layout.addLayout(query_layout)

        results_table = MyTable(column_ratios=[0.1, 0.3, 0.2, 0.2, 0.2])
        results_table.setColumnCount(5)  # Adjust based on expected columns
        results_table.setHorizontalHeaderLabels(['ID', 'Name', 'Code', 'Generic', 'Brand'])  # Adjust headers

        results_table.setRowCount(0)
        row = 0

        while query.next():
            results_table.insertRow(row)
            for col in range(5):  # Adjust based on expected columns
                item = QTableWidgetItem(str(query.value(col)))
                results_table.setItem(row, col, item)
            row += 1

        count_value.setText(str(row))

        dialog_layout.addWidget(results_table)
        dialog.resize(800, 600)
        dialog.exec()
        
        


    def show_products_info(self):
        
        # Fetch total products
        total_query = QSqlQuery()
        total_query.exec("SELECT COUNT(*) FROM product WHERE status = 'used'")
        if total_query.next():
            total_products = total_query.value(0)
            self.total_products_value.setText(str(total_products))
        else:
            self.total_products_value.setText("0")


        # Fetch out of stock products
        low_stock_query = QSqlQuery()
        low_stock_query.exec("""
            SELECT COUNT(*) AS out_of_stock_count
            FROM (
                SELECT p.id
                FROM product p
                LEFT JOIN batch b ON b.product_id = p.id
                LEFT JOIN (
                    SELECT product_id, MAX(COALESCE(reorder_level, 0)) AS reorder_level
                    FROM price_pack
                    GROUP BY product_id
                ) pp ON pp.product_id = p.id
                WHERE p.status = 'used'
                GROUP BY p.id
                HAVING COALESCE(SUM(b.quantity_remaining), 0) <= MAX(COALESCE(pp.reorder_level, 0))
            ) t;


        """)


    def get_stock_filter_clause(self):
        stock_filter = self.stock_status.currentText()
        if stock_filter == "Available":
            return " AND p.status = 'used'"
        if stock_filter == "In Stock":
            return " AND p.status = 'used' AND COALESCE(bs.total_stock, 0) > 0"
        if stock_filter == "Out of Stock":
            return " AND p.status = 'used' AND COALESCE(bs.total_stock, 0) <= 0"
        return ""


    def on_unified_search_text_changed(self):
        text = (self.search_edit.text() or "").strip()
        if text and text.isdigit():
            return
        self.search_timer.start(90)


    def handle_unified_search_enter(self):
        text = (self.search_edit.text() or "").strip()
        if not text:
            self.load_products_into_table(page=1, page_size=self.page_size)
            return

        if text.isdigit():
            self.search_by_barcode(text)
            return

        self.search_rows(text, page=1, page_size=self.page_size)


    def apply_filters_on_current_input(self):
        text = (self.search_edit.text() or "").strip()
        if text and text.isdigit():
            self.search_by_barcode(text)
            return

        if text:
            self.search_rows(text, page=1, page_size=self.page_size)
        else:
            self.load_products_into_table(page=1, page_size=self.page_size)


    def search_by_barcode(self, code_text=None):
        code_text = (code_text or self.search_edit.text() or "").strip()

        if not code_text:
            if self.current_search_text:
                self.search_rows(self.current_search_text, page=1, page_size=self.page_size)
            else:
                self.load_products_into_table(page=1, page_size=self.page_size)
            return

        from_clause = """
            FROM product p
            LEFT JOIN manufacturer m ON p.manufacturer_id = m.id
            LEFT JOIN (
                SELECT product_id, SUM(quantity_remaining) AS total_stock
                FROM batch
                GROUP BY product_id
            ) bs ON p.id = bs.product_id
        """

        where_clause = "WHERE TRIM(CAST(p.code AS TEXT)) = ?"
        where_clause += self.get_stock_filter_clause()

        query = QSqlQuery()
        query.prepare(f"""
            SELECT
                p.id,
                p.display_name,
                COALESCE(m.name, '') AS manufacturer_name,
                COALESCE(bs.total_stock, 0) AS total_stock
            {from_clause}
            {where_clause}
            LIMIT 1
        """)
        query.addBindValue(code_text)

        if not query.exec():
            print("Barcode search query failed:", query.lastError().text())
            return

        self.table.setRowCount(0)
        if not query.next():
            AppMessageBox.information(self, "Not Found", f"No product found for barcode '{code_text}'.")
            self.total_products_value.setText("<b>0</b>")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return

        product_id = int(query.value(0))
        display_name = str(query.value(1) or "")
        manufacturer_name = str(query.value(2) or "")
        total_stock = query.value(3) or 0

        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem("1"))
        self.table.setItem(0, 1, QTableWidgetItem(display_name))
        self.table.setItem(0, 2, QTableWidgetItem(manufacturer_name))
        self.table.setItem(0, 3, QTableWidgetItem(str(total_stock)))

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignCenter)

        detail = QPushButton("Details")
        detail.setCursor(Qt.PointingHandCursor)
        detail.setFixedSize(80, 28)
        detail.setStyleSheet("""
            QPushButton {
                background-color: #f5f0f6;
                color: #244A62;
                border: 1px solid #d8c7da;
                border-radius: 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #244A62;
                color: white;
                border: 1px solid #244A62;
            }
        """)
        layout.addWidget(detail)
        detail.clicked.connect(partial(self.detailpagesignal.emit, product_id))
        self.table.setCellWidget(0, 4, detail)

        self.total_products_value.setText("<b>1</b>")
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        

            
            


    def show_next_page(self):
        
        next_page = self.current_page + 1

        if self.current_search_text:
            self.search_rows(
                self.current_search_text,
                page=next_page,
                page_size=self.page_size
            )
        else:
            self.load_products_into_table(
                page=next_page,
                page_size=self.page_size
            )
    
    def show_previous_page(self):
        
        if self.current_page <= 1:
            return

        prev_page = self.current_page - 1

        if self.current_search_text:
            self.search_rows(
                self.current_search_text,
                page=prev_page,
                page_size=self.page_size
            )
        else:
            self.load_products_into_table(
                page=prev_page,
                page_size=self.page_size
            )

        
    
    
    def showEvent(self, event):
        
        super().showEvent(event)
        self.load_products_into_table()
        
        

    def search_rows(self, text, page=1, page_size=50):
        
        self.current_search_text = text
        self.current_page = page
        
        text = text.strip()

        if text == '':
            self.load_products_into_table(page=page, page_size=page_size)
            return

        category = self.search_category.currentText()
        pattern = f"%{text}%"
        prefix_pattern = f"{text}%"
        offset = (page - 1) * page_size

        self.table.setRowCount(0)

        # common FROM + JOIN part
        from_clause = """
            FROM product p
            LEFT JOIN manufacturer m
                ON p.manufacturer_id = m.id
            LEFT JOIN (
                SELECT product_id, SUM(quantity_remaining) AS total_stock
                FROM batch
                GROUP BY product_id
            ) bs
                ON p.id = bs.product_id
        """

        where_clause = "WHERE 1=1"
        where_clause += self.get_stock_filter_clause()

        bindings = []
        order_bindings = []
        order_clause = "ORDER BY p.id DESC"

        if category == "Product":
            where_clause += " AND p.display_name LIKE ?"
            bindings.append(pattern)
            order_clause = """
                ORDER BY
                    CASE
                        WHEN UPPER(p.display_name) = UPPER(?) THEN 0
                        WHEN UPPER(p.display_name) LIKE UPPER(?) THEN 1
                        ELSE 2
                    END,
                    p.display_name ASC,
                    p.id DESC
            """
            order_bindings.extend([text, prefix_pattern])

        elif category == "Brand":
            where_clause += " AND COALESCE(m.name, '') LIKE ?"
            bindings.append(pattern)
            order_clause = """
                ORDER BY
                    CASE
                        WHEN UPPER(COALESCE(m.name, '')) = UPPER(?) THEN 0
                        WHEN UPPER(COALESCE(m.name, '')) LIKE UPPER(?) THEN 1
                        ELSE 2
                    END,
                    COALESCE(m.name, '') ASC,
                    p.display_name ASC,
                    p.id DESC
            """
            order_bindings.extend([text, prefix_pattern])

        elif category == "All":
            where_clause += """
                AND (
                    p.display_name LIKE ?
                    OR COALESCE(m.name, '') LIKE ?
                )
            """
            bindings.extend([pattern, pattern])
            order_clause = """
                ORDER BY
                    CASE
                        WHEN UPPER(p.display_name) = UPPER(?) THEN 0
                        WHEN UPPER(p.display_name) LIKE UPPER(?) THEN 1
                        WHEN UPPER(COALESCE(m.name, '')) = UPPER(?) THEN 2
                        WHEN UPPER(COALESCE(m.name, '')) LIKE UPPER(?) THEN 3
                        ELSE 4
                    END,
                    p.display_name ASC,
                    p.id DESC
            """
            order_bindings.extend([text, prefix_pattern, text, prefix_pattern])

        else:
            where_clause += " AND p.display_name LIKE ?"
            bindings.append(pattern)
            order_clause = """
                ORDER BY
                    CASE
                        WHEN UPPER(p.display_name) = UPPER(?) THEN 0
                        WHEN UPPER(p.display_name) LIKE UPPER(?) THEN 1
                        ELSE 2
                    END,
                    p.display_name ASC,
                    p.id DESC
            """
            order_bindings.extend([text, prefix_pattern])

        # 1) count only filtered rows
        count_query = QSqlQuery()
        count_sql = f"""
            SELECT COUNT(*)
            {from_clause}
            {where_clause}
        """
        count_query.prepare(count_sql)

        for value in bindings:
            count_query.addBindValue(value)

        total_records = 0
        if count_query.exec() and count_query.next():
            total_records = int(count_query.value(0))
        else:
            print("Count query failed:", count_query.lastError().text())
            return

        # 2) load only current page
        data_query = QSqlQuery()
        data_sql = f"""
            SELECT
                p.id,
                p.display_name,
                COALESCE(m.name, '') AS manufacturer_name,
                COALESCE(bs.total_stock, 0) AS total_stock
            {from_clause}
            {where_clause}
            {order_clause}
            LIMIT ? OFFSET ?
        """
        data_query.prepare(data_sql)

        for value in bindings:
            data_query.addBindValue(value)
        for value in order_bindings:
            data_query.addBindValue(value)

        data_query.addBindValue(page_size)
        data_query.addBindValue(offset)

        if not data_query.exec():
            print("Search query failed:", data_query.lastError().text())
            return

        row = 0
        while data_query.next():
            self.table.insertRow(row)

            product_id = int(data_query.value(0))
            display_name = str(data_query.value(1) or "")
            manufacturer_name = str(data_query.value(2) or "")
            total_stock = data_query.value(3) or 0

            self.table.setItem(row, 0, QTableWidgetItem(str(offset + row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(display_name))
            self.table.setItem(row, 2, QTableWidgetItem(manufacturer_name))
            self.table.setItem(row, 3, QTableWidgetItem(str(total_stock)))

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setAlignment(Qt.AlignCenter)

            container = QWidget()

            layout = QHBoxLayout(container)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setAlignment(Qt.AlignCenter)

            detail = QPushButton("Details")
            detail.setCursor(Qt.PointingHandCursor)
            detail.setFixedSize(80, 28)

            detail.setStyleSheet("""
                QPushButton {
                    background-color: #f5f0f6;
                    color: #244A62;
                    border: 1px solid #d8c7da;
                    border-radius: 14px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #244A62;
                    color: white;
                    border: 1px solid #244A62;
                }
            """)

            layout.addWidget(detail)


            detail.clicked.connect(partial(self.detailpagesignal.emit, product_id))
            
            self.table.setCellWidget(row, 4, detail)


            row += 1

        self.total_products_value.setText(f"<b>{total_records}</b>")

        total_pages = max(1, (total_records + page_size - 1) // page_size)
        self.prev_button.setEnabled(page > 1)
        self.next_button.setEnabled(page < total_pages)    
        
        
            
        

    def load_products_into_table(self, page=1, page_size=50):
        
        self.current_page = page
        self.page_size = page_size
        self.current_search_text = ""

        stock_where = "WHERE 1=1"
        stock_where += self.get_stock_filter_clause()

        from_clause = """
            FROM product p
            LEFT JOIN manufacturer m ON p.manufacturer_id = m.id
            LEFT JOIN (
                SELECT product_id, SUM(quantity_remaining) AS total_stock
                FROM batch
                GROUP BY product_id
            ) bs ON p.id = bs.product_id
        """

        # total count
        count_query = QSqlQuery()
        if not count_query.exec(f"SELECT COUNT(*) {from_clause} {stock_where}"):
            print("Count error:", count_query.lastError().text())
            return

        total_records = 0
        if count_query.next():
            total_records = int(count_query.value(0))

        offset = (page - 1) * page_size

        query = QSqlQuery()
        query.prepare(f"""
            SELECT 
                p.id,
                p.display_name,
                COALESCE(m.name, '') AS manufacturer_name,
                COALESCE(bs.total_stock, 0) AS total_stock
            {from_clause}
            {stock_where}
            ORDER BY p.id DESC
            LIMIT ? OFFSET ?
        """)
        query.addBindValue(page_size)
        query.addBindValue(offset)

        if not query.exec():
            print("Load error:", query.lastError().text())
            return

        self.table.setRowCount(0)
        row = 0

        while query.next():
            self.table.insertRow(row)

            product_id = int(query.value(0))
            display_name = str(query.value(1) or "")
            manufacturer_name = str(query.value(2) or "")
            total_stock = query.value(3) or 0

            self.table.setItem(row, 0, QTableWidgetItem(str(offset + row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(display_name))
            self.table.setItem(row, 2, QTableWidgetItem(manufacturer_name))
            self.table.setItem(row, 3, QTableWidgetItem(str(total_stock)))
            
            
           
            container = QWidget()

            layout = QHBoxLayout(container)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setAlignment(Qt.AlignCenter)

            detail = QPushButton("Details")
            detail.setCursor(Qt.PointingHandCursor)
            detail.setFixedSize(80, 28)

            detail.setStyleSheet("""
                QPushButton {
                    background-color: #f5f0f6;
                    color: #244A62;
                    border: 1px solid #d8c7da;
                    border-radius: 14px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #244A62;
                    color: white;
                    border: 1px solid #244A62;
                }
            """)

            layout.addWidget(detail)

            detail.clicked.connect(partial(self.detailpagesignal.emit, product_id))
            
            self.table.setCellWidget(row, 4, detail)

            row += 1
            

        self.total_products_value.setText(f"<b>{total_records}</b>")

        total_pages = max(1, (total_records + page_size - 1) // page_size)
        self.prev_button.setEnabled(page > 1)
        self.next_button.setEnabled(page < total_pages) 
            
            
                    





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


class InventoryAdjustmentDialog(QDialog):
    adjustment_saved = Signal()

    REASONS = [
        "stock_count_mismatch",
        "manual_correction",
        "expired",
        "damaged",
        "disposed",
        "lost",
        "found",
        "broken_pack",
        "theft",
        "other",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory Adjustment")
        self.resize(1100, 650)

        self.current_user_id = self.get_current_user_id()

        layout = QVBoxLayout(self)

        header = QLabel("Batch-Level Inventory Adjustment")
        header.setObjectName("SectionTitle")
        layout.addWidget(header)

        instruction = QLabel(
            "Select a product, edit only the rows that changed, then save. "
            "Each changed row creates a separate adjustment record."
        )
        instruction.setWordWrap(True)
        layout.addWidget(instruction)

        filter_row = QHBoxLayout()
        product_label = QLabel("Product")
        product_label.setFixedWidth(70)
        self.product_selector = QComboBox()
        self.product_selector.setEditable(True)
        self.product_selector.setInsertPolicy(QComboBox.NoInsert)
        self.product_selector.currentIndexChanged.connect(self.load_batches_for_selected_product)

        filter_row.addWidget(product_label)
        filter_row.addWidget(self.product_selector, 1)
        layout.addLayout(filter_row)

        self.show_sold_out_checkbox = QCheckBox("Show sold-out batches")
        self.show_sold_out_checkbox.setChecked(False)
        self.show_sold_out_checkbox.stateChanged.connect(self.load_batches_for_selected_product)
        layout.addWidget(self.show_sold_out_checkbox)

        self.stock_summary = QLabel("System Stock: 0")
        layout.addWidget(self.stock_summary)

        self.batch_table = QTableWidget(0, 8)
        self.batch_table.setHorizontalHeaderLabels([
            "Batch ID",
            "Batch No",
            "Expiry",
            "System Qty",
            "Actual Qty",
            "Reason",
            "Note",
            "Delta",
        ])
        self.batch_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.batch_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.batch_table.setAlternatingRowColors(True)
        self.batch_table.horizontalHeader().setStretchLastSection(True)
        self.batch_table.verticalHeader().setVisible(False)
        self.batch_table.setColumnHidden(0, True)
        layout.addWidget(self.batch_table, 1)

        self.save_button = QPushButton("Save Adjustments", objectName="SaveButton")
        self.save_button.clicked.connect(self.save_adjustments)
        layout.addWidget(self.save_button)

        self.setStyleSheet(load_stylesheets())
        self.populate_product_selector()

    def get_current_user_id(self):
        username = QApplication.instance().property("username")
        if not username:
            return None

        query = QSqlQuery()
        query.prepare("SELECT id FROM auth WHERE username = ? LIMIT 1")
        query.addBindValue(username)
        if query.exec() and query.next():
            return int(query.value(0))
        return None

    def populate_product_selector(self):
        self.product_selector.blockSignals(True)
        self.product_selector.clear()
        self.product_selector.addItem("Select a product...", None)

        query = QSqlQuery()
        query.prepare("""
            SELECT id, display_name
            FROM product
            WHERE status = 'used'
            ORDER BY display_name ASC
        """)

        if not query.exec():
            AppMessageBox.critical(self, "Error", f"Failed to load products: {query.lastError().text()}")
            self.product_selector.blockSignals(False)
            return

        while query.next():
            self.product_selector.addItem(str(query.value(1) or ""), int(query.value(0)))

        self.product_selector.blockSignals(False)

    def get_selected_product_id(self):
        return self.product_selector.currentData()

    def load_batches_for_selected_product(self):
        product_id = self.get_selected_product_id()
        self.batch_table.setRowCount(0)
        self.stock_summary.setText("System Stock: 0")

        if not product_id:
            return

        include_sold_out = self.show_sold_out_checkbox.isChecked()

        sql = """
            SELECT
                id,
                COALESCE(batch_no, ''),
                COALESCE(expiry_date, ''),
                COALESCE(quantity_remaining, 0)
            FROM batch
            WHERE product_id = ?
        """

        if not include_sold_out:
            sql += "\n              AND COALESCE(quantity_remaining, 0) > 0"

        sql += """
            ORDER BY received_at ASC, id ASC
        """

        query = QSqlQuery()
        query.prepare(sql)
        query.addBindValue(product_id)

        if not query.exec():
            AppMessageBox.critical(self, "Error", f"Failed to load batches: {query.lastError().text()}")
            return

        row = 0
        total_stock = 0
        while query.next():
            batch_id = int(query.value(0))
            batch_no = str(query.value(1) or "")
            expiry_date = str(query.value(2) or "")
            system_qty = int(query.value(3) or 0)

            total_stock += system_qty
            self.batch_table.insertRow(row)

            id_item = QTableWidgetItem(str(batch_id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.batch_table.setItem(row, 0, id_item)

            batch_item = QTableWidgetItem(batch_no)
            batch_item.setFlags(batch_item.flags() & ~Qt.ItemIsEditable)
            self.batch_table.setItem(row, 1, batch_item)

            expiry_item = QTableWidgetItem(expiry_date)
            expiry_item.setFlags(expiry_item.flags() & ~Qt.ItemIsEditable)
            self.batch_table.setItem(row, 2, expiry_item)

            current_item = QTableWidgetItem(str(system_qty))
            current_item.setFlags(current_item.flags() & ~Qt.ItemIsEditable)
            self.batch_table.setItem(row, 3, current_item)

            actual_spin = QSpinBox()
            actual_spin.setRange(0, 100000000)
            actual_spin.setValue(system_qty)
            actual_spin.valueChanged.connect(self.update_row_delta)
            self.batch_table.setCellWidget(row, 4, actual_spin)

            reason_combo = QComboBox()
            reason_combo.addItem("Select reason...")
            reason_combo.addItems(self.REASONS)
            self.batch_table.setCellWidget(row, 5, reason_combo)

            note_edit = QLineEdit()
            note_edit.setPlaceholderText("Optional note")
            self.batch_table.setCellWidget(row, 6, note_edit)

            delta_item = QTableWidgetItem("0")
            delta_item.setFlags(delta_item.flags() & ~Qt.ItemIsEditable)
            self.batch_table.setItem(row, 7, delta_item)

            row += 1

        self.stock_summary.setText(f"System Stock: {total_stock}")

    def update_row_delta(self):
        for row in range(self.batch_table.rowCount()):
            system_item = self.batch_table.item(row, 3)
            delta_item = self.batch_table.item(row, 7)
            actual_widget = self.batch_table.cellWidget(row, 4)

            if not system_item or not delta_item or not actual_widget:
                continue

            current_qty = int(system_item.text() or 0)
            actual_qty = int(actual_widget.value())
            delta = actual_qty - current_qty
            delta_item.setText(str(delta))

    def save_adjustments(self):
        if not Permissions.has_permission("inventory.adjust"):
            AppMessageBox.warning(self, "Permission Denied", "Only admins can adjust inventory.")
            return

        if self.current_user_id is None:
            AppMessageBox.warning(self, "Session Error", "Unable to resolve current user ID.")
            return

        changed_rows = []
        for row in range(self.batch_table.rowCount()):
            batch_item = self.batch_table.item(row, 0)
            current_item = self.batch_table.item(row, 3)
            actual_widget = self.batch_table.cellWidget(row, 4)
            reason_widget = self.batch_table.cellWidget(row, 5)
            note_widget = self.batch_table.cellWidget(row, 6)

            if not batch_item or not current_item or not actual_widget or not reason_widget or not note_widget:
                continue

            batch_id = int(batch_item.text())
            old_qty = int(current_item.text() or 0)
            new_qty = int(actual_widget.value())

            if new_qty == old_qty:
                continue

            batch_no_item = self.batch_table.item(row, 1)
            batch_no = batch_no_item.text().strip() if batch_no_item else ""

            reason = reason_widget.currentText().strip()
            if reason == "Select reason...":
                AppMessageBox.warning(
                    self,
                    "Validation Error",
                    f"Reason is required for changed row {row + 1}."
                )
                return

            note = note_widget.text().strip()
            delta = new_qty - old_qty
            adjustment_type = "addition" if delta > 0 else "deduction"
            qty = abs(delta)

            changed_rows.append({
                "batch_id": batch_id,
                "batch_no": batch_no,
                "old_qty": old_qty,
                "new_qty": new_qty,
                "qty": qty,
                "adjustment_type": adjustment_type,
                "reason": reason,
                "note": note,
            })

        if not changed_rows:
            AppMessageBox.information(self, "No Changes", "No modified rows found.")
            return

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.critical(self, "Database Error", "Failed to start inventory adjustment transaction.")
            return

        insert_query = QSqlQuery(db)
        update_query = QSqlQuery(db)

        for row_data in changed_rows:
            insert_query.prepare("""
                INSERT INTO inventory_adjustment (
                    batch_id, qty, adjustment_type, old_qty, new_qty, reason, note, adjusted_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """)
            insert_query.addBindValue(row_data["batch_id"])
            insert_query.addBindValue(row_data["qty"])
            insert_query.addBindValue(row_data["adjustment_type"])
            insert_query.addBindValue(row_data["old_qty"])
            insert_query.addBindValue(row_data["new_qty"])
            insert_query.addBindValue(row_data["reason"])
            insert_query.addBindValue(row_data["note"])
            insert_query.addBindValue(self.current_user_id)

            if not insert_query.exec():
                db.rollback()
                AppMessageBox.critical(self, "Save Failed", f"Failed to insert adjustment: {insert_query.lastError().text()}")
                return

            update_query.prepare("""
                UPDATE batch
                SET quantity_remaining = ?
                WHERE id = ?
            """)
            update_query.addBindValue(row_data["new_qty"])
            update_query.addBindValue(row_data["batch_id"])

            if not update_query.exec():
                db.rollback()
                AppMessageBox.critical(self, "Save Failed", f"Failed to update batch stock: {update_query.lastError().text()}")
                return

        if not db.commit():
            db.rollback()
            AppMessageBox.critical(self, "Save Failed", "Failed to commit inventory adjustment transaction.")
            return

        AppMessageBox.information(self, "Saved", f"{len(changed_rows)} batch adjustment(s) saved successfully.")

        # Audit log — one row per adjusted batch (non-blocking)
        product_name = self.product_selector.currentText()
        for row_data in changed_rows:
            direction = "increased" if row_data["adjustment_type"] == "addition" else "decreased"
            batch_label = row_data["batch_no"] or str(row_data["batch_id"])
            log_activity(
                category="stock",
                action="stock_adjusted",
                entity_type="batch",
                entity_id=row_data["batch_id"],
                note=(
                    f"Stock was {direction} for {product_name}, batch {batch_label}. "
                    f"Quantity changed from {row_data['old_qty']} to {row_data['new_qty']}. "
                    f"Reason: {row_data['reason']}."
                ),
                previous_value=str(row_data["old_qty"]),
                new_value=str(row_data["new_qty"])
            )

        self.adjustment_saved.emit()
        self.accept()


class PriceChangeDialog(QDialog):
    prices_updated = Signal()

    PRODUCT_ID_COL = 0
    PRODUCT_COL = 1
    CODE_COL = 2
    CURRENT_COL = 3
    NEW_COL = 4
    VARIANCE_COL = 5
    REMOVE_COL = 6

    @staticmethod
    def dialog_section_style(kind):
        if kind == "header":
            return (
                "background-color: #DFE8EF;"
                "border: 1px solid #C9D5DF;"
                "border-radius: 3px;"
                "padding: 8px;"
            )
        if kind == "footer":
            return (
                "background-color: #DFE8EF;"
                "border: 1px solid #C9D5DF;"
                "border-radius: 3px;"
                "padding: 8px;"
            )
        return (
            "background-color: #EEF4F8;"
            "border: 1px solid #D6E1E8;"
            "border-radius: 3px;"
            "padding: 8px;"
        )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Price Change")
        self.resize(980, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        header_section = QWidget()
        header_section.setObjectName("dialogHeader")
        header_section.setStyleSheet(
            f"QWidget#dialogHeader {{ {self.dialog_section_style('header')} }}"
        )
        header_layout = QVBoxLayout(header_section)
        header_layout.setContentsMargins(10, 8, 10, 8)
        header_layout.setSpacing(6)

        heading = QLabel("Price Change")
        heading.setObjectName("SectionTitle")
        header_layout.addWidget(heading)
        header_layout.addStretch()

        instruction = QLabel(
            "Add a few products, update only the new prices you want to apply, then save. "
            "Only changed rows will be committed and logged."
        )
        instruction.setWordWrap(True)
        header_layout.addWidget(instruction)
        layout.addWidget(header_section)

        content_section = QWidget()
        content_section.setObjectName("dialogContent")
        content_section.setStyleSheet(
            f"QWidget#dialogContent {{ {self.dialog_section_style('content')} }}"
        )
        content_layout = QVBoxLayout(content_section)
        content_layout.setContentsMargins(10, 8, 10, 8)
        content_layout.setSpacing(8)

        selector_row = QHBoxLayout()
        selector_label = QLabel("Product")
        selector_label.setFixedWidth(70)
        self.product_selector = ProductSearchBox(self, query_fn=self._product_selector_query, placeholder="Search product...")
        self.product_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.product_selector.setMaxVisibleItems(15)
        self._skip_next_selector_return = False
        self.product_selector.product_selected_with_data.connect(
            lambda pid, name, data: self.on_product_selector_item_selected(name)
        )
        if self.product_selector.lineEdit() is not None:
            self.product_selector.lineEdit().returnPressed.connect(self.handle_product_selector_return)
        self.add_item_btn = QPushButton("Add Item", objectName="TopRightButton")
        self.add_item_btn.setCursor(Qt.PointingHandCursor)
        self.add_item_btn.setAutoDefault(False)
        self.add_item_btn.setDefault(False)
        self.add_item_btn.clicked.connect(self.add_selected_product_row)
        selector_row.addWidget(selector_label)
        selector_row.addWidget(self.product_selector, 1)
        selector_row.addWidget(self.add_item_btn)
        content_layout.addLayout(selector_row)

        self.summary_label = QLabel("No items selected.")
        content_layout.addWidget(self.summary_label)

        self.table = MyTable(column_ratios=[0.01, 0.30, 0.16, 0.14, 0.14, 0.13, 0.12])
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Product ID",
            "Product",
            "Code",
            "Current Price",
            "New Price",
            "Variance",
            "Remove",
        ])
        self.table.setMinimumWidth(900)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(self.PRODUCT_ID_COL, True)
        self.table.itemChanged.connect(self.on_item_changed)
        content_layout.addWidget(self.table, 1)
        layout.addWidget(content_section, 1)

        footer_section = QWidget()
        footer_section.setObjectName("dialogFooter")
        footer_section.setStyleSheet(
            f"QWidget#dialogFooter {{ {self.dialog_section_style('footer')} }}"
        )
        button_row = QHBoxLayout()
        button_row.setContentsMargins(10, 8, 10, 8)
        button_row.addStretch(1)
        cancel_btn = QPushButton("Cancel", objectName="TopRightButton")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Save Changes", objectName="SaveButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedWidth(132)
        self.save_btn.setAutoDefault(False)
        self.save_btn.setDefault(False)
        self.save_btn.clicked.connect(self.save_changes)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(self.save_btn)
        footer_section.setLayout(button_row)
        layout.addWidget(footer_section)

        self.setStyleSheet(load_stylesheets())
        self.setProperty("disableAutoDialogScroll", True)
        self.populate_product_selector()

    def populate_product_selector(self):
        self.product_selector.clear_selection()
        if self.product_selector.lineEdit() is not None:
            self.product_selector.lineEdit().setPlaceholderText("Search product or code...")

    def clear_product_selector(self):
        self.product_selector.clear_selection()
        if self.product_selector.lineEdit() is not None:
            self.product_selector.lineEdit().setPlaceholderText("Search product or code...")

    def _product_selector_query(self, search_text: str) -> list:
        """Custom query for price-change product selector: searches by name OR code."""
        query = QSqlQuery()
        query.prepare("""
            SELECT
                p.id,
                COALESCE(p.display_name, '') AS display_name,
                COALESCE(CAST(p.code AS TEXT), '') AS code,
                COALESCE((
                    SELECT pp.pack_price
                    FROM price_pack pp
                    WHERE pp.product_id = p.id
                    ORDER BY pp.is_default DESC, pp.id ASC
                    LIMIT 1
                ), 0) AS current_price
            FROM product p
            WHERE
                p.display_name LIKE ?
                OR TRIM(CAST(p.code AS TEXT)) LIKE ?
            ORDER BY p.display_name ASC
            LIMIT 10
        """)
        query.addBindValue(f"%{search_text}%")
        query.addBindValue(f"%{search_text}%")
        results = []
        if query.exec():
            while query.next():
                label = f"{str(query.value(1) or '')} [{str(query.value(2) or '')}]"
                results.append((label, {
                    "product_id": int(query.value(0) or 0),
                    "product_name": str(query.value(1) or ""),
                    "code": str(query.value(2) or ""),
                    "current_price": float(query.value(3) or 0.0),
                }))
        return results

    def on_product_selector_item_selected(self, text):
        index = self.product_selector.findText(text.strip(), Qt.MatchExactly)
        if index >= 0:
            self.product_selector.setCurrentIndex(index)
            if self.product_selector.lineEdit() is not None:
                self.product_selector.lineEdit().setText(text)
            self._skip_next_selector_return = True
            QTimer.singleShot(0, self.add_selected_product_row)

    def handle_product_selector_return(self):
        if self._skip_next_selector_return:
            self._skip_next_selector_return = False
            return
        self.add_selected_product_row()

    def resolve_selected_product(self):
        current_data = self.product_selector.currentData()
        if isinstance(current_data, dict):
            return current_data

        entered_text = ""
        if self.product_selector.lineEdit() is not None:
            entered_text = (self.product_selector.lineEdit().text() or "").strip()
        if not entered_text:
            return None

        for index in range(self.product_selector.count()):
            if self.product_selector.itemText(index).strip() == entered_text:
                selected = self.product_selector.itemData(index)
                if selected:
                    return selected

        query = QSqlQuery()
        query.prepare("""
            SELECT
                p.id,
                COALESCE(p.display_name, '') AS display_name,
                COALESCE(CAST(p.code AS TEXT), '') AS code,
                COALESCE((
                    SELECT pp.pack_price
                    FROM price_pack pp
                    WHERE pp.product_id = p.id
                    ORDER BY pp.is_default DESC, pp.id ASC
                    LIMIT 1
                ), 0) AS current_price
            FROM product p
            WHERE
                UPPER(TRIM(p.display_name)) = UPPER(TRIM(?))
                OR TRIM(CAST(p.code AS TEXT)) = ?
            ORDER BY p.display_name ASC
            LIMIT 1
        """)
        query.addBindValue(entered_text)
        query.addBindValue(entered_text)

        if not query.exec():
            AppMessageBox.critical(self, "Error", f"Failed to search product: {query.lastError().text()}")
            self.clear_product_selector()
            return None

        if not query.next():
            AppMessageBox.information(self, "Not Found", f"No product found for '{entered_text}'.")
            self.clear_product_selector()
            return None

        return {
            "product_id": int(query.value(0) or 0),
            "product_name": str(query.value(1) or ""),
            "code": str(query.value(2) or ""),
            "current_price": float(query.value(3) or 0.0),
        }

    def add_selected_product_row(self):
        selected = self.resolve_selected_product()
        if not selected:
            if self.product_selector.lineEdit() is None or not self.product_selector.lineEdit().text().strip():
                AppMessageBox.warning(self, "Selection Required", "Choose or search a product before adding it.")
            return

        product_id = int(selected["product_id"])
        for row in range(self.table.rowCount()):
            existing = self.table.item(row, self.PRODUCT_ID_COL)
            if existing and int(existing.text() or 0) == product_id:
                AppMessageBox.information(self, "Already Added", "This product is already in the list.")
                self.table.setCurrentCell(row, self.NEW_COL)
                self.clear_product_selector()
                return

        row = self.table.rowCount()
        self.table.blockSignals(True)
        self.table.insertRow(row)

        id_item = QTableWidgetItem(str(product_id))
        name_item = QTableWidgetItem(selected["product_name"])
        code_item = QTableWidgetItem(selected["code"])
        current_item = QTableWidgetItem(f"{float(selected['current_price']):.2f}")
        new_item = QTableWidgetItem(f"{float(selected['current_price']):.2f}")
        variance_item = QTableWidgetItem("0.00")

        for item in (id_item, name_item, code_item, current_item, variance_item):
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        self.table.setItem(row, self.PRODUCT_ID_COL, id_item)
        self.table.setItem(row, self.PRODUCT_COL, name_item)
        self.table.setItem(row, self.CODE_COL, code_item)
        self.table.setItem(row, self.CURRENT_COL, current_item)
        self.table.setItem(row, self.NEW_COL, new_item)
        self.table.setItem(row, self.VARIANCE_COL, variance_item)

        remove_btn = QPushButton("Remove", objectName="TopRightButton")
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setAutoDefault(False)
        remove_btn.setDefault(False)
        self.table.setCellWidget(row, self.REMOVE_COL, remove_btn)
        self.table.blockSignals(False)

        self.refresh_remove_buttons()
        self.update_summary()
        self.clear_product_selector()
        if self.product_selector.lineEdit() is not None:
            self.product_selector.lineEdit().setFocus()

    def refresh_remove_buttons(self):
        for row in range(self.table.rowCount()):
            button = self.table.cellWidget(row, self.REMOVE_COL)
            if button is None:
                continue
            try:
                button.clicked.disconnect()
            except Exception:
                pass
            button.clicked.connect(lambda _checked=False, current_row=row: self.remove_row(current_row))

    def remove_row(self, row):
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
            self.refresh_remove_buttons()
            self.update_summary()

    def on_item_changed(self, item):
        if item.column() != self.NEW_COL:
            return

        variance_item = self.table.item(item.row(), self.VARIANCE_COL)
        current_item = self.table.item(item.row(), self.CURRENT_COL)
        if variance_item is None or current_item is None:
            return

        try:
            new_price = float((item.text() or "").strip())
            current_price = float(current_item.text() or 0.0)
        except ValueError:
            variance_item.setText("Invalid")
            self.update_summary()
            return

        variance_item.setText(f"{(new_price - current_price):.2f}")
        self.update_summary()

    def update_summary(self):
        if self.table.rowCount() == 0:
            self.summary_label.setText("No items selected.")
            return

        changed_rows = 0
        for row in range(self.table.rowCount()):
            current_item = self.table.item(row, self.CURRENT_COL)
            new_item = self.table.item(row, self.NEW_COL)
            if current_item is None or new_item is None:
                continue
            try:
                current_price = float(current_item.text() or 0.0)
                new_price = float((new_item.text() or "").strip())
            except ValueError:
                continue
            if abs(new_price - current_price) > 0.000001:
                changed_rows += 1

        self.summary_label.setText(
            f"Selected Items: {self.table.rowCount()} | Pending Changes: {changed_rows}"
        )

    @Permissions.require_permission('product.update')
    def save_changes(self):
        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.critical(self, "Database Error", "Could not start price change transaction.")
            return

        try:
            app = QApplication.instance()
            current_user_id = app.property("user_id") if app else None
            current_username = (app.property("username") or "") if app else ""
            changed_count = 0

            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, self.PRODUCT_ID_COL)
                name_item = self.table.item(row, self.PRODUCT_COL)
                current_item = self.table.item(row, self.CURRENT_COL)
                new_item = self.table.item(row, self.NEW_COL)

                if None in (id_item, name_item, current_item, new_item):
                    continue

                product_id = int(id_item.text() or 0)
                product_name = str(name_item.text() or f"Product {product_id}")
                previous_price = float(current_item.text() or 0.0)
                new_price_text = (new_item.text() or "").strip()

                if not new_price_text:
                    continue

                try:
                    new_price = float(new_price_text)
                except ValueError:
                    raise Exception(f"Invalid new price for {product_name}.")

                if new_price < 0:
                    raise Exception(f"New price cannot be negative for {product_name}.")

                if abs(new_price - previous_price) <= 0.000001:
                    continue

                update_query = QSqlQuery()
                update_query.prepare("""
                    UPDATE price_pack
                    SET pack_price = ?
                    WHERE id = (
                        SELECT id
                        FROM price_pack
                        WHERE product_id = ?
                        ORDER BY is_default DESC, id ASC
                        LIMIT 1
                    )
                """)
                update_query.addBindValue(new_price)
                update_query.addBindValue(product_id)

                if not update_query.exec():
                    raise Exception(f"Failed to update {product_name}: {update_query.lastError().text()}")

                if update_query.numRowsAffected() == 0:
                    raise Exception(f"No default price row found for {product_name}.")

                change_query = QSqlQuery()
                change_query.prepare("""
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
                change_query.addBindValue(product_id)
                change_query.addBindValue(previous_price)
                change_query.addBindValue(new_price)
                change_query.addBindValue("price_change_dialog")
                change_query.addBindValue(current_user_id)
                change_query.addBindValue(current_username)

                if not change_query.exec():
                    raise Exception(f"Failed to log price change for {product_name}: {change_query.lastError().text()}")

                log_activity(
                    category="price",
                    action="price_updated",
                    entity_type="product",
                    entity_id=product_id,
                    note=(
                        f"Selling price updated for {product_name} (Product ID {product_id}). "
                        f"Pack price changed from {previous_price} to {new_price} from the Price Change dialog."
                    ),
                    previous_value=str(previous_price),
                    new_value=str(new_price)
                )

                changed_count += 1

            if changed_count == 0:
                raise Exception("Enter at least one changed price before saving.")

            if not db.commit():
                raise Exception("Could not commit price changes.")

            AppMessageBox.success(self, "Saved", f"{changed_count} price change(s) saved successfully.")
            self.prices_updated.emit()
            self.accept()

        except Exception as e:
            db.rollback()
            AppMessageBox.critical(self, "Error", str(e))




            
            
import math
from PySide6.QtWidgets import QDialog, QDialogButtonBox
from utilities.app_messagebox import AppMessageBox

class ImportDialog(QDialog):
    
    # ... your __init__ / UI methods ...
    def __init__(self, parent=None):
        
        super().__init__(parent)
        self.setWindowTitle("Import Stock Data")
        self.resize(600, 400)

        layout = QVBoxLayout()
        
        # Search Field
        self.search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search Product...")
        self.search_edit.textChanged.connect(self.search_rows)
        self.search_layout.addWidget(self.search_edit)
        layout.addLayout(self.search_layout)
        layout.addSpacing(10)
        
        
        self.row_height = 35

        self.stocktable = MyTable(column_ratios=[0.05, 0.20, 0.15, 0.20, 0.10, 0.10, 0.10, 0.10])
        headers = ['Id', 'Product', 'Brand', 'Formula', 'Packs', 'Units', 'Total Cost', 'Save']
        self.stocktable.setColumnCount(len(headers))
        self.stocktable.setHorizontalHeaderLabels(headers)

        self.stocktable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stocktable.verticalHeader().setDefaultSectionSize(self.row_height)
        self.stocktable.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        detail_col = headers.index("Save")
        self.stocktable.horizontalHeaderItem(detail_col).setTextAlignment(Qt.AlignCenter)

        self.stocktable.setStyleSheet("QTableWidget::item { color: #333; }")

        self.stocktable.verticalHeader().setFixedWidth(0)
        header = self.stocktable.horizontalHeader()
        header.setStretchLastSection(True)   

        self.stocktable.setMinimumWidth(1000)
        
        # Hide vertical header (row numbers)
        self.stocktable.verticalHeader().setVisible(False)
        
        # Alternating row colors
        self.stocktable.setAlternatingRowColors(True)

        # Selection behaviour
        self.stocktable.setSelectionBehavior(QTableWidget.SelectRows)
        self.stocktable.setSelectionMode(QTableWidget.SingleSelection)


        layout.addWidget(self.stocktable)
        self.setLayout(layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                font-family: Arial;
                font-size: 12pt;
            }

            QTableWidget {
                background-color: white;
                alternate-background-color: #f0f0f0;
                gridline-color: #d0d0d0;
                selection-background-color: #3399ff;
                selection-color: white;
                font-size: 11pt;
            }

            QHeaderView::section {
                background-color: #e0e0e0;
                color: #333;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }

            QDialogButtonBox QPushButton {
                background-color: #3399ff;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }

            QDialogButtonBox QPushButton:hover {
                background-color: #267acc;
            }

            QDialogButtonBox QPushButton:pressed {
                background-color: #1e5fa0;
            }
        """)
        
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)   # Save → dialog.accept()
        button_box.rejected.connect(self.reject)   # Cancel → dialog.reject()
        layout.addWidget(button_box)
    
    

    def search_rows(self, text):

        for row in range(self.stocktable.rowCount()):
            match = False
            for col in range(self.stocktable.columnCount() - 1):
                item = self.stocktable.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.stocktable.setRowHidden(row, not match)
