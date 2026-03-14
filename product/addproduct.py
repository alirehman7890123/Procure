from PySide6.QtWidgets import QWidget, QVBoxLayout, QDialog, QPushButton,QComboBox, QDialogButtonBox, QTableWidgetItem, QCompleter,QTableWidget, QFileDialog, QMessageBox, QGridLayout, QLineEdit, QFrame, QDateEdit, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import QSize, Qt, QFile, QDate, QEvent, QStringListModel
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from datetime import date, datetime
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
        self.estimate_cost_btn = QPushButton("Set Stock Estimate Cost", objectName="TopRightButton")
        self.estimate_cost_btn.setCursor(Qt.PointingHandCursor)
        self.estimate_cost_btn.clicked.connect(self.set_estimate_cost)
        
        
        self.productlist = QPushButton("Products List", objectName="TopRightButton")
        self.productlist.setCursor(Qt.PointingHandCursor)
        self.productlist.setFixedWidth(200)

        self.import_file_button = QPushButton("Import File", objectName="TopRightButton")
        self.import_file_button.setCursor(Qt.PointingHandCursor)
        self.import_file_button.setFixedWidth(200)

        self.import_file_button.clicked.connect(self.import_file)
    

        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addWidget(self.estimate_cost_btn)
        
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
        
        
        self.populate_product_fields()
        self.populate_stock_and_batch_fields()
        self.populate_pricing_fields()
        
        
        # connect keyup events to calculate unit price
        self.pack_price_input.textChanged.connect(self.calculate_unit_price)
        self.pack_size_input.textChanged.connect(self.calculate_unit_price)
        
        
        self.layout.addSpacing(20)
        
        
        

        # === Add Button ===
        save_button = QPushButton("Save Product", objectName="SaveButton")
        save_button.setCursor(Qt.PointingHandCursor)

        self.layout.addWidget(save_button)
        self.layout.addStretch()
        
        
        
        
        
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)
        
        
        self.setStyleSheet(load_stylesheets())

        
        save_button.clicked.connect(lambda: self.save_product(  
                                                                self.name_input, 
                                                                self.brand_input,
                                                                self.formula_input,
                                                                self.code_input, 
                                                                
                                                                self.quantity_input, 
                                                                self.unit_cost_input, 
                                                                self.batch_input, 
                                                                self.expiry_input,
                                                                
                                                                self.pack_price_input,
                                                                self.pack_size_input, 
                                                            
                                                            ))



    def set_estimate_cost(self):
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Estimated Inventory Cost")
        dialog.setFixedWidth(500)
        dialog.setFixedHeight(450)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("Enter Estimated Inventory Cost")
        layout.addWidget(title)

        # Estimate Cost Field
        cost_input = QLineEdit()
        cost_input.setPlaceholderText("Enter amount")
        layout.addWidget(cost_input)

        # Admin Password Field
        password_input = QLineEdit()
        password_input.setPlaceholderText("Admin Password Required")
        password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_input)

        # Load existing value
        query = QSqlQuery()
        if query.exec("SELECT opening_inventory_value FROM accounting_settings WHERE id = 1"):
            if query.next():
                existing_value = query.value(0)
                if existing_value is not None:
                    cost_input.setText(str(existing_value))

        # Save Button
        save_button = QPushButton("Save")
        save_button.setStyleSheet("background-color: #420000; color: #fff;")
        layout.addWidget(save_button)
        
        layout.addStretch()

        def handle_save():
            try:
                new_cost = float(cost_input.text())
            except ValueError:
                QMessageBox.warning(dialog, "Invalid Input", "Enter a valid numeric value.")
                return

            admin_password = password_input.text().strip()

            if not admin_password:
                QMessageBox.warning(dialog, "Authentication Required", "Admin password is required.")
                return

            if not self.verify_admin_password(admin_password):
                QMessageBox.critical(dialog, "Access Denied", "Invalid admin password.")
                return

            # Insert or Update id = 1
            query = QSqlQuery()
            query.prepare("""
                INSERT INTO accounting_settings (id, opening_inventory_value, updated_at)
                VALUES (1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id)
                DO UPDATE SET
                    opening_inventory_value = excluded.opening_inventory_value,
                    updated_at = CURRENT_TIMESTAMP
            """)
            query.addBindValue(new_cost)

            if not query.exec():
                QMessageBox.critical(dialog, "Error", query.lastError().text())
                return

            QMessageBox.information(dialog, "Success", "Estimated cost updated successfully.")
            dialog.accept()

        save_button.clicked.connect(handle_save)

        dialog.exec()
            
        
        
        
    def verify_admin_password(self, password: str) -> bool:
        
        from PySide6.QtSql import QSqlQuery
        import bcrypt

        query = QSqlQuery()
        query.prepare("""
            SELECT password_hash
            FROM auth
            WHERE role = 'admin'
            AND status = 'active'
            LIMIT 1
        """)

        if not query.exec():
            print("Admin verification failed:", query.lastError().text())
            return False

        if not query.next():
            return False

        stored_hash = query.value(0)

        if not stored_hash:
            return False

        try:
            return bcrypt.checkpw(password.encode(), stored_hash.encode())
        except Exception:
            return False

        
    
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
        
        forms = [
            "AEROSOL","BALM","BUBBLE GUM","CAP","CAPLET","CAPS SR","CREAM","DRAGEES","DROPS",
            "DRY SUSP","E AND E DROPS","EAR DROPS","ELIXIR","EMUL","ENEMA","EXPC","EYE DROPS",
            "EYE GEL","EYE OINT","EYE SUSP","FORM","GEL","GRANULES","INF","INHALER","INJ",
            "INJ CS","INJ DS","INJ IM/IV","INJ SC","INJ SR","INJ-IM","INJ-IV","LINCTUS",
            "LINIMENT","LIQUID","LOTION","LOZENGES","MIXTURE","MOUTH SPRAY","MOUTH WASH",
            "NASAL DROPS","NASAL SPRAY","NEBULISER","OIL","OINT","ORAL SOLN","PAINT",
            "PASTE","PATCHES","PELLETS","POULTICE","POWDER","ROTA CAPS","SACHET","SCRUB",
            "SHAMPOO","SOAP","SOFT CAPS","SOLN","SPRAY","SUPPOSITORIES","SUSP","SUSP DS",
            "SYP","SYRINGE","TAB","TAB ENTERIC COATED","TABS CHEWABLE","TABS DS","TABS EFR",
            "TABS SL","TABS SR","TINC","TOOTH PASTE","VAG CREAM","VAG OVULE","VAG PESSARIES","VAG TABS"
        ]

        forms = sorted([f.title() for f in forms])

        
        
        self.name_input = QComboBox()
        self.name_input.setEditable(True)
        
        self.name_input.setStyleSheet("""
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #0078d7;
                selection-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
            }

            QComboBox::down-arrow {
                image: none;
            }
            """)
        
        line_edit = self.name_input.lineEdit()
        line_edit.textEdited.connect(self.force_uppercase)
        
        
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
        
        self.product_model = QStringListModel(self)
        self.completer.setModel(self.product_model)
        
        
        
        
        
        
        
        
        
        self.dosage = QLineEdit()
        self.dosage.setPlaceholderText('Dose')
        
        self.form = QComboBox()
        self.form.clear()
        self.form.addItems(forms)
        self.form.setStyleSheet("""
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #0078d7;
                selection-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
            }

            QComboBox::down-arrow {
                image: none;
            }
            """)
        
        
        self.form.setEditable(True)
        
        
        self.brand_input = QComboBox()
        self.setup_manufacturer_combobox(self.brand_input)
        self.brand_input.setStyleSheet("""
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #0078d7;
                selection-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
            }

            QComboBox::down-arrow {
                image: none;
            }
            """)
        
        self.formula_input = QLineEdit()
        self.code_input = QLineEdit()
        
        
        # --- Name and Brand on same row ---
        name_brand_row = QHBoxLayout()
        
        product_label = QLabel("Product")
        name_brand_row.addWidget(product_label, 1)
        name_brand_row.addWidget(self.name_input, 4)
        
        
        name_brand_row.addWidget(self.dosage, 1)
        name_brand_row.addWidget(self.form, 1)
        
        
        
        brand_label = QLabel("Manufacturer")
        # align label to right
        brand_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        name_brand_row.addWidget(brand_label, 1)
        name_brand_row.addWidget(self.brand_input, 5)
        
        self.layout.addLayout(name_brand_row)
        
        self.layout.addSpacing(10)
        
        # --- Formula and Code on same row ---
        formula_code_row = QHBoxLayout()
        
        formula_label = QLabel("Formula")
        formula_code_row.addWidget(formula_label, 1)
        formula_code_row.addWidget(self.formula_input, 6)
        
        code_label = QLabel("Code")
        code_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        formula_code_row.addWidget(code_label, 1)
        formula_code_row.addWidget(self.code_input, 5)
        
        self.layout.addLayout(formula_code_row)
        
        
        
        
        
        # --- Spacer Line ---
        self.layout.addSpacing(20)
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
        

    def populate_stock_and_batch_fields(self):
        
        batch_row = QHBoxLayout()
        
        # --- Stock, Cost, Batch, Expiry on same row ---
        
        quantity_label = QLabel("Qty (units)")
        self.quantity_input = QLineEdit()
        batch_row.addWidget(quantity_label, 1)
        batch_row.addWidget(self.quantity_input, 2)
        
        unit_cost_label = QLabel("Unit Cost")
        unit_cost_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.unit_cost_input = QLineEdit()
        batch_row.addWidget(unit_cost_label, 1)
        
        batch_row.addWidget(self.unit_cost_input, 2)
        
        
        self.batch_input = QLineEdit()
        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDisplayFormat("dd MMM yyyy")
        self.expiry_input.setMinimumDate(QDate.currentDate())
        self.expiry_input.setDate(self.expiry_input.minimumDate()) 

        self.expiry_input.setStyleSheet("""
            QDateEdit {
                padding: 4px;
            }

            QCalendarWidget QWidget {
                background-color: white;
                color: black;
            }

            QCalendarWidget QAbstractItemView {
                selection-background-color: #0078d7;
                selection-color: white;
                color: black;
            }

            QCalendarWidget QToolButton {
                background: none;
                color: black;
            }
        """)
        
        self.expiry_input.setKeyboardTracking(False)

        batch_label = QLabel("Batch No")
        batch_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        batch_row.addWidget(batch_label, 1)
        batch_row.addWidget(self.batch_input, 2)
        
        batch_row.addWidget(self.expiry_input, 3)
        
        self.layout.addLayout(batch_row)
        self.layout.setSpacing(20)
        
        
        # --- Spacer Line ---
        self.layout.addSpacing(20)
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
        
        
    def force_uppercase(self, text):
        line_edit = self.name_input.lineEdit()
        line_edit.blockSignals(True)
        line_edit.setText(text.upper())
        line_edit.blockSignals(False)

    
    def populate_manufacturer_combobox(self, combo: QComboBox):
        
        combo.clear()

        query = QSqlQuery("""
            SELECT id, name
            FROM manufacturer
            WHERE status = 'active'
            ORDER BY name
        """)

        while query.next():
            manufacturer_id = query.value(0)
            manufacturer_name = query.value(1)
            combo.addItem(manufacturer_name, manufacturer_id)


    def handle_new_manufacturer_entry(self, combo: QComboBox):
        
        name = combo.currentText().strip()

        if not name:
            return

        # check if already exists in combobox
        for i in range(combo.count()):
            if combo.itemText(i).strip().lower() == name.lower():
                combo.setCurrentIndex(i)
                return

        # insert new manufacturer
        query = QSqlQuery()
        query.prepare("""
            INSERT INTO manufacturer (name)
            VALUES (?)
        """)
        query.addBindValue(name)

        if not query.exec():
            print("Failed to insert manufacturer:", query.lastError().text())
            return

        new_id = query.lastInsertId()

        # add directly instead of reloading everything
        combo.addItem(name, new_id)
        combo.setCurrentIndex(combo.count() - 1)
        print("New Manufacturer added .. right about now...")



   
    def populate_pricing_fields(self):
        
        
        # --- Pack Price, Pack Size, Unit Price on same row ---
        pricing_row = QHBoxLayout()
        
        pack_price_label = QLabel("Pack Sale Price")
        self.pack_price_input = QLineEdit()
        pricing_row.addWidget(pack_price_label, 1)
        pricing_row.addWidget(self.pack_price_input, 2)
        
        self.pack_size_input = QLineEdit()
        self.pack_size_input.setPlaceholderText("Pack Size")
        pricing_row.addWidget(self.pack_size_input, 1)
        
        unit_price_label = QLabel("Unit Sale Price:")
        unit_price_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.unit_price_input = QLabel()
        
        pricing_row.addWidget(unit_price_label, 1)
        pricing_row.addWidget(self.unit_price_input, 7)
        
        self.layout.addLayout(pricing_row)
        self.layout.setSpacing(10)
        
        
        
        
    def setup_manufacturer_combobox(self, combo: QComboBox):
        
        combo.setEditable(True)
        combo.lineEdit().focusInEvent = lambda event, le=combo.lineEdit(): (
            le.selectAll(),
            QLineEdit.focusInEvent(le, event)
        )
        combo.setInsertPolicy(QComboBox.NoInsert)

        self.populate_manufacturer_combobox(combo)

        # avoid duplicate connections if method is called again
        try:
            combo.lineEdit().editingFinished.disconnect()
        except:
            pass

        combo.lineEdit().editingFinished.connect(
            lambda: self.handle_new_manufacturer_entry(combo)
        )
        
        
    
    
    def insert_subheading(self, text):
        subheading = QLabel(text, objectName="SubSectionTitle")
        subheading.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        subheading.setStyleSheet("margin-top: 20px; margin-bottom: 10px;")
        self.layout.addWidget(subheading)
    

    def on_item_selected(self, text):
        text = text.strip()

        index = self.name_input.findText(text, Qt.MatchFixedString)
        if index < 0:
            return

        self.name_input.setCurrentIndex(index)
        self.name_input.lineEdit().setText(text)

        data = self.name_input.itemData(index)
        print("Selected text is:", text, data)
        
        
        # move the cursor to qty field
        self.qty_input.setFocus()
    
    
    
    def calculate_unit_price(self):
        
        
        packsize = self.pack_size_input.text().strip()
        price = self.pack_price_input.text().strip()
        
        # validate pack size and price
        if packsize == '' or price == '':
            self.unit_price_input.setText("0.00")
            return
        
        
        unit_price = 0.0
        try:
            packsize_int = int(packsize)
            price_float = float(price)
            if packsize_int > 0:
                unit_price = price_float / packsize_int
            else:
                unit_price = 0.0
        except Exception:
            unit_price = 0.0
        
        self.unit_price_input.setText(f"{unit_price:.2f}")

    
    

    def save_product(
            self,
            product_combo,
            brand_combo,
            formula_input,
            code_input,
            qty_input,
            unit_cost_input,
            batch_input,
            expiry_input,
            pack_price_input,
            pack_size_input,
        ):
        
        print("Going to save the product")

        # ---------- Read input ----------
        existing_product_id = product_combo.currentData()
        display_name = product_combo.currentText().strip()
        
        print(display_name, existing_product_id)

        manufacturer_id = brand_combo.currentData()
        generic_name = formula_input.text().strip() or None
        code = code_input.text().strip() or None

        qty_text = qty_input.text().strip()
        unit_cost_text = unit_cost_input.text().strip()
        batch_no = batch_input.text().strip() or None
        pack_size = pack_size_input.text().strip() or None
        pack_price_text = pack_price_input.text().strip()

        quantity = float(qty_text) if qty_text else 0.0
        unit_cost = float(unit_cost_text) if unit_cost_text else None
        pack_price = float(pack_price_text) if pack_price_text else 0.0

        # ---------- Expiry ----------
        expiry_date = None
        qdate = expiry_input.date()
        if qdate.isValid():
            parsed_expiry = qdate.toPython()
            if parsed_expiry > date.today():
                expiry_date = parsed_expiry.isoformat()

        # ---------- Validation ----------
        if not display_name:
            QMessageBox.information(None, "Missing Data", "Product name is required.")
            return

        db = QSqlDatabase.database()
        if not db.transaction():
            QMessageBox.information(None, "Error", "Failed to start transaction.")
            return

        try:
            # ==================================================
            # 1. Resolve product_id
            # ==================================================
            if existing_product_id is not None:
                
                product_id = int(existing_product_id)
                print("Existing product selected. Product ID:", product_id)

            else:
                
                brand_name = display_name
                if brand_name is None:
                    raise Exception("Brand is required for a new product.")

                product_query = QSqlQuery(db)
                product_query.prepare("""
                    INSERT INTO product (
                        display_name,
                        code,
                        reg_no,
                        generic_name,
                        brand,
                        form,
                        strength,
                        packing,
                        pack_size,
                        manufacturer_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """)
                
                
                reg_no = ''
                form = self.form.currentText().strip() or None
                strength = self.dosage.text()
                packing = ''
                display_name = f"{brand_name} {form} {strength}"
                product_query.addBindValue(display_name)
                product_query.addBindValue(code)
                product_query.addBindValue(reg_no)
                product_query.addBindValue(generic_name)
                product_query.addBindValue(brand_name)
                product_query.addBindValue(form)
                product_query.addBindValue(strength)
                product_query.addBindValue(packing)
                product_query.addBindValue(pack_size)
                product_query.addBindValue(manufacturer_id)

                if not product_query.exec():
                    raise Exception(product_query.lastError().text())

                product_id = int(product_query.lastInsertId())

            # ==================================================
            # 2. Insert batch
            # ==================================================
            batch_query = QSqlQuery(db)
            batch_query.prepare("""
                INSERT INTO batch (
                    batch_no,
                    expiry_date,
                    product_id,
                    total_received,
                    paid_qty,
                    quantity_remaining,
                    unit_cost,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """)
            batch_query.addBindValue(batch_no)
            batch_query.addBindValue(expiry_date)
            batch_query.addBindValue(product_id)
            batch_query.addBindValue(quantity)
            batch_query.addBindValue(quantity)
            batch_query.addBindValue(quantity)
            batch_query.addBindValue(unit_cost)
            batch_query.addBindValue("OPENING")

            if not batch_query.exec():
                raise Exception(batch_query.lastError().text())

            print("Batch stored")

            # ==================================================
            # 3. Insert price_pack
            # ==================================================
            price_query = QSqlQuery(db)
            price_query.prepare("""
                INSERT INTO price_pack (product_id, pack_size, pack_price)
                VALUES (?, ?, ?)
            """)
            price_query.addBindValue(product_id)
            price_query.addBindValue(pack_size)
            price_query.addBindValue(pack_price)

            if not price_query.exec():
                raise Exception(price_query.lastError().text())

            print("Price stored")

            # ==================================================
            # 4. Commit
            # ==================================================
            if not db.commit():
                raise Exception("Transaction commit failed.")

            QMessageBox.information(None, "Success", "Product saved successfully.")
            self.clear_product_fields()

        except Exception as e:
            db.rollback()
            QMessageBox.information(None, "Failed", str(e))

    

    def load_product_suggestions(self):
        
        current_text = self.name_input.lineEdit().text().strip()

        if not current_text:
            self.name_input.blockSignals(True)
            self.name_input.clear()
            self.name_input.setCurrentIndex(-1)
            self.name_input.blockSignals(False)
            self.product_model.setStringList([])
            self.completer.popup().hide()
            return

        query = QSqlQuery()
        query.prepare("""
            SELECT id, display_name
            FROM product
            WHERE display_name LIKE ?
            LIMIT 10
        """)
        query.addBindValue(f"%{current_text}%")

        products = []
        product_data = []

        if not query.exec():
            print("Something wrong happened...", query.lastError().text())
            return

        while query.next():
            product_id = query.value(0)
            display_name = str(query.value(1)).strip()
            products.append(display_name)
            product_data.append((display_name, product_id))

        self.name_input.blockSignals(True)
        self.name_input.clear()

        for name, product_id in product_data:
            self.name_input.addItem(name, product_id)

        self.name_input.setCurrentIndex(-1)
        self.name_input.lineEdit().setText(current_text)
        self.name_input.blockSignals(False)

        self.product_model.setStringList(products)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionPrefix(current_text)

        if products:
            self.completer.complete()
        else:
            self.completer.popup().hide()



    def clear_product_fields(self):

        self.name_input.setCurrentIndex(-1)
        self.code_input.clear()
        self.brand_input.clear()
        self.pack_size_input.clear()
        
        self.qty_input.clear()
        
        self.formula_input.clear()
        self.batch_input.clear()
        self.expiry_input.setDate(QDate.currentDate())
        
        self.unit_cost_input.clear()
        self.pack_price_input.clear()
        self.unit_price_input.setText('0.0')
        
        
    
    
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
    "purchaseitem": ["purchaseitem", "purchase item", "PurchaseItem"],
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
        
        db = QSqlDatabase.database()

        if not db.isValid() or not db.isOpen():
            QMessageBox.critical(self, "DB Error", "Database is not open.")
            return

        def get_cell_text(row, col):
            item = self.table.item(row, col)
            return item.text().strip() if item and item.text() else ""

        def to_int_or_none(value):
            value = str(value).strip()
            if not value:
                return None
            try:
                return int(float(value))
            except Exception:
                return None

        def extract_generic_and_strength(generic_text):
            generic_text = str(generic_text).strip()

            if "[" in generic_text and "]" in generic_text:
                base = generic_text.split("[", 1)[0].strip()
                strength = generic_text.split("[", 1)[1].split("]", 1)[0].strip()
                return base, strength

            return generic_text, None

        expected_headers = [
            "Reg. #",
            "Brand",
            "Generic",
            "Form",
            "Packing",
            "Size",
            "Manufacturer_ID"
        ]

        header_map = {}
        for col in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(col)
            if header_item:
                header_map[header_item.text().strip()] = col

        missing = [h for h in expected_headers if h not in header_map]
        if missing:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Missing required columns:\n{', '.join(missing)}"
            )
            return

        if not db.transaction():
            QMessageBox.critical(self, "DB Error", "Could not start transaction.")
            return

        errors = []
        inserted_count = 0
        query = QSqlQuery()

        for row in range(self.table.rowCount()):
            try:
                reg_no = get_cell_text(row, header_map["Reg. #"])
                brand = get_cell_text(row, header_map["Brand"])
                generic_raw = get_cell_text(row, header_map["Generic"])
                form = get_cell_text(row, header_map["Form"])
                packing = get_cell_text(row, header_map["Packing"])
                pack_size = to_int_or_none(get_cell_text(row, header_map["Size"]))
                manufacturer_id = to_int_or_none(get_cell_text(row, header_map["Manufacturer_ID"]))

                if not brand:
                    errors.append(f"Row {row + 1}: Brand is required.")
                    continue

                generic_name, strength = extract_generic_and_strength(generic_raw)

                parts = [brand, form, strength]
                display_name = " ".join(part.strip() for part in parts if part and str(part).strip())

                query.prepare("""
                    INSERT INTO product (
                        display_name,
                        code,
                        reg_no,
                        generic_name,
                        brand,
                        form,
                        strength,
                        packing,
                        pack_size,
                        manufacturer_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """)

                query.addBindValue(display_name)
                query.addBindValue(None)                    # code
                query.addBindValue(reg_no or None)
                query.addBindValue(generic_name or None)
                query.addBindValue(brand)
                query.addBindValue(form or None)
                query.addBindValue(strength or None)
                query.addBindValue(packing or None)
                query.addBindValue(pack_size)
                query.addBindValue(manufacturer_id)

                if not query.exec():
                    errors.append(f"Row {row + 1}: {query.lastError().text()}")
                    continue

                inserted_count += 1

            except Exception as e:
                errors.append(f"Row {row + 1}: {str(e)}")

        if errors:
            db.rollback()
            QMessageBox.warning(
                self,
                "Import Failed",
                "\n".join(errors[:20]) + ("\n..." if len(errors) > 20 else "")
            )
            return

        if not db.commit():
            db.rollback()
            QMessageBox.critical(self, "DB Error", "Failed to commit import.")
            return

        QMessageBox.information(
            self,
            "Import Successful",
            f"Imported {inserted_count} products successfully."
        )

        super().accept()
    
    

    # def accept(self):
    #     """Save imported products + stock + batch (handles optional category)."""
    #     # 1) build mapping from headers (if headers present)
    #     hdr_map = _build_header_map(self.table)

    #     # fallback positional orders
    #     # order_with_category (15 cols)
    #     order_with_cat = ["name","code","category","formula","brand","form","strength",
    #                       "packsize","packs","units","reorder","costprice","saleprice","purchaseitem","batch","expiry"]
        
    #     col_count = self.table.columnCount()
    #     if not hdr_map:
    #         # no useful headers found; choose positional mapping if col count matches
    #         if col_count == len(order_with_cat):
    #             for i, fld in enumerate(order_with_cat):
    #                 hdr_map.setdefault(fld, i)
            
    #         else:
    #             # best-effort: map available columns by index to order_no_cat (trim or pad)
    #             for i in range(col_count):
    #                 if i < len(order_with_cat):
    #                     hdr_map.setdefault(order_with_cat[i], i)

    #     # 2) collect rows into list of dicts
    #     rows = []
    #     for r in range(self.table.rowCount()):
    #         rd = {}
    #         for fld in ["name","code","category","formula","brand","form","strength",
    #                     "packsize","packs","units","reorder","costprice", "saleprice","purchaseitem","batch","expiry"]:
    #             if fld in hdr_map:
    #                 col = hdr_map[fld]
    #                 item = self.table.item(r, col)
    #                 rd[fld] = item.text().strip() if item else ""
    #             else:
    #                 rd[fld] = ""  # missing column -> blank
    #         rows.append(rd)

    #     # 3) DB insertion (in a transaction)
    #     db = QSqlDatabase.database()
    #     if not db.isValid() or not db.isOpen():
    #         QMessageBox.critical(self, "DB Error", "Database is not open.")
    #         return

    #     if not db.transaction():
    #         # proceed anyway but warn
    #         print("Warning: could not start transaction, proceeding without transaction.")

    #     errors = []
    #     q = QSqlQuery()
    #     for r in rows:
    #         # prepare data and conversions
    #         name = r.get("name") or None
    #         code = r.get("code") or None
    #         category = r.get("category") or None
    #         formula = r.get("formula") or None
    #         brand = r.get("brand") or None
    #         form = r.get("form") or None
    #         strength = r.get("strength") or None

    #         # numeric conversions with safe fallback
    #         def to_int(x):
    #             try:
    #                 return int(float(x))
    #             except Exception:
    #                 return None
    #         def to_float(x):
    #             try:
    #                 return float(x)
    #             except Exception:
    #                 return None
                
    #         def to_int_or_none(x):
    #             if x is None:
    #                 return None
    #             if isinstance(x, float) and math.isnan(x):
    #                 return None
    #             try:
    #                 return int(x)
    #             except Exception:
    #                 return None
                

    #         packsize = to_int(r.get("packsize") or 0)
    #         packs = to_int(r.get("packs") or 0)
    #         units = to_int(r.get("units") or 0)
            
    #         if packsize is None:
    #             packsize = 0
    #         if packs is None:
    #             packs = 0
    #         if units is None:
    #             units = 0
            
    #         units = (packsize * packs) + units
    #         reorder = to_int(r.get("reorder") or 0)
    #         costprice = to_float(r.get("costprice") or 0.0)
    #         saleprice = to_float(r.get("saleprice") or 0.0)

    #         purchaseitem = to_int_or_none(r.get("purchaseitem"))
    #         batch_val = r.get("batch") or None
    #         expiry_iso = r.get("expiry") or ""
    #         # expiry_iso = _parse_date_iso(r.get("expiry") or "")

    #         # 3.a Insert or get product id (ON CONFLICT by code; requires unique constraint on product.code)
    #         # Use RETURNING id for Postgres; if DB doesn't return it, fallback to SELECT.
    #         now = datetime.now()
    #         # q.prepare("""
    #         #     INSERT INTO product (name, code, category, brand, formula, form, strength, status)
    #         #     VALUES (:name, :code, :category, :brand, :formula, :form, :strength, :status)
    #         #     ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
    #         #     RETURNING id
    #         # """)
            
    #         q.prepare("""
    #             INSERT OR IGNORE INTO product (name, code, category, brand, formula, form, strength, status)
    #             VALUES (:name, :code, :category, :brand, :formula, :form, :strength, :status)
    #         """)
            
            
    #         q.bindValue(":name", name)
    #         q.bindValue(":code", code)
    #         q.bindValue(":category", category)
    #         q.bindValue(":brand", brand)
    #         q.bindValue(":formula", formula)
    #         q.bindValue(":form", form)
    #         q.bindValue(":strength", strength)

    #         if not q.exec():
    #             errors.append(f"Product insert failed (code={code}): {q.lastError().text()}")
    #             # try to continue to next row
    #             continue
            
    #         else:
                
    #             print("Product inserted/exists for code=", code)
    #             product_id = q.lastInsertId()
            
    #         # sel = QSqlQuery()
    #         # sel.prepare("SELECT id FROM product WHERE code = :code LIMIT 1")
    #         # sel.bindValue(":code", code)
            
            
    #         # if sel.exec() and sel.next():
    #         #     product_id = sel.value(0)
    #         # else:
    #         #     errors.append(f"Could not determine product id for code={code}")
    #         #     continue


    #         # 3.b Insert stock
    #         saleprice_raw = r.get("saleprice") or "0"
    #         print("Sale Price is: ", saleprice_raw)
    #         try:
    #             saleprice = float(saleprice_raw)
    #         except Exception:
    #             saleprice = 0.0

    #         q2 = QSqlQuery()
    #         q2.prepare("""
    #             INSERT INTO stock (product, packsize, units, reorder, saleprice)
    #             VALUES (:product, :packsize, :units, :reorder, :saleprice)
    #         """)
            
    #         q2.bindValue(":product", product_id)
    #         q2.bindValue(":packsize", packsize if packsize is not None else 0)
    #         q2.bindValue(":units", units if units is not None else 0)
    #         q2.bindValue(":reorder", reorder if reorder is not None else 0)
    #         q2.bindValue(":saleprice", saleprice)


    #         if not q2.exec():
    #             errors.append(f"Stock insert failed for code={code}: {q2.lastError().text()}")



    #         print("Total Cost is: ", costprice)
    #         # --- Insert into stockcost ---
    #         stockcost_query = QSqlQuery()
    #         stockcost_query.prepare("""
    #             INSERT INTO stockcost (product, qty, totalcost, stocktype)
    #             VALUES (?, ?, ?, ?)
    #         """)
            
    #         # units = int(packsize) * int(packs)
    #         # units = str(units)
    #         stockcost_query.addBindValue(product_id)
    #         stockcost_query.addBindValue(units)   
    #         stockcost_query.addBindValue(costprice)
    #         stockcost_query.addBindValue('onhand')

    #         if not stockcost_query.exec():
    #             errors.append(f"Batch insert failed for code={code} {stockcost_query.lastError().text()}")
                

    #         # 3.c Insert batch (if batch provided)
    #         if batch_val:
    #             q3 = QSqlQuery()
    #             q3.prepare("""
    #                 INSERT INTO batch (purchaseitem, product, batch, expiry)
    #                 VALUES (:purchaseitem, :product, :batch, :expiry)
    #             """)
    #             q3.bindValue(":purchaseitem", purchaseitem or None)
    #             q3.bindValue(":product", product_id)
    #             q3.bindValue(":batch", batch_val)
    #             q3.bindValue(":expiry", expiry_iso or None)

    #             if not q3.exec():
    #                 errors.append(f"Batch insert failed for code={code}, batch={batch_val}: {q3.lastError().text()}")

    #     # commit/rollback
    #     if errors:
    #         try:
    #             db.rollback()
    #         except Exception:
    #             pass
    #         QMessageBox.warning(self, "Import completed with errors", "\n".join(errors))
    #     else:
    #         try:
    #             db.commit()
    #         except Exception:
    #             pass
    #         QMessageBox.information(self, "Import successful", f"Imported {len(rows)} rows successfully.")

    #     super().accept()
        
        
        
        
        
        
        
        
         
import math
from PySide6.QtWidgets import QDialog, QDialogButtonBox

class EstimateDialog(QDialog):
    
    # ... your __init__ / UI methods ...
    def __init__(self, parent=None):
        
        super().__init__(parent)
        self.setWindowTitle("Import Stock Data")
        self.resize(600, 400)

        self.layout = QVBoxLayout()
        
        self.insert_subheading("Set INITIAL STOCK's Estimate Cost")
        
        set_estimate_edit = QLineEdit()
        self.layout.addWidget(set_estimate_edit)
        
        self.layout.addStretch()
                
        self.setLayout(self.layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                font-family: Arial;
                font-size: 12pt;
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
        self.layout.addWidget(button_box)
    
    
    
    def insert_subheading(self, title):
        
        # === Sub Header Row ===
        subheader_layout = QHBoxLayout()
        subheading = QLabel(title, objectName="SubHeading")
        
        subheader_layout.addWidget(subheading)
        self.layout.addLayout(subheader_layout)
        
        
    

    def search_rows(self, text):

        for row in range(self.stocktable.rowCount()):
            match = False
            for col in range(self.stocktable.columnCount() - 1):
                item = self.stocktable.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.stocktable.setRowHidden(row, not match)




