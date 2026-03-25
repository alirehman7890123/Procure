from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHeaderView,QDialog, QLineEdit,QComboBox, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal, QTimer
from PySide6.QtSql import QSqlQuery
from functools import partial
from PySide6.QtGui import QColor


from utilities.stylus import load_stylesheets



class ProductListWidget(QWidget):
    
    detailpagesignal = Signal(int)  

    def __init__(self, parent=None):

        super().__init__(parent)
        
        self.current_page = 1
        self.page_size = 50
        self.current_search_text = ""

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Product Information", objectName="SectionTitle")
        self.addproduct = QPushButton("Add Product", objectName="TopRightButton")
        self.addproduct.setCursor(Qt.PointingHandCursor)
        self.addproduct.setFixedWidth(150)
        
        
        
        header_layout.addWidget(heading, 1)
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
        self.layout.addSpacing(20)
        
        info_layout = QHBoxLayout()
        
        total_products_label = QLabel("Resulted Records: ")
        total_products_label.setFixedWidth(200)
        self.total_products_value = QLabel("0")
        
        # push to the left
        self.total_products_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.total_products_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) 

        
        info_layout.addWidget(total_products_label)
        info_layout.addWidget(self.total_products_value, 1)
        
        
        low_stock = QPushButton("Low Stock", objectName="TopRightButton")
        low_stock.setFixedWidth(150)
        low_stock.clicked.connect(lambda: self.view_low_stock())
        
        info_layout.addWidget(low_stock)
        low_stock.setCursor(Qt.PointingHandCursor)

        

        self.layout.addLayout(info_layout)
        self.layout.addSpacing(20)
        

        # Search Field
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search Product...")
        
        # convert input to uppercase
        self.search_edit.textChanged.connect(lambda text: self.search_edit.setText(text.upper()))

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.search_rows(self.search_edit.text()))
        
        self.search_edit.textChanged.connect(lambda: self.search_timer.start(300))


        search_layout.addWidget(self.search_edit, 6)
        self.layout.addLayout(search_layout)
        
        self.search_category = QComboBox()
        self.search_category.addItems(["Product", "Brand", "All"])
        self.search_category.setFixedWidth(150)
        search_layout.addWidget(self.search_category, 1)
        
        
        self.layout.addSpacing(10)
        
        


        self.row_height = 34

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.12, 0.12])
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
                GROUP BY p.id, p.display_name, p.code, p.generic_name, p.brand
                HAVING COALESCE(SUM(b.quantity_remaining), 0) = 0;
            """)


        # Show the results in a new dialog or table
        self.show_query_results(low_stock_query)
        
        
        
    def view_expired_products(self):
        
        print("view expired products clicked")

        # Implement the logic to view expired products
        expired_query = QSqlQuery()
        expired_query.exec("""
            SELECT * FROM product p
            JOIN stock s ON p.id = s.product
            WHERE s.expiry_date < CURRENT_DATE
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
        total_query.exec("SELECT COUNT(*) FROM product")
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
                GROUP BY p.id
                HAVING COALESCE(SUM(b.quantity_remaining), 0) = 0
            ) t;


        """)
        

            
            


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

        where_clause = ""
        bindings = []

        if category == "Product":
            where_clause = "WHERE p.display_name LIKE ?"
            bindings.append(pattern)

        elif category == "Brand":
            where_clause = "WHERE COALESCE(m.name, '') LIKE ?"
            bindings.append(pattern)

        elif category == "All":
            where_clause = """
                WHERE (
                    p.display_name LIKE ?
                    OR COALESCE(m.name, '') LIKE ?
                )
            """
            bindings.extend([pattern, pattern])

        else:
            where_clause = "WHERE p.display_name LIKE ?"
            bindings.append(pattern)

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
            ORDER BY p.id DESC
            LIMIT ? OFFSET ?
        """
        data_query.prepare(data_sql)

        for value in bindings:
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
            layout.setContentsMargins(6, 2, 6, 2)
            layout.setAlignment(Qt.AlignCenter)

            container = QWidget()

            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
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

        # total count
        count_query = QSqlQuery()
        if not count_query.exec("SELECT COUNT(*) FROM product"):
            print("Count error:", count_query.lastError().text())
            return

        total_records = 0
        if count_query.next():
            total_records = int(count_query.value(0))

        offset = (page - 1) * page_size

        query = QSqlQuery()
        query.prepare("""
            SELECT 
                p.id,
                p.display_name,
                COALESCE(m.name, '') AS manufacturer_name,
                COALESCE(bs.total_stock, 0) AS total_stock
            FROM product p
            LEFT JOIN manufacturer m ON p.manufacturer_id = m.id
            LEFT JOIN (
                SELECT product_id, SUM(quantity_remaining) AS total_stock
                FROM batch
                GROUP BY product_id
            ) bs ON p.id = bs.product_id
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
            layout.setContentsMargins(0, 0, 0, 0)
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



            
            
            
import math
from PySide6.QtWidgets import QDialog, QDialogButtonBox

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
        
        
        self.row_height = 40

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
