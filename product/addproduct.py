from PySide6.QtWidgets import QWidget, QVBoxLayout, QDialog, QPushButton,QComboBox, QDialogButtonBox, QTableWidgetItem, QCompleter,QTableWidget, QFileDialog, QMessageBox, QGridLayout, QLineEdit, QFrame, QDateEdit, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import QSize, Qt, QFile, QDate, QEvent, QStringListModel
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from datetime import datetime
import sys
import pandas as pd  # <-- for reading CSV/Excel easily

from utilities.stylus import load_stylesheets



class AddProductWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)
        

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        
        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Product Information", objectName="SectionTitle")
        
        self.productlist = QPushButton("Products List", objectName="TopRightButton")
        self.productlist.setCursor(Qt.PointingHandCursor)
        self.productlist.setFixedWidth(200)

        self.import_file_button = QPushButton("Import File", objectName="TopRightButton")
        self.import_file_button.setCursor(Qt.PointingHandCursor)
        self.import_file_button.setFixedWidth(200)

        self.import_file_button.clicked.connect(self.import_file)
    

        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.productlist)
        header_layout.addWidget(self.import_file_button)

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
        
        self.indicators = {}
        
        
        self.insert_subheading("PRODUCT INFORMATION")
        self.populate_product_fields()
        
        self.populate_medicine_fields()
        
        self.insert_subheading("STOCK INFORMATION")
        self.populate_stock_and_batch_fields()
        
        
        
        

        # === Add Button ===
        save_button = QPushButton("Save Product", objectName="SaveButton")
        save_button.setCursor(Qt.PointingHandCursor)

        self.layout.addWidget(save_button)
        self.layout.addStretch()
        
        self.category_input.currentTextChanged.connect(self.on_category_changed)
        
        
        self.completer = QCompleter()
        self.completer.setCompletionMode(QCompleter.PopupCompletion)

        self.name_input.lineEdit().setCompleter(self.completer)

        self.name_input.lineEdit().completer().popup().setStyleSheet("""QVBoxLayout,
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


        self.name_input.lineEdit().textEdited.connect(self.load_product_suggestions)
        self.completer.activated.connect(self.on_item_selected)
        
        
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)
        
        
        self.setStyleSheet(load_stylesheets())

        
        save_button.clicked.connect(lambda: self.save_product(self.name_input, 
                                                            self.code_input, 
                                                            self.category_input, 
                                                            self.brand_input,
                                                            self.formula_input,
                                                            self.form_input,
                                                            self.strength_input,
                                                            
                                                            self.pack_size_input, 
                                                            self.packs_input,
                                                            self.units_input, 
                                                            self.reorder_input, 
                                                            
                                                            self.total_cost_input, 
                                                            self.sale_price_input,
                                                            self.batch_input, 
                                                            self.expiry_input ))



    
    
    def import_file(self):
        
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Product File",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )

        if not file_name:
            return  # User cancelled

        try:
            if file_name.endswith(".csv"):
                df = pd.read_csv(file_name)
            else:
                df = pd.read_excel(file_name)

            # Show popup with contents
            df = df.fillna("")
            dialog = ImportDialog(df, self)
            dialog.exec()

        except Exception as e:
            print("Error reading file:", e)
    
    
    
    def populate_product_fields(self):
        
        labels = ["Product Name", "Code/Barcode", "Category", "Brand"]
        
        self.name_input = QComboBox()
        self.name_input.setEditable(True)
        self.code_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.addItems(["Medicine", "General Item", "Other"])
        self.brand_input = QLineEdit()
        
        fields = [self.name_input, self.code_input, self.category_input, self.brand_input]
        
        self.insert_labels_and_fields(labels, fields)
        
        
    def populate_medicine_fields(self):
        
        # === Sub Header Row ===
        self.medicine_layout = QHBoxLayout()
        self.medicine_subheading = QLabel("MEDICINE & BATCH  INFORMATION", objectName="SubHeading")
        
        self.medicine_layout.addWidget(self.medicine_subheading)
        self.layout.addLayout(self.medicine_layout)
        
        self.layout.addSpacing(10)
        
        self.medicine_subheading.hide()
        
        self.formula_input = QLineEdit()
        self.form_input = QLineEdit()
        self.strength_input = QLineEdit()
        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.batch_input = QLineEdit()
        self.expiry_input.setDate(QDate.currentDate())

        self.medicine_fields = [
            ("Formula:", self.formula_input),
            ("Form (Tablet/Syrup):", self.form_input),
            ("Strength:", self.strength_input),
            ("Batch No:", self.batch_input),
            ("Expiry Date:", self.expiry_input)
            
        ]
        
        
        
        # Keep track of full row containers for show/hide
        self.medicine_rows = []

        for label, field in self.medicine_fields:
            # --- row container ---
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            # indicator
            indicator = QFrame()
            indicator.setFixedWidth(4)
            indicator.setStyleSheet("background-color: #ccc; border: none;")

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            lbl.setFixedWidth(250)
            field.setStyleSheet("margin-left: 18px;")

            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            row_layout.addWidget(indicator)
            row_layout.addWidget(lbl, 1)
            row_layout.addWidget(field, 8)

            # Add whole row widget into main layout
            self.layout.addWidget(row_widget)
            self.layout.setSpacing(15)

            # Map indicator for highlighting
            self.indicators[field] = indicator
            field.installEventFilter(self)

            # Initially hide medicine rows
            self.medicine_rows.append(row_widget)
            
        
        self.layout.addSpacing(20)
            
    
    def populate_stock_and_batch_fields(self):
        
        # Labels + Fields
        labels = ["Pack Size", "Packs", "Cost Price", "Units", "Reorder Level", "Sale Price per Pack"]
        
        self.pack_size_input = QLineEdit()
        self.total_cost_input = QLineEdit()
        self.packs_input = QLineEdit()
        self.units_input = QLineEdit()
        self.reorder_input = QLineEdit()
        self.sale_price_input = QLineEdit()
        
        fields = [
            self.pack_size_input,  self.packs_input, self.total_cost_input, self.units_input,
            self.reorder_input, self.sale_price_input
        ]
        
        self.insert_labels_and_fields(labels, fields)
        
            
            
    def insert_labels_and_fields(self, labels, fields):
        
        
        for (label, field) in zip(labels, fields):

            row = QHBoxLayout()
            
            # Left line indicator
            indicator = QFrame()
            indicator.setFixedWidth(4)
            indicator.setStyleSheet("background-color: #ccc; border: none;")
            
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setMinimumWidth(250)
            lbl.setStyleSheet("padding-left: 10px;")

            row.addWidget(indicator) 
            row.addWidget(lbl, 1)
            row.addWidget(field, 8)

            self.layout.addLayout(row)
            self.layout.setSpacing(15)  # reduce space between rows
            
            # Keep mapping
            self.indicators[field] = indicator

            # Install event filters to track focus
            field.installEventFilter(self)
            
        self.layout.addSpacing(20)
        
        
    def insert_subheading(self, title):
        
        # === Sub Header Row ===
        subheader_layout = QHBoxLayout()
        subheading = QLabel(title, objectName="SubHeading")
        
        subheader_layout.addWidget(subheading)
        self.layout.addLayout(subheader_layout)
        
        self.layout.addSpacing(10)
        
        

    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.indicators[obj].setStyleSheet("background-color: #47034E; border: none;")  # active blue
        elif event.type() == QEvent.FocusOut:
            self.indicators[obj].setStyleSheet("background-color: #ccc; border: none;")  # reset gray
        return super().eventFilter(obj, event)
    
    


    def on_category_changed(self, category):
        if category == "Medicine":
            self.medicine_subheading.show()
            for row in self.medicine_rows:
                row.show()
        else:
            self.medicine_subheading.hide()
            for row in self.medicine_rows:
                row.hide()

    
    

    def on_item_selected(self, text):
        
        text = self.name_input.currentText()
        data = self.name_input.currentData()
        
        print("Selected text is: ",text, data)
        data = int(data)
        
        query = QSqlQuery()
        query.prepare("""
            SELECT * FROM product
            WHERE id = ? """)
        
        query.addBindValue(data)
        
        if not query.exec():
            
            print("Cannot Get the product")
            
        else:
            
            if query.next():
                
                code = query.value(1)
                formula = query.value(3)
                maker = query.value(4)
                form = query.value(5)
                dose = query.value(6)        
                
                self.code_input.setText(str(code))
                self.formula_input.setText(str(formula))
                self.brand_input.setText(str(maker))
                self.form_input.setText(str(form))
                self.strength_input.setText(str(dose))
                
        print("Fields are being populated...")



    
    
    def save_product( self, product, code, category, brand, formula, form, strength,
                                packsize, pack, unit, reorder, cost, sale, batch, expiry):
        
        
        print("Going to save the product")
        # --- Get form values ---
        product = product.currentText()
        code = code.text()
        if code == '':
            code = None
            
        category = category.currentText()
        brand = brand.text()
        formula = formula.text()
        form = form.text()
        strength = strength.text()
        

        packsize = packsize.text().strip()
        packs = pack.text().strip()
        units = unit.text().strip()
        
        packsize = packsize if packsize != '' else '0'
        packs = packs if packs != '' else '0'
        units = units if units != '' else '0'

        # Convert units = (packs * packsize) + units
        total_units = int(packs) * int(packsize) + int(units)
        reorder = reorder.text()
        cost = cost.text()
        sale = sale.text()
        
        reorder = reorder if reorder != '' else '0'
        cost = cost if cost != '' else '0.0'
        sale = sale if sale != '' else '0.0'

        batch = batch.text()
        expiry = expiry.date().toPython().isoformat()

        db = QSqlDatabase.database()
        print("Startign transaction")
        if not db.transaction():
            QMessageBox.information(None, "Error", "Failed to start transaction")
            return

        # --- Insert into product ---
        product_query = QSqlQuery()
        product_query.prepare("""
            INSERT INTO product (name, code, category, brand, formula, form, strength)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        product_query.addBindValue(product)
        product_query.addBindValue(code)
        product_query.addBindValue(category)
        product_query.addBindValue(brand)
        product_query.addBindValue(formula)
        product_query.addBindValue(form)
        product_query.addBindValue(strength)

        if not product_query.exec():
            db.rollback()
            QMessageBox.information(None, "Failed", product_query.lastError().text())
            return

        print("Proudct is stored")
        product_id = product_query.lastInsertId()

        print("Product storing id is: ", product_id)
        
        # --- Insert into stock ---
        stock_query = QSqlQuery()
        stock_query.prepare("""
            INSERT INTO stock (product, packsize, units, reorder, saleprice)
            VALUES (?, ?, ?, ?, ?)
        """)
        stock_query.addBindValue(product_id)
        stock_query.addBindValue(packsize)
        stock_query.addBindValue(total_units)
        stock_query.addBindValue(reorder)
        stock_query.addBindValue(sale)

        if not stock_query.exec():
            db.rollback()
            QMessageBox.information(None, "Failed", stock_query.lastError().text())
            return


        print("Stock is stored...")

        # --- Insert into batch (if given) ---
        if batch != '':
            batch_query = QSqlQuery()
            batch_query.prepare("""
                INSERT INTO batch (product, batch, expiry, status)
                VALUES (?, ?, ?, ?)
            """)
            
            
            today = QDate.currentDate()
            
            if isinstance(expiry, QDate):

                expiry = expiry.toString("yyyy-MM-dd")

                # Calculate difference in days
                days_diff = today.daysTo(expiry)

                if days_diff < 0:
                    status = "expired"
                elif days_diff <= 60:  # within 2 months
                    status = "near expiry"
                else:
                    status = "valid"
                    
            else:
                expiry = str(expiry) if expiry is not None else ""
                status = "Unknown"

            batch_query.addBindValue(product_id)
            batch_query.addBindValue(batch)
            batch_query.addBindValue(expiry)
            batch_query.addBindValue(status)

            if not batch_query.exec():
                db.rollback()
                QMessageBox.information(None, "Failed", batch_query.lastError().text())
                return
            
            print("Batch is stored...")

        # --- Insert into stockcost ---
        stockcost_query = QSqlQuery()
        stockcost_query.prepare("""
            INSERT INTO stockcost (product, qty, totalcost, stocktype)
            VALUES (?, ?, ?, ?)
        """)
        
        units = int(packsize) * int(packs)
        units = str(units)
        stockcost_query.addBindValue(product_id)
        stockcost_query.addBindValue(units)   
        stockcost_query.addBindValue(cost)
        stockcost_query.addBindValue('onhand')

        if not stockcost_query.exec():
            db.rollback()
            QMessageBox.information(None, "Failed", stockcost_query.lastError().text())
            return

        # --- Commit if all successful ---
        if not db.commit():
            db.rollback()
            QMessageBox.information(None, "Error", "Transaction commit failed")
            return

        QMessageBox.information(None, "Success", "All inserts were successful")
        # --- Clear Fields ---
        self.clear_product_fields()

    
    

    def load_product_suggestions(self):
        
        print("Loading Product Suggestions")

        current_text = self.name_input.currentText()
        print("Current Text is: ", current_text)
        
        if current_text == '':
            return 
        
        query = QSqlQuery()
        query.prepare("SELECT id, name, form, strength FROM product WHERE name LIKE ? LIMIT 10")
        print("Current Text is: ", current_text)
        query.addBindValue(f"%{current_text}%")
        
        products = []
        
        if not query.exec():
            
            print("Something wrong happened...")
        
        else:
        
            while query.next():
                
                product_id = query.value(0)
                name = query.value(1)
                form = query.value(2)
                strength = query.value(3)
                
                label = f"{name} {form} {strength}".strip()
                products.append(label)
                self.name_input.addItem(label, product_id)
                
        print(products)

        
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        data = products
        model = QStringListModel()
        model.setStringList(data)
        
        
        self.completer.setModel(model)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)


        print("Setting Current Text")
        self.name_input.lineEdit().setText(current_text)
        
        
        

    def clear_product_fields(self):

        self.name_input.clear()
        self.code_input.clear()
        self.brand_input.clear()
        self.pack_size_input.clear()
        self.packs_input.clear()
        self.units_input.clear()
        
        self.formula_input.clear()
        self.form_input.clear()
        self.strength_input.clear()
        self.batch_input.clear()
        self.expiry_input.clear()
        
        self.total_cost_input.clear()
        self.sale_price_input.clear()
        
        
    
    
    def show_import_popup(self):
        # Simulate reading CSV (replace with real file picker)
        df = pd.DataFrame({
            "ID": [1, 2, 3],
            "Name": ["Paracetamol", "Ibuprofen", "Vitamin C"],
            "Price": [50, 80, 120]
        })

        dialog = ImportDialog(df, self)
        dialog.exec()  # <-- this makes it modal


        
        
        





