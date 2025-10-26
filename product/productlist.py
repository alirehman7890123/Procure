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


        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Product Information", objectName="SectionTitle")
        self.addproduct = QPushButton("Add Product", objectName="TopRightButton")
        self.addproduct.setCursor(Qt.PointingHandCursor)
        self.addproduct.setFixedWidth(200)
        
        self.addstock = QPushButton("Add Stock", objectName="TopRightButton")
        self.addstock.setCursor(Qt.PointingHandCursor)
        self.addstock.setFixedWidth(200)
        
        self.addstock.clicked.connect(lambda: self.add_stock())
        
        
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.addstock)
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
        
        total_products_label = QLabel("Total Products: ")
        self.total_products_value = QLabel("0") 

        low_products_label = QLabel(" | Low Stock Products: ")
        self.low_products_value = QLabel("0")
        
        expired_products_label = QLabel(" | Expired Products: ")
        self.expired_products_value = QLabel("0")
        
        info_layout.addWidget(total_products_label, 2)
        info_layout.addWidget(self.total_products_value, 2)
        info_layout.addSpacing(30)
        info_layout.addWidget(low_products_label, 2)
        info_layout.addWidget(self.low_products_value, 2)
        info_layout.addSpacing(30)
        info_layout.addWidget(expired_products_label, 2)
        info_layout.addWidget(self.expired_products_value, 2)
        
        low_stock = QPushButton("View Low Stock", objectName="TopRightButton")
        low_stock.clicked.connect(lambda: self.view_low_stock())
        
        info_layout.addWidget(low_stock, 2)
        low_stock.setCursor(Qt.PointingHandCursor)

        expiry_alert = QPushButton("View Expired Products", objectName="TopRightButton")
        expiry_alert.clicked.connect(lambda: self.view_expired_products())
        expiry_alert.setCursor(Qt.PointingHandCursor)
        
        info_layout.addWidget(expiry_alert, 2)
        

        self.layout.addLayout(info_layout)
        self.layout.addSpacing(20)
        

        # Search Field
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search Product...")

        search_by = QLabel("Search By")
        search_by.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.search_in = QComboBox()
        self.search_in.addItems(["Product", "Code", "Formula", "Brand"])
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.search_rows(self.search_edit.text()))
        
        self.search_edit.textChanged.connect(lambda: self.search_timer.start(300))


        search_layout.addWidget(self.search_edit, 6)
        search_layout.addWidget(search_by, 1)
        search_layout.addWidget(self.search_in, 2)
        self.layout.addLayout(search_layout)
        self.layout.addSpacing(10)
        
        


        self.row_height = 40

        self.table = MyTable(column_ratios=[0.05, 0.25, 0.15, 0.12, 0.12, 0.10, 0.08, 0.08, 0.05])
        headers = ['No.', 'Product', 'Code/Barcode', 'Category', 'Manufacturer', 'Stock', 'Level', 'Status', 'Detail']
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

        self.layout.addWidget(self.table)
        
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

        
        self.layout.addStretch()
        self.show_products_info()

        
        self.setStyleSheet(load_stylesheets())
        
        
        
    def view_low_stock(self):
        
        print("view low stock clicked")

        # Implement the logic to view low stock products
        low_stock_query = QSqlQuery()
        low_stock_query.exec("""
            SELECT * FROM product p
            JOIN stock s ON p.id = s.product
            WHERE s.units <= s.reorder
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
        results_table.setHorizontalHeaderLabels(['ID', 'Name', 'Code', 'Category', 'Brand'])  # Adjust headers

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

        # Fetch low stock products
        low_stock_query = QSqlQuery()
        low_stock_query.exec("""
            SELECT COUNT(*) FROM product p
            JOIN stock s ON p.id = s.product
            WHERE s.units <= s.reorder
        """)
        if low_stock_query.next():
            low_stock_products = low_stock_query.value(0)
            self.low_products_value.setText(str(low_stock_products))
        else:
            self.low_products_value.setText("0")

        # Fetch expired products
        expired_query = QSqlQuery()
        expired_query.exec("""
            SELECT COUNT(*) FROM product p
            JOIN stock s ON p.id = s.product
            WHERE s.expiry_date < CURRENT_DATE
        """)
        if expired_query.next():
            expired_products = expired_query.value(0)
            self.expired_products_value.setText(str(expired_products))
        else:
            self.expired_products_value.setText("0")
            
            


    def show_next_page(self):
        
        import math
        from PySide6.QtSql import QSqlQuery, QSqlQueryModel
        from PySide6.QtWidgets import QMessageBox


        # get total rows
        count_q = QSqlQuery()
        if not count_q.exec_("SELECT COUNT(*) FROM product"):
            QMessageBox.critical(None, "Error", f"Count query failed: {count_q.lastError().text()}")
            return
        
        count_q.next()
        total_rows = count_q.value(0) or 0
        total_pages = max(1, math.ceil(int(total_rows) / int(self.page_size)))
        
        print("Total Pages are: ", total_pages)

        # don't advance beyond last page
        if self.current_page >= total_pages:
            self.next_button.setEnabled(False)
            return

        self.current_page += 1
        offset = (self.current_page - 1) * self.page_size

        sql = f"SELECT * FROM product LIMIT {self.page_size} OFFSET {offset}"
        query = QSqlQuery()
        query.prepare(sql)

        if not query.exec():
            QMessageBox.critical(None, "Error", f"Query failed: {query.lastError().text()}")
            return
       
        try:
            # self.table.clearContents()
            # rows = model.rowCount()
            # cols = model.columnCount()
            # self.table.setRowCount(rows)
            # self.table.setColumnCount(cols)
            # # set headers if available
            # headers = [model.headerData(c, 1) for c in range(cols)]
            # self.table.setHorizontalHeaderLabels([str(h) if h is not None else "" for h in headers])
            # for r in range(rows):
            #     for c in range(cols):
            #         value = model.data(model.index(r, c))
            #         item = QTableWidgetItem(str(value) if value is not None else "")
            #         self.table.setItem(r, c, item)
            
            self.table.setRowCount(0)  # Clear existing rows
            row = 0
            
            print("Query Successful Got the rows, populating table now")

            while query.next():

                counter = str(offset + row + 1)
                self.table.insertRow(row)

                product_id = query.value(0)
                name = query.value(1)
                code = query.value(2)
                category = query.value(3)
                brand = query.value(4)
                form = query.value(6)
                strength = query.value(7)
                
                name = f"{name} {form} {strength}"
                
                counter = QTableWidgetItem(counter)
                name = QTableWidgetItem(name)
                code = QTableWidgetItem(code)
                category = QTableWidgetItem(category)
                brand = QTableWidgetItem(brand)

                
                self.table.setItem(row, 0, counter)
                self.table.setItem(row, 1, name)
                self.table.setItem(row, 2, code)
                self.table.setItem(row, 3, category)
                self.table.setItem(row, 4, brand)
                
                product_id = int(product_id)
                
                
                # bring stock and level from stock table
                stock_query = QSqlQuery()
                stock_query.prepare("SELECT packsize, units, reorder from stock where product = ?")
                stock_query.addBindValue(product_id)
                
                if stock_query.exec() and stock_query.next():
                    
                    packsize = stock_query.value(0)
                    units = stock_query.value(1)
                    reorder = stock_query.value(2)
                    
                    # packsize = int(packsize)
                    # units = int(units)
                    # reorder = int(reorder)
                    
                    level = ""
                    
                    
                    if packsize != 0:
                        
                        packs = units // packsize
                        
                        if packs > reorder:
                            level = 'normal'
                        else:
                            level = 'low'
                        
                        
                        rems = units % packsize

                        if packs > 0 and rems > 0:
                            stock = f"{packs} + ({rems})"
                        elif packs > 0:
                            stock = f"{packs}"
                        else:
                            stock = f"    ({rems})"

                    
                    
                    stock = QTableWidgetItem(str(stock))
                    # stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    level = QTableWidgetItem(level)
                    
                    self.table.setItem(row, 5, stock)
                    self.table.setItem(row, 6, level)
                
                    
                
                
                # inserting product status from batch table
                
                batch_query = QSqlQuery()
                batch_query.prepare("SELECT status, resolved FROM batch WHERE product = :product_id")
                batch_query.bindValue(":product_id", product_id)
                
                status = "Valid"
                
                if batch_query.exec():
                    
                    while batch_query.next():

                        batch_status = batch_query.value(0)
                        resolved = batch_query.value(1)
                        
                        if resolved:
                            continue
                        
                        if batch_status == 'near-expiry' or batch_status == 'expired':
                            status = 'Near / Expired'
                        
                        
                else:
                    
                    print("Error executing batch query:", batch_query.lastError().text())
                
                
                status = QTableWidgetItem(status)
                self.table.setItem(row, 7, status)
                
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
                
                
                self.table.setCellWidget(row, 8, detail)
                detail.clicked.connect(partial(self.detailpagesignal.emit, product_id))
                
                row += 1
            
                    
        except Exception:
            # if fallback fails, at least inform user
            QMessageBox.information(None, "Info", "Unable to populate table widget with model; check table type.")

        # update buttons enabled state
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < total_pages)

        
    
    def show_previous_page(self):
        
        import math
        from PySide6.QtSql import QSqlQuery, QSqlQueryModel
        from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

        if not hasattr(self, "page_size"):
            self.page_size = 50
        if not hasattr(self, "current_page"):
            self.current_page = 1

        # Get total row count
        count_q = QSqlQuery()
        if not count_q.exec_("SELECT COUNT(*) FROM product"):
            QMessageBox.critical(None, "Error", f"Count query failed: {count_q.lastError().text()}")
            return
        count_q.next()
        total_rows = count_q.value(0) or 0
        total_pages = max(1, math.ceil(int(total_rows) / int(self.page_size)))

        # Don't go below page 1
        if self.current_page <= 1:
            self.prev_button.setEnabled(False)
            return

        self.current_page -= 1
        offset = (self.current_page - 1) * self.page_size

        # Query for that page
        sql = f"SELECT * FROM product LIMIT {self.page_size} OFFSET {offset}"
        query = QSqlQuery()
        query.prepare(sql)
        
        if not query.exec():
            QMessageBox.critical(None, "Error", f"Query failed: {query.lastError().text()}")
            return


        try:
            # self.table.clearContents()
            # rows = model.rowCount()
            # cols = model.columnCount()
            # self.table.setRowCount(rows)
            # self.table.setColumnCount(cols)
            # # set headers if available
            # headers = [model.headerData(c, 1) for c in range(cols)]
            # self.table.setHorizontalHeaderLabels([str(h) if h is not None else "" for h in headers])
            # for r in range(rows):
            #     for c in range(cols):
            #         value = model.data(model.index(r, c))
            #         item = QTableWidgetItem(str(value) if value is not None else "")
            #         self.table.setItem(r, c, item)
            
            self.table.setRowCount(0)  # Clear existing rows
            row = 0

            while query.next():

                counter = counter = str(offset + row + 1)
                self.table.insertRow(row)

                product_id = query.value(0)
                name = query.value(1)
                code = query.value(2)
                category = query.value(3)
                brand = query.value(4)
                form = query.value(6)
                strength = query.value(7)
                
                name = f"{name} {form} {strength}"
                
                counter = QTableWidgetItem(counter)
                name = QTableWidgetItem(name)
                code = QTableWidgetItem(code)
                category = QTableWidgetItem(category)
                brand = QTableWidgetItem(brand)

                
                self.table.setItem(row, 0, counter)
                self.table.setItem(row, 1, name)
                self.table.setItem(row, 2, code)
                self.table.setItem(row, 3, category)
                self.table.setItem(row, 4, brand)
                
                product_id = int(product_id)
                
                
                # bring stock and level from stock table
                stock_query = QSqlQuery()
                stock_query.prepare("SELECT packsize, units, reorder from stock where product = ?")
                stock_query.addBindValue(product_id)
                
                if stock_query.exec() and stock_query.next():
                    
                    packsize = stock_query.value(0)
                    units = stock_query.value(1)
                    reorder = stock_query.value(2)
                    
                    # packsize = int(packsize)
                    # units = int(units)
                    # reorder = int(reorder)
                    
                    level = ""
                    
                    
                    if packsize != 0:
                        
                        packs = units // packsize
                        
                        if packs > reorder:
                            level = 'normal'
                        else:
                            level = 'low'
                        
                        
                        rems = units % packsize

                        if packs > 0 and rems > 0:
                            stock = f"{packs} + ({rems})"
                        elif packs > 0:
                            stock = f"{packs}"
                        else:
                            stock = f"    ({rems})"

                    
                    level = QTableWidgetItem(level)
                    if level == 'low':
                        level.setForeground(QColor("red"))
                    
                    
                    
                    
                    stock = QTableWidgetItem(str(stock))
                    
                    self.table.setItem(row, 5, stock)
                    self.table.setItem(row, 6, level)
                
                    
                
                
                # inserting product status from batch table
                
                batch_query = QSqlQuery()
                batch_query.prepare("SELECT status, resolved FROM batch WHERE product = :product_id")
                batch_query.bindValue(":product_id", product_id)
                
                status = "Valid"
                
                if batch_query.exec():
                    
                    while batch_query.next():

                        batch_status = batch_query.value(0)
                        resolved = batch_query.value(1)
                        
                        if resolved:
                            continue
                        
                        if batch_status == 'near-expiry' or batch_status == 'expired':
                            status = 'Near / Expired'
                        
                        
                else:
                    
                    print("Error executing batch query:", batch_query.lastError().text())
                
                
                status = QTableWidgetItem(status)
                self.table.setItem(row, 7, status)
                
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
                
                
                self.table.setCellWidget(row, 8, detail)
                detail.clicked.connect(partial(self.detailpagesignal.emit, product_id))
                
                row += 1
            
                    
        except Exception:
            # if fallback fails, at least inform user
            QMessageBox.information(None, "Info previous", "Unable to populate table widget with model; check table type.")

        # update buttons enabled state
        
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < total_pages)



        
    
    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_products_into_table()
        

    def search_rows(self, text):
        
        # search text from db

        if text.strip() == '':
            return

        field = self.search_in.currentText().lower()
        
        column_map = {
            "product": "name",
            "code": "code",
            "brand": "brand",
            "formula": "formula"
        }

        column = column_map.get(field, "name")  # default to name


        pattern = f"%{text}%"
        
        search_query = QSqlQuery()
        search_query.prepare(f"SELECT * FROM product WHERE {column} LIKE ? LIMIT 50")
        search_query.addBindValue(pattern)
        
                
        if search_query.exec():
            
            print("Searching for ", text, " and query is successful")
            
            
            self.table.setRowCount(0)  # Clear existing rows
            row = 0
            
            while search_query.next():
                
                print("returned records")
                
                counter = row + 1
                counter = str(counter)
                self.table.insertRow(row)
                
                product_id = search_query.value(0)
                name = search_query.value(1)
                code = search_query.value(2)
                category = search_query.value(3)
                brand = search_query.value(4)
                form = search_query.value(6)
                strength = search_query.value(7)
                
                name = f"{name} {form} {strength}"
                
                counter = QTableWidgetItem(counter)
                name = QTableWidgetItem(name)
                code = QTableWidgetItem(code)
                category = QTableWidgetItem(category)
                brand = QTableWidgetItem(brand)

                
                self.table.setItem(row, 0, counter)
                self.table.setItem(row, 1, name)
                self.table.setItem(row, 2, code)
                self.table.setItem(row, 3, category)
                self.table.setItem(row, 4, brand)
                
                product_id = int(product_id)
                
                
                # bring stock and level from stock table
                stock_query = QSqlQuery()
                stock_query.prepare("SELECT packsize, units, reorder from stock where product = ?")
                stock_query.addBindValue(product_id)
                
                if stock_query.exec() and stock_query.next():
                    
                    packsize = stock_query.value(0)
                    units = stock_query.value(1)
                    reorder = stock_query.value(2)
                    
                    # packsize = int(packsize)
                    # units = int(units)
                    # reorder = int(reorder)
                    
                    level = ""
                    
                    
                    if packsize != 0:
                        
                        packs = units // packsize
                        
                        if packs > reorder:
                            level = 'normal'
                        else:
                            level = 'low'
                        
                        
                        rems = units % packsize

                        if packs > 0 and rems > 0:
                            stock = f"{packs} + ({rems})"
                        elif packs > 0:
                            stock = f"{packs}"
                        else:
                            stock = f"    ({rems})"

                    
                    
                    stock = QTableWidgetItem(str(stock))
                    # stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    level = QTableWidgetItem(level)
                    
                    self.table.setItem(row, 5, stock)
                    self.table.setItem(row, 6, level)
                
                    
                
                
                # inserting product status from batch table
                
                batch_query = QSqlQuery()
                batch_query.prepare("SELECT status, resolved FROM batch WHERE product = :product_id")
                batch_query.bindValue(":product_id", product_id)
                
                status = "Valid"
                
                if batch_query.exec():
                    
                    while batch_query.next():

                        batch_status = batch_query.value(0)
                        resolved = batch_query.value(1)
                        
                        if resolved:
                            continue
                        
                        if batch_status == 'near-expiry' or batch_status == 'expired':
                            status = 'Near / Expired'
                        
                        
                else:
                    
                    print("Error executing batch query:", batch_query.lastError().text())
                
                
                status = QTableWidgetItem(status)
                self.table.setItem(row, 7, status)
                
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
                
                
                self.table.setCellWidget(row, 8, detail)
                detail.clicked.connect(partial(self.detailpagesignal.emit, product_id))
                
                row += 1
            
        
                
                
                
                
        
        
        
        
        
        
        # for row in range(self.table.rowCount()):
        #     match = False
        #     for col in range(self.table.columnCount() - 1):
        #         item = self.table.item(row, col)
        #         if item and text.lower() in item.text().lower():
        #             match = True
        #             break
        #     self.table.setRowHidden(row, not match)
    


    def load_products_into_table(self):
        

        query = QSqlQuery()
        query.exec("SELECT id, name, code, category, brand FROM product LIMIT 50")

        self.table.setRowCount(0)  # Clear existing rows

        row = 0
        
        while query.next():
            
            counter = row + 1
            counter = str(counter)
            self.table.insertRow(row)
            
            product_id = query.value(0)
            name = query.value(1)
            code = query.value(2)
            category = query.value(3)
            brand = query.value(4)
            
            
            counter = QTableWidgetItem(counter)
            name = QTableWidgetItem(name)
            code = QTableWidgetItem(code)
            category = QTableWidgetItem(category)
            brand = QTableWidgetItem(brand)

            
            self.table.setItem(row, 0, counter)
            self.table.setItem(row, 1, name)
            self.table.setItem(row, 2, code)
            self.table.setItem(row, 3, category)
            self.table.setItem(row, 4, brand)
            
            product_id = int(product_id)
            
            
            # bring stock and level from stock table
            stock_query = QSqlQuery()
            stock_query.prepare("SELECT packsize, units, reorder from stock where product = ?")
            stock_query.addBindValue(product_id)
            
            if stock_query.exec() and stock_query.next():
                
                packsize = stock_query.value(0)
                units = stock_query.value(1)
                reorder = stock_query.value(2)
                
                # packsize = int(packsize)
                # units = int(units)
                # reorder = int(reorder)
                
                level = ""
                
                
                if packsize != 0:
                    
                    packs = units // packsize
                    
                    if packs > reorder:
                        level = 'normal'
                    else:
                        level = 'low'
                    
                    
                    rems = units % packsize

                    if packs > 0 and rems > 0:
                        stock = f"{packs} + ({rems})"
                    elif packs > 0:
                        stock = f"{packs}"
                    else:
                        stock = f"    ({rems})"

                
                
                stock = QTableWidgetItem(str(stock))
                # stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                level = QTableWidgetItem(level)
                
                self.table.setItem(row, 5, stock)
                self.table.setItem(row, 6, level)
            
                
            
            
            # inserting product status from batch table
            
            batch_query = QSqlQuery()
            batch_query.prepare("SELECT status, resolved FROM batch WHERE product = :product_id")
            batch_query.bindValue(":product_id", product_id)
            
            status = "Valid"
            
            if batch_query.exec():
                
                while batch_query.next():

                    batch_status = batch_query.value(0)
                    resolved = batch_query.value(1)
                    
                    if resolved:
                        continue
                    
                    if batch_status == 'near-expiry' or batch_status == 'expired':
                        status = 'Near / Expired'
                    
                    
            else:
                
                print("Error executing batch query:", batch_query.lastError().text())
            
            
            status = QTableWidgetItem(status)
            self.table.setItem(row, 7, status)
            
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
            
            
            self.table.setCellWidget(row, 8, detail)
            detail.clicked.connect(partial(self.detailpagesignal.emit, product_id))
            
            row += 1
        
        
        
        

    
    
    def add_stock(self):
        
        print("Add stock clicked")
        # Implement add stock functionality here
        
        dialog = ImportDialog()
        
        self.stock_table = dialog.stocktable
        print("Stock table in dialog:", self.stock_table)

        # get product list and populate table
        product_query = QSqlQuery()
        product_query.exec("""
                           SELECT 
                                p.id,
                                p.name,
                                p.code,
                                p.brand,
                                p.formula,
                                p.form,
                                p.strength,
                                s.stock_adjusted,
                                s.cost_adjusted,
                                s.qty,
                                s.totalcost
                            FROM stockcost AS s
                            JOIN product AS p ON s.product = p.id
                            WHERE (s.stock_adjusted = 0 OR s.cost_adjusted = 0)
                            AND s.stocktype = 'onhand';
                            
                            """
                        )
        
        if product_query.exec():
            
            print("Product query executed successfully")
            row = 0
            
            while product_query.next():
                
                self.stock_table.insertRow(row)
                
                product_id = product_query.value(0)
                
                # Fetch packsize, current units from stock table
                stock_query = QSqlQuery()
                stock_query.prepare("SELECT packsize, units FROM stock WHERE product = :product_id")
                stock_query.bindValue(":product_id", product_id)

                if stock_query.exec() and stock_query.next():
                    packsize = stock_query.value(0) or 0
                    stockunits = stock_query.value(1) or 0
                else:
                    print("Error retrieving stock information:", stock_query.lastError().text())
                
                
                
                name = product_query.value(1)
                code = product_query.value(2)
                brand = product_query.value(3)
                formula = product_query.value(4)
                form = product_query.value(5)
                strength = product_query.value(6)
                stockadjusted = product_query.value(7)
                costaddjusted = product_query.value(8)
                qty = product_query.value(9)
                totalcost = product_query.value(10)
                
                name = f"{name} {strength} {form}"
                
                id_item = QTableWidgetItem(str(product_id))
                name_item = QTableWidgetItem(name)
                brand_item = QTableWidgetItem(brand)
                formula_item = QTableWidgetItem(formula)
                
                self.stock_table.setItem(row, 0, id_item)
                self.stock_table.setItem(row, 1, name_item)
                self.stock_table.setItem(row, 2, brand_item)
                self.stock_table.setItem(row, 3, formula_item)
                
                if stockadjusted == 1 :
                    
                    if packsize > 0:
                    
                        packs = qty // packsize
                        units = qty % packsize
                    
                        packs = QTableWidgetItem(packs)
                        units = QTableWidgetItem(units)
                        packs.setFlags(packs.flags() & ~Qt.ItemIsEditable)
                        units.setFlags(units.flags() & ~Qt.ItemIsEditable)
                        self.stock_table.setItem(row, 4, packs)
                        self.stock_table.setItem(row, 5, units)
                    
                else:
                    
                    packs_edit = QLineEdit()
                    units_edit = QLineEdit()
                    self.stock_table.setCellWidget(row, 4, packs_edit)
                    self.stock_table.setCellWidget(row, 5, units_edit)
                
                
                totalcost_edit = QLineEdit()
                save_button =QPushButton("Save")
                save_button.setCursor(Qt.PointingHandCursor)
                
                save_button.setStyleSheet("""
                                          
                    QLineEdit {
                        background-color: #f5f5f5;
                        color: #333;
                    }                      
                    QPushButton {
                        background-color: #340238;
                        color: #fff;
                        padding: 6px 14px;  
                    }
                    QPushButton:pressed {
                        background-color: #47034E;
                        color: #fff;
                    }
                """)
                
                
                if stockadjusted == 0:
                    # Editable cells
                    save_button.clicked.connect(partial(
                        self.save_stock_adjustment,
                        product_id,
                        packs_edit,
                        units_edit,
                        totalcost_edit,
                        False,
                        self.stock_table
                    ))

                else:
                    # Static (already adjusted) cells
                    packs_item = self.stock_table.item(row, 4)
                    units_item = self.stock_table.item(row, 5)
                    
                    packs_text = packs_item.text() if packs_item else ""
                    units_text = units_item.text() if units_item else ""

                    save_button.clicked.connect(partial(
                        self.save_stock_adjustment,
                        product_id,
                        packs_text,
                        units_text,
                        totalcost_edit,
                        True,
                        self.stock_table
                    ))




                self.stock_table.setCellWidget(row, 6, totalcost_edit)
                self.stock_table.setCellWidget(row, 7, save_button)
                
                row += 1
        
        else:
            
            print("No products found or error in query.")
            print("Error executing product query:", product_query.lastError().text())   


        dialog.exec()  # Show the dialog
        
        


    def save_stock_adjustment(self, product_id, packs_src, units_src, totalcost_src, already_adjusted, table):
        

        # Fetch packsize, current units from stock table
        stock_query = QSqlQuery()
        stock_query.prepare("SELECT packsize, units FROM stock WHERE product = :product_id")
        stock_query.bindValue(":product_id", product_id)

        if stock_query.exec() and stock_query.next():
            packsize = stock_query.value(0) or 0
            stockunits = stock_query.value(1) or 0
        else:
            print("Error retrieving stock information:", stock_query.lastError().text())
            return

        # Parse inputs safely
        
        
        if already_adjusted:
            # Text values passed directly
            packs_text = packs_src
            units_text = units_src
            # maybe skip or just re-update
        else:
            # Widgets passed, read their text
            packs_text = packs_src.text()
            units_text = units_src.text()
            
        
        cost_text = totalcost_src.text()

        update_fields = []
        update_values = {}

        # --- Stock adjustment ---
        if packs_text != '' or units_text != '':
            
            packs_text = int(packs_text) if packs_text != '' else 0
            units_text = int(units_text) if units_text != '' else 0
            
            entered_units = packs_text * packsize + units_text
            total_units = stockunits + units_text + (packs_text * packsize)


            # update stock
            new_stock = QSqlQuery()
            new_stock.prepare("UPDATE stock SET units = :units WHERE product = :product_id")
            new_stock.bindValue(":units", total_units)
            new_stock.bindValue(":product_id", product_id)

            if new_stock.exec():
                print("Stock updated successfully.")
            else:
                print("Error updating stock:", new_stock.lastError().text())
                
                

            update_fields.append("qty = :units")
            update_fields.append("stock_adjusted = 1")
            update_values[":units"] = entered_units
            print(f"StockCost Stock updated → Product ID {product_id}: Units={total_units}")
        

        # --- Cost adjustment ---
        if cost_text != "":  # only skip if field is blank
            
            totalcost = float(cost_text)
            update_fields.append("totalcost = :totalcost")
            update_fields.append("cost_adjusted = 1")
            update_values[":totalcost"] = totalcost
            print(f"StockCost Cost updated → Product ID {product_id}: TotalCost={totalcost}")

        # Nothing to update?
        if not update_fields:
            print(f"No valid input for Product ID {product_id}. Nothing updated.")
            return

        # Build dynamic SQL
        sql = f"""
            UPDATE stockcost
            SET {', '.join(update_fields)}
            WHERE product = :product_id AND stocktype = 'onhand'
        """

        update_query = QSqlQuery()
        update_query.prepare(sql)
        for key, value in update_values.items():
            update_query.bindValue(key, value)
        update_query.bindValue(":product_id", product_id)

        # Execute
        if update_query.exec():
            print(f"Stock adjustment saved successfully for Product ID {product_id}.")
            
            # Hide the row after saving
            row = table.currentRow()
            table.setRowHidden(row, True)
            
            
            # index = self.table.indexAt(event.pos())
            # if index.isValid():
            #     row = index.row()
            #     self.table.setRowHidden(row, True)
            
            # self.stock_table.cellClicked.connect(lambda: self.hide_row_on_click(row=self.stock_table.currentRow()))

        else:
            print("Error saving stock adjustment:", update_query.lastError().text())
            
            
    
    def hide_row_on_click(self, row):

        print("Stock table in dialog: for hidden row", self.stock_table)
        self.stock_table.setRowHidden(row, True)






    
    # def save_stock_adjustment(self, product_id, packs_edit, units_edit, totalcost_edit):
        
        
    #     # get packsize, units, from stock table for the product
        
    #     stock_query = QSqlQuery()
    #     stock_query.prepare("SELECT packsize, units FROM stock WHERE product = :product_id")
    #     stock_query.bindValue(":product_id", product_id)

    #     if stock_query.exec() and stock_query.next():
    #         packsize = stock_query.value(0)
    #         stockunits = stock_query.value(1)
    #     else:
    #         print("Error retrieving stock information:", stock_query.lastError().text())
    #         return
        
        
    #     try:
            
    #         entered_units = int(units_edit.text() or 0)
    #         entered_packs = int(packs_edit.text() or 0)
    #         totalcost = float(totalcost_edit.text() or 0)

    #         if packsize > 0:
    #             total_units = entered_units + entered_packs * packsize + stockunits
    #         else:
    #             total_units = entered_units + entered_packs + stockunits

                
    #         # update stock 
    #         new_stock = QSqlQuery()
    #         new_stock.prepare("UPDATE stock SET units = :units WHERE product = :product_id")
    #         new_stock.bindValue(":units", total_units)
    #         new_stock.bindValue(":product_id", product_id)

    #         if new_stock.exec():
    #             print("Stock updated successfully.")
    #         else:
    #             print("Error updating stock:", new_stock.lastError().text())
                
                

    #     except ValueError:
    #         print("Invalid input. Please enter numeric values for packs, units, and total cost.")
    #         return
        
        
    #     # Update the stockcost table
    #     update_query = QSqlQuery()
    #     update_query.prepare("""
    #         UPDATE stockcost
    #         SET qty = :units,
    #             totalcost = :totalcost,
    #             stock_adjusted = 1,
    #             cost_adjusted = 1
    #         WHERE product = :product_id AND stocktype = 'onhand'
    #     """)
    #     update_query.bindValue(":units", total_units)
    #     update_query.bindValue(":totalcost", totalcost)
    #     update_query.bindValue(":product_id", product_id)
        
    #     if update_query.exec():
    #         print("Stock adjustment saved successfully.")
    #     else:
    #         print("Error saving stock adjustment:", update_query.lastError().text())
        
        




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
