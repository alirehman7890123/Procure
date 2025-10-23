from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHeaderView,QDialog, QLineEdit, QSizePolicy, QVBoxLayout, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QFile, Qt, Signal
from PySide6.QtSql import QSqlQuery
from functools import partial

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
        
        
        # Search Field
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search Product...")
        search_edit.textChanged.connect(self.search_rows)
        search_layout.addWidget(search_edit)
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
        
        self.layout.addStretch()


        
        self.setStyleSheet(load_stylesheets())

    
    def showEvent(self, event):
        
        super().showEvent(event)
        print("Widget shown — refreshing data")
        self.load_products_into_table()
        

    def search_rows(self, text):
        
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
    


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
        
        stock_table = dialog.stocktable
        print("Stock table in dialog:", stock_table)
        
        
        
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
                
                stock_table.insertRow(row)
                
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
                
                stock_table.setItem(row, 0, id_item)
                stock_table.setItem(row, 1, name_item)
                stock_table.setItem(row, 2, brand_item)
                stock_table.setItem(row, 3, formula_item)
                
                if stockadjusted == 1 :
                    
                    if packsize > 0:
                    
                        packs = qty // packsize
                        units = qty % packsize
                    
                        packs = QTableWidgetItem(packs)
                        units = QTableWidgetItem(units)
                        stock_table.setItem(row, 4, packs)
                        stock_table.setItem(row, 5, units)
                    
                else:
                    
                    packs_edit = QLineEdit()
                    units_edit = QLineEdit()
                    stock_table.setCellWidget(row, 4, packs_edit)
                    stock_table.setCellWidget(row, 5, units_edit)
                
                
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
                        False
                    ))

                else:
                    # Static (already adjusted) cells
                    packs_item = stock_table.item(row, 4)
                    units_item = stock_table.item(row, 5)
                    packs_text = packs_item.text() if packs_item else ""
                    units_text = units_item.text() if units_item else ""

                    save_button.clicked.connect(partial(
                        self.save_stock_adjustment,
                        product_id,
                        packs_text,
                        units_text,
                        totalcost_edit,
                        True
                    ))




                stock_table.setCellWidget(row, 6, totalcost_edit)
                stock_table.setCellWidget(row, 7, save_button)
                
                row += 1
        
        else:
            
            print("No products found or error in query.")
            print("Error executing product query:", product_query.lastError().text())   


        dialog.exec()  # Show the dialog
        
        


    def save_stock_adjustment(self, product_id, packs_src, units_src, totalcost_src, already_adjusted):
        
        
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
        else:
            print("Error saving stock adjustment:", update_query.lastError().text())



    
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
    
    