def _parse_date_iso(s):
    """Try common date formats and return ISO date (YYYY-MM-DD) or None."""
    if not s:
        return None
    s = s.strip()
    fmts = ("%d/%m/%y", "%d/%m/%Y", "%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y")
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            return dt.date().isoformat()
        except Exception:
            pass
    # try to pick 2-digit year heuristically like "12/12/25" -> 2025 (strptime handles %y)
    return None

# synonyms for header matching (lowercase)
_SYNONYMS = {
    "name": ["name", "product", "product name"],
    "code": ["code", "sku", "barcode", "product code"],
    "category": ["category", "cat"],
    "formula": ["formula", "generic", "composition"],
    "brand": ["brand", "company"],
    "form": ["form", "dosage form"],
    "strength": ["strength", "dose"],
    "packsize": ["packsize", "pack size", "pack"],
    "packs": ["packs", "pack"],
    "units": ["units", "unit", "quantity"],
    "reorder": ["reorder", "reorder level", "reorderlevel"],
    "costprice": ["costprice", "cost"],
    "saleprice": ["saleprice", "price", "mrp", "sale price"],
    "purchaseitem": ["purchaseitem", "purchase item"],
    "batch": ["batch", "batchno", "batch no", "batch number"],
    "expiry": ["expiry", "expiry date", "expiration", "exp"],
}

