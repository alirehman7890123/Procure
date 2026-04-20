from PySide6.QtWidgets import QWidget, QVBoxLayout, QDialog, QPushButton,QComboBox, QDialogButtonBox, QTableWidgetItem, QCompleter,QTableWidget, QFileDialog, QMessageBox, QGridLayout, QLineEdit, QFrame, QDateEdit, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout, QGraphicsDropShadowEffect, QHeaderView, QApplication
from PySide6.QtGui import QColor
from PySide6.QtCore import QSize, Qt, QFile, QDate, QEvent, QStringListModel, Signal, QTimer
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from datetime import date, datetime
import re
from utilities.product_search_widget import ProductSearchBox
import sys
import pandas as pd  # <-- for reading CSV/Excel easily

from utilities.stylus import load_stylesheets
from utilities.permissions import Permissions
from services.accounting_settings_service import (
    load_opening_inventory_value,
    save_opening_inventory_value,
)



class AddProductWidget(QWidget):
    detailpagesignal = Signal(int)
    DEFAULT_MARGIN_PERCENT = 14.5

    def __init__(self, parent=None):

        super().__init__(parent)
        

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        
        # === Header Row ===
        header_layout = QHBoxLayout()
        heading = QLabel("Product Information", objectName="SectionTitle")
        self.estimate_cost_btn = QPushButton("Set Stock Estimate Cost", objectName="TopRightButton")
        self.estimate_cost_btn.setCursor(Qt.PointingHandCursor)
        self.estimate_cost_btn.clicked.connect(self.set_estimate_cost)
        
        
        self.productlist = QPushButton("Products List", objectName="TopRightButton")
        self.productlist.setCursor(Qt.PointingHandCursor)

        self.import_file_button = QPushButton("Import File", objectName="TopRightButton")
        self.import_file_button.setCursor(Qt.PointingHandCursor)

        self.import_file_button.clicked.connect(self.import_file)
    

        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.addWidget(heading)
        header_layout.addStretch()
        header_layout.addWidget(self.estimate_cost_btn)
        
        header_layout.addWidget(self.productlist)
        # header_layout.addWidget(self.import_file_button)

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
        self.layout.addSpacing(8)
        
        self.indicators = {}
        self.recent_entry_status = {}
        self.last_recent_batch_id = None
        self.section_widgets = {}

        # Card container for product entry form (same section style as sales page)
        self.form_frame = QFrame()
        self.form_frame.setObjectName("sectionCard")
        self.form_layout = QVBoxLayout(self.form_frame)
        self.form_layout.setContentsMargins(14, 12, 14, 12)
        self.form_layout.setSpacing(12)
        self.layout.addWidget(self.form_frame, 0)
        
        
        self.populate_product_fields()
        self.populate_stock_and_batch_fields()
        self.populate_pricing_fields()
        
        
        # connect keyup events to calculate unit price
        self.pack_price_input.textChanged.connect(self.calculate_unit_price)
        self.pack_size_input.textChanged.connect(self.calculate_unit_price)
        self.pack_price_input.textChanged.connect(self.calculate_pack_cost_from_margin)
        self.margin_input.textChanged.connect(self.calculate_pack_cost_from_margin)
        self.calculate_pack_cost_from_margin()
        
        
        # === Action Buttons ===
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(10)

        self.save_button = QPushButton("Save Product", objectName="SaveButton")
        self.save_button.setCursor(Qt.PointingHandCursor)

        self.clear_button = QPushButton("Clear Fields", objectName="TopRightButton")
        self.clear_button.setCursor(Qt.PointingHandCursor)

        action_row.addWidget(self.save_button, 1)
        action_row.addWidget(self.clear_button)

        self.layout.addLayout(action_row)
        self.layout.addSpacing(12)
        self.build_recent_products_section()
        self.layout.addStretch()
        
        
        
        
        
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)
        
        
        self.setStyleSheet(load_stylesheets())

        
        self.save_button.clicked.connect(self.save_product)
        self.clear_button.clicked.connect(self.confirm_clear_fields)
        self.setup_enter_navigation()

    def field_label(self, text, align_right=False):
        label = QLabel(text)
        label.setMinimumWidth(82)
        if align_right:
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setStyleSheet("font-size: 12px; font-weight: 600; padding-left: 0;")
        return label

    def force_uppercase_line_edit(self, line_edit, text):
        cursor_pos = line_edit.cursorPosition()
        upper_text = str(text or "").upper()
        if line_edit.text() == upper_text:
            return
        line_edit.blockSignals(True)
        line_edit.setText(upper_text)
        line_edit.setCursorPosition(min(cursor_pos, len(upper_text)))
        line_edit.blockSignals(False)

    def section_divider(self):
        line = QFrame()
        line.setObjectName("lineSeparator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("""
                QFrame#lineSeparator {
                    border: none;
                    border-top: 1px solid #D3DDE6;
                }
            """)
        return line

    def create_entry_section(self):
        frame = QFrame()
        frame.setObjectName("productEntrySection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)
        self.apply_section_highlight(frame, False)
        self.form_layout.addWidget(frame)
        return frame, layout

    def apply_section_highlight(self, frame, active):
        background = "#DCE7F0" if active else "#E7EFF6"
        border = "#B9CBD9" if active else "#C9D8E4"
        frame.setStyleSheet(f"""
            QFrame#productEntrySection {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 4px;
            }}
        """)

    def register_section_focus(self, frame, widgets):
        tracked = []
        for widget in widgets:
            if widget is None:
                continue
            tracked.append(widget)
            widget.installEventFilter(self)
            line_edit = getattr(widget, "lineEdit", None)
            if callable(line_edit):
                child = line_edit()
                if child is not None:
                    tracked.append(child)
                    child.installEventFilter(self)
        self.section_widgets[frame] = tracked

    def eventFilter(self, watched, event):
        if event.type() == QEvent.FocusIn:
            if isinstance(watched, QLineEdit) and not watched.isReadOnly():
                QTimer.singleShot(0, watched.selectAll)
        if event.type() in (QEvent.FocusIn, QEvent.FocusOut):
            QTimer.singleShot(0, self.update_section_highlight_from_focus)
        return super().eventFilter(watched, event)

    def update_section_highlight_from_focus(self):
        focus_widget = QApplication.focusWidget()
        for frame, widgets in self.section_widgets.items():
            active = focus_widget in widgets
            self.apply_section_highlight(frame, active)

    def build_recent_products_section(self):
        recent_title = QLabel("Recently Added Products", objectName="SubSectionTitle")
        recent_title.setStyleSheet("margin-top: 0; margin-bottom: 4px;")
        self.layout.addWidget(recent_title)

        self.recent_products_table = QTableWidget(0, 8)
        self.recent_products_table.setObjectName("StandardTable")
        self.recent_products_table.setHorizontalHeaderLabels([
            "Type", "Product", "Manufacturer", "Batch", "Expiry (MM-YY)", "Qty", "Pack Size", "Price"
        ])
        self.recent_products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_products_table.setSelectionMode(QTableWidget.SingleSelection)
        self.recent_products_table.verticalHeader().setVisible(False)
        self.recent_products_table.setAlternatingRowColors(True)
        self.recent_products_table.setFixedHeight(150)
        self.recent_products_table.horizontalHeader().setStretchLastSection(False)
        self.recent_products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.recent_products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.recent_products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        for col in range(3, 8):
            self.recent_products_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.recent_products_table.cellDoubleClicked.connect(self.open_recent_product_detail)
        self.layout.addWidget(self.recent_products_table)
        self.refresh_recent_products_table()

    def default_expiry_date(self):
        return QDate.currentDate()

    def parse_expiry_month_year(self, text):
        raw = str(text or "").strip()
        collapsed = raw.replace("_", "").replace(" ", "")
        if not collapsed or collapsed in {"-", "--"}:
            return None
        if not raw:
            return None

        match = re.fullmatch(r"(\d{2})-(\d{2})", raw)
        if not match:
            return None

        month = int(match.group(1))
        year_two_digits = int(match.group(2))
        if month < 1 or month > 12:
            return None

        year = 2000 + year_two_digits
        normalized = QDate(year, month, 1)
        if not normalized.isValid():
            return None

        current_month_start = QDate.currentDate().addDays(1 - QDate.currentDate().day())
        if normalized < current_month_start:
            return None

        return normalized

    def expiry_month_year_text(self, date_value):
        if date_value is None or not date_value.isValid():
            return ""
        return date_value.toString("MM-yy")

    def refresh_recent_products_table(self, highlight_batch_id=None):
        if not hasattr(self, "recent_products_table"):
            return

        query = QSqlQuery()
        query.prepare("""
            SELECT
                b.id,
                p.id,
                p.display_name,
                COALESCE(m.name, '-'),
                COALESCE(b.batch_no, '-'),
                b.expiry_date,
                b.total_received,
                COALESCE((
                    SELECT pp.pack_size
                    FROM price_pack pp
                    WHERE pp.product_id = p.id
                    ORDER BY pp.is_default DESC, pp.id DESC
                    LIMIT 1
                ), ''),
                COALESCE((
                    SELECT pp.pack_price
                    FROM price_pack pp
                    WHERE pp.product_id = p.id
                    ORDER BY pp.is_default DESC, pp.id DESC
                    LIMIT 1
                ), 0)
            FROM batch b
            JOIN product p ON p.id = b.product_id
            LEFT JOIN manufacturer m ON m.id = p.manufacturer_id
            ORDER BY b.id DESC
            LIMIT 5
        """)

        rows = []
        if query.exec():
            while query.next():
                batch_id = int(query.value(0))
                product_id = int(query.value(1))
                expiry_value = query.value(5)
                expiry_text = "-"
                if expiry_value:
                    try:
                        expiry_text = datetime.fromisoformat(str(expiry_value)).strftime("%m-%y")
                    except Exception:
                        expiry_text = str(expiry_value)

                rows.append([
                    self.recent_entry_status.get(batch_id, "-"),
                    str(query.value(2) or "-"),
                    str(query.value(3) or "-"),
                    str(query.value(4) or "-"),
                    expiry_text,
                    f"{float(query.value(6) or 0):.0f}",
                    str(query.value(7) or "-"),
                    f"{float(query.value(8) or 0):.2f}",
                    batch_id,
                    product_id,
                ])

        self.recent_products_table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            batch_id = row_values[-2]
            product_id = row_values[-1]
            for col_index, value in enumerate(row_values[:-2]):
                item = QTableWidgetItem(value)
                if col_index == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                if col_index == 1:
                    item.setData(Qt.UserRole, product_id)
                    item.setData(Qt.UserRole + 1, batch_id)
                if highlight_batch_id is not None and batch_id == highlight_batch_id:
                    item.setBackground(QColor("#E4F1FB"))
                    item.setForeground(QColor("#1F3E57"))
                self.recent_products_table.setItem(row_index, col_index, item)
        if highlight_batch_id is not None:
            self.last_recent_batch_id = highlight_batch_id

    def open_recent_product_detail(self, row, _column):
        item = self.recent_products_table.item(row, 1)
        if not item:
            return
        product_id = item.data(Qt.UserRole)
        if product_id is None:
            return
        try:
            self.detailpagesignal.emit(int(product_id))
        except (TypeError, ValueError):
            return



    @Permissions.require_permission('inventory.adjust')
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
        existing_value = load_opening_inventory_value()
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
                AppMessageBox.warning(dialog, "Invalid Input", "Enter a valid numeric value.")
                return

            admin_password = password_input.text().strip()

            if not admin_password:
                AppMessageBox.warning(dialog, "Authentication Required", "Admin password is required.")
                return

            if not self.verify_admin_password(admin_password):
                AppMessageBox.critical(dialog, "Access Denied", "Invalid admin password.")
                return

            try:
                save_opening_inventory_value(new_cost)
            except Exception as exc:
                AppMessageBox.critical(dialog, "Error", str(exc))
                return

            AppMessageBox.information(dialog, "Success", "Estimated cost updated successfully.")
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

        
        
        self.name_input = ProductSearchBox(self)
        self.name_input.lineEdit().textEdited.connect(self.force_uppercase)
        self.name_input.setStyleSheet("""
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #5A9EC9;
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
        self.name_input.product_selected.connect(
            lambda pid, name: self.on_item_selected(name)
        )
        self.name_input.activated[int].connect(self.on_name_index_activated)
        self.name_input.lineEdit().returnPressed.connect(self.on_name_enter_pressed)
        
        
        
        
        
        
        
        
        
        self.dosage = QLineEdit()
        self.dosage.setPlaceholderText('Dose')
        
        self.form = QComboBox()
        self.form.clear()
        self.form.addItems(forms)
        self.form.setStyleSheet("""
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #5A9EC9;
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
                selection-background-color: #5A9EC9;
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
        self.pack_size_input = QLineEdit()
        self.rack_input = QLineEdit()
        
        
        self.name_input.setPlaceholderText("Product name")
        self.dosage.setPlaceholderText("Dosage")
        self.form.setPlaceholderText("Form")
        self.brand_input.setPlaceholderText("Manufacturer")
        self.formula_input.setPlaceholderText("Formula")
        self.code_input.setPlaceholderText("Code")
        self.pack_size_input.setPlaceholderText("Pack Size")
        self.rack_input.setPlaceholderText("Rack")

        section_frame, section_layout = self.create_entry_section()

        main_grid = QGridLayout()
        main_grid.setContentsMargins(0, 0, 0, 0)
        main_grid.setHorizontalSpacing(10)
        main_grid.setVerticalSpacing(8)

        product_label = self.field_label("Product")
        main_grid.addWidget(product_label, 0, 0)
        main_grid.addWidget(self.name_input, 0, 1)
        main_grid.addWidget(self.dosage, 0, 2)
        main_grid.addWidget(self.form, 0, 3)
        manufacturer_label = self.field_label("Manufacturer", align_right=True)
        main_grid.addWidget(manufacturer_label, 0, 4)
        main_grid.addWidget(self.brand_input, 0, 5)

        formula_label = self.field_label("Formula")
        main_grid.addWidget(formula_label, 1, 0)
        main_grid.addWidget(self.formula_input, 1, 1, 1, 1)

        pack_size_label = self.field_label("Pack Size", align_right=True)
        main_grid.addWidget(pack_size_label, 1, 2)
        main_grid.addWidget(self.pack_size_input, 1, 3)

        rack_label = self.field_label("Rack", align_right=True)
        main_grid.addWidget(rack_label, 1, 4)
        main_grid.addWidget(self.rack_input, 1, 5)

        main_grid.setColumnStretch(1, 5)
        main_grid.setColumnStretch(2, 2)
        main_grid.setColumnStretch(3, 2)
        main_grid.setColumnStretch(4, 1)
        main_grid.setColumnStretch(5, 4)

        section_layout.addLayout(main_grid)
        self.register_section_focus(section_frame, [
            self.name_input, self.dosage, self.form, self.brand_input,
            self.formula_input, self.rack_input, self.pack_size_input
        ])
        

    def populate_stock_and_batch_fields(self):
        section_frame, section_layout = self.create_entry_section()

        batch_grid = QGridLayout()
        batch_grid.setContentsMargins(0, 0, 0, 0)
        batch_grid.setHorizontalSpacing(10)
        batch_grid.setVerticalSpacing(8)

        batch_label = self.field_label("Batch")
        self.batch_input = QLineEdit()
        self.batch_input.textEdited.connect(lambda text: self.force_uppercase_line_edit(self.batch_input, text))
        batch_grid.addWidget(batch_label, 0, 0)
        batch_grid.addWidget(self.batch_input, 0, 1)
        
        expiry_label = self.field_label("Expiry (MM-YY)", align_right=True)
        self.expiry_input = QLineEdit()
        self.expiry_input.setPlaceholderText("MM-YY")
        self.expiry_input.setInputMask("00-00;_")
        batch_grid.addWidget(expiry_label, 0, 2)
        batch_grid.addWidget(self.expiry_input, 0, 3)

        pack_price_label = self.field_label("Sale Price", align_right=True)
        self.pack_price_input = QLineEdit()
        batch_grid.addWidget(pack_price_label, 0, 4)
        batch_grid.addWidget(self.pack_price_input, 0, 5)

        quantity_label = self.field_label("Qty", align_right=True)
        self.quantity_input = QLineEdit()
        batch_grid.addWidget(quantity_label, 0, 6)
        batch_grid.addWidget(self.quantity_input, 0, 7)

        unit_cost_label = self.field_label("Cost (Derived)")
        self.unit_cost_input = QLineEdit()
        self.unit_cost_input.setPlaceholderText("auto-derived from sale price")
        self.unit_cost_input.setReadOnly(True)
        batch_grid.addWidget(unit_cost_label, 1, 0)
        batch_grid.addWidget(self.unit_cost_input, 1, 1)

        margin_label = self.field_label("Margin %", align_right=True)
        self.margin_input = QLineEdit()
        self.margin_input.setPlaceholderText("Margin %")
        self.margin_input.setText(f"{self.DEFAULT_MARGIN_PERCENT:.1f}")
        batch_grid.addWidget(margin_label, 1, 2)
        batch_grid.addWidget(self.margin_input, 1, 3)

        batch_grid.setColumnStretch(1, 3)
        batch_grid.setColumnStretch(3, 3)
        batch_grid.setColumnStretch(5, 3)
        batch_grid.setColumnStretch(7, 3)

        section_layout.addLayout(batch_grid)
        self.register_section_focus(section_frame, [
            self.batch_input, self.expiry_input, self.pack_price_input, self.quantity_input,
            self.unit_cost_input, self.margin_input
        ])
        
        
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
        section_frame, section_layout = self.create_entry_section()

        pricing_grid = QGridLayout()
        pricing_grid.setContentsMargins(0, 0, 0, 0)
        pricing_grid.setHorizontalSpacing(10)
        pricing_grid.setVerticalSpacing(8)

        unit_price_label = self.field_label("Unit Price")
        self.unit_price_input = QLabel()
        self.unit_price_input.setStyleSheet("font-size: 12px; font-weight: 700; color: #2F5D7C; padding-left: 0;")
        pricing_grid.addWidget(unit_price_label, 0, 0)
        pricing_grid.addWidget(self.unit_price_input, 0, 1)

        code_label = self.field_label("Code", align_right=True)
        pricing_grid.addWidget(code_label, 0, 2)
        pricing_grid.addWidget(self.code_input, 0, 3)

        discount_group_label = self.field_label("Discount", align_right=True)
        self.discount_group_combo = QComboBox()
        self.populate_discount_group_combobox(self.discount_group_combo)
        pricing_grid.addWidget(discount_group_label, 0, 4)
        pricing_grid.addWidget(self.discount_group_combo, 0, 5)

        tax_group_label = self.field_label("Tax")
        self.tax_group_combo = QComboBox()
        self.populate_tax_group_combobox(self.tax_group_combo)
        pricing_grid.addWidget(tax_group_label, 1, 0)
        pricing_grid.addWidget(self.tax_group_combo, 1, 1)

        reorder_label = self.field_label("Reorder", align_right=True)
        self.reorder_level = QLineEdit()
        self.reorder_level.setPlaceholderText("Reorder Level (units)")
        pricing_grid.addWidget(reorder_label, 1, 2)
        pricing_grid.addWidget(self.reorder_level, 1, 3)

        pricing_grid.setColumnStretch(1, 3)
        pricing_grid.setColumnStretch(3, 3)
        pricing_grid.setColumnStretch(5, 3)

        section_layout.addLayout(pricing_grid)
        self.register_section_focus(section_frame, [
            self.unit_price_input, self.code_input, self.discount_group_combo,
            self.tax_group_combo, self.reorder_level
        ])
        
        
        
        
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

    def populate_tax_group_combobox(self, combo: QComboBox):
        combo.clear()
        combo.addItem("None", None)
        query = QSqlQuery("""
            SELECT id, name, tax_percent, COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1)
            FROM tax_group
            WHERE status = 'active'
            ORDER BY name
        """)
        while query.next():
            group_id = query.value(0)
            group_name = str(query.value(1) or "").strip()
            tax_percent = float(query.value(2) or 0.0)
            fixed_amount = float(query.value(3) or 0.0)
            apply_on_sale = bool(int(query.value(4) or 0))
            combo.addItem(
                f"{group_name} ({tax_percent:.2f}% + {fixed_amount:.2f}, {'Sale On' if apply_on_sale else 'Sale Off'})",
                group_id,
            )

    def populate_discount_group_combobox(self, combo: QComboBox):
        combo.clear()
        combo.addItem("None", None)
        query = QSqlQuery("""
            SELECT id, name, discount_percent, COALESCE(fixed_amount, 0), COALESCE(apply_on_sale, 1)
            FROM discount_group
            WHERE status = 'active'
            ORDER BY name
        """)
        while query.next():
            group_id = query.value(0)
            group_name = str(query.value(1) or "").strip()
            discount_percent = float(query.value(2) or 0.0)
            fixed_amount = float(query.value(3) or 0.0)
            apply_on_sale = bool(int(query.value(4) or 0))
            combo.addItem(
                f"{group_name} ({discount_percent:.2f}% + {fixed_amount:.2f}, {'Sale On' if apply_on_sale else 'Sale Off'})",
                group_id,
            )
        
        
    
    
    def insert_subheading(self, text):
        subheading = QLabel(text, objectName="SubSectionTitle")
        subheading.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        subheading.setStyleSheet("margin-top: 20px; margin-bottom: 10px;")
        self.form_layout.addWidget(subheading)

    def focus_next_field(self, widget):
        widget.setFocus()
        if hasattr(widget, "selectAll"):
            widget.selectAll()

    def setup_enter_navigation(self):
        # Traverse fields in order using Enter key.
        self.dosage.returnPressed.connect(lambda: self.focus_next_field(self.form))
        self.form.lineEdit().returnPressed.connect(lambda: self.focus_next_field(self.brand_input))
        self.brand_input.lineEdit().returnPressed.connect(lambda: self.focus_next_field(self.formula_input))
        self.formula_input.returnPressed.connect(lambda: self.focus_next_field(self.pack_size_input))
        self.pack_size_input.returnPressed.connect(lambda: self.focus_next_field(self.rack_input))
        self.rack_input.returnPressed.connect(lambda: self.focus_next_field(self.batch_input))
        self.batch_input.returnPressed.connect(lambda: self.focus_next_field(self.expiry_input))
        self.expiry_input.returnPressed.connect(lambda: self.focus_next_field(self.pack_price_input))
        self.pack_price_input.returnPressed.connect(lambda: self.focus_next_field(self.margin_input))
        self.margin_input.returnPressed.connect(lambda: self.focus_next_field(self.quantity_input))
        self.quantity_input.returnPressed.connect(lambda: self.focus_next_field(self.code_input))
        self.unit_cost_input.returnPressed.connect(lambda: self.focus_next_field(self.code_input))
        self.code_input.returnPressed.connect(lambda: self.focus_next_field(self.reorder_level))
        self.reorder_level.returnPressed.connect(self.save_button.click)
    

    def on_item_selected(self, text):
        text = text.strip()

        index = self.name_input.findText(text, Qt.MatchFixedString)
        if index < 0:
            return

        self.name_input.setCurrentIndex(index)
        self.name_input.lineEdit().setText(text)

        data = self.name_input.itemData(index)
        print("Selected text is:", text, data)

        # Existing product selected: autofill known details and continue at batch entry.
        if data is not None:
            try:
                product_id = int(data)
            except (TypeError, ValueError):
                product_id = None

            if product_id is not None:
                self.autofill_existing_product_details(product_id)
                self.batch_input.setFocus()
                self.batch_input.selectAll()

    def on_name_index_activated(self, index):
        if index < 0:
            return
        text = self.name_input.itemText(index).strip()
        if text:
            self.on_item_selected(text)

    def on_name_enter_pressed(self):
        text = self.name_input.lineEdit().text().strip()
        if not text:
            self.focus_next_field(self.dosage)
            return

        index = self.name_input.findText(text, Qt.MatchFixedString)
        if index >= 0 and self.name_input.itemData(index) is not None:
            self.on_item_selected(text)
        else:
            # Product not found: keep existing new-product flow.
            self.focus_next_field(self.dosage)


    def autofill_existing_product_details(self, product_id):
        query = QSqlQuery()
        query.prepare("""
            SELECT
                generic_name,
                manufacturer_id,
                strength,
                discount_group_id,
                tax_group_id,
                COALESCE(rack, ''),
                (
                    SELECT pack_size
                    FROM price_pack
                    WHERE product_id = product.id
                    ORDER BY is_default DESC, id DESC
                    LIMIT 1
                ) AS pack_size,
                (
                    SELECT pack_price
                    FROM price_pack
                    WHERE product_id = product.id
                    ORDER BY is_default DESC, id DESC
                    LIMIT 1
                ) AS pack_price,
                (
                    SELECT margin_percent
                    FROM price_pack
                    WHERE product_id = product.id
                    ORDER BY is_default DESC, id DESC
                    LIMIT 1
                ) AS margin_percent
            FROM product
            WHERE id = ?
            LIMIT 1
        """)
        query.addBindValue(product_id)

        if not query.exec() or not query.next():
            print("Failed to load selected product details:", query.lastError().text())
            return

        generic_name = str(query.value(0) or "").strip()
        manufacturer_id = query.value(1)
        strength = str(query.value(2) or "").strip()
        discount_group_id = query.value(3)
        tax_group_id = query.value(4)
        rack = str(query.value(5) or "").strip()
        pack_size = query.value(6)
        pack_price = query.value(7)
        margin_percent = query.value(8)

        # Autofill formula if available, otherwise clear stale text.
        self.formula_input.setText(generic_name)
        self.dosage.setText(strength)
        self.rack_input.setText(rack)

        # Autofill pack size when available and clear stale value otherwise.
        self.pack_size_input.setText(str(pack_size) if pack_size not in (None, "") else "")

        # Autofill pack sale price when available and clear stale value otherwise.
        self.pack_price_input.setText(str(pack_price) if pack_price not in (None, "") else "")
        if margin_percent not in (None, ""):
            self.margin_input.setText(f"{float(margin_percent or self.DEFAULT_MARGIN_PERCENT):.2f}")
        else:
            self.margin_input.setText(f"{self.DEFAULT_MARGIN_PERCENT:.1f}")
        self.calculate_pack_cost_from_margin()

        # Autofill manufacturer when available.
        if manufacturer_id is None:
            self.brand_input.setCurrentIndex(-1)
        else:
            idx = self.brand_input.findData(manufacturer_id)
            if idx >= 0:
                self.brand_input.setCurrentIndex(idx)
            else:
                # Manufacturer might be missing from current combobox list (e.g. inactive).
                m_query = QSqlQuery()
                m_query.prepare("SELECT name FROM manufacturer WHERE id = ? LIMIT 1")
                m_query.addBindValue(manufacturer_id)
                if m_query.exec() and m_query.next():
                    m_name = str(m_query.value(0) or "").strip()
                    if m_name:
                        self.brand_input.addItem(m_name, manufacturer_id)
                        self.brand_input.setCurrentIndex(self.brand_input.count() - 1)

        discount_index = self.discount_group_combo.findData(discount_group_id)
        self.discount_group_combo.setCurrentIndex(discount_index if discount_index >= 0 else 0)
        tax_index = self.tax_group_combo.findData(tax_group_id)
        self.tax_group_combo.setCurrentIndex(tax_index if tax_index >= 0 else 0)
    
    
    
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

    def _float_or_default(self, value, default=0.0):
        try:
            text = str(value or "").strip()
            if not text:
                return float(default)
            return float(text)
        except Exception:
            return float(default)

    def calculate_pack_cost_from_margin(self):
        sale_price = self._float_or_default(self.pack_price_input.text(), 0.0)
        margin_percent = self._float_or_default(self.margin_input.text(), self.DEFAULT_MARGIN_PERCENT)
        if sale_price <= 0:
            self.unit_cost_input.clear()
            return
        margin_percent = max(0.0, min(99.99, margin_percent))
        pack_cost = sale_price * (1 - (margin_percent / 100.0))
        self.unit_cost_input.setText(f"{pack_cost:.2f}")

    
    

    @Permissions.require_permission('product.create')
    def save_product(self):
        
        print("Going to save the product")

        # ---------- Read input ----------
        existing_product_id = self.name_input.currentData()
        display_name = self.name_input.currentText().strip()
        
        print(display_name, existing_product_id)

        manufacturer_id = self.brand_input.currentData()
        discount_group_id = self.discount_group_combo.currentData()
        tax_group_id = self.tax_group_combo.currentData()
        generic_name = self.formula_input.text().strip() or None
        code = self.code_input.text().strip() or None
        rack = self.rack_input.text().strip()

        qty_text = self.quantity_input.text().strip()
        batch_no = self.batch_input.text().strip() or None
        pack_size = self.pack_size_input.text().strip() or None
        pack_price_text = self.pack_price_input.text().strip()
        margin_text = self.margin_input.text().strip()
        reorder_level = self.reorder_level.text()
        quantity = float(qty_text) if qty_text else 0.0
        pack_price = float(pack_price_text) if pack_price_text else 0.0
        margin_percent = self._float_or_default(margin_text, self.DEFAULT_MARGIN_PERCENT)
        pack_cost_entered = pack_price * (1 - (margin_percent / 100.0)) if pack_price > 0 else None
        reorder_level = float(reorder_level) if reorder_level else 0
        

        # ---------- Expiry ----------
        expiry_date = None
        expiry_text = self.expiry_input.text().strip()
        expiry_collapsed = expiry_text.replace("_", "").replace(" ", "")
        if not expiry_collapsed or expiry_collapsed in {"-", "--"}:
            expiry_text = ""
        if expiry_text:
            parsed_expiry = self.parse_expiry_month_year(expiry_text)
            if parsed_expiry is None:
                AppMessageBox.information(None, "Missing Data", "Expiry must be in MM-YY format, for example 04-26.")
                self.expiry_input.setFocus()
                self.expiry_input.selectAll()
                return
            expiry_date = parsed_expiry.toString("yyyy-MM-dd")

        # ---------- Validation ----------
        if not display_name:
            AppMessageBox.information(None, "Missing Data", "Product name is required.")
            return

        if not qty_text:
            AppMessageBox.information(None, "Missing Data", "Quantity is required.")
            return

        if quantity < 0:
            AppMessageBox.information(None, "Missing Data", "Quantity cannot be less than 0.")
            return

        if not pack_size:
            AppMessageBox.information(None, "Missing Data", "Pack size is required.")
            return

        try:
            pack_size_num = float(pack_size)
        except Exception:
            AppMessageBox.information(None, "Missing Data", "Pack size must be a valid number.")
            return

        if pack_size_num <= 0:
            AppMessageBox.information(None, "Missing Data", "Pack size must be greater than 0.")
            return

        if not pack_price_text:
            AppMessageBox.information(None, "Missing Data", "Sale price is required.")
            return

        if pack_price <= 0:
            AppMessageBox.information(None, "Missing Data", "Sale price must be greater than 0.")
            return

        if margin_percent < 0 or margin_percent >= 100:
            AppMessageBox.information(None, "Missing Data", "Margin % must be between 0 and 99.99.")
            self.margin_input.setFocus()
            self.margin_input.selectAll()
            return

        db = QSqlDatabase.database()
        if not db.transaction():
            AppMessageBox.information(None, "Error", "Failed to start transaction.")
            return

        try:
            # ==================================================
            # 1. Resolve product_id
            # ==================================================
            created_new_product = False
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
                        rack,
                        manufacturer_id,
                        discount_group_id,
                        tax_group_id,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                product_query.addBindValue(rack)
                product_query.addBindValue(manufacturer_id)
                product_query.addBindValue(discount_group_id)
                product_query.addBindValue(tax_group_id)
                product_query.addBindValue("used")

                if not product_query.exec():
                    raise Exception(product_query.lastError().text())

                product_id = int(product_query.lastInsertId())
                created_new_product = True

            # Ensure product is marked as used for both existing and new saves.
            status_query = QSqlQuery(db)
            status_query.prepare("""
                UPDATE product
                SET
                    status = 'used',
                    code = ?,
                    generic_name = ?,
                    manufacturer_id = ?,
                    discount_group_id = ?,
                    tax_group_id = ?,
                    rack = ?
                WHERE id = ?
            """)
            status_query.addBindValue(code)
            status_query.addBindValue(generic_name)
            status_query.addBindValue(manufacturer_id)
            status_query.addBindValue(discount_group_id)
            status_query.addBindValue(tax_group_id)
            status_query.addBindValue(rack)
            status_query.addBindValue(product_id)
            if not status_query.exec():
                raise Exception(status_query.lastError().text())

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
            unit_cost = round(pack_cost_entered / pack_size_num, 6) if pack_cost_entered and pack_size_num > 0 else pack_cost_entered
            batch_query.addBindValue(unit_cost)
            batch_query.addBindValue("OPENING")

            if not batch_query.exec():
                raise Exception(batch_query.lastError().text())
            batch_id = int(batch_query.lastInsertId())
            self.recent_entry_status[batch_id] = "New" if created_new_product else "Existing"

            print("Batch stored")

            # ==================================================
            # 3. Save or update current default price_pack
            # ==================================================
            default_price_pack_id = None
            existing_default_query = QSqlQuery(db)
            existing_default_query.prepare("""
                SELECT id
                FROM price_pack
                WHERE product_id = ?
                ORDER BY is_default DESC, id DESC
                LIMIT 1
            """)
            existing_default_query.addBindValue(product_id)
            if not existing_default_query.exec():
                raise Exception(existing_default_query.lastError().text())
            if existing_default_query.next():
                default_price_pack_id = existing_default_query.value(0)

            if default_price_pack_id is not None:
                normalize_default_query = QSqlQuery(db)
                normalize_default_query.prepare("""
                    UPDATE price_pack
                    SET is_default = 0
                    WHERE product_id = ?
                      AND id <> ?
                """)
                normalize_default_query.addBindValue(product_id)
                normalize_default_query.addBindValue(default_price_pack_id)
                if not normalize_default_query.exec():
                    raise Exception(normalize_default_query.lastError().text())

                price_query = QSqlQuery(db)
                price_query.prepare("""
                    UPDATE price_pack
                    SET pack_size = ?, pack_price = ?, margin_percent = ?, reorder_level = ?, is_default = 1
                    WHERE id = ?
                """)
                price_query.addBindValue(pack_size)
                price_query.addBindValue(pack_price)
                price_query.addBindValue(margin_percent)
                price_query.addBindValue(reorder_level)
                price_query.addBindValue(default_price_pack_id)
            else:
                price_query = QSqlQuery(db)
                price_query.prepare("""
                    INSERT INTO price_pack (product_id, pack_size, pack_price, margin_percent, reorder_level, is_default)
                    VALUES (?, ?, ?, ?, ?, 1)
                """)
                price_query.addBindValue(product_id)
                price_query.addBindValue(pack_size)
                price_query.addBindValue(pack_price)
                price_query.addBindValue(margin_percent)
                price_query.addBindValue(reorder_level)

            if not price_query.exec():
                raise Exception(price_query.lastError().text())

            print("Price stored")

            # ==================================================
            # 4. Commit
            # ==================================================
            if not db.commit():
                raise Exception("Transaction commit failed.")

            AppMessageBox.information(None, "Success", "Product saved successfully.")
            self.refresh_recent_products_table(highlight_batch_id=batch_id)
            self.clear_product_fields()

        except Exception as e:
            db.rollback()
            AppMessageBox.information(None, "Failed", str(e))

    

    def clear_product_fields(self):

        self.dosage.clear()
        self.name_input.setCurrentIndex(-1)
        self.name_input.lineEdit().clear()
        self.code_input.clear()
        self.brand_input.setCurrentIndex(-1)
        self.brand_input.lineEdit().clear()
        self.pack_size_input.clear()
        self.rack_input.clear()
        
        self.quantity_input.clear()
        
        self.formula_input.clear()
        self.batch_input.clear()
        self.expiry_input.clear()
        
        self.unit_cost_input.clear()
        self.pack_price_input.clear()
        self.margin_input.setText(f"{self.DEFAULT_MARGIN_PERCENT:.1f}")
        self.unit_price_input.setText('0.0')
        self.discount_group_combo.setCurrentIndex(0)
        self.tax_group_combo.setCurrentIndex(0)
        self.reorder_level.clear()
        self.calculate_pack_cost_from_margin()
        self.name_input.setFocus()
        if self.name_input.lineEdit() is not None:
            self.name_input.lineEdit().selectAll()

    def confirm_clear_fields(self):
        _, accepted = AppMessageBox.confirm(
            self,
            "Clear Product Form",
            "Clear the current product entry fields?",
            confirm_label="Clear Fields",
            cancel_label="Keep Editing",
        )
        if accepted:
            self.clear_product_fields()
        
        
    
    
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
            AppMessageBox.critical(self, "DB Error", "Database is not open.")
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
            AppMessageBox.critical(
                self,
                "Import Error",
                f"Missing required columns:\n{', '.join(missing)}"
            )
            return

        if not db.transaction():
            AppMessageBox.critical(self, "DB Error", "Could not start transaction.")
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
                        rack,
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
                query.addBindValue("")
                query.addBindValue(manufacturer_id)

                if not query.exec():
                    errors.append(f"Row {row + 1}: {query.lastError().text()}")
                    continue

                inserted_count += 1

            except Exception as e:
                errors.append(f"Row {row + 1}: {str(e)}")

        if errors:
            db.rollback()
            AppMessageBox.warning(
                self,
                "Import Failed",
                "\n".join(errors[:20]) + ("\n..." if len(errors) > 20 else "")
            )
            return

        if not db.commit():
            db.rollback()
            AppMessageBox.critical(self, "DB Error", "Failed to commit import.")
            return

        AppMessageBox.information(
            self,
            "Import Successful",
            f"Imported {inserted_count} products successfully."
        )

        super().accept()
    
    

   
        
        
        
        
        
         
import math
from PySide6.QtWidgets import QDialog, QDialogButtonBox
from utilities.app_messagebox import AppMessageBox

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