def _build_header_map(table):
    """Return dict field -> column index if found. Case-insensitive, uses synonyms.
       If header not present, leave absent and caller may fallback to positional mapping."""
    headers = []
    for c in range(table.columnCount()):
        h = table.horizontalHeaderItem(c)
        headers.append(h.text().strip().lower() if h else "")
    mapping = {}
    for field, syns in _SYNONYMS.items():
        for s in syns:
            if s in headers:
                mapping[field] = headers.index(s)
                break
    return mapping



import math




class ImportDialog(QDialog):
    
    # ... your __init__ / UI methods ...
    def __init__(self, df, parent=None):
        
        super().__init__(parent)
        self.setWindowTitle("Imported Product List")
        self.resize(600, 400)

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns.tolist())

        # Fill table with dataframe values
        for row in range(len(df)):
            for col in range(len(df.columns)):
               self.table.setItem(row, col, QTableWidgetItem(str(df.iat[row, col])))

        layout.addWidget(self.table)
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
    
    
    

    def accept(self):
        """Save imported products + stock + batch (handles optional category)."""
        # 1) build mapping from headers (if headers present)
        hdr_map = _build_header_map(self.table)

        # fallback positional orders
        # order_with_category (15 cols)
        order_with_cat = ["name","code","category","formula","brand","form","strength",
                          "packsize","packs","units","reorder","costprice","saleprice","purchaseitem","batch","expiry"]
        
        col_count = self.table.columnCount()
        if not hdr_map:
            # no useful headers found; choose positional mapping if col count matches
            if col_count == len(order_with_cat):
                for i, fld in enumerate(order_with_cat):
                    hdr_map.setdefault(fld, i)
            
            else:
                # best-effort: map available columns by index to order_no_cat (trim or pad)
                for i in range(col_count):
                    if i < len(order_with_cat):
                        hdr_map.setdefault(order_with_cat[i], i)

        # 2) collect rows into list of dicts
        rows = []
        for r in range(self.table.rowCount()):
            rd = {}
            for fld in ["name","code","category","formula","brand","form","strength",
                        "packsize","packs","units","reorder","costprice", "saleprice","purchaseitem","batch","expiry"]:
                if fld in hdr_map:
                    col = hdr_map[fld]
                    item = self.table.item(r, col)
                    rd[fld] = item.text().strip() if item else ""
                else:
                    rd[fld] = ""  # missing column -> blank
            rows.append(rd)

        # 3) DB insertion (in a transaction)
        db = QSqlDatabase.database()
        if not db.isValid() or not db.isOpen():
            QMessageBox.critical(self, "DB Error", "Database is not open.")
            return

        if not db.transaction():
            # proceed anyway but warn
            print("Warning: could not start transaction, proceeding without transaction.")

        errors = []
        q = QSqlQuery()
        for r in rows:
            # prepare data and conversions
            name = r.get("name") or None
            code = r.get("code") or None
            category = r.get("category") or None
            formula = r.get("formula") or None
            brand = r.get("brand") or None
            form = r.get("form") or None
            strength = r.get("strength") or None

            # numeric conversions with safe fallback
            def to_int(x):
                try:
                    return int(float(x))
                except Exception:
                    return None
            def to_float(x):
                try:
                    return float(x)
                except Exception:
                    return None
                
            def to_int_or_none(x):
                if x is None:
                    return None
                if isinstance(x, float) and math.isnan(x):
                    return None
                try:
                    return int(x)
                except Exception:
                    return None
                

            packsize = to_int(r.get("packsize") or 0)
            packs = to_int(r.get("packs") or 0)
            units = to_int(r.get("units") or 0)
            
            if packsize is None:
                packsize = 0
            if packs is None:
                packs = 0
            if units is None:
                units = 0
            
            units = (packsize * packs) + units
            reorder = to_int(r.get("reorder") or 0)
            costprice = to_float(r.get("costprice") or 0.0)
            saleprice = to_float(r.get("saleprice") or 0.0)

            purchaseitem = to_int_or_none(r.get("purchaseitem"))
            batch_val = r.get("batch") or None
            expiry_iso = r.get("expiry") or ""
            # expiry_iso = _parse_date_iso(r.get("expiry") or "")

            # 3.a Insert or get product id (ON CONFLICT by code; requires unique constraint on product.code)
            # Use RETURNING id for Postgres; if DB doesn't return it, fallback to SELECT.
            now = datetime.now()
            # q.prepare("""
            #     INSERT INTO product (name, code, category, brand, formula, form, strength, status)
            #     VALUES (:name, :code, :category, :brand, :formula, :form, :strength, :status)
            #     ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
            #     RETURNING id
            # """)
            
            q.prepare("""
                INSERT OR IGNORE INTO product (name, code, category, brand, formula, form, strength, status)
                VALUES (:name, :code, :category, :brand, :formula, :form, :strength, :status)
            """)
            
            
            q.bindValue(":name", name)
            q.bindValue(":code", code)
            q.bindValue(":category", category)
            q.bindValue(":brand", brand)
            q.bindValue(":formula", formula)
            q.bindValue(":form", form)
            q.bindValue(":strength", strength)

            if not q.exec():
                errors.append(f"Product insert failed (code={code}): {q.lastError().text()}")
                # try to continue to next row
                continue
            
            else:
                
                print("Product inserted/exists for code=", code)
                product_id = q.lastInsertId()
            
            # sel = QSqlQuery()
            # sel.prepare("SELECT id FROM product WHERE code = :code LIMIT 1")
            # sel.bindValue(":code", code)
            
            
            # if sel.exec() and sel.next():
            #     product_id = sel.value(0)
            # else:
            #     errors.append(f"Could not determine product id for code={code}")
            #     continue


            # 3.b Insert stock
            saleprice_raw = r.get("saleprice") or "0"
            print("Sale Price is: ", saleprice_raw)
            try:
                saleprice = float(saleprice_raw)
            except Exception:
                saleprice = 0.0

            q2 = QSqlQuery()
            q2.prepare("""
                INSERT INTO stock (product, packsize, units, reorder, saleprice)
                VALUES (:product, :packsize, :units, :reorder, :saleprice)
            """)
            
            q2.bindValue(":product", product_id)
            q2.bindValue(":packsize", packsize if packsize is not None else 0)
            q2.bindValue(":units", units if units is not None else 0)
            q2.bindValue(":reorder", reorder if reorder is not None else 0)
            q2.bindValue(":saleprice", saleprice)


            if not q2.exec():
                errors.append(f"Stock insert failed for code={code}: {q2.lastError().text()}")



            print("Total Cost is: ", costprice)
            # --- Insert into stockcost ---
            stockcost_query = QSqlQuery()
            stockcost_query.prepare("""
                INSERT INTO stockcost (product, qty, totalcost, stocktype)
                VALUES (?, ?, ?, ?)
            """)
            
            # units = int(packsize) * int(packs)
            # units = str(units)
            stockcost_query.addBindValue(product_id)
            stockcost_query.addBindValue(units)   
            stockcost_query.addBindValue(costprice)
            stockcost_query.addBindValue('onhand')

            if not stockcost_query.exec():
                errors.append(f"Batch insert failed for code={code} {stockcost_query.lastError().text()}")
                

            # 3.c Insert batch (if batch provided)
            if batch_val:
                q3 = QSqlQuery()
                q3.prepare("""
                    INSERT INTO batch (purchaseitem, product, batch, expiry)
                    VALUES (:purchaseitem, :product, :batch, :expiry)
                """)
                q3.bindValue(":purchaseitem", purchaseitem or None)
                q3.bindValue(":product", product_id)
                q3.bindValue(":batch", batch_val)
                q3.bindValue(":expiry", expiry_iso or None)

                if not q3.exec():
                    errors.append(f"Batch insert failed for code={code}, batch={batch_val}: {q3.lastError().text()}")

        # commit/rollback
        if errors:
            try:
                db.rollback()
            except Exception:
                pass
            QMessageBox.warning(self, "Import completed with errors", "\n".join(errors))
        else:
            try:
                db.commit()
            except Exception:
                pass
            QMessageBox.information(self, "Import successful", f"Imported {len(rows)} rows successfully.")

        super().accept()